#!/usr/bin/env python3
"""
lsgpu - List GPUs with details, outputs, and connected monitors.

Similar to lscpu, lsusb, lspci but for graphics cards.
Shows GPU name, driver, VRAM, utilization, temperature, power draw,
and maps each output port to the connected monitor via EDID.

Usage:
    lsgpu              Full output
    lsgpu --json       JSON output for scripting
    lsgpu --short      Compact one-line-per-GPU output

License: GPL-2.0
"""

import argparse
import glob as glob_mod
import json as json_mod
import math
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict

__version__ = "0.1.0"

# PNP manufacturer IDs (subset of the official PNP ID registry)
# Source: https://uefi.org/PNP_ID_List
# History: https://github.com/onkoe/pnpid/blob/main/list.csv
# See also: /usr/share/hwdata/pnp.ids (hwdata package)
PNP_MANUFACTURERS = {
    "AAC": "AcerView", "ACR": "Acer", "AOC": "AOC", "AUS": "ASUS",
    "BNQ": "BenQ", "CMN": "Chimei Innolux", "DEL": "Dell",
    "ENC": "Eizo", "FUS": "Fujitsu Siemens", "GSM": "LG (GoldStar)",
    "HPN": "HP", "HWP": "HP", "IVM": "Iiyama", "LEN": "Lenovo",
    "LGD": "LG Display", "MAX": "Maxdata", "MEI": "Panasonic",
    "MEL": "Mitsubishi", "NEC": "NEC", "PHL": "Philips",
    "SAM": "Samsung", "SDC": "Samsung Display", "SNY": "Sony",
    "SHP": "Sharp", "TSB": "Toshiba", "VSC": "ViewSonic",
    "HSD": "HannStar", "BOE": "BOE", "AUO": "AU Optronics",
    "INL": "InnoLux", "MSI": "MSI", "GBT": "Gigabyte",
}

# Sparkline block characters (8 levels)
SPARK_CHARS = "▁▂▃▄▅▆▇█"


@dataclass
class Monitor:
    """Monitor connected to a GPU output."""
    manufacturer: str = ""
    model: str = ""
    serial: str = ""
    diagonal_inches: int = 0


@dataclass
class Output:
    """A GPU output port."""
    name: str = ""
    connected: bool = False
    monitor: Optional[Monitor] = None


@dataclass
class NvidiaStats:
    """Runtime stats from nvidia-smi."""
    gpu_util: int = 0        # percent
    mem_used: int = 0        # MB
    mem_total: int = 0       # MB
    temperature: int = 0     # celsius
    power_draw: float = 0.0  # watts


@dataclass
class AmdStats:
    """Runtime stats from sysfs for AMD GPUs."""
    gpu_util: int = 0        # percent
    mem_used: int = 0        # bytes
    mem_total: int = 0       # bytes
    temperature: int = 0     # celsius
    power_draw: float = 0.0  # watts

    @property
    def mem_used_mb(self) -> int:
        return self.mem_used // (1024 * 1024) if self.mem_used else 0

    @property
    def mem_total_mb(self) -> int:
        return self.mem_total // (1024 * 1024) if self.mem_total else 0


@dataclass
class GpuProcess:
    """A process running on a GPU."""
    pid: int = 0
    name: str = ""
    used_memory_mb: int = 0


@dataclass
class GPU:
    """Represents a graphics card."""
    card: str = ""           # card0, card1, ...
    name: str = ""           # full GPU name
    pci_address: str = ""
    driver: str = ""
    vram_bytes: int = 0
    outputs: List[Output] = field(default_factory=list)
    nvidia_stats: Optional[NvidiaStats] = None
    amd_stats: Optional[AmdStats] = None
    processes: List[GpuProcess] = field(default_factory=list)

    @property
    def vram_gb(self) -> float:
        return self.vram_bytes / (1024 ** 3) if self.vram_bytes else 0

    @property
    def connected_outputs(self) -> List[Output]:
        return [o for o in self.outputs if o.connected]

    @property
    def gpu_util(self) -> Optional[int]:
        if self.nvidia_stats:
            return self.nvidia_stats.gpu_util
        if self.amd_stats:
            return self.amd_stats.gpu_util
        return None


def _load_overrides():
    """Load overrides from config."""
    home = os.environ.get("HOME", os.path.expanduser("~"))
    paths = [
        os.path.join(home, ".config/lsdisplay/overrides.json"),
        os.path.expanduser("~/.config/lsdisplay/overrides.json"),
        "/etc/lsdisplay/overrides.json",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p) as f:
                    import json
                    data = json.load(f)
                return {k: v for k, v in data.items() if not k.startswith("_")}
            except Exception:
                pass
    return {}

_OVERRIDES = None
def get_overrides():
    global _OVERRIDES
    if _OVERRIDES is None:
        _OVERRIDES = _load_overrides()
    return _OVERRIDES


def parse_edid(data: bytes) -> Monitor:
    """Parse EDID binary data to identify a monitor."""
    if len(data) < 128:
        return Monitor()

    m1, m2 = data[8], data[9]
    mfg_id = chr(((m1 >> 2) & 0x1F) + 64) + chr(((m1 & 0x3) << 3 | (m2 >> 5)) + 64) + chr((m2 & 0x1F) + 64)

    name = ""
    serial_str = ""
    w_mm, h_mm = 0, 0
    for i in range(4):
        offset = 54 + i * 18
        if offset + 18 > len(data):
            break
        if data[offset] != 0 or data[offset + 1] != 0:
            # Detailed timing — extract physical size in mm
            w = data[offset + 12] | ((data[offset + 14] & 0xF0) << 4)
            h = data[offset + 13] | ((data[offset + 14] & 0x0F) << 8)
            if w > 0 and h > 0 and w_mm == 0:
                w_mm, h_mm = w, h
        else:
            tag = data[offset + 3]
            text = data[offset + 5:offset + 18].decode("ascii", errors="replace").strip().rstrip("\n\r")
            if tag == 0xFC:
                name = text
            elif tag == 0xFF:
                serial_str = text

    # Fallback to bytes 21-22
    if w_mm == 0:
        w_mm, h_mm = data[21] * 10, data[22] * 10

    diagonal = round(math.sqrt(w_mm**2 + h_mm**2) / 25.4) if w_mm and h_mm else 0

    # Apply overrides
    product_code = data[10] | (data[11] << 8)
    key = f"{mfg_id}{product_code:04X}"
    overrides = get_overrides()
    if key in overrides:
        ov = overrides[key]
        if "model" in ov:
            name = ov["model"]
        if "diagonal" in ov:
            diagonal = ov["diagonal"]
        if "serial" in ov:
            serial_str = ov["serial"]

    return Monitor(
        manufacturer=PNP_MANUFACTURERS.get(mfg_id, mfg_id),
        model=name,
        serial=serial_str,
        diagonal_inches=diagonal,
    )


def get_nvidia_stats(pci_addr: str) -> Optional[NvidiaStats]:
    """Get runtime stats from nvidia-smi for a given PCI address."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
             "--format=csv,noheader,nounits", "-i", pci_addr],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        parts = [p.strip() for p in out.split(",")]
        if len(parts) >= 5:
            return NvidiaStats(
                gpu_util=int(parts[0]),
                mem_used=int(parts[1]),
                mem_total=int(parts[2]),
                temperature=int(parts[3]),
                power_draw=float(parts[4]),
            )
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        pass
    return None


def _read_sysfs_int(path: str, default: int = 0) -> int:
    """Read an integer from a sysfs file."""
    try:
        with open(path) as f:
            return int(f.read().strip())
    except (IOError, ValueError, PermissionError):
        return default


def get_amd_stats(card_path: str) -> Optional[AmdStats]:
    """Get runtime stats from sysfs for an AMD GPU."""
    device_path = os.path.join(card_path, "device")

    gpu_busy = os.path.join(device_path, "gpu_busy_percent")
    if not os.path.exists(gpu_busy):
        return None

    gpu_util = _read_sysfs_int(gpu_busy)
    mem_used = _read_sysfs_int(os.path.join(device_path, "mem_info_vram_used"))
    mem_total = _read_sysfs_int(os.path.join(device_path, "mem_info_vram_total"))

    # Temperature: find hwmon directory
    temperature = 0
    power_draw = 0.0
    hwmon_dirs = glob_mod.glob(os.path.join(device_path, "hwmon", "hwmon*"))
    if hwmon_dirs:
        hwmon = hwmon_dirs[0]
        temp_raw = _read_sysfs_int(os.path.join(hwmon, "temp1_input"))
        temperature = temp_raw // 1000  # millidegrees to degrees

        power_raw = _read_sysfs_int(os.path.join(hwmon, "power1_average"))
        power_draw = power_raw / 1_000_000.0  # microwatts to watts

    return AmdStats(
        gpu_util=gpu_util,
        mem_used=mem_used,
        mem_total=mem_total,
        temperature=temperature,
        power_draw=power_draw,
    )


def get_gpu_processes() -> Dict[str, List[GpuProcess]]:
    """Get processes running on NVIDIA GPUs. Returns dict keyed by GPU index."""
    processes: Dict[str, List[GpuProcess]] = {}
    try:
        out = subprocess.check_output(
            ["nvidia-smi",
             "--query-compute-apps=gpu_uuid,pid,name,used_gpu_memory",
             "--format=csv,noheader,nounits"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        if not out:
            return processes

        # We need to map GPU UUID to PCI address. Get the mapping.
        uuid_out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=gpu_uuid,pci.bus_id",
             "--format=csv,noheader"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        uuid_to_pci = {}
        for line in uuid_out.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 2:
                uuid_to_pci[parts[0]] = parts[1].lower()

        for line in out.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 4:
                gpu_uuid = parts[0]
                pci = uuid_to_pci.get(gpu_uuid, gpu_uuid)
                proc = GpuProcess(
                    pid=int(parts[1]),
                    name=parts[2],
                    used_memory_mb=int(parts[3]) if parts[3].strip() else 0,
                )
                processes.setdefault(pci, []).append(proc)
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        pass

    # Also try simpler approach: query by pid,name,used_gpu_memory without UUID
    if not processes:
        try:
            out = subprocess.check_output(
                ["nvidia-smi",
                 "--query-compute-apps=pid,name,used_gpu_memory",
                 "--format=csv,noheader,nounits"],
                text=True, stderr=subprocess.DEVNULL
            ).strip()
            if out:
                for line in out.splitlines():
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 3:
                        proc = GpuProcess(
                            pid=int(parts[0]),
                            name=parts[1],
                            used_memory_mb=int(parts[2]) if parts[2].strip() else 0,
                        )
                        # Put under empty key (will be assigned to first GPU)
                        processes.setdefault("", []).append(proc)
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
            pass

    return processes


def _sparkline(values: List[int], max_val: int = 100) -> str:
    """Generate a sparkline string from a list of values."""
    if not values:
        return ""
    chars = []
    for v in values:
        idx = int(v / max_val * (len(SPARK_CHARS) - 1))
        idx = max(0, min(idx, len(SPARK_CHARS) - 1))
        chars.append(SPARK_CHARS[idx])
    return "".join(chars)


def scan_gpus() -> List[GPU]:
    """Scan /sys/class/drm for GPUs and their outputs."""
    drm_dir = "/sys/class/drm"
    if not os.path.isdir(drm_dir):
        return []

    # Get GPU processes up front
    all_processes = get_gpu_processes()

    gpus = []
    for entry in sorted(os.listdir(drm_dir)):
        if not re.match(r"^card\d+$", entry):
            continue

        card_path = os.path.join(drm_dir, entry)
        device_link = os.path.join(card_path, "device")

        gpu = GPU(card=entry)

        # PCI address and GPU name
        try:
            pci_addr = os.path.basename(os.readlink(device_link))
            gpu.pci_address = pci_addr
            lspci_out = subprocess.check_output(
                ["lspci", "-s", pci_addr], text=True, stderr=subprocess.DEVNULL
            ).strip()
            gpu.name = re.sub(r"^[0-9a-f:.]+\s+\S+\s+\S+\s+controller:\s*", "", lspci_out, flags=re.IGNORECASE)
        except (OSError, subprocess.CalledProcessError):
            pass

        # Driver
        driver_link = os.path.join(device_link, "driver")
        if os.path.islink(driver_link):
            gpu.driver = os.path.basename(os.readlink(driver_link))

        # VRAM
        vram_file = os.path.join(device_link, "mem_info_vram_total")
        if os.path.exists(vram_file):
            try:
                with open(vram_file) as f:
                    gpu.vram_bytes = int(f.read().strip())
            except (IOError, ValueError):
                pass

        # NVIDIA stats
        if gpu.driver == "nvidia":
            gpu.nvidia_stats = get_nvidia_stats(gpu.pci_address)
            # Assign processes by matching PCI address suffix (bus:slot.func)
            # sysfs: "0000:82:00.0", nvidia-smi: "00000000:82:00.0"
            pci_suffix = gpu.pci_address.lower().split(":")[-2] + ":" + gpu.pci_address.lower().split(":")[-1]
            for key, procs in all_processes.items():
                if key == "" and len(all_processes) == 1:
                    gpu.processes = procs
                elif key:
                    key_suffix = key.lower().split(":")[-2] + ":" + key.lower().split(":")[-1]
                    if pci_suffix == key_suffix:
                        gpu.processes = procs
                        break

        # AMD stats
        if gpu.driver in ("amdgpu", "radeon"):
            gpu.amd_stats = get_amd_stats(card_path)

        # Scan outputs
        for sub in sorted(os.listdir(drm_dir)):
            if sub.startswith(entry + "-"):
                port_name = sub[len(entry) + 1:]
                port_dir = os.path.join(drm_dir, sub)

                connected = False
                status_file = os.path.join(port_dir, "status")
                try:
                    with open(status_file) as f:
                        connected = f.read().strip() == "connected"
                except (IOError, PermissionError):
                    pass

                monitor = None
                edid_file = os.path.join(port_dir, "edid")
                if os.path.exists(edid_file):
                    try:
                        with open(edid_file, "rb") as f:
                            edid_data = f.read()
                        if len(edid_data) >= 128:
                            connected = True
                            monitor = parse_edid(edid_data)
                    except (IOError, PermissionError):
                        pass

                gpu.outputs.append(Output(name=port_name, connected=connected, monitor=monitor))

        gpus.append(gpu)

    return gpus


def _format_stats_line(gpu: GPU) -> str:
    """Format the stats portion of a GPU details line."""
    if gpu.nvidia_stats:
        s = gpu.nvidia_stats
        return f" | GPU:{s.gpu_util}% MEM:{s.mem_used}/{s.mem_total}MB {s.temperature}°C {s.power_draw:.1f}W"
    if gpu.amd_stats:
        s = gpu.amd_stats
        return f" | GPU:{s.gpu_util}% MEM:{s.mem_used_mb}/{s.mem_total_mb}MB {s.temperature}°C {s.power_draw:.1f}W"
    return ""


def print_gpus(gpus: List[GPU], show_all: bool = False):
    """Print GPU information."""
    print("GRAPHICS CARDS")
    print("=" * 14)
    print()

    for gpu in gpus:
        print(f"  {gpu.card}: {gpu.name}")

        # Details line
        details = f"         Driver: {gpu.driver}"
        if gpu.vram_bytes:
            details += f" | VRAM: {gpu.vram_gb:.0f} GB"
        details += _format_stats_line(gpu)
        print(details)

        # Outputs
        outputs_to_show = gpu.outputs if show_all else [o for o in gpu.outputs if o.connected]
        for out in outputs_to_show:
            if out.connected and out.monitor:
                m = out.monitor
                diag = f' {m.diagonal_inches}"' if m.diagonal_inches else ""
                model = m.model if m.model.upper() != m.manufacturer.upper() else ""
                print(f"    \u251c\u2500 {out.name}: connected \u2190 {m.manufacturer} {model}{diag}".rstrip())
            elif out.connected:
                print(f"    \u251c\u2500 {out.name}: connected")
            else:
                print(f"    \u251c\u2500 {out.name}: -")

        # GPU processes
        if gpu.processes:
            print(f"    Processes:")
            for proc in gpu.processes:
                pname = os.path.basename(proc.name) if proc.name else "?"
                print(f"      PID {proc.pid}  {pname}  {proc.used_memory_mb}MB")

        print()

    # Summary
    total_gpu = len(gpus)
    total_out = sum(len(g.connected_outputs) for g in gpus)
    print(f"Total: {total_gpu} GPU(s), {total_out} output(s) connected")


def print_short(gpus: List[GPU]):
    """Print compact one-line-per-GPU output."""
    for gpu in gpus:
        vram = f"{gpu.vram_gb:.0f}GB" if gpu.vram_bytes else ""
        n_conn = len(gpu.connected_outputs)
        n_total = len(gpu.outputs)
        stats = ""
        if gpu.nvidia_stats:
            s = gpu.nvidia_stats
            stats = f" [{s.gpu_util}% {s.temperature}\u00b0C {s.power_draw:.0f}W]"
        elif gpu.amd_stats:
            s = gpu.amd_stats
            stats = f" [{s.gpu_util}% {s.temperature}\u00b0C {s.power_draw:.0f}W]"
        print(f"  {gpu.card}: {gpu.name} | {gpu.driver} {vram} | {n_conn}/{n_total} outputs{stats}")


def watch_gpus(interval=2):
    """Monitor GPU stats in real-time with sparkline history."""
    import time
    from datetime import datetime

    # History: card -> list of utilization values (last 20)
    history: Dict[str, List[int]] = {}
    max_history = 20

    print("GPU MONITOR (Ctrl+C to stop)")
    print("=" * 27)
    print()

    # First clear, then just move cursor home (no flash)
    print("\033[2J\033[H", end="")
    try:
        while True:
            print("\033[H", end="")  # cursor home, no clear
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"GPU MONITOR \u2014 {ts} (Ctrl+C to stop)    ")
            print()

            gpus = scan_gpus()
            for gpu in gpus:
                name_short = gpu.name.split("[")[-1].rstrip("]") if "[" in gpu.name else gpu.name

                # Get stats (nvidia or amd)
                has_stats = gpu.nvidia_stats or gpu.amd_stats
                if not has_stats:
                    print(f"  {gpu.card} {name_short} ({gpu.driver})")
                    continue

                if gpu.nvidia_stats:
                    util = gpu.nvidia_stats.gpu_util
                    mem_used = gpu.nvidia_stats.mem_used
                    mem_total = gpu.nvidia_stats.mem_total
                    temp = gpu.nvidia_stats.temperature
                    power = gpu.nvidia_stats.power_draw
                else:
                    util = gpu.amd_stats.gpu_util
                    mem_used = gpu.amd_stats.mem_used_mb
                    mem_total = gpu.amd_stats.mem_total_mb
                    temp = gpu.amd_stats.temperature
                    power = gpu.amd_stats.power_draw

                # Update history
                if gpu.card not in history:
                    history[gpu.card] = []
                history[gpu.card].append(util)
                if len(history[gpu.card]) > max_history:
                    history[gpu.card] = history[gpu.card][-max_history:]

                spark = _sparkline(history[gpu.card])

                # GPU utilization bar
                bar_w = 30
                gpu_filled = int(util / 100 * bar_w)
                gpu_bar = "\u2588" * gpu_filled + "\u2591" * (bar_w - gpu_filled)

                # Memory bar
                mem_pct = mem_used / mem_total * 100 if mem_total else 0
                mem_filled = int(mem_pct / 100 * bar_w)
                mem_bar = "\u2588" * mem_filled + "\u2591" * (bar_w - mem_filled)

                print(f"  {gpu.card} {name_short}")
                print(f"    GPU  [{gpu_bar}] {util:3d}%  {spark}    ")
                print(f"    MEM  [{mem_bar}] {mem_used}/{mem_total}MB ({mem_pct:.0f}%)    ")
                print(f"    TEMP {temp}\u00b0C   POWER {power:.1f}W    ")

                # Show processes in watch mode too
                if gpu.processes:
                    for proc in gpu.processes:
                        pname = os.path.basename(proc.name) if proc.name else "?"
                        print(f"    \u2514 PID {proc.pid}  {pname}  {proc.used_memory_mb}MB    ")
                print()

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


def main():
    parser = argparse.ArgumentParser(
        prog="lsgpu",
        description="List graphics cards with driver, VRAM, utilization, and connected monitors.",
        epilog="""examples:
  lsgpu              list all GPUs with connected outputs
  lsgpu -a           list all GPUs with all outputs (including disconnected)
  lsgpu --short      compact one-line-per-GPU output
  lsgpu --json       JSON output for scripting
  lsgpu --watch      real-time GPU monitoring (Ctrl+C to stop)
  lsgpu --json | jq '.[].name'

info shown per GPU:
  name, PCI address, driver, VRAM
  NVIDIA: utilization %, memory, temperature, power draw
  AMD: utilization %, memory, temperature, power draw (via sysfs)
  output ports with connected monitor (manufacturer, model, size from EDID)

source: https://github.com/AGuyMarc/lsgpu
license: GPL-2.0""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--json", action="store_true", help="output as JSON (for scripting)")
    parser.add_argument("--short", "-s", action="store_true", help="compact one-line-per-GPU output")
    parser.add_argument("--all", "-a", action="store_true", help="show all outputs including disconnected")
    parser.add_argument("--watch", "-w", nargs="?", const=2, type=int, metavar="SEC",
                        help="real-time monitoring (default: 2s interval)")
    parser.add_argument("--version", "-V", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()

    if args.watch is not None:
        watch_gpus(args.watch)
        return

    gpus = scan_gpus()

    if not gpus:
        print("No GPUs found.", file=sys.stderr)
        sys.exit(1)

    if args.json:
        data = []
        for gpu in gpus:
            d = {
                "card": gpu.card,
                "name": gpu.name,
                "pci_address": gpu.pci_address,
                "driver": gpu.driver,
                "vram_gb": round(gpu.vram_gb, 1),
                "outputs": [],
            }
            if gpu.nvidia_stats:
                d["nvidia_stats"] = asdict(gpu.nvidia_stats)
            if gpu.amd_stats:
                d["amd_stats"] = {
                    "gpu_util": gpu.amd_stats.gpu_util,
                    "mem_used_mb": gpu.amd_stats.mem_used_mb,
                    "mem_total_mb": gpu.amd_stats.mem_total_mb,
                    "temperature": gpu.amd_stats.temperature,
                    "power_draw": gpu.amd_stats.power_draw,
                }
            if gpu.processes:
                d["processes"] = [asdict(p) for p in gpu.processes]
            for out in gpu.outputs:
                od = {"name": out.name, "connected": out.connected}
                if out.monitor:
                    od["monitor"] = asdict(out.monitor)
                d["outputs"].append(od)
            data.append(d)
        print(json_mod.dumps(data, indent=2, ensure_ascii=False))
        return

    if args.short:
        print_short(gpus)
        return

    print_gpus(gpus, show_all=args.all)


if __name__ == "__main__":
    main()
