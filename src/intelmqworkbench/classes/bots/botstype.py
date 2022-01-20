# -*- coding: utf-8 -*-

"""
Created on 29.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

from typing import Optional, List

from intelmqworkbench.classes.bots.botsitem import BOTSItem


class BOTSType:

    def __init__(self):
        self.type_: Optional[str] = None
        self.bots: List[BOTSItem] = list()

    def to_json(self) -> dict:
        bots = list()
        for item in self.bots:
            bots.append(item.to_json())
        return {
            self.type_: bots
        }
