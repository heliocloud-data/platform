# OpenTofu Tests

This directory contains OpenTofu native tests for the root module.

Current layout:

- `root_smoke.tftest.hcl`: A low-friction smoke test that runs `plan` and asserts a few stable contracts on the root module.

Run the suite from the repository root:

```sh
tofu test
```

Run a single test file:

```sh
tofu test -filter=tests/root_smoke.tftest.hcl
```

Useful conventions for adding more tests:

- Prefer `command = plan` for contract tests that should not create infrastructure.
- Keep test variable values local to the `.tftest.hcl` file unless multiple test files need to share them.
- Assert on stable behavior such as naming, sizing, labels, and fixed configuration values.
- Add `apply`-based tests only when the branch has dedicated test infrastructure and credentials for cleanup.
