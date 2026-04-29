# Testing

This repository uses native OpenTofu test files.


## Layout

- `tests/main.tftest.hcl`
- `modules/<module>/tests/<module>.tftest.hcl`


## Commands

```bash
tofu init
tofu test
tofu test -filter=tests/main.tftest.hcl

```

Module level:

```bash
tofu -chdir=modules/<module> test -filter=tests/<module>.tftest.hcl
```

