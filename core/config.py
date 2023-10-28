"""
config.py

This module provides a Config class for reading and managing configuration options
from a configuration file. It also defines a custom exception, SchedulingConflictError,
for indicating scheduling conflicts in the configuration.

Usage:
    The ConfigReader class allows you to read and access various configuration settings, including options related
    to self-scheduling and delay scheduling. It ensures that configuration options do not conflict when using features
    like self-scheduling and delay scheduling.

Note:
    - When using self-scheduling and delay scheduling features, it is important to ensure that configuration options do
      not conflict with each other.
"""

import configparser
import logging
import os


class SchedulingConflictError(Exception):
    """Custom exception to indicate a scheduling conflict in configuration."""

# TODO: Update and add docstrings
# TODO: Add lock-file configuration with %s(email) support


class Config:
    """
    Read and manage configuration options from a configuration file.

    This class allows you to read and access various configuration options from a configuration file. It provides
    properties for retrieving configuration settings, including options related to self-scheduling and delay scheduling.

    Note:
        - It is important to ensure that configuration options do not conflict, especially when using self-scheduling
          and delay scheduling features.
    """
    _instance = None

    def __init__(self, config_file):
        """
        Initialize a Config object.

        Args:
            config_file (str): Path to the configuration file.
        """
        self.config = configparser.ConfigParser()
        self.file_path = config_file
        self.fallback_base_path = os.path.dirname(os.path.realpath(self.file_path))
        self.config.read(config_file)

    @property
    def is_self_scheduling(self):
        """
        Get the 'script_is_self_scheduling' configuration option.

        If set to True, the script is designed to handle its own scheduling and may run indefinitely if free offers are
        available.

        Note:
            - This option is intended for advanced use cases where the script's internal logic manages scheduling.
            - Do not use this option in conjunction with the 'allow_scheduling' option; they should not both be set to True simultaneously.

        Returns:
            bool: True if the script is self-scheduling, False otherwise.
        """
        return self.config.getboolean(
            "General", "script_is_self_scheduling", fallback=False
        )

    @property
    def allow_scheduling(self):
        """
        Get the 'allow_scheduling' configuration option.

        If set to True, the script may delay a package purchase if the package can't be purchased at execution time.
        The delay is implemented using the `sched` package if the package can be purchased in between the current time
        and the current time plus the 'max_delay_scheduling_time' configuration option.

        Note:
            - This option cannot be used in conjunction with the 'is_self_scheduling' option.
              Both options should not be set to True simultaneously.

        Returns:
            bool: True if scheduling is allowed, False otherwise.
        """
        return self.config.getboolean("General", "allow_scheduling", fallback=False)

    @property
    def max_delay_scheduling_time(self):
        """
        Get the 'max_delay_scheduling_time' configuration option.

        This option specifies the maximum delay, in seconds, for scheduling a package purchase if 'allow_scheduling' is set to True.
        The script may delay the purchase for this duration using the `sched` package if the package can be purchased in
        between the current time and the current time plus the specified delay.

        Note:
            - This option is relevant only when 'allow_scheduling' is set to True.
            - Setting a longer delay may cause the script to wait longer before attempting a purchase.

        Returns:
            int: The maximum delay scheduling time in seconds.
        """
        return self.config.getint("General", "max_delay_scheduling_time", fallback=0)

    @property
    def login_sleep_time(self) -> float:
        """
        Get the login sleep time.

        This property determines the delay, in seconds, between consecutive checks for
        the presence of the verification code in the email inbox.

        Returns:
            float: The login sleep time, as specified in the configuration file.
                If not configured, it defaults to 0.2 seconds (200 milliseconds).
        """
        return self.config.getfloat("General", "login_sleep_time", fallback=0.2)

    @property
    def max_login_attempts(self) -> int:
        """
        Get the maximum verification code check attempts.

        This property determines the maximum number of attempts the script will make to
        check for the presence of the verification code in the email inbox before giving up.

        Returns:
            int: The maximum number of verification code check attempts.
                If not configured, it defaults to 10 attempts.
        """
        return self.config.getint("General", "max_verification_attempts", fallback=10)

    @property
    def gmail_credentials_location(self):
        """
        Get the location of Gmail credentials.

        This property retrieves the path to the file containing Gmail credentials, which may be used for
        authentication or access to Gmail services.

        Returns:
            str: The path to the Gmail credentials file.
        """
        return self.config.get('Paths', 'gmail_credentials_location', fallback=os.path.join(self.fallback_base_path, 'credentials.json'))

    @property
    def gmail_token_location(self):
        """
        Get the location to store the Gmail token.

        This property retrieves the directory path where the Gmail token should be stored after authentication. The token is
        typically used for maintaining access to Gmail services.

        Returns:
            str: The directory path to store the Gmail token.
        """
        return self.config.get('Paths', 'gmail_token_location', fallback=self.fallback_base_path)

    @property
    def webstore_sessions_location(self):
        """
        Get the location to store the webstore sessions.

        This property retrieves the directory path where webstore sessions should be stored. Webstore sessions are used to
        maintain state and user interactions when accessing webstore services.

        Returns:
            str: The  directorypath to store the webstore sessions.
        """
        return self.config.get('Paths', 'webstore_sessions_location', fallback=self.fallback_base_path)

    def __get_log_level_for_logger(self, key, default_level):
        log_level = self.config.get('Logging', key, fallback='')
        return logging._nameToLevel.get(log_level, default_level)

    @property
    def default_log_level(self):
        return self.__get_log_level_for_logger('default_level', logging.INFO)

    @property
    def gmail_log_level(self):
        return self.__get_log_level_for_logger('gmail_level', self.default_log_level)

    @property
    def lotr_webstore_log_level(self):
        return self.__get_log_level_for_logger('lotr_webstore_level', self.default_log_level)

    def valiate(self):
        if self.is_self_scheduling and self.allow_scheduling:
            raise SchedulingConflictError('Please use only is_self_scheduling or allow_scheduling')

    @classmethod
    def load_config(cls, file_path: str):
        if isinstance(file_path, cls):
            return file_path
        elif not isinstance(file_path, str):
            return None
        instance = cls(file_path)
        instance.valiate()
        return instance

    @classmethod
    def load_global_config(cls, file_path: str):
        cls._instance = cls.load_config(file_path)

    @classmethod
    def get_global_config(cls):
        return cls._instance
