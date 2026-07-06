PHONY: clean init fmt validate deps features tests k8s-templating-tests

REPORT_DIR := reports

clean:
	rm -rf .terraform modules/*/.terraform temp

fmt:
	tofu fmt --recursive
# 	pre-commit run --all-files || echo "Fixing new-lines at end-of-file"
# 	pre-commit uninstall

init:
	find modules -mindepth 1 -maxdepth 1 -type d | sort | xargs  -I {}  tofu -chdir={} init
	tofu init

validate:
	tofu validate
	find modules -mindepth 1 -maxdepth 1 -type d | sort | xargs  -I {}  tofu -chdir={} validate

deps:
	python3 -m pip install -r requirements.txt
	python3 -m pip install -r requirements-dev.txt
	python3 -m pip install -r requirements-behave.txt

tests: k8s-templating-tests

k8s-templating-tests:
	export PYTHONPATH=$(PYTHONPATH):$(shell pwd):$(shell pwd)/tests
	mkdir -p $(REPORT_DIR)/k8s-templating-tests
	python3 -m pytest \
		-c pytest-k8s-templating-tests.ini \
		--junit-prefix=HelioCloud-platform-k8s-templating-tests \
		--junitxml=$(REPORT_DIR)/k8s-templating-tests/TEST-HelioCloud-platform-k8s-templating-tests.xml \
		--snapshot-update

feature-tests:
	python3 -m behave --junit features

# Runs all end-to-end tests against the portal
feature-tests-portal:
	python3 -m behave --junit --tags=@Portal features

feature-tests-daskhub:
	python3 -m behave --junit --tags=@Daskhub features

feature-tests-daskhub-run_notebook:
	python3 -m behave --junit features/daskhub_run_notebook.feature
	
feature-tests-daskhub-server_launch:
	python3 -m behave --junit features/daskhub_server_launch.feature
