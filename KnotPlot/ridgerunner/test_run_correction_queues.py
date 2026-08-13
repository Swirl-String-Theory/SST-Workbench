#!/usr/bin/env python3
"""Tests for run_correction_queues.py."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from run_correction_queues import (
    CONTINUE,
    SKIP_RR,
    UNFINISHED,
    resolve_queue,
)


class TestCorrectionQueues(unittest.TestCase):
    def test_unfinished_and_continue(self) -> None:
        self.assertEqual(resolve_queue("unfinished", Path(".")), UNFINISHED)
        self.assertEqual(resolve_queue("continue", Path(".")), CONTINUE)
        self.assertIn("knot_0.1", SKIP_RR)

    def test_dry_run_cli(self) -> None:
        from run_correction_queues import main

        with mock.patch("run_correction_queues.batch_main", return_value=0) as batch:
            rc = main(["--queue", "unfinished", "--dry-run", "-t", "4"])
        self.assertEqual(rc, 0)
        argv = batch.call_args[0][0]
        self.assertIn("--dry-run", argv)
        self.assertIn("-rr", argv)
        self.assertIn("normal", argv)
        self.assertTrue(any("link_6.3.3" in a for a in argv))


if __name__ == "__main__":
    unittest.main()
