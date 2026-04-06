import os

import pytest
from utils import (
    which,
    do_execute_kustomize,
)

from daskhub.jinja_utils import apply_jinja_templates_by_dir

PREJINJA_DASKHUB_HELM_CHART_PATH = "daskhub/deploy/eksctl"
POSTJINJA_DASKHUB_HELM_CHART_PATH = "temp/daskhub/deploy/eksctl"

RENDER_PARAMS = {
    "config": {
        "eksctl": {
            "metadata": {"name": "eks-helio", "region": "us-south-100"},
            "availabilityZones": [
                "<INSERT_PRIMARY_AVAILABILITY_ZONE>",
                "<INSERT_SECONDARY_AVAILABILITY_ZONE>",
            ],
        },
        "daskhub": {
            "namespace": "daskhub",
        },
    }
}


@pytest.mark.skipif(which("kustomize") is None, reason="kustomize not installed")
def test_eksctl_default(snapshot):
    """
    This test checks that the output produced by the helm template
    consistent w/ what we expect.  It's also a living document intended
    to show how kustomize fits into our chain.
    """

    apply_jinja_templates_by_dir(
        PREJINJA_DASKHUB_HELM_CHART_PATH,
        POSTJINJA_DASKHUB_HELM_CHART_PATH,
        RENDER_PARAMS,
    )

    do_execute_kustomize(
        snapshot,
        "test_eksctl_templating",
        params={
            "values_to_remove_from_snapshot": [],
            "overlay_path": "eksctl/overlays/production",
            "output_filename": "test_eksctl_default.yaml",
            "wd": "temp/daskhub/deploy",
            "extra_opts": "",
        },
    )
