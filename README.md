# lsgpus

List GPUs with details, outputs, and connected monitors.

Like `lscpu`, `lsusb`, `lspci`, `lsblk`, `lsmem` — but for graphics cards.

A useful CLI tool for Linux users and admins. Zero-dependency — just Python 3.7+ and /sys/class/drm. Reads info from standard tools (nvidia-smi/rocm-smi) when present — no CUDA, no ROCm, no pycuda needed.

> **Binary renamed in v0.2.0.** The installed command is now `lsgpus` (with a trailing `s`) instead of `lsgpu`, to avoid a name clash with the `lsgpu(1)` utility shipped by [`igt-gpu-tools`](https://gitlab.freedesktop.org/drm/igt-gpu-tools) on both Debian/Ubuntu and Arch. The GitHub repository keeps its original name (`AGuyMarc/lsgpu`).

**Companion tool:** [`lsdisplay`](https://github.com/AGuyMarc/lsdisplay) — list the connected displays/monitors that those GPUs drive.

## Why this exists

I built `lsgpus` and its companion [`lsdisplay`](https://github.com/AGuyMarc/lsdisplay) in parallel, both for the same reason: setting up my sysadmin workstation — six monitors driven by three GPUs (two NVIDIA cards plus the Arrow Lake iGPU), one of them a 65" overview TV — and finding that no single Linux command could tell me which card was driving which physical screen, doing what.

Try answering this concretely: *which* GPU is driving the 32" Samsung sitting in the bottom-right corner of my desk right now, and what is that card actually doing?

`lsgpus` answers the silicon side. It lists each card, its driver, current load, and the processes pinning its VRAM:

```
GRAPHICS CARDS
==============

  card0: NVIDIA Corporation GA107 [GeForce RTX 3050 6GB] (rev a1)
         Driver: nvidia | GPU:26% MEM:4422/6144MB 48°C 27.3W
    ├─ DP-4: connected ← Iiyama PL2792Q 27"
    ├─ HDMI-A-2: connected ← Iiyama PL2792Q 27"
    ├─ HDMI-A-3: connected ← Iiyama PL2792Q 27"

  card1: NVIDIA Corporation AD106 [GeForce RTX 4060 Ti] (rev a1)
         Driver: nvidia | GPU:0% MEM:12794/16380MB 48°C 15.1W
    ├─ HDMI-A-1: connected ← Samsung QE32Q50A 32"
    Processes:
      PID 9728  ollama  12744MB

  card2: Intel Corporation Arrow Lake-S [Intel Graphics] (rev 06)
         Driver: i915
    ├─ HDMI-A-4: connected ← Iiyama PL2793Q 27"
    ├─ HDMI-A-5: connected ← Samsung TQ65QN800DTXXC 65"

Total: 3 GPUs, 6 outputs connected
```

→ `HDMI-A-1` lives on `card1`, the RTX 4060 Ti, currently pinned by Ollama with 12.7 GB of VRAM.

`lsdisplay` answers the screen-and-cable side. It identifies each physical panel and shows where it sits on my desk:

```
CONNECTED DISPLAYS
==================

  HDMI-A-2     1440x2560+1441+0        27"  75Hz  Iiyama PL2792Q       HDMI         S/N:1152032422031   rot=left [PRIMARY]
  HDMI-A-3     1440x2560+2881+0        27"  75Hz  Iiyama PL2792Q       HDMI         S/N:1152032422030   rot=left
  HDMI-A-5     5376x3024+0+2561        65"  60Hz  Samsung TQ65QN800DTXXC HDMI       S/N:94:e6:ba:dd:9a:7a
  DP-4         1440x2560+0+0           27"  75Hz  Iiyama PL2792Q       DisplayPort  S/N:1152031921274   rot=left
  HDMI-A-4     1440x2560+4322+0        27"  75Hz  Iiyama PL2793Q       HDMI         S/N:12464540C1808   rot=left
  HDMI-A-1     1920x1080+5376+2561     32"  60Hz  Samsung QE32Q50A     HDMI         S/N:bc:45:5b:e4:e8:13

Total: 6 displays connected

LAYOUT
======

  +-------------+-------------+------------+-------------+
  |             |             |            |             |
  |             |             |            |             |
  |             |             |            |             |
  |             |             |            |             |
  |             |             |            |             |
  |    DP-4     |  HDMI-A-2*  |  HDMI-A-3  |  HDMI-A-4   |
  |             |             |            |             |
  |             |             |            |             |
  |             |             |            |             |
  |             |             |            |             |
  |             |             |            |             |
  +-------------+-------------+------------+----------+-----------------+
  |                                                   |                 |
  |                                                   |    HDMI-A-1     |
  |                                                   |                 |
  |                                                   |                 |
  |                                                   +-----------------+
  |                                                   |
  |                     HDMI-A-5                      |
  |                                                   |
  |                                                   |
  |                                                   |
  |                                                   |
  |                                                   |
  |                                                   |
  |                                                   |
  +---------------------------------------------------+
```

→ that `HDMI-A-1` is the 32" Samsung in the bottom-right corner of my desk. The three Iiyama 27" on the top row are all on `card0` (RTX 3050 6 GB); the fourth 27" and the 65" overview TV come straight out of the Intel Arrow Lake iGPU (`card2`).

Together they tell the whole story: the silicon, the cable, the panel, and what each card is currently doing. That's the workflow `lsgpus` exists for — and zero-dependency Python is what makes it work on the locked-down sysadmin boxes where I actually need it.

## Daily use: tracking VRAM for local AI

If you run local LLMs (Ollama, vLLM, llama.cpp, text-generation-webui) or image/video models (ComfyUI, Forge, Stable Diffusion WebUI, Fooocus), you spend half your day asking the same four questions:

- *Which card has enough free VRAM to load this model right now?*
- *What is currently pinning 12 GB on `card1` — Ollama still loaded, ComfyUI that didn't release, an orphaned `python` process?*
- *Did Ollama actually land on the 4060 Ti, or did it fall back to the iGPU / a smaller card?*
- *Why is inference suddenly slow — is something else competing for the GPU?*

`lsgpus` answers all of those in a single shot. The `Processes:` block under each card (NVIDIA cards today) shows the PIDs that own VRAM and how much, **broken out by card** — no need to grep `nvidia-smi` and cross-reference `/proc/<pid>/cmdline` to figure out which Python process is which.

Looking at `card1` from the workstation above:

```
  card1: NVIDIA Corporation AD106 [GeForce RTX 4060 Ti] (rev a1)
         Driver: nvidia | GPU:0% MEM:12794/16380MB 48°C 15.1W
    ├─ HDMI-A-1: connected ← Samsung QE32Q50A 32"
    Processes:
      PID 9728  ollama  12744MB
```

Reading this: the card is idle (`GPU:0%`), but 12.7 GB of its 16.4 GB are pinned by `ollama` — typical of a model loaded and waiting for the next request. From those four lines I now know:

- I have ~3.6 GB of headroom left on this card before the next load OOMs,
- the heavy tenant is Ollama (not a forgotten ComfyUI worker I should kill),
- if I want to load a bigger model, my options are: close Ollama, drop to a smaller quant, or move to a card with more free VRAM — and `lsgpus` shows the headroom on all cards in the same call.

For real-time monitoring — watching a model load, diagnosing a sudden inference slowdown, seeing tokens-per-second pressure on the GPU — `lsgpus --watch` redraws in place with a rolling 20-sample utilization sparkline (▁▂▃▄▅▆▇█) and a progress bar next to each card, while keeping the process list visible so VRAM creep is observable as it happens:

```bash
lsgpus --watch        # default 2 s interval
lsgpus --watch 5      # 5 s interval (gentler on the system)
# press Ctrl+C to stop (there is no quit key; Esc / q / Ctrl+D do nothing)
```

![lsgpus --watch during an Ollama run: VRAM climbing and the RTX 4060 Ti pegged at 98%, while a second model runs on the RTX 3050](docs/lsgpus-watch.gif)

In a typical local-AI workflow that looks like: launch `lsgpus --watch` in a side terminal, start `ollama run <model>` in another, see the VRAM of the chosen card climb to its plateau, then watch the utilization sparkline pulse as each generation runs.

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

### Fedora (COPR)

Available from the [`ls-tools` COPR repository](https://copr.fedorainfracloud.org/coprs/guy-marc-aprin/ls-tools/):

```bash
sudo dnf copr enable guy-marc-aprin/ls-tools
sudo dnf install lsgpus
```

Builds are provided for Fedora 43, 44 and rawhide (x86_64). The Fedora package is
named `lsgpus`. Enabling the COPR also gives you `lsdisplay` (the companion
display-listing tool).

Updates come with the system: `sudo dnf upgrade` picks up new releases automatically
once the COPR is enabled. To remove the repository later:

```bash
sudo dnf copr remove guy-marc-aprin/ls-tools
```

**RHEL / Rocky / AlmaLinux / CentOS Stream** — the same COPR works; just enable the
COPR plugin first:

```bash
sudo dnf install dnf-plugins-core
sudo dnf copr enable guy-marc-aprin/ls-tools
sudo dnf install lsgpus
```

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
lsgpus --all        # Include disconnected outputs
lsgpus --watch      # Real-time monitoring (Ctrl+C to stop)
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
