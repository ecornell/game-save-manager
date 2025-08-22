Tests layout and guidelines
==========================

This repository splits tests into two informal categories:

- Unit tests:
  - Fast, isolated, do not touch the real filesystem.
  - Use fixtures from `tests/conftest.py` such as:
    - `fake_mkdtemp_func` — returns a deterministic temp path instead of creating real dirs.
    - `fake_mkdir_func` — no-op replacement for `Path.mkdir` to avoid creating directories.
    - `write_text_capture` — in-memory capture for `Path.write_text` calls.
    - `fake_file_tree_factory` / `fake_walk_builder` — build an `os.walk` replacement from a nested dict; prefer `fake_walk_builder` which accepts `pathlib.Path`.
  - Unit tests are good for exercising logic without file I/O and should use the above fixtures.

- Integration tests:
  - Touch the real filesystem (create temp dirs/files under `tmp_path`).
  - Mark these tests with `@pytest.mark.integration` or run them explicitly.
  - Examples include tests that call `SaveBackupManager.create_backup()` against real temporary dirs to validate end-to-end behavior.

Quick how-to
------------

- Run only unit tests (skip integration):

```bash
pytest -q -m "not integration"
```

- Run only integration tests:

```bash
pytest -q -m integration
```

Recommended patterns
--------------------

- Prefer `fake_walk_builder(Path(...), nested_dict)` when you need to stub `os.walk` in unit tests. See `tests/TEST_TEMPLATE.md` for an example.
- For isolated tests, avoid touching disk: monkeypatch `backup.os.walk`, `tempfile.mkdtemp`, `shutil.copytree`, and `Path.write_text` as needed — but prefer the shared fixtures in `tests/conftest.py`.
- Use `@pytest.mark.integration` on tests that create real files so they can be filtered in CI.

Where to find the fixtures
--------------------------

Open `tests/conftest.py` — it documents and exposes the helpers mentioned above.

If you want a lint rule or pre-commit hook to suggest `fake_walk_builder` usage, add it and I can help wire it into CI.
