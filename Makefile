PHONY: clean init fmt validate deps features tests k8s-templating-tests k8s-prep

REPORT_DIR := reports

TERRAFORM_BIN := tofu

TERRAFORM_EXTRA_ARGS :=
TERRAFORM_APPLY_EXTRA_ARGS := 
TERRAFORM_OUTPUT_EXTRA_ARGS :=

# Following variables are used to determine the environment specific variable
# files for terraform/tofu files
#
# The environment specific variable files are expected to be in the following:
#   ${HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER}/${HELIOCLOUD_TERRAFORM_ENVIRONMENT_SUBDIR}/${HELIOCLOUD_TERRAFORM_ENVIRONMENT}/${HELIOCLOUD_TERRAFORM_ENVIRONMENT_VARIABLE_FILE}
HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER := $(shell pwd)

HELIOCLOUD_TERRAFORM_ENVIRONMENT_SUBDIR := environments
# HELIOCLOUD_TERRAFORM_ENVIRONMENT := development
HELIOCLOUD_TERRAFORM_ENVIRONMENT_VARIABLE_FILE=terraform.tfvars.json

clean:
	rm -rf .terraform modules/*/.terraform temp .cluster* .makefile_output.*

fmt: tf-fmt

deps:
	python3 -m pip install -r requirements.txt
	python3 -m pip install -r requirements-dev.txt
	python3 -m pip install -r requirements-behave.txt

tests: k8s-templating-tests

# Terraform/Tofu targets
tf-fmt:
	$(TERRAFORM_BIN) fmt --recursive $(TERRAFORM_EXTRA_ARGS)

tf-init:
	find modules -mindepth 1 -maxdepth 1 -type d | sort | xargs  -I {}  $(TERRAFORM_BIN) -chdir={} init
	$(TERRAFORM_BIN) init $(TERRAFORM_EXTRA_ARGS)

tf-apply:
	@if [ -z "$(HELIOCLOUD_TERRAFORM_ENVIRONMENT)" ]; then \
		echo "error: HELIOCLOUD_TERRAFORM_ENVIRONMENT not set, try again"; \
		exit 1; \
	fi

	@echo "Using:"
	@echo "    HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER:       $(HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER)"
	@echo "    HELIOCLOUD_TERRAFORM_ENVIRONMENT_SUBDIR:        $(HELIOCLOUD_TERRAFORM_ENVIRONMENT_SUBDIR)"
	@echo "    HELIOCLOUD_TERRAFORM_ENVIRONMENT:               $(HELIOCLOUD_TERRAFORM_ENVIRONMENT)"
	@echo "    HELIOCLOUD_TERRAFORM_ENVIRONMENT_VARIABLE_FILE: $(HELIOCLOUD_TERRAFORM_ENVIRONMENT_VARIABLE_FILE)"
	@echo ""

	$(eval TERRAFORM_APPLY_EXTRA_ARGS := $(TERRAFORM_APPLY_EXTRA_ARGS) -var-file=$(shell pwd)/$(HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER)/$(HELIOCLOUD_TERRAFORM_ENVIRONMENT_SUBDIR)/$(HELIOCLOUD_TERRAFORM_ENVIRONMENT)/$(HELIOCLOUD_TERRAFORM_ENVIRONMENT_VARIABLE_FILE))
	$(TERRAFORM_BIN) apply $(TERRAFORM_EXTRA_ARGS) $(TERRAFORM_APPLY_EXTRA_ARGS)

tf-validate:
	$(TERRAFORM_BIN) validate $(TERRAFORM_EXTRA_ARGS)
	find modules -mindepth 1 -maxdepth 1 -type d | sort | xargs  -I {}  $(TERRAFORM_BIN) -chdir={} validate $(TERRAFORM_EXTRA_ARGS)

# AWS CLI targets

# This target will update the eks nodegroups, which should be done once after a kubernetes
# control plane update, and whenever AWS provides a new AMI release version for the current
# kubernetes version which is typically once per week.
#
# As coded this task is performed asynchronously.
aws-eks-update-nodegroup-version:
	@if [ -z "$(HELIOCLOUD_TERRAFORM_ENVIRONMENT)" ]; then \
		echo "error: HELIOCLOUD_TERRAFORM_ENVIRONMENT not set, try again"; \
		exit 1; \
	fi

	@echo "Using:"
	@echo "    HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER:       $(HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER)"
	@echo "    HELIOCLOUD_TERRAFORM_ENVIRONMENT_SUBDIR:        $(HELIOCLOUD_TERRAFORM_ENVIRONMENT_SUBDIR)"
	@echo "    HELIOCLOUD_TERRAFORM_ENVIRONMENT:               $(HELIOCLOUD_TERRAFORM_ENVIRONMENT)"
	@echo "    HELIOCLOUD_TERRAFORM_ENVIRONMENT_VARIABLE_FILE: $(HELIOCLOUD_TERRAFORM_ENVIRONMENT_VARIABLE_FILE)"
	@echo ""

	$(eval TERRAFORM_OUTPUT_EXTRA_ARGS := $(TERRAFORM_OUTPUT_EXTRA_ARGS) -var-file=$(shell pwd)/$(HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER)/$(HELIOCLOUD_TERRAFORM_ENVIRONMENT_SUBDIR)/$(HELIOCLOUD_TERRAFORM_ENVIRONMENT)/$(HELIOCLOUD_TERRAFORM_ENVIRONMENT_VARIABLE_FILE))

	$(TERRAFORM_BIN) output $(TERRAFORM_EXTRA_ARGS) $(TERRAFORM_OUTPUT_EXTRA_ARGS) -json| jq .eks_cluster_name.value > .makefile_output.aws-eks-update-nodegroup-version_output.txt
	$(eval EKS_CLUSTER_NAME := $(shell cat $(shell pwd)/.makefile_output.aws-eks-update-nodegroup-version_output.txt))

	bash scripts/update-eks-nodegroups-version.sh $(EKS_CLUSTER_NAME)
	rm -rf .makefile_output.aws-eks-update-nodegroup-version_output.txt


# This target will render the environment specific k8s manifests and helm values
# files.
k8s-prep:
	@if [ -z "$(HELIOCLOUD_TERRAFORM_ENVIRONMENT)" ]; then \
		echo "error: HELIOCLOUD_TERRAFORM_ENVIRONMENT not set, try again"; \
		exit 1; \
	fi

	@echo "Using:"
	@echo "    HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER:       $(HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER)"
	@echo "    HELIOCLOUD_TERRAFORM_ENVIRONMENT_SUBDIR:        $(HELIOCLOUD_TERRAFORM_ENVIRONMENT_SUBDIR)"
	@echo "    HELIOCLOUD_TERRAFORM_ENVIRONMENT:               $(HELIOCLOUD_TERRAFORM_ENVIRONMENT)"
	@echo "    HELIOCLOUD_TERRAFORM_ENVIRONMENT_VARIABLE_FILE: $(HELIOCLOUD_TERRAFORM_ENVIRONMENT_VARIABLE_FILE)"
	@echo ""

	python setup_commands/kube/apply_tf_outputs_to_k8s.py --environment_folder=$(HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER) --dest_folder=$(HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER)/kube $(HELIOCLOUD_TERRAFORM_ENVIRONMENT)

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
	@if [ -z "$(HELIOCLOUD_TERRAFORM_ENVIRONMENT)" ]; then \
		echo "error: HELIOCLOUD_TERRAFORM_ENVIRONMENT not set, try again"; \
		exit 1; \
	fi

	@echo "Using:"
	@echo "    HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER:       $(HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER)"
	@echo "    HELIOCLOUD_TERRAFORM_ENVIRONMENT:               $(HELIOCLOUD_TERRAFORM_ENVIRONMENT)"
	@echo ""

	python3 -m behave --junit --tags=@Portal features

feature-tests-daskhub:
	python3 -m behave --junit --tags=@Daskhub features

feature-tests-daskhub-run_notebook:
	python3 -m behave --junit features/daskhub_run_notebook.feature
	
feature-tests-daskhub-server_launch:
	python3 -m behave --junit features/daskhub_server_launch.feature
