# -*- coding: utf-8 -*-

"""
Created on 17.01.20
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'


class IntelMQBotInstance:

    def __init__(self):
        self.name: str = None
        self.config: dict = None
        self.bot: any = None

    @property
    def parameters(self):
        return self.config.get('parameters', {})
