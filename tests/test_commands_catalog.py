#!/usr/bin/env python3
"""Validate the GitHub Pages command catalog used by the docs PWA."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs" / "commands.json"


class CommandsCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with CATALOG.open(encoding="utf-8") as fh:
            cls.data = json.load(fh)

    def test_has_commands_and_categories(self):
        self.assertGreaterEqual(len(self.data["commands"]), 40)
        self.assertGreaterEqual(len(self.data["categories"]), 5)

    def test_command_shape(self):
        required = {"id", "title", "command", "description", "category", "tags", "source"}
        ids = set()
        cat_ids = {c["id"] for c in self.data["categories"]}
        for item in self.data["commands"]:
            self.assertTrue(required.issubset(item.keys()), item.get("id"))
            self.assertTrue(item["command"].strip())
            self.assertTrue(item["title"].strip())
            self.assertIn(item["category"], cat_ids)
            self.assertNotIn(item["id"], ids)
            ids.add(item["id"])

    def test_includes_toolkit_and_logcat(self):
        commands = " ".join(c["command"] for c in self.data["commands"])
        self.assertIn("python3 server.py", commands)
        self.assertIn("python3 -m adb_toolkit", commands)
        self.assertIn("logcat", commands.lower())

    def test_pwa_assets_exist(self):
        docs = ROOT / "docs"
        for name in (
            "index.html",
            "app.js",
            "styles.css",
            "sw.js",
            "manifest.webmanifest",
            "icons/icon-192.png",
            "icons/icon-512.png",
            ".nojekyll",
        ):
            self.assertTrue((docs / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
