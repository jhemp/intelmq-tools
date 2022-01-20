# -*- coding: utf-8 -*-

"""
Created on 29.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

from typing import List, Optional

from intelmqworkbench.classes.bots.botsitem import BOTSItem
from intelmqworkbench.classes.bots.botstype import BOTSType
from intelmqworkbench.classes.intelmqbot import IntelMQBot
from intelmqworkbench.exceptions import IntelMQWorkbenchValueException


class BOTS:

    def __init__(self):
        self.__types: List[BOTSType] = list()
        self.location: Optional[str] = None

    def add_bot(self, bot: BOTSItem) -> None:
        not_found = True
        for item in self.__types:
            if item.type_ == bot.type_:
                item.bots.append(bot)
                not_found = False
                break
        if not_found:
            type_ = BOTSType()
            type_.type_ = bot.type_
            type_.bots.append(bot)
            self.__types.append(type_)

    def add_type(self, type_: BOTSType) -> None:
        not_found = True
        for item in self.__types:
            if item.type_ == type_.type_:
                # if already exists just merge
                item.bots = item.bots + type_.bots
                not_found = False
                break

        if not_found:
            self.__types.append(type_)

    @property
    def types(self) -> List[str]:
        output = list()
        for item in self.__types:
            output.append(item.type_)
        return output

    def get_bots_of_type(self, type_: str) -> Optional[List[BOTSItem]]:
        for item in self.__types:
            if item.type_ == type_:
                return item.bots

    def get_bot_item_by_bot(self, bot: IntelMQBot) -> Optional[BOTSItem]:
        for type_ in self.__types:
            if type_.type_ == bot.group:
                for bots_bot in type_.bots:
                    if bots_bot.module == bot.module:
                        return bots_bot
        return None

    def get_items(self) -> List[BOTSItem]:
        output = list()
        for type_ in self.__types:
            for item in type_.bots:
                output.append(item)
        return output

    def to_json(self) -> dict:
        output = dict()
        for type_ in self.__types:
            output[type_.type_] = dict()
            for bot in type_.bots:
                output[type_.type_][bot.name] = {
                    'description': bot.description,
                    'module': bot.module,
                    'parameters': bot.parameters.to_json()
                }
        return output

    def remove_element(self, type_: str, module: str, name: str) -> None:
        removed = False
        for item in self.__types:
            if item.type_ == type_:
                counter = -1
                for bot in item.bots:
                    counter += 1
                    if bot.module == module and bot.name == name:
                        item.bots.pop(counter)
                        removed = True
                        break
            if removed:
                break


