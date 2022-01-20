# -*- coding: utf-8 -*-

"""
Created on 29.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

from typing import Optional


from intelmqworkbench.classes.parameters import Parameters


class RuntimeItem:

    def __init__(self):
        self.name: str = 'NotSet'
        self.description: Optional[str] = None
        self.module: Optional[str] = None
        self.parameters: Optional[Parameters] = None
        self.bot_id: str = 'NotSet'
        self.enabled: bool = False
        self.group: Optional[str] = None
        self.groupname: Optional[str] = None
        self.run_mode: Optional[str] = None

    @property
    def type_(self) -> str:
        return self.group

    def to_json(self) -> dict:
        parameters = dict()
        if self.parameters:
            parameters = self.parameters.to_json()
        return {
            self.bot_id: {
                'bot_id': self.bot_id,
                'description': self.description,
                'enabled': self.enabled,
                'group': self.group,
                'groupname': self.groupname,
                'module': self.module,
                'name': self.name,
                'parameters': parameters,
                'run_mode': self.run_mode,
            }
        }

    def __repr__(self) -> str:
        return '{} - ({})'.format(self.name, self.module)
