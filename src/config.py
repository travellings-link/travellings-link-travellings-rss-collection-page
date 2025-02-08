import tomllib

from src.utils import SingletonMeta


class ConfigManager(metaclass=SingletonMeta):
    def __init__(self, config_file):
        self.config_file = config_file
        with open(config_file, "rb") as f:
            self.config = tomllib.load(f)

    def get(self, section, option, default=None):
        return self.config.get(section, {}).get(option, default)


config_file = "config.toml"
config_manager = ConfigManager(config_file)
