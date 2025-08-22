# Test template: using fake_walk_builder

Use the `fake_walk_builder` fixture to create an `os.walk` replacement from a nested dict.

Example:

```python
def test_my_unit(monkeypatch, fake_walk_builder):
    nested = {
        'dirA': {
            'sub': {
                'file1.txt': None
            },
            'file2.bin': None
        },
        'rootfile.txt': None
    }

    fake_walk = fake_walk_builder(Path("/fake/save_dir"), nested)
    monkeypatch.setattr(my_module.os, 'walk', fake_walk)

    # ... exercise code that uses os.walk ...
```

Notes:
- The nested dict keys that map to dict values are treated as directories.
- Leaf keys with None are treated as files.
- The builder yields parent directories before children (top-down order).

