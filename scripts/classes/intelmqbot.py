# -*- coding: utf-8 -*-

"""
Created on 17.01.20
"""
import os
from typing import List

from scripts.classes.intelmqbotinstance import IntelMQBotInstance
from scripts.classes.intelmqdetails import IntelMQDetails

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'


class IntelMQBot:

    def __init__(self):
        self.class_name: str = None
        self.bot_alias: str = None
        self.instances: List[IntelMQBotInstance] = list()
        self.code_module: str = None
        self.default_parameters: dict = None
        self.custom_default_parameters: dict = None
        self.code_file = None
        self.installed = False
        self.intelmq_defaults = dict()
        self.custom = True

    @property
    def bot_type(self) -> str:
        for base in IntelMQDetails.BOT_FOLDER_BASES:
            path_part = '{0}{1}{0}'.format(os.path.sep, base)
            if path_part in self.code_file.lower():
                return base.title()[:-1]

    @property
    def entry_point(self) -> str:
        entry_point = '{}:{}.run'.format(self.code_module, self.bot_alias)
        return entry_point

    @property
    def description(self) -> str:
        if self.default_parameters:
            return self.default_parameters.get('description', None)
        elif self.custom_default_parameters:
            return self.custom_default_parameters.get('description', None)
        else:
            return 'No description specified in configuration'

    @property
    def in_use(self) -> bool:
        return len(self.instances) > 0

    @property
    def configuration(self) -> dict:
        result = dict()
        result.update(self.default_parameters)
        result.update(self.intelmq_defaults)
        return result

    @property
    def module(self) -> str:
        return self.code_module.rsplit('.', 1)[0]

    def get_bots_config(self, full: bool) -> dict:

        if self.default_parameters:
            configuration = self.default_parameters
        else:
            # if there is an unreferenced bot
            configuration = {
                'description': self.description,
                'module': self.code_module,
                'parameters': dict()
            }
        result = {
            self.bot_type: configuration
        }
        if full:
            return result
        else:
            return result[self.bot_type]
