# -*- coding: utf-8 -*-

"""
Created on 17.01.20
"""
import os

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'


class IntelMQDetails:

    BOT_FOLDER_BASES = ['collectors', 'experts', 'parsers', 'outputs']

    def __init__(self):
        self.config_dir: str = None
        self.intelmq_location: str = None
        self.entry_point_location: str = None
        self.bin_folder: str = None
        self.version = '2.1.1'

    @property
    def bot_folder(self) -> str:
        return os.path.join(self.intelmq_location, 'bots')

    @property
    def base_bots_file(self):
        return os.path.join(self.bot_folder, 'BOTS')

    @property
    def running_bots_file(self):
        return os.path.join(self.config_dir, 'BOTS')

    @property
    def defaults_conf_file(self):
        return os.path.join(self.config_dir, 'defaults.conf')

    @property
    def runtime_file(self):
        return os.path.join(self.config_dir, 'runtime.conf')

    @property
    def pipeline_file(self):
        return os.path.join(self.config_dir, 'pipeline.conf')

    @property
    def empty(self):
        return self.config_dir is None and self.intelmq_location is None and self.version == '2.1.1'
