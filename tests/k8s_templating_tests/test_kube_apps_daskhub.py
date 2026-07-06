
import os

import pytest

import k8s_templating_tests.utils as utils

from pathlib import Path

app_path="apps/daskhub"

logical_test_name="test_kube_apps_daskhub"
test_workspace_dir=f"temp/{logical_test_name}"
k8s_workspace_dir=f"{test_workspace_dir}/kube"
environment_name="unit-test"

@pytest.fixture(scope="function", autouse=True)
def before():
    utils.delete_workspace(k8s_workspace_dir)
    utils.prepare_workspace(k8s_workspace_dir, "tests/resources", environment_name)

def test_something(snapshot):
    original_output_file=f"{test_workspace_dir}/ORIGINAL-apps-daskhub.yaml"
    cleaned_output_file=f"{test_workspace_dir}/CLEANED-apps-daskhub.yaml"
    utils.run_helm_template(
        name="daskhub",
        chart="./",
        namespace="daskhub",
        values_files=["values.yaml", f"values-{environment_name}.yaml"],
        post_render_hook="./kustomize-post-renderer-hook.sh",
        output_file=original_output_file,
        wd=f"{k8s_workspace_dir}/{app_path}"
    )

    utils.sanitize_snapshots(
        input_file=original_output_file,
        output_file=cleaned_output_file,
        values_to_remove_from_snapshot=[
            "/data/checksum_hook-image-puller",
            "/data/hub.config.ConfigurableHTTPProxy.auth_token",
            "/data/hub.config.JupyterHub.cookie_secret",
            "/data/hub.config.CryptKeeper.keys",
            "/data/values.yaml",
            "/spec/template/metadata/annotations/checksum?config-map",
            "/spec/template/metadata/annotations/checksum?secret",
            "/spec/template/metadata/annotations/checksum?auth-token",
            "/spec/template/metadata/annotations/checksum?proxy-secret",
        ]
    )

    snapshot.snapshot_dir = f"tests/snapshots/{logical_test_name}"
    with open(cleaned_output_file, "r") as f:
        actual = f.read()

    snapshot.assert_match(actual, "BASELINE-apps-daskhub.yaml")
