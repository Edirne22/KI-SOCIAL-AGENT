import unittest
from datetime import datetime, timezone, timedelta
import shutil
from pathlib import Path
import re

import archive_published

class TestArchivePublished(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path("test_tmp_archive")
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True)

        self.orig_root = archive_published.ROOT
        self.orig_pub = archive_published.PUBLISHED_FILE
        self.orig_bak = archive_published.BACKUP_FILE
        self.orig_arch = archive_published.ARCHIVE_DIR

        archive_published.ROOT = self.tmp_dir
        archive_published.PUBLISHED_FILE = self.tmp_dir / "content" / "PUBLISHED.md"
        archive_published.BACKUP_FILE = self.tmp_dir / "content" / "PUBLISHED.md.bak.2026-09-17-b"
        archive_published.ARCHIVE_DIR = self.tmp_dir / "content" / "archive"

        (self.tmp_dir / "content").mkdir(parents=True)

    def tearDown(self):
        archive_published.ROOT = self.orig_root
        archive_published.PUBLISHED_FILE = self.orig_pub
        archive_published.BACKUP_FILE = self.orig_bak
        archive_published.ARCHIVE_DIR = self.orig_arch

        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)

    def test_backup_created_if_not_exists(self):
        content = "# Freigegebene Beiträge\n\n## Facebook [GEPOSTET 2026-09-17 10:00]\nText: Test"
        archive_published.PUBLISHED_FILE.write_text(content, encoding="utf-8")

        ref_dt = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)
        archive_published.archive_published(now_dt=ref_dt)

        self.assertTrue(archive_published.BACKUP_FILE.exists())
        self.assertEqual(archive_published.BACKUP_FILE.read_text(encoding="utf-8"), content)

    def test_posted_older_than_7_days_archived(self):
        content = """# Freigegebene Beiträge

## Facebook [GEPOSTET 2026-09-01 10:00]
Text: Old post

## Instagram [GEPOSTET 2026-09-15 10:00]
Text: Recent post
"""
        archive_published.PUBLISHED_FILE.write_text(content, encoding="utf-8")
        archive_published.BACKUP_FILE.write_text(content, encoding="utf-8")

        ref_dt = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)
        archive_published.archive_published(now_dt=ref_dt)

        pub_text = archive_published.PUBLISHED_FILE.read_text(encoding="utf-8")
        self.assertNotIn("2026-09-01", pub_text)
        self.assertIn("2026-09-15", pub_text)

        arch_file = archive_published.ARCHIVE_DIR / "PUBLISHED_2026-09.md"
        self.assertTrue(arch_file.exists())
        arch_text = arch_file.read_text(encoding="utf-8")
        self.assertIn("2026-09-01", arch_text)

    def test_initial_run_archives_all_before_today(self):
        content = """# Freigegebene Beiträge

## Facebook [GEPOSTET 2026-09-15 10:00]
Text: Post 2 days ago

## Instagram Reel [GEPOSTET 2026-09-17 08:00]
Text: Post today
"""
        archive_published.PUBLISHED_FILE.write_text(content, encoding="utf-8")
        archive_published.BACKUP_FILE.write_text(content, encoding="utf-8")

        ref_dt = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)
        archive_published.archive_published(now_dt=ref_dt, initial_run=True)

        pub_text = archive_published.PUBLISHED_FILE.read_text(encoding="utf-8")
        self.assertNotIn("2026-09-15", pub_text)
        self.assertIn("2026-09-17", pub_text)

    def test_freigegeben_older_than_14_days_becomes_verworfen(self):
        content = """# Freigegebene Beiträge

## Instagram
Status: FREIGEGEBEN
Datum: 2026-08-30
Text: Very old unposted freigegeben

## Facebook
Status: FREIGEGEBEN
Datum: 2026-09-10
Text: Recent unposted freigegeben

## Story
Status: ENTWURF
Datum: 2026-08-01
Text: Draft
"""
        archive_published.PUBLISHED_FILE.write_text(content, encoding="utf-8")
        archive_published.BACKUP_FILE.write_text(content, encoding="utf-8")

        ref_dt = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)
        archive_published.archive_published(now_dt=ref_dt)

        pub_text = archive_published.PUBLISHED_FILE.read_text(encoding="utf-8")
        self.assertIn("Status: VERWORFEN", pub_text)
        self.assertIn("Status: FREIGEGEBEN", pub_text)
        self.assertIn("Status: ENTWURF", pub_text)

if __name__ == "__main__":
    unittest.main()
