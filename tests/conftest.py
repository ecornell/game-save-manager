import tempfile
from pathlib import Path
import os
import pytest
from typing import Dict, Tuple


def fake_mkdtemp(prefix: str | None = None, dir: str | None = None) -> str:
    # Provide sensible defaults when callers pass None to mirror tempfile.mkdtemp
    base_dir = Path(dir) if dir is not None else Path(tempfile.gettempdir())
    prefix_str = prefix or ""
    return str(base_dir / (prefix_str + "TMP"))


def fake_mkdir(self, mode=0o777, parents=False, exist_ok=False):
    # No-op to avoid creating directories on the real filesystem during unit tests
    return None


def write_text_capture_factory():
    writes = {}

    def write_text(self, content, encoding='utf-8'):
        writes[str(self)] = content
        return len(content)

    return writes, write_text


@pytest.fixture
def fake_mkdtemp_func():
    return fake_mkdtemp


@pytest.fixture
def fake_mkdir_func():
    return fake_mkdir


@pytest.fixture
def write_text_capture():
    return write_text_capture_factory()


def _nested_to_walk_map(root: str, nested: dict) -> Dict[str, Tuple[list, list]]:
    """
    Convert a nested dict file-tree into a flat mapping suitable for a fake os.walk.

    nested format example:
    {
        'dirA': {
            'sub': {
                'file1.txt': None
            },
            'file2.bin': None
        },
        'rootfile.txt': None
    }

    Returns a mapping like { 'C:/path': (['subdir1', ...], ['file1', ...']), ... }
    """
    mapping: Dict[str, Tuple[list, list]] = {}

    def build(curr_path: Path, subtree: dict):
        dirs = []
        files = []
        for name, val in subtree.items():
            if isinstance(val, dict):
                dirs.append(name)
            else:
                files.append(name)
        mapping[str(curr_path)] = (dirs, files)
        for name, val in subtree.items():
            if isinstance(val, dict):
                build(curr_path / name, val)

    build(Path(root), nested)
    return mapping


@pytest.fixture
def fake_file_tree_factory():
    """Return a factory that builds a fake os.walk from a nested dict and root path.

    Usage in tests:
        fake_walk = fake_file_tree_factory()(root, nested_dict)
        monkeypatch.setattr(os, 'walk', fake_walk)
    """

    def factory(root: str, nested: dict):
        mapping = _nested_to_walk_map(root, nested)

        def fake_walk(top, topdown=True, onerror=None, followlinks=False):
            top = str(Path(top))
            # select keys that are under the provided top path, include the top itself
            keys = [k for k in mapping.keys() if k == top or k.startswith(top + os.sep)]
            # sort by path depth to yield parent directories before children (top-down)
            keys.sort(key=lambda p: len(Path(p).parts))
            for k in keys:
                dirs, files = mapping[k]
                yield k, list(dirs), list(files)

        return fake_walk

    return factory


@pytest.fixture
def fake_os_walk():
    """A tiny convenience fake os.walk that yields no files (useful default)."""

    def walk_empty(top, topdown=True, onerror=None, followlinks=False):
        yield str(Path(top)), [], []

    return walk_empty


@pytest.fixture
def fake_walk_builder(fake_file_tree_factory):
    """Return a small builder that accepts a Path and nested dict and returns an os.walk replacement."""

    def builder(root: Path, nested: dict):
        return fake_file_tree_factory(str(root), nested)

    return builder
