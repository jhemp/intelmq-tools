# -*- coding: utf-8 -*-

"""
Created on 17.01.20
"""
from typing import List, Optional, Type

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

from intelmq.lib.bot import Bot

from intelmqworkbench.classes.parameters import Parameters
from intelmqworkbench.classes.runtime.runtimeitem import RuntimeItem


class IntelMQBot:

    def __init__(self):
        self.bot_variable: Optional[str] = None

        # class/code details
        self.clazz: Optional[Type[Bot]] = None
        self.file_path: Optional[str] = None

        self.description: Optional[str] = None
        self.group: Optional[str] = None
        self.name: Optional[str] = None
        self.default_parameters: Optional[Parameters] = None
        self.runtime_items: List[RuntimeItem] = list()
        self.installed: bool = False
        self.custom: bool = False

    @property
    def class_name(self) -> str:
        return self.clazz.__name__

    @property
    def module(self) -> str:
        return self.clazz.__module__

    @property
    def groupname(self) -> str:
        return '{}s'.format(self.group).lower()

    def __repr__(self) -> str:
        return '{} - ({})'.format(self.name, self.class_name)

    def get_runtime_item_by_id(self, bot_id: str) -> Optional[RuntimeItem]:
        for item in self.runtime_items:
            if item.bot_id == bot_id:
                return item
        return None
