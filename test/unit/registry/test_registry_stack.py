import pytest
import unittest
from unittest.mock import patch, MagicMock

from registry.lambdas.app.core.constants import (
    DEFAULT_PANDA_LAYERS_ARN,
)


def which(program):
    """
    This function provides the location of an executable that *should be on the
    path.  This is ultimately used to determine if 'node' is installed in the
    environment, which is a requirement for all tests within this file.
    """
    import os

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


class TestRegistryStack(unittest.TestCase):
    @pytest.mark.skipif(which("node") is None, reason="node not installed")
    @patch("base_aws.base_aws_stack.BaseAwsStack")
    @patch("aws_cdk.aws_docdb.DatabaseCluster")
    @patch("aws_cdk.aws_lambda.Function")
    @patch("aws_cdk.aws_s3.Bucket")
    def test_constructor_config__default(
        self, base_aws_stack, database_cluster, lambda_function, s3_bucket
    ) -> None:
        """
        This test checks verifies the resulting configuration with the default settings.
        """

        # This is certainly feels strange, but appeared to be required for this
        # test to run successfully on the CI server.  Basically, importing
        # RegistryStack also does an of 'aws_cdk.__init__' which causes an
        # exception during start up.  By moving the import here, and supplying
        # a patch, we're able to instantiate the stack.
        from registry.registry_stack import RegistryStack

        cfg = {
            "registry": {
                "destroyOnRemoval": False,
                "datasetBucketNames": [],
                "catalog": {
                    "masterUser": "Ash Ketchum",
                    "name": "Pikachu",
                    "contact": "pikachu25@pokemoncenter.com",
                },
            }
        }

        scope = None
        construct_id = "constructid"
        rs = RegistryStack(scope, construct_id, cfg, base_aws_stack)
        self.assertEqual(rs.pandas_layer_arn, DEFAULT_PANDA_LAYERS_ARN)

        # Update the configs to include empty values for the optional
        # elements.
        cfg["registry"]["layers"] = {}

        scope = None
        construct_id = "constructid"
        rs = RegistryStack(scope, construct_id, cfg, base_aws_stack)
        self.assertEqual(rs.pandas_layer_arn, DEFAULT_PANDA_LAYERS_ARN)

    @pytest.mark.skipif(which("node") is None, reason="node not installed")
    @patch("base_aws.base_aws_stack.BaseAwsStack")
    @patch("aws_cdk.aws_docdb.DatabaseCluster")
    @patch("aws_cdk.aws_lambda.Function")
    @patch("aws_cdk.aws_s3.Bucket")
    def test_constructor_config__pandas_arn_set(
        self, base_aws_stack, database_cluster, lambda_function, s3_bucket
    ) -> None:
        """
        This test checks verifies the resulting configuration with the panda layers set.
        """

        # This is certainly feels strange, but appeared to be required for this
        # test to run successfully on the CI server.  Basically, importing
        # RegistryStack also does an of 'aws_cdk.__init__' which causes an
        # exception during start up.  By moving the import here, and supplying
        # a patch, we're able to instantiate the stack.
        from registry.registry_stack import RegistryStack

        cfg = {
            "registry": {
                "destroyOnRemoval": False,
                "datasetBucketNames": [],
                "catalog": {
                    "masterUser": "Ash Ketchum",
                    "name": "Pikachu",
                    "contact": "pikachu25@pokemoncenter.com",
                },
                "layers": {
                    "pandas": "" "arn:aws:lambda:pkm-alola-1:000000000760:layer:BEWEAR-Python39:6",
                },
            }
        }

        scope = None
        construct_id = "constructid"
        rs = RegistryStack(scope, construct_id, cfg, base_aws_stack)
        self.assertEqual(
            rs.pandas_layer_arn, "arn:aws:lambda:pkm-alola-1:000000000760:layer:BEWEAR-Python39:6"
        )
