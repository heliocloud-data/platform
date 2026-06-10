# Testing Guide (OpenTofu)

This repository uses OpenTofu native tests (`.tftest.hcl`) for all modules.

The testing strategy is:

- Module-level tests → real validation (what matters)
- Root module test → smoke only (Helm limitations prevent full plan testing)

---

## Prerequisites

- OpenTofu installed (`tofu`)
- AWS credentials configured (no real resources are created)
- Network access to download providers

---

## How Tests Are Structured

Each module has its own test file:

- `modules/*/tests/*.tftest.hcl`

Examples:
- `modules/heliocloud_auth/tests/...`
- `modules/heliocloud_eks_addon_*/tests/...`
- `modules/heliocloud_portal/tests/...`

Root test:
- `tests/main.tftest.hcl` (no run block by design)

---

## Run All Module Tests

Run all module tests individually (recommended):

```
for dir in modules/*; do
  if [ -d "$dir/tests" ]; then
    echo "Running tests in $dir"
    (cd "$dir" && tofu init -upgrade && tofu test)
  fi
done
```

---

## Run a Single Module Test

Example:

```
cd modules/heliocloud_auth
tofu init
tofu test
```

---

## Run Root Test

```
tofu init
tofu test ./tests
```

Expected output:

```
Success! 0 passed, 0 failed.
```

This is intentional.

---

## Why Root Tests Don’t Fully Run

The root module includes:

- AWS → EKS → Kubernetes → Helm provider chaining

The Helm provider requires values that are only known after apply, which causes:

```
Provider configuration is incomplete
```

OpenTofu test limitations:

- Cannot exclude resources in `tftest`
- Cannot catch provider init failures cleanly
- Cannot evaluate Helm releases at plan time

So instead:

- Test all modules independently
- Keep root test as a non-breaking smoke boundary

---

## What Is Actually Being Tested

Module tests validate:

- Resource configuration (names, sizes, labels)
- IAM wiring
- Networking setup
- Scaling behavior
- Cognito / auth configuration
- Pod identity wiring

They intentionally avoid:

- Unknown values at plan time (ARNs, dynamic outputs)
- Helm rendered values

---

## CI Recommendation

Run module tests only:

```
for dir in modules/*; do
  if [ -d "$dir/tests" ]; then
    (cd "$dir" && tofu init -upgrade && tofu test)
  fi
done
```

Optional root smoke test:

```
tofu test ./tests
```

---

## Summary

- Full coverage at module level
- Stable, deterministic tests
- No flaky Helm/provider failures
- CI-safe execution

This is the correct testing pattern for:
- EKS-based platforms
- Helm-driven infrastructure
- Multi-provider Terraform/OpenTofu setups
