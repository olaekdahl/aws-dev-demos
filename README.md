# AWS Dev Class – Python Demos

This repo contains complete Python demos mapped to the module flow.

## Prereqs

- Python 3.11+
- AWS CLI configured (or env vars set)
- An AWS account where you can create resources

## Setup

```bash
python3 -m venv .venv
# mac/linux
source .venv/bin/activate
# windows powershell
# .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
pip install -e .
```

### Why `pip install -e .`?

Scripts in subdirectories (e.g., `m03-aws-auth-and-profiles/whoami.py`) import shared utilities from the `common/` package at the project root. By default, Python can't resolve these imports when running scripts from subdirectories.

Installing the project in **editable mode** (`-e`) registers the `common` package in your virtual environment, making it importable from anywhere. "Editable" means changes to the `common/` code take effect immediately—no reinstall needed.

## Safety

Many scripts create AWS resources. Most deletes require `--yes`.

Generated: 2026-02-03
