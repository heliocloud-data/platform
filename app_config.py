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

    # If an instance config is present, load and override the default
    if hc_id is not None:
        with open(f"{basedir}/{hc_id}.yaml", encoding="utf-8") as instance_config_file:
            new_dict = {}
            update_cfgs(new_dict, [configuration, yaml.safe_load(instance_config_file)])
            configuration = new_dict

    return configuration


def update_cfgs(dest: dict, cfgs: list):
    if not isinstance(dest, dict):
        raise ValueError(f"dest is not a dict")
    if not isinstance(cfgs, list):
        raise ValueError(f"cfgs is not a list")

    for cfg in cfgs:
        if not isinstance(cfg, dict):
            raise ValueError(f"Element in cfgs is not a dict")

        for key, value in cfg.items():
            if key not in dest:
                dest[key] = value
            elif not isinstance(dest[key], dict) or not isinstance(cfg[key], dict):
                # this key already exist, but it isn't a dict, overwrite
                dest[key] = value
            else:
                # this key already exists and it's a dictionary, smart
                # merge.
                update_cfgs(dest[key], [cfg[key]])
