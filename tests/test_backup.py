import os
import json
import shutil
import datetime
from pathlib import Path
import sys

# Ensure repository root is on sys.path so tests can import backup.py as a module
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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


def test_interrupted_backup_leaves_no_partial_and_metadata_on_success(tmp_path, monkeypatch):
    # Prepare many small files to exercise copy loop
    save_dir = tmp_path / "many_saves"
    save_dir.mkdir()
    for i in range(10):
        (save_dir / f"f{i}.txt").write_text(f"data{i}")

    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    manager = backup.SaveBackupManager(save_dir, backup_dir, max_backups=5)

    # Monkeypatch shutil.copy2 to raise after a few copies to simulate interruption
    import shutil as _shutil
    original_copy2 = _shutil.copy2
    counter = {"count": 0}

    def failing_copy2(src, dst, follow_symlinks=True):
        counter["count"] += 1
        # allow first two files then fail to simulate crash
        if counter["count"] == 3:
            raise KeyboardInterrupt("simulated interruption")
        return original_copy2(src, dst, follow_symlinks=follow_symlinks)

    monkeypatch.setattr("shutil.copy2", failing_copy2)

    # Attempt backup; should handle exception and return None (failure)
    res = manager.create_backup("interrupted")
    assert res is None

    # Ensure there are no visible backup_* directories (hidden tmp dirs may exist but should be cleaned)
    visible_backups = [p for p in backup_dir.iterdir() if p.is_dir() and not p.name.startswith('.')]
    assert len(visible_backups) == 0

    # Now restore copy2 and perform a successful backup to verify metadata is written
    monkeypatch.setattr("shutil.copy2", original_copy2)
    success = manager.create_backup("final")
    assert success is not None

    meta = (success / ".backup_meta.json")
    assert meta.exists()
    data = json.loads(meta.read_text(encoding='utf-8'))
    assert "checksum" in data and "completed_at" in data and "move_method" in data
