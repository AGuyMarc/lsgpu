# Changelog

All notable changes to **lsgpus**. This is the canonical upstream changelog;
`debian/changelog` tracks Debian packaging only.

> The installed binary, man page and Debian package are named `lsgpus` (with a
> trailing `s`) since 0.2.0. The GitHub repository and the Python module stay
> `lsgpu`.

## 0.2.6 — 2026-08-22

* build: migrate to `pyproject.toml` (PEP 517/518); `setup.py` dropped.
* packaging: Fedora COPR spec and "Fedora (COPR)" install docs added.

## 0.2.5 — 2026-07-28

* watch: clear the frame with ANSI erase sequences instead of trailing-space
  padding. Each row now erases to end-of-line and the bottom of the frame
  erases to end-of-screen, so a shrinking frame (a GPU or process that
  disappeared) or pre-existing terminal text below it no longer lingers.

## 0.2.4 — 2026-06-04

* watch: the `--watch` header now carries the same identity as the default
  listing — the canonical PCI bus id + nvidia-smi GPU index
  (`[PCI 02:00.0 | nvidia-smi GPU0]`) and the `Driver:` line. These were only
  in the non-watch output before; nothing is lost in watch mode anymore.
* docs: refresh the README demo GIF and the man OUTPUT sample to the new header.

## 0.2.3 — 2026-06-04

* watch: show the **full card name** in `--watch` headers. The previous code
  kept only the bracketed model and left a dangling `]`
  (e.g. `GeForce RTX 3050 6GB] (rev a1)`); it now shows the complete name.
* docs(README): add an animated demo of `lsgpus --watch` during an Ollama run
  (VRAM climbing, GPU pegged, process list) in the real-time monitoring section.
* docs(man): add a static sample of a `--watch` frame to the OUTPUT section.

## 0.2.2 — 2026-06-04

* docs(man): document the two options that were missing from the man page —
  `--all`/`-a` (show disconnected outputs) and `--watch`/`-w [SEC]` (live
  in-place refresh; stop with **Ctrl+C** — there is no quit key). Add matching
  EXAMPLES. The man had drifted behind the binary.

## 0.2.1 — 2026-05-29

* Show the canonical **PCI bus id** and the **nvidia-smi GPU index** next to
  each card — e.g. `card1: … [PCI 02:00.0 | nvidia-smi GPU0]`. This resolves
  the long-standing confusion between the kernel DRM `cardN` numbering (probe
  order, what `lsgpus` lists) and the bus-sorted `GPU N` index reported by
  `nvidia-smi` on multi-GPU machines — the PCI bus id is the only stable,
  unambiguous identifier. Also surfaced in `--short` and as `nvidia_index` in
  `--json`.
* Declare the license as the SPDX expression `GPL-2.0-or-later` and drop the
  deprecated `License :: OSI Approved ::` classifier in `setup.py`.
* tests: add a version-consistency guard that fails if the version sources
  (`setup.py`, `__version__`, man `.TH`, `debian/changelog`, this file) diverge.

## 0.2.0 — 2026-05-19

* Rename the installed binary `lsgpu` → `lsgpus` and the man page `lsgpu(1)` →
  `lsgpus(1)` to avoid the clash with the `lsgpu(1)` tool shipped by
  `igt-gpu-tools`. The Debian source/binary package is renamed to `lsgpus`
  with `Replaces`/`Breaks` for a clean migration. The GitHub repository keeps
  the name `AGuyMarc/lsgpu`. (Reported by seraf1 while packaging the AUR build.)

## 0.1.5 — 2026-05-18

* Clarify the dependency model in the README: Python 3.7+ and `/sys/class/drm`
  only; reads `nvidia-smi` / `rocm-smi` when present, but no CUDA / ROCm /
  pycuda required.

## 0.1.4 — 2026-05-15

* Packaging fixes: ship the man page and README, add a `debian/copyright`,
  move the `/usr/bin/lsgpu` symlink to `debian/lsgpu.links`, drop the postinst
  hack. Fix maintainer name `Aprin` → `APRIN`.

## 0.1.3 — 2026-05-15

* Lower `debhelper-compat` from 13 to 11 so the source package builds out of
  the box on Ubuntu 22.04 LTS. (Reported by bigbob.)

## 0.1.2 — 2026-05-14

* Add the SPDX license header (`GPL-2.0-or-later`).
* EDID DTD sanity check: prefer the coarse size when the DTD diagonal exceeds
  2× the coarse diagonal — fixes ~8" panels reported as 59" (e.g. SGN L01N8A,
  BOE panels). (Reported by Blaise on LinuxFr.org.)

## 0.1.1 — 2026-05-03

* Initial release: NVIDIA stats (`nvidia-smi`), AMD stats (sysfs), GPU process
  listing, real-time `--watch` sparklines, EDID monitor identification,
  override-file support, connected-only default (`-a` for all).
