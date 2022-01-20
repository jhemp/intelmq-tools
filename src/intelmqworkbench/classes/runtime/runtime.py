# -*- coding: utf-8 -*-

"""
Created on 29.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

from typing import List, Optional

from intelmqworkbench.classes.runtime.runtimeitem import RuntimeItem


class Runtime:

    def __init__(self):
        self.__items: List[RuntimeItem] = list()
        self.location: Optional[str] = None

    def to_json(self) -> dict:
        output = dict()
        for item in self.__items:
            output.update(item.to_json())
        return output

    def add_item(self, runtime_item: RuntimeItem) -> None:
        self.__items.append(runtime_item)

    def get_items(self) -> List[RuntimeItem]:
        return self.__items

    def get_runtime_items_for_module(self, module_name: str) -> List[RuntimeItem]:
        output = list()
        for item in self.__items:
            if item.module == module_name:
                output.append(item)
        return output

    def get_item_by_id(self, bot_id: str) -> Optional[RuntimeItem]:
        for item in self.__items:
            if item.bot_id == bot_id:
                return item
        return None

    def remove_by_bot_id(self, bot_id: str) -> None:
        count = -1
        for item in self.__items:
            count += 1
            if item.bot_id == bot_id:
                self.__items.pop(count)
                break

    def is_referenced_destination(self, bot_id: str) -> bool:
        for item in self.__items:
            if item.parameters and item.parameters.has_key('destination_queues'):
                destinations = item.parameters.get_value('destination_queues')
                if destinations is not None:
                    for value in destinations.values():
                        if bot_id in value:
                            return True
        return False



