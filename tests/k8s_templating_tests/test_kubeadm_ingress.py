
import os

import pytest

import k8s_templating_tests.utils as utils

from pathlib import Path

app_path="kubeadm/ingress"

logical_test_name="test_kube_kubeadm_ingress"
test_workspace_dir=f"temp/{logical_test_name}"
k8s_workspace_dir=f"{test_workspace_dir}/kube"
environment_name="unit-test"

@pytest.fixture(scope="function", autouse=True)
def before():
    utils.delete_workspace(k8s_workspace_dir)
    utils.prepare_workspace(k8s_workspace_dir, "tests/resources", environment_name)

def test_something(snapshot):
    original_output_file=f"{test_workspace_dir}/ORIGINAL-kubeadm-ingress.yaml"
    cleaned_output_file=f"{test_workspace_dir}/CLEANED-kubeadm-ingress.yaml"
    utils.run_helm_template(
        name="ingress",
        chart="./",
        namespace="kube-system",
        values_files=["values.yaml", f"values-{environment_name}.yaml"],
        output_file=original_output_file,
        wd=f"{k8s_workspace_dir}/{app_path}"
    )

    utils.sanitize_snapshots(
        input_file=original_output_file,
        output_file=cleaned_output_file,
        values_to_remove_from_snapshot=[
            "/data/redis-password",
        ]
    )

    snapshot.snapshot_dir = f"tests/snapshots/{logical_test_name}"
    with open(cleaned_output_file, "r") as f:
        actual = f.read()

    snapshot.assert_match(actual, "BASELINE-kubeadm-ingress.yaml")
