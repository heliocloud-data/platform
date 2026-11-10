PHONY: clean init fmt validate deps features tests k8s-templating-tests k8s-prep

REPORT_DIR := reports

TERRAFORM_BIN := tofu

TERRAFORM_EXTRA_ARGS :=
TERRAFORM_PLAN_EXTRA_ARGS := 
TERRAFORM_APPLY_EXTRA_ARGS := 
TERRAFORM_OUTPUT_EXTRA_ARGS :=


# Check for the presence of the heliocloud-context-env file, if so we can assume we're running from within the environment
# directory.
ifneq ($$(./heliocloud-context-env),)
	MAKEFILE_ABSPATH := $(abspath $(lastword $(MAKEFILE_LIST)))
	HELIOCLOUD_TERRAFORM_ENVIRONMENT_ABSPATH := $(dir $(MAKEFILE_ABSPATH))
	HELIOCLOUD_TERRAFORM_ENVIRONMENT := $(shell basename $(HELIOCLOUD_TERRAFORM_ENVIRONMENT_ABSPATH))
	HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER := $(abspath $(dir $(MAKEFILE_ABSPATH))/../..)

	HELIOCLOUD_TERRAFORM_ENVIRONMENT_SUBDIR := environments
	HELIOCLOUD_TERRAFORM_ENVIRONMENT_VARIABLE_FILE=terraform.tfvars.json

	-include ./heliocloud-context-env
	export

	HELIOCLOUD_PLATFORM_ROOT := $(abspath $(HELIOCLOUD_PLATFORM_RELPATH))

else
	# Following variables are used to determine the environment specific variable
	# files for terraform/tofu files
	#
	# The environment specific variable files are expected to be in the following:
	#   ${HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER}/${HELIOCLOUD_TERRAFORM_ENVIRONMENT_SUBDIR}/${HELIOCLOUD_TERRAFORM_ENVIRONMENT}/${HELIOCLOUD_TERRAFORM_ENVIRONMENT_VARIABLE_FILE}
	HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER := $(shell pwd)
	HELIOCLOUD_PLATFORM_ROOT := $(shell pwd)

	HELIOCLOUD_TERRAFORM_ENVIRONMENT_SUBDIR := environments
	# HELIOCLOUD_TERRAFORM_ENVIRONMENT := development
	HELIOCLOUD_TERRAFORM_ENVIRONMENT_VARIABLE_FILE=terraform.tfvars.json

	$(eval TERRAFORM_PLAN_EXTRA_ARGS := $(TERRAFORM_PLAN_EXTRA_ARGS) -var-file=$(HELIOCLOUD_PLATFORM_ROOT)/$(HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER)/$(HELIOCLOUD_TERRAFORM_ENVIRONMENT_SUBDIR)/$(HELIOCLOUD_TERRAFORM_ENVIRONMENT)/$(HELIOCLOUD_TERRAFORM_ENVIRONMENT_VARIABLE_FILE))
	$(eval TERRAFORM_APPLY_EXTRA_ARGS := $(TERRAFORM_APPLY_EXTRA_ARGS) -var-file=$(HELIOCLOUD_PLATFORM_ROOT)/$(HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER)/$(HELIOCLOUD_TERRAFORM_ENVIRONMENT_SUBDIR)/$(HELIOCLOUD_TERRAFORM_ENVIRONMENT)/$(HELIOCLOUD_TERRAFORM_ENVIRONMENT_VARIABLE_FILE))
	$(eval TERRAFORM_OUTPUT_EXTRA_ARGS := $(TERRAFORM_OUTPUT_EXTRA_ARGS) -var-file=$(HELIOCLOUD_PLATFORM_ROOT)/$(HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER)/$(HELIOCLOUD_TERRAFORM_ENVIRONMENT_SUBDIR)/$(HELIOCLOUD_TERRAFORM_ENVIRONMENT)/$(HELIOCLOUD_TERRAFORM_ENVIRONMENT_VARIABLE_FILE))

endif

printenv:
	@echo "MAKEFILE_ABSPATH: $(MAKEFILE_ABSPATH)"
	@echo "HELIOCLOUD_TERRAFORM_ENVIRONMENT_ABSPATH: $(HELIOCLOUD_TERRAFORM_ENVIRONMENT_ABSPATH)"
	@echo "HELIOCLOUD_TERRAFORM_ENVIRONMENT: $(HELIOCLOUD_TERRAFORM_ENVIRONMENT)"
	@echo "HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER: $(HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER)"
	@echo "HELIOCLOUD_TERRAFORM_ENVIRONMENT_SUBDIR: $(HELIOCLOUD_TERRAFORM_ENVIRONMENT_SUBDIR)"
	@echo "------"

clean:
	rm -rf .terraform modules/*/.terraform temp .cluster* .makefile_output.* tfplan tf_outputs.json

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

tf-plan:
	@if [ -z "$(HELIOCLOUD_TERRAFORM_ENVIRONMENT)" ]; then \
		echo "error: HELIOCLOUD_TERRAFORM_ENVIRONMENT not set, try again"; \
		exit 1; \
	fi

	$(TERRAFORM_BIN) plan $(TERRAFORM_EXTRA_ARGS) $(TERRAFORM_PLAN_EXTRA_ARGS)

tf-apply:
	@if [ -z "$(HELIOCLOUD_TERRAFORM_ENVIRONMENT)" ]; then \
		echo "error: HELIOCLOUD_TERRAFORM_ENVIRONMENT not set, try again"; \
		exit 1; \
	fi

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

	$(TERRAFORM_BIN) output $(TERRAFORM_EXTRA_ARGS) $(TERRAFORM_OUTPUT_EXTRA_ARGS) -json| jq .eks_cluster_name.value > .makefile_output.aws-eks-update-nodegroup-version_output.txt
	$(eval EKS_CLUSTER_NAME := $(shell cat $(shell pwd)/.makefile_output.aws-eks-update-nodegroup-version_output.txt))

	bash scripts/update-eks-nodegroups-version.sh $(EKS_CLUSTER_NAME)
	rm -rf .makefile_output.aws-eks-update-nodegroup-version_output.txt


# k8
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

	python $(HELIOCLOUD_PLATFORM_ROOT)/setup_commands/kube/apply_tf_outputs_to_k8s.py \
		--environment_folder=$(HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER) \
		--dest_folder=$(HELIOCLOUD_TERRAFORM_ENVIRONMENTS_FOLDER)/kube \
		$(HELIOCLOUD_TERRAFORM_ENVIRONMENT)

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
