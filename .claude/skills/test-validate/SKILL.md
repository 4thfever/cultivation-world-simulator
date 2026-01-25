---
name: test-validate
description: Run Python tests using the project venv
---

## Commands

```bash
# Run all tests
.venv/bin/pytest

# Run specific test file
.venv/bin/pytest tests/test_<name>.py -v

# Run with coverage
.venv/bin/pytest --cov=src

# Run server (dev mode)
.venv/bin/python src/server/main.py --dev
```
