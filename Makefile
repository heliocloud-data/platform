PHONY: clean init fmt validate

clean:
	rm -rf .terraform modules/*/.terraform

fmt:
	tofu fmt --recursive
	pre-commit run --all-files || echo "Fixing new-lines at end-of-file"
	pre-commit uninstall

init:
	find modules -mindepth 1 -maxdepth 1 -type d | sort | xargs  -I {}  tofu -chdir={} init
	tofu init

validate:
	tofu validate
	find modules -mindepth 1 -maxdepth 1 -type d | sort | xargs  -I {}  tofu -chdir={} validate
