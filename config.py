import yaml

class Config:

    def load_configs(self, basedir: str = None, id: str = None) -> dict:
        """
        Get the config for this HelioCloud instance.
        """
        # Get the instance for this instance
        # First load the default instance

        if basedir is None:
            basedir = 'instance'

        configuration = dict()
        with open(f"{basedir}/default.yaml", "r") as default_config_file:
            configuration = yaml.safe_load(default_config_file)

        with open(f"{basedir}/{id}.yaml") as instance_config_file:
            configuration.update(yaml.safe_load(instance_config_file))

        return configuration
