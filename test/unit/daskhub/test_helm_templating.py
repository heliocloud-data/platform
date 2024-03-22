import os

import pytest
from utils import (
    which,
    sanitize_snapshots,
)

PATH_TO_RESOURCES = f"{os.path.dirname(__file__)}/../resources/test_helm_templating"

HELM_OPT_KUBE_VERSION = "1.29"
HELM_OPT_API_VERSION = "1.29"

HELM_OPT_JUPYTERHUB_VERSION = "1.2.0"
HELM_OPT_DASKHUB_CURR_VERSION = "2022.08.02"
HELM_OPT_DASKHUB_NEXT1_VERSION = "2022.11.0"


@pytest.fixture(scope="function", autouse=True)
def before():
    """
    Update the helm repositories prior to executing the tests, this ensures that the required
    dependent helm charts are already installed on the system.
    """
    os.system("helm repo add jupyterhub https://hub.jupyter.org/helm-chart/")
    os.system("helm repo update")
    os.system(f"helm pull jupyterhub/jupyterhub --version={HELM_OPT_JUPYTERHUB_VERSION}")

    os.system("helm repo add dask https://helm.dask.org/")
    os.system("helm repo update")
    os.system(f"helm pull dask/daskhub --version={HELM_OPT_DASKHUB_CURR_VERSION}")

    os.system("helm repo add dask https://helm.dask.org/")
    os.system("helm repo update")
    os.system(f"helm pull dask/daskhub --version={HELM_OPT_DASKHUB_NEXT1_VERSION}")


def do_execute_helm_template(snapshot, params: dict):
    """
    This test checks that the output produced by the helm template
    consistent w/ what we expect.  It's also a living document intended
    to show how kustomize fits into our chain.
    """
    values_to_remove_from_snapshot = params["values_to_remove_from_snapshot"]

    name = params["repo_name"]
    chart = params["chart"]["name"]
    version = params["chart"]["version"]
    namespace = params["namespace"]
    extra_ops = params["extra_opts"]

    output_filename = params["output_filename"]
    output_file_original = os.path.abspath(f"temp/test_helm_templating/ORIGINAL-{output_filename}")
    output_file_cleaned = os.path.abspath(f"temp/test_helm_templating/CLEANED-{output_filename}")
    values = params["values"]

    helm_cmd = f"helm template {name} {chart} --api-versions={HELM_OPT_API_VERSION} --api-versions={HELM_OPT_KUBE_VERSION} --namespace={namespace} --version={version}"

    if "wd" in params and params["wd"] != "":
        helm_cmd = f"cd {params['wd']} && pwd && {helm_cmd}"
    for value in values:
        helm_cmd = f"{helm_cmd} --values={value}"

    if "post_render_hook" in params and params["post_render_hook"] != "":
        helm_cmd = f"{helm_cmd} --post-renderer={params['post_render_hook']}"

    helm_cmd = f"{helm_cmd} {extra_ops}"

    # Write the file
    cmd = f"{helm_cmd} > {output_file_original}"
    print(cmd)

    os.makedirs(os.path.dirname(output_file_original), exist_ok=True)
    os.system(cmd)

    # Clean the file, by removing any non-deterministic settings that will change run-to-run
    sanitize_snapshots(output_file_original, output_file_cleaned, values_to_remove_from_snapshot)

    snapshot.snapshot_dir = f"{PATH_TO_RESOURCES}/snapshots"
    with open(output_file_cleaned, "r") as f:
        actual = f.read()

    snapshot.assert_match(actual, output_filename)


@pytest.mark.skipif(which("helm") is None, reason="kustomize not installed")
def test_with_values_no_kustomize_jupyterhub_deployment_autohttps_enabled(snapshot):
    """
    This test checks that the output produced by the helm template
    consistent w/ what we expect.  It's also a living document intended
    to show how kustomize fits into our chain.
    """

    do_execute_helm_template(
        snapshot,
        params={
            "repo_name": "jupyterhub",
            "chart": {
                "name": "jupyterhub/jupyterhub",
                "version": HELM_OPT_JUPYTERHUB_VERSION,
            },
            "namespace": "daskhub",
            "values": [
                f"{PATH_TO_RESOURCES}/jupyterhub-letsencrypt-values-{HELM_OPT_JUPYTERHUB_VERSION}.yaml",
            ],
            "extra_opts": "--debug --dry-run",
            "output_filename": "test_with_values_no_kustomize_jupyterhub_deployment_autohttps_enabled.yaml",
            "values_to_remove_from_snapshot": [
                "/data/hub.config.ConfigurableHTTPProxy.auth_token",
                "/data/hub.config.JupyterHub.cookie_secret",
                "/data/hub.config.CryptKeeper.keys",
                "/spec/template/metadata/annotations/checksum?config-map",
                "/spec/template/metadata/annotations/checksum?secret",
                "/spec/template/metadata/annotations/checksum?auth-token",
                "/spec/template/metadata/annotations/checksum?proxy-secret",
            ],
        },
    )


@pytest.mark.skipif(which("kustomize") is None, reason="kustomize not installed")
@pytest.mark.skipif(which("helm") is None, reason="kustomize not installed")
def test_with_values_with_kustomize_jupyterhub_deployment_autohttps_enabled(snapshot):
    """
    This test checks that the output produced by the helm template
    consistent w/ what we expect.  It's also a living document intended
    to show how kustomize fits into our chain.
    """

    do_execute_helm_template(
        snapshot,
        params={
            "repo_name": "jupyterhub",
            "chart": {
                "name": "jupyterhub/jupyterhub",
                "version": HELM_OPT_JUPYTERHUB_VERSION,
            },
            "namespace": "daskhub",
            "values": [
                f"{PATH_TO_RESOURCES}/jupyterhub-letsencrypt-values-{HELM_OPT_JUPYTERHUB_VERSION}.yaml",
            ],
            "post_render_hook": "./kustomize-post-renderer-hook.sh",
            "wd": "daskhub/deploy",
            "extra_opts": "--debug --dry-run",
            "output_filename": "test_with_values_with_kustomize_jupyterhub_deployment_autohttps_enabled.yaml",
            "values_to_remove_from_snapshot": [
                "/data/checksum_hook-image-puller",
                "/data/hub.config.ConfigurableHTTPProxy.auth_token",
                "/data/hub.config.JupyterHub.cookie_secret",
                "/data/hub.config.CryptKeeper.keys",
                "/spec/template/metadata/annotations/checksum?config-map",
                "/spec/template/metadata/annotations/checksum?secret",
                "/spec/template/metadata/annotations/checksum?auth-token",
                "/spec/template/metadata/annotations/checksum?proxy-secret",
            ],
        },
    )


@pytest.mark.skipif(which("kustomize") is None, reason="kustomize not installed")
@pytest.mark.skipif(which("helm") is None, reason="kustomize not installed")
def test_with_values_with_kustomize_daskhub_deployment(snapshot):
    """
    This test checks that the output produced by the helm template
    consistent w/ what we expect.  It's also a living document intended
    to show how kustomize fits into our chain.
    """

    do_execute_helm_template(
        snapshot,
        params={
            "repo_name": "daskhub",
            "chart": {
                "name": "dask/daskhub",
                "version": HELM_OPT_DASKHUB_CURR_VERSION,
            },
            "namespace": "daskhub",
            "values": [
                "dh-auth.yaml.template",
                "dh-config.yaml.template",
                "dh-secrets.yaml.template",
            ],
            "post_render_hook": "./kustomize-post-renderer-hook.sh",
            "wd": "daskhub/deploy",
            "extra_opts": "--debug --dry-run",
            "output_filename": "test_with_values_with_kustomize_daskhub_deployment.yaml",
            "values_to_remove_from_snapshot": [
                "/data/checksum_hook-image-puller",
                "/data/hub.config.ConfigurableHTTPProxy.auth_token",
                "/data/hub.config.JupyterHub.cookie_secret",
                "/data/hub.config.CryptKeeper.keys",
                "/data/values.yaml",
                "/spec/template/metadata/annotations/checksum?config-map",
                "/spec/template/metadata/annotations/checksum?secret",
                "/spec/template/metadata/annotations/checksum?auth-token",
                "/spec/template/metadata/annotations/checksum?proxy-secret",
            ],
        },
    )


@pytest.mark.skipif(which("kustomize") is None, reason="kustomize not installed")
@pytest.mark.skipif(which("helm") is None, reason="kustomize not installed")
def test_with_values_no_kustomize_daskhub_deployment_next(snapshot):
    """
    This test checks that the output produced by the helm template
    consistent w/ what we expect.  It's also a living document intended
    to show how kustomize fits into our chain.
    """

    do_execute_helm_template(
        snapshot,
        params={
            "repo_name": "daskhub",
            "chart": {
                "name": "dask/daskhub",
                "version": HELM_OPT_DASKHUB_NEXT1_VERSION,
            },
            "namespace": "daskhub",
            "values": [
                "dh-auth.yaml.template",
                "dh-config.yaml.template",
                "dh-secrets.yaml.template",
            ],
            "post_render_hook": "./kustomize-post-renderer-hook.sh",
            "wd": "daskhub/deploy",
            "extra_opts": "--debug --dry-run",
            "output_filename": "test_with_values_no_kustomize_daskhub_deployment_next.yaml",
            "values_to_remove_from_snapshot": [
                "/data/checksum_hook-image-puller",
                "/data/hub.config.ConfigurableHTTPProxy.auth_token",
                "/data/hub.config.JupyterHub.cookie_secret",
                "/data/hub.config.CryptKeeper.keys",
                "/data/values.yaml",
                "/spec/template/metadata/annotations/checksum?config-map",
                "/spec/template/metadata/annotations/checksum?secret",
                "/spec/template/metadata/annotations/checksum?auth-token",
                "/spec/template/metadata/annotations/checksum?proxy-secret",
            ],
        },
    )
