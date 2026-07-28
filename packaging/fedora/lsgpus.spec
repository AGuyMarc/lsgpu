# SPDX-License-Identifier: GPL-2.0-or-later
# Paquet Fedora/COPR — lsgpus (Guy-Marc APRIN)
# Cale sur la derniere release publiee : v0.2.5 (2026-07-28).
#
# ATTENTION aux noms (asymetrie voulue) :
#   - depot GitHub          : lsgpu   (nom inchange, preserve les liens AUR/LinuxFr)
#   - nom de distribution   : lsgpus  (setup.py name="lsgpus")
#   - binaire installe      : lsgpus  (evite le conflit avec igt-gpu-tools qui livre /usr/bin/lsgpu)
#   - module Python importe : lsgpu   (lsgpu.py)
#   - page de manuel        : lsgpus.1
# => la tarball GitHub se deplie dans lsgpu-<version>/ (nom du DEPOT), d'ou le -n ci-dessous.

Name:           lsgpus
Version:        0.2.5
Release:        1%{?dist}
Summary:        List GPUs with details — like lscpu/lsusb but for graphics cards

License:        GPL-2.0-or-later
URL:            https://github.com/AGuyMarc/lsgpu
Source0:        %{url}/archive/v%{version}/lsgpu-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-wheel

%global _description %{expand:
lsgpus lists the GPUs of a Linux machine the way lscpu lists CPUs: vendor,
model, driver, and — when the tooling is present — NVIDIA stats (nvidia-smi)
and AMD stats (sysfs), the monitor-to-GPU mapping (via EDID), running GPU
processes, and a real-time --watch view with sparklines. Pure Python 3, zero
mandatory dependencies (no CUDA/ROCm/pycuda needed — it just reads whatever
nvidia-smi / rocm-smi / sysfs expose).}

%description %{_description}

# Empeche l'installation cote-a-cote avec /usr/bin/lsgpu d'igt-gpu-tools :
# noms de binaires differents, donc pas de conflit de fichier — rien a declarer.

%prep
# La tarball GitHub du depot "lsgpu" se deplie dans lsgpu-%%{version}/
%autosetup -n lsgpu-%{version}

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
# Le module importable s'appelle "lsgpu" (le binaire, lui, est "lsgpus")
%pyproject_save_files lsgpu
# Page de manuel (nom : lsgpus.1)
install -Dpm 0644 lsgpus.1 %{buildroot}%{_mandir}/man1/lsgpus.1

%check
%{python3} -m unittest discover -s tests -v ||:

%files -f %{pyproject_files}
%license LICENSE
%doc README.md
%{_bindir}/lsgpus
%{_mandir}/man1/lsgpus.1*

%changelog
* Tue Jul 28 2026 Guy-Marc APRIN <2026@gm.casa> - 0.2.5-1
- Aligne sur la release GitHub v0.2.5 (fix rendu --watch : effacement ANSI).
* Fri Jul 03 2026 Guy-Marc APRIN <2026@gm.casa> - 0.2.4-1
- Premier paquet RPM (COPR) — aligne sur la release GitHub v0.2.4.
