# lsgpus

List GPUs with details, outputs, and connected monitors.

Like `lscpu`, `lsusb`, `lspci`, `lsblk`, `lsmem` — but for graphics cards.

A useful CLI tool for Linux users and admins. Zero-dependency — just Python 3.7+ and /sys/class/drm. Reads info from standard tools (nvidia-smi/rocm-smi) when present — no CUDA, no ROCm, no pycuda needed.

> **Binary renamed in v0.2.0.** The installed command is now `lsgpus` (with a trailing `s`) instead of `lsgpu`, to avoid a name clash with the `lsgpu(1)` utility shipped by [`igt-gpu-tools`](https://gitlab.freedesktop.org/drm/igt-gpu-tools) on both Debian/Ubuntu and Arch. The GitHub repository keeps its original name (`AGuyMarc/lsgpu`).

**Companion tool:** [`lsdisplay`](https://github.com/AGuyMarc/lsdisplay) — list the connected displays/monitors that those GPUs drive.

## Features

- **GPU details**: name, driver, PCI address, VRAM
- **NVIDIA stats**: utilization, memory, temperature, power draw (via nvidia-smi)
- **Output mapping**: each port mapped to its connected monitor via EDID
- **Monitor identification**: manufacturer, model, serial, diagonal size
- **JSON output** for scripting
- No external Python dependencies, works with Python 3.7+

## Installation

### Debian / Ubuntu (.deb)

Download the `.deb` from the [Releases page](https://github.com/AGuyMarc/lsgpu/releases/latest), then:

```bash
sudo dpkg -i lsgpus_0.2.0-1_all.deb
```

The package installs `/usr/bin/lsgpus`, the man page `lsgpus(1)`, and documentation.

**Upgrading from v0.1.x** (when the package was named `lsgpu`): the new package declares `Replaces: lsgpu (<< 0.2.0)` and `Breaks: lsgpu (<< 0.2.0)`, so `dpkg -i lsgpus_0.2.0-1_all.deb` cleanly removes the old `lsgpu` package on install. If you prefer an explicit cleanup first:

```bash
sudo apt remove lsgpu
sudo dpkg -i lsgpus_0.2.0-1_all.deb
```

### Arch Linux / Manjaro (AUR)

Available in the AUR thanks to [@seraf1](https://aur.archlinux.org/account/seraf1):

```bash
yay -S lsgpu-git
```

Package page: https://aur.archlinux.org/packages/lsgpu-git

(The AUR package name may follow the binary rename to `lsgpus-git` after seraf1's next update — check the AUR page for the current name.)

### From source

```bash
git clone https://github.com/AGuyMarc/lsgpu
cd lsgpu
sudo cp lsgpu.py /usr/local/bin/lsgpus
sudo chmod +x /usr/local/bin/lsgpus
```

## Usage

```bash
lsgpus              # Full output
lsgpus --short      # Compact one-line-per-GPU
lsgpus --json       # JSON output
```

## Example output

```
GRAPHICS CARDS
==============

  card0: NVIDIA Corporation GA107 [GeForce RTX 3050 6GB] (rev a1)
         Driver: nvidia | VRAM: 6 GB | GPU:0% MEM:2077/6144MB 37°C 16.7W
    ├─ DP-4: connected ← Iiyama PL2792Q 27"
    ├─ HDMI-A-2: connected ← Iiyama PL2792Q 27"
    ├─ HDMI-A-3: connected ← Iiyama PL2792Q 27"

  card1: NVIDIA Corporation AD106 [GeForce RTX 4060 Ti] (rev a1)
         Driver: nvidia | VRAM: 16 GB | GPU:0% MEM:277/16380MB 41°C 14.9W
    ├─ DP-1: -
    ├─ DP-2: -
    ├─ DP-3: -
    ├─ HDMI-A-1: connected ← Samsung SAMSUNG 32"

  card2: Intel Corporation Arrow Lake-S [Intel Graphics] (rev 06)
         Driver: i915
    ├─ HDMI-A-4: connected ← Iiyama PL2793Q 27"
    ├─ HDMI-A-5: connected ← Samsung SAMSUNG 65"

Total: 3 GPU(s), 6 output(s) connected
```

## Requirements

- Python 3.7+
- Linux with `/sys/class/drm`
- `lspci` (from pciutils)
- `nvidia-smi` (optional, for NVIDIA stats)

## See also

Hardware enumeration `ls*` family on Linux:

- [`lsdisplay`](https://github.com/AGuyMarc/lsdisplay) — connected displays/monitors (companion to this tool)
- `lsgpu(1)` from `igt-gpu-tools` — low-level Intel Graphics Tests utility (different audience)
- `lscpu` — CPU architecture info
- `lspci` — PCI devices
- `lsusb` — USB devices
- `lsblk` — block devices (disks, partitions)
- `lsmem` — memory ranges
- `lsmod` — kernel modules
- `lsipc` — IPC facilities
- `lsns` — namespaces

## License

GPL-2.0. See [LICENSE](LICENSE) for the full text.
