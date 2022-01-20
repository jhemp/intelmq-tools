# -*- coding: utf-8 -*-

"""
Created on 15.10.20
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

import os
from typing import Optional

from intelmqworkbench.exceptions import IntelMQWorkbenchConfigException


class IntelMQWorkbenchConfig:

    BOT_FOLDER_BASES = ['collectors', 'experts', 'parsers', 'outputs']

    def __init__(self):
        self.__bin_folder = '/usr/bin'
        self.__custom_bot_folder: Optional[str] = None
        self.__runtime_conf_file: Optional[str] = None
        self.__runtime_yaml_file: Optional[str] = None
        self.__default_BOTS_file: Optional[str] = None
        self.__runtime_BOTS_file: Optional[str] = None
        self.__custom_bot_location: Optional[str] = None
        self.__default_bot_location: Optional[str] = None
        self.__bin_folder: Optional[str] = None
        self.__pipeline_conf_file: Optional[str] = None
        self.__default_logging_path: Optional[str] = None
        self.__harmonization_conf_file: Optional[str] = None
        self.output_folder: Optional[str] = None
        self.fake_root: Optional[str] = None
        self.intelmq_folder = None
        self.version = None
        self.__config_dir = '/etc/intelmq'

    def __get_folder(self, path: str) -> str:
        if self.is_dev:
            folder = path
            if folder.startswith('/'):
                folder = folder[1:]
            return os.path.join(self.fake_root, folder)
        else:
            return path

    @property
    def config_dir(self) -> str:
        return self.__get_folder(self.__config_dir)

    @config_dir.setter
    def config_dir(self, value: str) -> None:
        self.__config_dir = value

    @property
    def bin_folder(self) -> str:
        return self.__get_folder(self.__bin_folder)

    @bin_folder.setter
    def bin_folder(self, value: str) -> None:
        self.__bin_folder = value

    @property
    def custom_bot_folder(self) -> str:
        return self.__custom_bot_folder

    @custom_bot_folder.setter
    def custom_bot_folder(self, value: str) -> None:
        self.__custom_bot_folder = value

    @property
    def default_logging_path(self) -> str:
        return self.__get_folder(self.__default_logging_path)

    @default_logging_path.setter
    def default_logging_path(self, value: str) -> None:
        self.__default_logging_path = value

    @property
    def harmonization_conf_file(self) -> str:
        return self.__get_folder(self.__harmonization_conf_file)

    @harmonization_conf_file.setter
    def harmonization_conf_file(self, value: str) -> None:
        self.__harmonization_conf_file = value

    @property
    def runtime_conf_file(self) -> str:
        if self.__runtime_conf_file:
            return self.__runtime_conf_file
        else:
            return os.path.join(self.config_dir, 'runtime.conf')

    @runtime_conf_file.setter
    def runtime_conf_file(self, value: str) -> None:
        self.__runtime_conf_file = value

    @property
    def runtime_yaml_file(self) -> str:
        if self.__runtime_yaml_file:
            return self.__runtime_yaml_file
        else:
            return os.path.join(self.config_dir, 'runtime.yaml')

    @runtime_yaml_file.setter
    def runtime_yaml_file(self, value: str) -> None:
        self.__runtime_yaml_file = value

    @property
    def bot_folder(self) -> str:
        if self.__default_bot_location:
            return self.__default_bot_location
        else:
            return os.path.join(self.intelmq_folder, 'bots')

    @bot_folder.setter
    def bot_folder(self, value: str) -> None:
        self.__default_bot_location = value

    @property
    def pipeline_conf_file(self) -> str:
        if self.__pipeline_conf_file:
            return self.__pipeline_conf_file
        else:
            return os.path.join(self.config_dir, 'pipeline.conf')

    @pipeline_conf_file.setter
    def pipeline_conf_file(self, value: str) -> None:
        self.__pipeline_conf_file = value

    @property
    def default_BOTS(self) -> str:
        if self.__default_BOTS_file:
            return self.__default_BOTS_file
        else:
            return os.path.join(self.intelmq_folder, 'bots', 'BOTS')

    @default_BOTS.setter
    def default_BOTS(self, value: str) -> None:
        self.__default_BOTS_file = value

    @property
    def running_BOTS(self) -> str:
        if self.__default_BOTS_file:
            return self.__default_BOTS_file
        else:
            return os.path.join(self.config_dir, 'BOTS')

    @running_BOTS.setter
    def running_BOTS(self, value: str) -> None:
        self.__default_BOTS_file = value

    @staticmethod
    def __check_folder(folder_path: str) -> None:
        if not os.path.exists(folder_path):
            raise IntelMQWorkbenchConfigException('The folder "{}" does not exist'.format(folder_path))

    def validate(self) -> None:
        if self.__bin_folder and self.custom_bot_folder:

            if self.fake_root:
                self.__check_folder(self.fake_root)
            self.__check_folder(self.bin_folder)
            self.__check_folder(self.custom_bot_folder)
            self.__check_folder(self.intelmq_folder)

        else:
            raise IntelMQWorkbenchConfigException(
                'One of the following parameters is not set: bin_folder, custom_bot_folder or intelmq_folder'
            )

    @property
    def is_dev(self) -> bool:
        return not (self.fake_root is None or self.fake_root == '')


