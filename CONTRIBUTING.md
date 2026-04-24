# Contributing

Use Python `3.13.2` for local tooling in this repo.

Create a virtual environment and install the development requirements:

```sh
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Then install the git hooks from the repository root:

```sh
pre-commit install
```

Run all hooks manually:

```sh
pre-commit run --all-files
```

The current hooks:

- run `tofu fmt -recursive` for OpenTofu files
- ensure files end with a trailing newline
