import os

import pytest
from utils import (
    which,
    do_execute_helm_template,
)

from daskhub.jinja_utils import apply_jinja_templates_by_dir

PATH_TO_RESOURCES = f"{os.path.dirname(__file__)}/../resources/test_helm_templating"

HELM_OPT_KUBE_VERSION = "1.29"
HELM_OPT_API_VERSION = "1.29"

HELM_OPT_JUPYTERHUB_VERSION = "3.2.1"
HELM_OPT_DASKHUB_CURR_VERSION = "2024.1.1"
HELM_OPT_DASKHUB_NEXT1_VERSION = "2024.1.1"

PREJINJA_DASKHUB_HELM_CHART_PATH = "daskhub/deploy/daskhub"
POSTJINJA_DASKHUB_HELM_CHART_PATH = "temp/daskhub/deploy/daskhub"

HELIOCLOUD_DASKHUB_RENDER_PARAMS = {
    "config": {
        "global": {"domain_url": "<INSERT_DOMAIN_URL>"},
        "eksctl": {"metadata": {"name": "eks-helio"}},
        "daskhub": {
            "namespace": "daskhub",
            "api_key1": "<INSERT_API_KEY1>",
            "api_key2": "<INSERT_API_KEY2>",
            "admin_users": ["Me!"],
            "contact_email": "<INSERT_CONTACT_EMAIL>",
            "GENERIC_DOCKER_LOCATION": "<GENERIC_DOCKER_LOCATION>",
            "GENERIC_DOCKER_VERSION": "<GENERIC_DOCKER_VERSION>",
            "MLTRCH_DOCKER_LOCATION": "<MLTRCH_DOCKER_LOCATION>",
            "MLTRCH_DOCKER_VERSION": "<MLTRCH_DOCKER_VERSION>",
            "MLTF_DOCKER_LOCATION": "<MLTF_DOCKER_LOCATION>",
            "MLTF_DOCKER_VERSION": "<MLTF_DOCKER_VERSION>",
            "domain_record": "daskhub",
        },
    }
}


@pytest.fixture(scope="function", autouse=True)
def before():
    """
    Update the helm repositories prior to executing the tests, this ensures that the required
    dependent helm charts are already installed on the system.
    """
    os.system("helm repo add jupyterhub https://hub.jupyter.org/helm-chart/")
    os.system("helm repo update")
    os.system(f"helm pull jupyterhub/jupyterhub --version={HELM_OPT_JUPYTERHUB_VERSION}")


@pytest.mark.skipif(which("kustomize") is None, reason="kustomize not installed")
@pytest.mark.skipif(which("helm") is None, reason="helm not installed")
def test_with_values_with_kustomize_daskhub_deployment(snapshot):
    """
    This test checks that the output produced by the helm template
    consistent w/ what we expect.  It's also a living document intended
    to show how kustomize fits into our chain.
    """

    apply_jinja_templates_by_dir(
        PREJINJA_DASKHUB_HELM_CHART_PATH,
        POSTJINJA_DASKHUB_HELM_CHART_PATH,
        HELIOCLOUD_DASKHUB_RENDER_PARAMS,
    )

    do_execute_helm_template(
        snapshot,
        params={
            "repo_name": "daskhub",
            "chart": {
                "name": "./",
            },
            "namespace": "daskhub",
            "values": [
                "values.yaml",
                "values-production.yaml",
            ],
            "post_render_hook": "./kustomize-post-renderer-hook.sh",
            "wd": POSTJINJA_DASKHUB_HELM_CHART_PATH,
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
                "/spec/template/metadata/annotations/checksum?proxy-secret",
                "/spec/strategy/rollingUpdate",  # This guy appears on GitLab CI for some reason
            ],
        },
    )


@pytest.mark.skipif(which("kustomize") is None, reason="kustomize not installed")
@pytest.mark.skipif(which("helm") is None, reason="helm not installed")
def test_with_values_no_kustomize_daskhub_deployment_next(snapshot):
    """
    This test checks that the output produced by the helm template
    consistent w/ what we expect.  It's also a living document intended
    to show how kustomize fits into our chain.
    """

    apply_jinja_templates_by_dir(
        PREJINJA_DASKHUB_HELM_CHART_PATH,
        POSTJINJA_DASKHUB_HELM_CHART_PATH,
        HELIOCLOUD_DASKHUB_RENDER_PARAMS,
    )

    # Update the dependency in the helm chart to be the next version.
    os.system(
        f"sed 's#version: {HELM_OPT_DASKHUB_CURR_VERSION}#version: {HELM_OPT_DASKHUB_NEXT1_VERSION}#' -i {POSTJINJA_DASKHUB_HELM_CHART_PATH}/Chart.yaml"
    )

    do_execute_helm_template(
        snapshot,
        params={
            "repo_name": "daskhub",
            "chart": {
                "name": "./",
            },
            "namespace": "daskhub",
            "values": [
                "values.yaml",
                "values-production.yaml",
            ],
            "post_render_hook": "./kustomize-post-renderer-hook.sh",
            "wd": POSTJINJA_DASKHUB_HELM_CHART_PATH,
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
                "/spec/strategy/rollingUpdate",  # This guy appears on GitLab CI for some reason
            ],
        },
    )
