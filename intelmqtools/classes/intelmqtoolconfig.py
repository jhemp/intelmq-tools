# -*- coding: utf-8 -*-

"""
Created on 15.10.20
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

import os

from intelmqtools.exceptions import IntelMQToolConfigException


class IntelMQToolConfig:

    BOT_FOLDER_BASES = ['collectors', 'experts', 'parsers', 'outputs']

    def __init__(self):
        self.__bin_folder = '/usr/bin'
        self.custom_bot_folder = None
        self.fake_root = None
        self.intelmq_folder = None
        self.version = None
        self.config_dir = '/etc/intelmq'
        self.log_lvl = 0

    def __get_folder(self, path: str) -> str:
        if self.is_dev:
            folder = path
            if folder.startswith('/'):
                folder = folder[1:]
            return os.path.join(self.fake_root, folder)
        else:
            return path

    @property
    def bin_folder(self) -> str:
        return self.__get_folder(self.__bin_folder)

    @bin_folder.setter
    def bin_folder(self, value: str) -> None:
        self.__bin_folder = value

    @staticmethod
    def __check_folder(folder_path: str) -> None:
        if os.path.exists(folder_path):
            return folder_path
        else:
            raise IntelMQToolConfigException('The folder "{}" does not exist'.format(folder_path))

    def validate(self) -> None:
        if self.__bin_folder and self.custom_bot_folder:

            if self.fake_root:
                self.__check_folder(self.fake_root)
            self.__check_folder(self.bin_folder)
            self.__check_folder(self.custom_bot_folder)
            self.__check_folder(self.intelmq_folder)

        else:
            raise IntelMQToolConfigException('One of the following parameters is not set: bin, bot')

    @property
    def is_dev(self) -> bool:
        return self.fake_root is not None

    @property
    def bot_folder(self) -> str:
        return os.path.join(self.intelmq_folder, 'bots')

    @property
    def base_bots_file(self) -> str:
        return os.path.join(self.bot_folder, 'BOTS')

    @property
    def running_bots_file(self) -> str:
        return os.path.join(self.config_dir, 'BOTS')

    @property
    def defaults_conf_file(self) -> str:
        return os.path.join(self.config_dir, 'defaults.conf')

    @property
    def runtime_file(self) -> str:
        return os.path.join(self.config_dir, 'runtime.conf')

    @property
    def pipeline_file(self) -> str:
        return os.path.join(self.config_dir, 'pipeline.conf')

