#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Guy-Marc APRIN <2026@gm.casa>
# NB: contact email rotates yearly — 2027@gm.casa in 2027, etc.
"""Tests unitaires pour lsgpu."""
import json
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lsgpu import (
    parse_edid, PNP_MANUFACTURERS, Monitor, GPU, Output,
    NvidiaStats, AmdStats, GpuProcess,
)


class TestPNPManufacturers(unittest.TestCase):
    def test_known_manufacturers(self):
        self.assertEqual(PNP_MANUFACTURERS["SAM"], "Samsung")
        self.assertEqual(PNP_MANUFACTURERS["IVM"], "Iiyama")

    def test_manufacturer_count(self):
        self.assertGreater(len(PNP_MANUFACTURERS), 20)


class TestParseEdid(unittest.TestCase):
    def test_empty_data(self):
        m = parse_edid(b"")
        self.assertEqual(m.manufacturer, "")

    def test_short_data(self):
        m = parse_edid(b"\x00" * 50)
        self.assertEqual(m.manufacturer, "")


class TestDataclasses(unittest.TestCase):
    def test_monitor(self):
        m = Monitor(manufacturer="Samsung", model="QN65", diagonal_inches=65)
        self.assertEqual(m.manufacturer, "Samsung")
        self.assertEqual(m.diagonal_inches, 65)

    def test_gpu_vram(self):
        g = GPU(card="card0", vram_bytes=6 * 1024**3)
        self.assertAlmostEqual(g.vram_gb, 6.0)

    def test_gpu_vram_zero(self):
        g = GPU(card="card0", vram_bytes=0)
        self.assertEqual(g.vram_gb, 0)

    def test_gpu_connected_outputs(self):
        g = GPU(card="card0", outputs=[
            Output(name="DP-1", connected=True),
            Output(name="DP-2", connected=False),
            Output(name="HDMI-1", connected=True),
        ])
        self.assertEqual(len(g.connected_outputs), 2)

    def test_gpu_util_nvidia(self):
        g = GPU(card="card0", nvidia_stats=NvidiaStats(gpu_util=75))
        self.assertEqual(g.gpu_util, 75)

    def test_gpu_util_amd(self):
        g = GPU(card="card0", amd_stats=AmdStats(gpu_util=50))
        self.assertEqual(g.gpu_util, 50)

    def test_gpu_util_none(self):
        g = GPU(card="card0")
        self.assertIsNone(g.gpu_util)

    def test_amd_stats_mb(self):
        a = AmdStats(mem_used=1024 * 1024 * 512, mem_total=1024 * 1024 * 4096)
        self.assertEqual(a.mem_used_mb, 512)
        self.assertEqual(a.mem_total_mb, 4096)

    def test_gpu_process(self):
        p = GpuProcess(pid=1234, name="python", used_memory_mb=512)
        self.assertEqual(p.pid, 1234)


class TestSparkline(unittest.TestCase):
    def test_sparkline_chars(self):
        from lsgpu import SPARK_CHARS
        self.assertEqual(len(SPARK_CHARS), 8)


class TestCLI(unittest.TestCase):
    def _run(self, *args):
        script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lsgpu.py")
        return subprocess.run(
            [sys.executable, script] + list(args),
            capture_output=True, text=True, timeout=10
        )

    def test_help(self):
        r = self._run("--help")
        self.assertEqual(r.returncode, 0)
        self.assertIn("lsgpus", r.stdout)

    def test_version(self):
        r = self._run("--version")
        self.assertEqual(r.returncode, 0)
        self.assertIn("lsgpus", r.stdout)
        self.assertIn("0.", r.stdout)

    def test_json_output(self):
        r = self._run("--json")
        if r.returncode == 0:
            data = json.loads(r.stdout)
            self.assertIsInstance(data, list)

    def test_short_output(self):
        r = self._run("--short")
        if r.returncode == 0:
            self.assertGreater(len(r.stdout), 0)

    def test_all_flag(self):
        r = self._run("-a")
        if r.returncode == 0:
            # With -a, disconnected ports should show
            self.assertGreater(len(r.stdout), 0)


if __name__ == "__main__":
    unittest.main()
