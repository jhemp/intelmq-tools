# -*- coding: utf-8 -*-

"""
Created on 29.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

import json
from typing import List, Optional


class PipelineItem:

    def __init__(self):
        self.source: Optional[str] = None
        self.destinations: List[str] = list()
        self.bot_id: Optional[str] = None

    def to_json(self) -> dict:
        data = dict()
        if self.destinations:
            data['destination-queues'] = json.dumps(self.destinations)
        if self.source:
            data['source-queue'] = self.source
        return {
            self.bot_id: data
        }
