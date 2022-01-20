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


class BOTSItem:

    def __init__(self):
        self.type_: Optional[str] = None
        self.name: Optional[str] = None
        self.description: Optional[str] = None
        self.module: Optional[str] = None
        self.parameters: Optional[Parameters] = None

    def to_json(self) -> dict:
        parameters = dict()
        if self.parameters:
            parameters = self.parameters.to_json()
        return {
            self.name: {
                'description': self.description,
                'module': self.module,
                'parameters': parameters
            }
        }

    def __repr__(self) -> str:
        return '{} - ({})'.format(self.name, self.type_)
