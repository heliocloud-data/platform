PHONY: clean init fmt validate deps features

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

deps:
	python3 -m pip install -r requirements-behave.txt

# export HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER=jhuapl-deployment 
feature-tests:
	python3 -m behave --junit features

# Runs all end-to-end tests against the portal
feature-tests-portal:
	python3 -m behave --junit --tags=@Portal features

feature-tests-daskhub:
	python3 -m behave --junit --tags=@Daskhub features

feature-test-daskhub-server_launch:
	python3 -m behave --junit features/daskhub_server_launch.feature
