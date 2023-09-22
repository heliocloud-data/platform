import os

import pytest

from utils import (
    which,
    sanitize_snapshots,
)

PATH_TO_RESOURCES = f"{os.path.dirname(__file__)}/../resources/test_helm_templating"


@pytest.mark.skipif(which("helm") is None, reason="kustomize not installed")
def test_with_values_no_kustomize_jupyterhub_deployment_autohttps_enabled(snapshot):
    """
    This test checks that the output produced by the helm template
    consistent w/ what we expect.  It's also a living document intended
    to show how kustomize fits into our chain.
    """
    values_to_remove_from_snapshot = [
        "/data/hub.config.ConfigurableHTTPProxy.auth_token",
        "/data/hub.config.JupyterHub.cookie_secret",
        "/data/hub.config.CryptKeeper.keys",
        "/spec/template/metadata/annotations/checksum?config-map",
        "/spec/template/metadata/annotations/checksum?secret",
        "/spec/template/metadata/annotations/checksum?auth-token",
        "/spec/template/metadata/annotations/checksum?proxy-secret",
    ]

    name = "jupyterhub"
    chart = "jupyterhub/jupyterhub"
    version = "1.2.0"
    namespace = "daskhub"
    extra_ops = "--debug --dry-run"

    output_filename = "test_with_values_no_kustomize_jupyterhub_deployment_autohttps_enabled.yaml"
    output_file_original = f"temp/test_helm_templating/ORIGINAL-{output_filename}"
    output_file_cleaned = f"temp/test_helm_templating/CLEANED-{output_filename}"
    value_file_1 = f"{PATH_TO_RESOURCES}/jupyterhub-letsencrypt-values-{version}.yaml"

    # Write the file
    cmd = f"helm template {name} {chart} --namespace={namespace} --version={version} --values={value_file_1} {extra_ops} > {output_file_original}"
    print(cmd)

    os.makedirs(os.path.dirname(output_file_original), exist_ok=True)
    os.system(cmd)

    # Clean the file, by removing any non-deterministic settings that will change run-to-run
    sanitize_snapshots(output_file_original, output_file_cleaned, values_to_remove_from_snapshot)

    snapshot.snapshot_dir = f"{PATH_TO_RESOURCES}/snapshots"
    with open(output_file_cleaned, "r") as f:
        actual = f.read()

    snapshot.assert_match(actual, output_filename)


@pytest.mark.skipif(which("kustomize") is None, reason="kustomize not installed")
@pytest.mark.skipif(which("helm") is None, reason="kustomize not installed")
def test_with_values_with_kustomize_jupyterhub_deployment_autohttps_enabled(snapshot):
    """
    This test checks that the output produced by the helm template
    consistent w/ what we expect.  It's also a living document intended
    to show how kustomize fits into our chain.
    """
    values_to_remove_from_snapshot = [
        "/data/hub.config.ConfigurableHTTPProxy.auth_token",
        "/data/hub.config.JupyterHub.cookie_secret",
        "/data/hub.config.CryptKeeper.keys",
        "/spec/template/metadata/annotations/checksum?config-map",
        "/spec/template/metadata/annotations/checksum?secret",
        "/spec/template/metadata/annotations/checksum?auth-token",
        "/spec/template/metadata/annotations/checksum?proxy-secret",
    ]

    name = "jupyterhub"
    chart = "jupyterhub/jupyterhub"
    version = "1.2.0"
    namespace = "daskhub"
    extra_ops = "--debug --dry-run"

    output_filename = "test_with_values_with_kustomize_jupyterhub_deployment_autohttps_enabled.yaml"
    output_file_original = os.path.abspath(f"temp/test_helm_templating/ORIGINAL-{output_filename}")
    output_file_cleaned = os.path.abspath(f"temp/test_helm_templating/CLEANED-{output_filename}")
    value_file_1 = os.path.abspath(
        f"{PATH_TO_RESOURCES}/jupyterhub-letsencrypt-values-{version}.yaml"
    )

    post_render_hook = "./kustomize-post-renderer-hook.sh"
    # Write the file
    cmd = f"cd daskhub/deploy && pwd && helm template {name} {chart} --namespace={namespace} --version={version} --values={value_file_1} --post-renderer={post_render_hook} {extra_ops} > {output_file_original}"
    print(cmd)

    os.makedirs(os.path.dirname(output_file_original), exist_ok=True)
    os.system(cmd)

    # Clean the file, by removing any non-deterministic settings that will change run-to-run
    sanitize_snapshots(output_file_original, output_file_cleaned, values_to_remove_from_snapshot)

    snapshot.snapshot_dir = f"{PATH_TO_RESOURCES}/snapshots"
    with open(output_file_cleaned, "r") as f:
        actual = f.read()

    snapshot.assert_match(actual, output_filename)
