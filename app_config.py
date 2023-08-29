"""
Utility functions for loading CDK instance configurations intended for use
within the CDK as well as unit and integration tests.
"""
import yaml


def load_configs(basedir: str = None, hc_id: str = None) -> dict:
    """
    Get the config for this HelioCloud instance.
    """

    # Get the instance for this instance
    # First load the default instance

    if basedir is None:
        basedir = "instance"

    configuration = {}
    with open(f"{basedir}/default.yaml", "r", encoding="utf-8") as default_config_file:
        configuration = yaml.safe_load(default_config_file)

    with open(f"{basedir}/{hc_id}.yaml", encoding="utf-8") as instance_config_file:
        configuration.update(yaml.safe_load(instance_config_file))

    return configuration
