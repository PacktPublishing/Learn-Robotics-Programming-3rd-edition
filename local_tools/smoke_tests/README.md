# Smoke Tests

This folder contains centralized smoke tests that can be run against any chapter folder.

## Files

- `smoke_inventor_hat_service.py`
- `smoke_poses_and_boundary.py`

## Prerequisites

Run from the repository root and use Poetry so dependencies are available.

## Environment Variables

- `SMOKE_TEST_TARGET_DIR`
  - Path to the chapter folder to test.
  - Example: `chapter-12/complete` or `chapter-17/cross-merge`.
- `SMOKE_TEST_SOURCE_FOLDER` (optional)
  - Source folder inside the target chapter.
  - Default: `robot`.

## Usage

### Run inventor hat smoke test

```bash
SMOKE_TEST_TARGET_DIR=<chapter-folder> poetry run python local_tools/smoke_tests/smoke_inventor_hat_service.py
```

### Run poses and boundary smoke test

```bash
SMOKE_TEST_TARGET_DIR=<chapter-folder> poetry run python local_tools/smoke_tests/smoke_poses_and_boundary.py
```

### Run both

```bash
SMOKE_TEST_TARGET_DIR=<chapter-folder> \
  poetry run python local_tools/smoke_tests/smoke_inventor_hat_service.py && \
SMOKE_TEST_TARGET_DIR=<chapter-folder> \
  poetry run python local_tools/smoke_tests/smoke_poses_and_boundary.py
```

## Examples

### Chapter 12 complete

```bash
SMOKE_TEST_TARGET_DIR=chapter-12/complete poetry run python local_tools/smoke_tests/smoke_inventor_hat_service.py
SMOKE_TEST_TARGET_DIR=chapter-12/complete poetry run python local_tools/smoke_tests/smoke_poses_and_boundary.py
```

### Chapter 17 cross-merge

```bash
SMOKE_TEST_TARGET_DIR=chapter-17/cross-merge poetry run python local_tools/smoke_tests/smoke_inventor_hat_service.py
SMOKE_TEST_TARGET_DIR=chapter-17/cross-merge poetry run python local_tools/smoke_tests/smoke_poses_and_boundary.py
```

## Notes

- If you run with system Python instead of Poetry, dependency errors can occur (for example `ModuleNotFoundError: No module named 'numpy'`).
- The scripts print the resolved target directory and source folder to help troubleshooting.
