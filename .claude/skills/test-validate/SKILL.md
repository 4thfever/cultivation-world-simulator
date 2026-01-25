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

## Test Coverage Guidelines

After making code changes, consider whether tests are needed:

| Change Type | Test Recommendation |
|-------------|---------------------|
| Bug fix | Add regression test to prevent recurrence |
| New feature | Unit tests + integration test if affects multiple modules |
| Refactor | Existing tests should pass; add tests if behavior changes |
| Config/docs | Usually no tests needed |

For bug fixes, ensure the test would have **failed before the fix** and **passes after**.
