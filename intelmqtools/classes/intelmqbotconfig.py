# -*- coding: utf-8 -*-

"""
Created on 28.05.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

from typing import Optional


class IntelMQBotConfig:

    def __init__(self):
        self.name: Optional[str] = None
        self.description: Optional[str] = None
        self.parameters = dict()

    def to_dict(self, module: str) -> dict:
        result = dict()
        result['description'] = self.description
        result['parameters'] = self.parameters
        result['module'] = module
        return result
