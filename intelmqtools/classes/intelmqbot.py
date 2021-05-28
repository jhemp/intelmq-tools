# -*- coding: utf-8 -*-

"""
Created on 17.01.20
"""
import os
from typing import List, Optional

from intelmqtools.classes.intelmqbotconfig import IntelMQBotConfig
from intelmqtools.classes.intelmqbotinstance import IntelMQBotInstance

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

from intelmqtools.classes.intelmqtoolconfig import IntelMQToolConfig


class IntelMQBot:

    def __init__(self):
        self.bot_alias: Optional[str] = None
        self.instances: List[IntelMQBotInstance] = list()

        # class/code details
        self.class_name: Optional[str] = None
        self.module: Optional[str] = None
        self.file_path: Optional[str] = None
        self.parent_class: Optional[str] = None

        # misc
        self.custom = True
        self.has_issues = False
        self.executable_exists = False

        # bot details and configuration
        self.bots_config: Optional[IntelMQBotConfig] = None
        self.running_config: Optional[dict] = None
        self.default_bots: Optional[IntelMQBotConfig] = None

    @property
    def executable_name(self) -> str:
        return self.module

    @property
    def bot_type(self) -> Optional[str]:
        for base in IntelMQToolConfig.BOT_FOLDER_BASES:
            path_part = '{0}{1}{0}'.format(os.path.sep, base)
            if path_part in self.file_path.lower():
                return base.title()[:-1]

    @property
    def entry_point(self) -> str:
        entry_point = '{}:{}.run'.format(self.module, self.bot_alias)
        return entry_point

    @property
    def in_use(self) -> bool:
        return len(self.instances) > 0

    def __repr__(self):
        return '{}({})'.format(self.class_name, self.parent_class)

    @property
    def description(self) -> str:
        if self.default_bots and self.default_bots.description:
            return self.default_bots.description
        if self.bots_config and self.bots_config.description:
            return self.bots_config.description
        else:
            return 'Could not find description'

    @property
    def installed(self) -> bool:
        return self.bots_config is not None and self.executable_exists

    @property
    def strange(self) -> bool:
        if self.bots_config:
            if not self.executable_exists:
                return True
        else:
            if self.executable_exists:
                return True
        return False

    @property
    def has_running_config(self) -> bool:
        return len(self.instances) > 0
