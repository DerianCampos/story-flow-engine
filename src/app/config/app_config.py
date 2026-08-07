import os
from dotenv import load_dotenv
from pyaml_env import parse_config
from threading import Lock
from typing import Dict, Any, Optional

from src.app.shared.log_config import get_logger, initialize_logging
from src.app.shared.utils.retry_decorator import retry_on_exception
from src.app.config.paths import Paths

APP_ENV = "APP_ENV"
DEFAULT_ENVIRONMENT = "local"

log = get_logger(__name__)


class AppConfig:
    """
    Singleton class for loading and managing application configuration.
    This class is responsible for:
    - Loading environment variables from a `.env` file.
    - Parsing YAML configuration files based on the current environment.
    """
    _instance: Optional['AppConfig'] = None
    _lock = Lock()

    def __init__(self):
        """
        Initializes the AppConfiguration instance.
        Sets the default environment and loads the configuration.
        """
        if AppConfig._instance is not None:
            raise RuntimeError("Use AppConfiguration.instance() to get the singleton instance")

        self.env: str = DEFAULT_ENVIRONMENT
        self.config: Dict[str, Any] = {}
        self._initialized = False
        self.load_app_configuration()
        self._initialized = True

    @classmethod
    def instance(cls) -> 'AppConfig':
        """
        Provides a thread-safe Singleton instance of AppConfiguration.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-checked locking
                    cls._instance = cls()
        return cls._instance

    def load_app_configuration(self):
        """
        Loads the application configuration by:
        - Fetching environment variables.
        - Parsing the environment-specific YAML configuration file.
        - Initializing the root logger from the `logging` config section.
        """
        self.load_environment_variables()
        self.load_config_yaml_file()
        self.initialize_logging()

    def initialize_logging(self):
        """
        Configures the root logger from the `logging` section of the YAML config.
        Local/container runs use plain text output (`format_type: "text"`);
        dev/prod use single-line JSON (the default).
        """
        logging_config = self.get_config("logging", default={})
        initialize_logging(
            level=logging_config.get("level", "INFO").upper(),
            format_type=logging_config.get("format_type", "json"),
            console_enabled=logging_config.get("console", {}).get("enabled", True),
            console_colored=logging_config.get("console", {}).get("colored", False),
        )

    @retry_on_exception()
    def load_environment_variables(self):
        """
        Loads environment variables from the `.env` file.
        Sets the application environment using the `APP_ENV` variable.
        """
        try:
            log.info(f"Loading environment variables from .env file...{Paths.ENV_FILE_PATH}")
            load_dotenv(Paths.ENV_FILE_PATH)
            env_value = os.environ.get(APP_ENV, DEFAULT_ENVIRONMENT)
            self.env = env_value.lower() if env_value else DEFAULT_ENVIRONMENT

            log.info(f"Environment set to: {self.env}")

        except Exception as e:
            log.error(f"Error loading environment variables. Exception: {e}")
            raise

    @retry_on_exception()
    def load_config_yaml_file(self):
        """
        Loads the YAML configuration file specific to the current environment.
        """
        config_file = f"config_{self.env}.yml"

        try:
            full_config_file_path = Paths.CONFIG_DIR / config_file

            if not full_config_file_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {full_config_file_path}")

            self.config = parse_config(path=str(full_config_file_path))
            log.info(f"Successfully loaded configuration from: {config_file}")

        except Exception as e:
            log.error(f"Error loading configuration file {config_file}. Exception: {e}")
            raise

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Gets a specific configuration value by key.

        Args:
            key: The configuration key (supports dot notation like 'database.host')
            default: Default value if key is not found

        Returns:
            The configuration value or default
        """
        keys = key.split('.')
        value = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    @classmethod
    def reset_instance(cls):
        """
        Resets the singleton instance (useful for testing).
        """
        with cls._lock:
            cls._instance = None
