# Testing

## CPython reference

```bash
python -m unittest discover -s tests -v
python examples/foundation.py
```

## asmpython differential probe

```bash
python tools/dualrun.py tests/parity/model_snapshot.py
```

Classifications:

- CPython failure: engine/reference bug
- Compile failure: asmpython compiler rejection
- Native nonzero exit: asmpython runtime/FFI gap
- Different output: asmpython observable miscompile
