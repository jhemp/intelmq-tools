# -*- coding: utf-8 -*-

"""
Created on 29.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

from typing import List, Optional

from intelmqworkbench.classes.pipeline.pipelineitem import PipelineItem


class Pipeline:

    def __init__(self):
        self.__items: List[PipelineItem] = list()

    def to_json(self) -> dict:
        output = dict()
        for item in self.__items:
            output.update(item.to_json())
        return output

    def add_item(self, runtime_item: PipelineItem) -> None:
        self.__items.append(runtime_item)

    def get_item_for(self, bot_id: str) -> Optional[PipelineItem]:
        for item in self.__items:
            if item.bot_id == bot_id:
                return item
        return None

    def has_bot_id(self, bot_id: str) -> bool:
        for item in self.__items:
            if item.bot_id == bot_id:
                return True
        return False

    def is_bot_id_contained(self, bot_id: str) -> bool:
        for item in self.__items:
            if item.bot_id == bot_id:
                return True
            if item.source == bot_id:
                return True
            for destination in item.destinations:
                if destination == bot_id:
                    return True
        return False
