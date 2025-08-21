import os
import json
import shutil
import datetime
from pathlib import Path

import pytest
import time

import backup



def test_load_and_save_games_config(tmp_path):
    cfg_path = tmp_path / "games_config.json"
    # File doesn't exist yet -> load should create default
    cfg = backup.load_games_config(cfg_path)
    assert "games" in cfg
    assert cfg_path.exists()

    # Modify and save
    cfg["settings"]["default_max_backups"] = 5
    backup.save_games_config(cfg_path, cfg)

    reloaded = backup.load_games_config(cfg_path)
    assert reloaded["settings"]["default_max_backups"] == 5


def test_create_backup_no_files(tmp_path):
    save_dir = tmp_path / "saves_empty"
    save_dir.mkdir()
    backup_dir = tmp_path / "backups"

    manager = backup.SaveBackupManager(save_dir, backup_dir, max_backups=3)
    result = manager.create_backup()
    assert result is None


def test_create_backup_and_cleanup_and_description(tmp_path):
    save_dir = tmp_path / "saves"
    save_dir.mkdir()
    (save_dir / "file1.txt").write_text("hello")

    backup_dir = tmp_path / "backups"
    manager = backup.SaveBackupManager(save_dir, backup_dir, max_backups=2)

    # Create three backups; only 2 most recent should remain
    p1 = manager.create_backup("first")
    assert p1 is not None
    # ensure timestamp for backup name changes (timestamp granularity is seconds)
    time.sleep(1)
    (save_dir / "file2.txt").write_text("more")
    p2 = manager.create_backup("second")
    assert p2 is not None
    time.sleep(1)
    (save_dir / "file3.txt").write_text("again")
    p3 = manager.create_backup("third")
    assert p3 is not None

    backups = manager._get_backup_list()
    # cleanup runs automatically after create_backup, and max_backups is 2
    assert len(backups) <= 2

    # Check description file exists in the most recent backup
    most_recent = Path(backups[0])
    desc = most_recent / ".backup_description"
    assert desc.exists()
    assert desc.read_text(encoding='utf-8') in ("first", "second", "third")


def test_restore_backup(tmp_path):
    # prepare save dir with old content
    save_dir = tmp_path / "save_dir"
    save_dir.mkdir()
    (save_dir / "a.txt").write_text("old")

    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    # create a backup folder manually
    name = "backup_20250101_000000"
    bpath = backup_dir / name
    bpath.mkdir()
    (bpath / "a.txt").write_text("new")

    manager = backup.SaveBackupManager(save_dir, backup_dir, max_backups=5)
    # restore the single backup (choice 1), skip confirmation for test
    ok = manager.restore_backup(backup_choice=1, skip_confirmation=True)
    assert ok is True

    # verify file content was replaced
    assert (save_dir / "a.txt").read_text() == "new"
