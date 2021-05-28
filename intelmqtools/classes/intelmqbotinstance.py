# -*- coding: utf-8 -*-

"""
Created on 17.01.20
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

from typing import Optional

from intelmqtools.classes.intelmqbotconfig import IntelMQBotConfig


class IntelMQBotInstance(IntelMQBotConfig):

    def __init__(self):
        super().__init__()
        self.bot_id: Optional[str] = None
        self.enabled = False
        self.group: Optional[str] = None
        self.groupname: Optional[str] = None
        self.run_mode: Optional[str] = None
        self.module: Optional[str] = None

        self.bot: any = None

    def to_dict(self, module: str) -> dict:
        result = super().to_dict(module)
        result['bot_id'] = self.bot_id
        result['enabled'] = self.enabled
        result['group'] = self.group
        result['groupname'] = self.groupname
        result['run_mode'] = self.run_mode
        result['module'] = self.module
        result['name'] = self.name
        return result


