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
import tempfile
import errno



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
            raise RuntimeError("simulated interruption")
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


def test_exdev_fallback_moves_and_metadata_copied(tmp_path, monkeypatch):
    # Simulate os.replace raising EXDEV so code falls back to shutil.move
    save_dir = tmp_path / "saves_exdev"
    save_dir.mkdir()
    (save_dir / "a.txt").write_text("content")

    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    manager = backup.SaveBackupManager(save_dir, backup_dir, max_backups=3)

    import os as _os
    import errno as _errno

    def fake_replace(a, b):
        raise OSError(_errno.EXDEV, "simulated cross-device link")

    monkeypatch.setattr(_os, "replace", fake_replace)

    # Wrap shutil.move to record calls and delegate to the real implementation
    # Wrap shutil.move to record calls and delegate to the real implementation
    original_move = shutil.move
    move_called = {"called": False, "args": None}

    def recording_move(src, dst, *args, **kwargs):
        move_called["called"] = True
        move_called["args"] = (src, dst)
        # Delegate to the real move to actually transfer files during the test
        return original_move(src, dst, *args, **kwargs)

    monkeypatch.setattr(shutil, "move", recording_move)

    # Perform backup; fallback to shutil.move should succeed and metadata should show 'copied'
    result = manager.create_backup("exdev-test")
    assert result is not None

    meta = (result / ".backup_meta.json")
    assert meta.exists()
    data = json.loads(meta.read_text(encoding='utf-8'))
    assert data.get("move_method") == "copied"
    # Ensure shutil.move was called due to EXDEV fallback
    assert move_called["called"] is True



def test_move_failure_cleanup_on_exception(tmp_path, monkeypatch):
    # Simulate os.replace raising EXDEV and shutil.move also failing to ensure cleanup
    save_dir = tmp_path / "saves_move_fail"
    save_dir.mkdir()
    (save_dir / "a.txt").write_text("content")

    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    manager = backup.SaveBackupManager(save_dir, backup_dir, max_backups=3)

    import os as _os
    import errno as _errno

    def fake_replace(a, b):
        raise OSError(_errno.EXDEV, "simulated cross-device link")

    def fake_move(a, b):
        raise RuntimeError("simulated move failure")

    # Patch os.replace to force fallback, and patch shutil.move to fail
    monkeypatch.setattr(_os, "replace", fake_replace)
    monkeypatch.setattr(shutil, "move", fake_move)

    # Attempt backup; should handle exception and return None
    res = manager.create_backup("move-fail")
    assert res is None

    # Ensure no visible final backups
    visible_backups = [p for p in backup_dir.iterdir() if p.is_dir() and not p.name.startswith('.')]
    assert len(visible_backups) == 0

    # Ensure no leftover temp dirs (those start with .backup_)
    tmp_dirs = [p for p in backup_dir.iterdir() if p.is_dir() and p.name.startswith('.backup_')]
    assert len(tmp_dirs) == 0
