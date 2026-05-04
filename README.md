# lsgpu

List GPUs with details, outputs, and connected monitors.

Like `lscpu`, `lsusb`, `lspci` — but for graphics cards.

A useful CLI tool for Linux users and admins. Zero-dependency — no CUDA, no ROCm, no pycuda needed.

## Features

- **GPU details**: name, driver, PCI address, VRAM
- **NVIDIA stats**: utilization, memory, temperature, power draw (via nvidia-smi)
- **Output mapping**: each port mapped to its connected monitor via EDID
- **Monitor identification**: manufacturer, model, serial, diagonal size
- **JSON output** for scripting
- No external Python dependencies, works with Python 3.6+

## Installation

```bash
sudo cp lsgpu.py /usr/local/bin/lsgpu
sudo chmod +x /usr/local/bin/lsgpu
```

## Usage

```bash
lsgpu              # Full output
lsgpu --short      # Compact one-line-per-GPU
lsgpu --json       # JSON output
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

- Python 3.6+
- Linux with `/sys/class/drm`
- `lspci` (from pciutils)
- `nvidia-smi` (optional, for NVIDIA stats)

## License

GPL-2.0. See [LICENSE](LICENSE) for the full text.
