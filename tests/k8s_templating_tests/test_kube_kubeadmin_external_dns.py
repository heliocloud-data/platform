
import os

import pytest

import k8s_templating_tests.utils as utils

app_path="kubeadm/external-dns"

logical_test_name="test_kube_kubeadm_external-dns"
test_workspace_dir=f"temp/{logical_test_name}"
k8s_workspace_dir=f"{test_workspace_dir}/kube"
environment_name="unit-test"

@pytest.fixture(scope="function", autouse=True)
def before():
    utils.delete_workspace(k8s_workspace_dir)
    utils.prepare_workspace(k8s_workspace_dir, "tests/resources", environment_name)

def test_something(snapshot):
    original_output_file=f"{test_workspace_dir}/ORIGINAL-kubeadm-external-dns.yaml"
    utils.run_kustomize(
        kustomization_dir=f"{k8s_workspace_dir}/{app_path}/overlays/{environment_name}",
        output_file=original_output_file)

    cleaned_output_file=original_output_file

    snapshot.snapshot_dir = f"tests/snapshots/{logical_test_name}"
    with open(cleaned_output_file, "r") as f:
        actual = f.read()

    snapshot.assert_match(actual, "BASELINE-kubeadm-external-dns.yaml")
