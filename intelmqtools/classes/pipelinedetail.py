# -*- coding: utf-8 -*-

"""
Created on 17.01.20
"""
from typing import List

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'


class PipelineDetail:

    def __init__(self):
        self.bot_instance_name: str = None
        self.source: str = None
        self.destinations: List[PipelineDetail] = list()