# -*- coding: utf-8 -*-

"""
Created on 29.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

from typing import Union, List, Optional


class Parameters:

    def __init__(self):
        self.values: Optional[dict] = None
        self.read_config: bool = False

    def to_json(self) -> Optional[dict]:
        return self.values

    def __convert_value(self, value: any) -> any:
        if value is None:
            return None
        else:
            if isinstance(value, dict):
                temp = dict()
                for key, item in value.items():
                    temp[key] = self.__convert_value(item)
                return temp
            elif isinstance(value, list):
                temp = list()
                for item in value:
                    temp.append(self.__convert_value(item))
                return temp
            else:
                try:
                    item = int(value)
                    return item
                except ValueError:
                    return value

    def add_values(self, data: dict) -> None:
        if self.values is None:
            self.values = dict()
        if data:
            for key, value in data.items():
                converted_value = self.__convert_value(value)
                self.values[key] = converted_value

    def add_value(self, key: str, data: Union[list, bool, str, int, dict]) -> None:
        if self.values is None:
            self.values = dict()
        self.values[key] = data

    def has_values(self) -> bool:
        if self.values:
            return len(self.values) > 0
        return False

    def has_key(self, key: str) -> bool:
        if self.values:
            return key in self.values.keys()
        return False

    def merge_parameters(self, parameters) -> None:
        if self.values is None:
            self.values = dict()
        self.values.update(parameters.values)

    def get_keys(self) -> List[str]:
        if self.values:
            return list(self.values.keys())
        return list()

    def get_value(self, key: str) -> Optional[Union[list, bool, str, int, dict]]:
        if self.values:
            return self.values[key]
        return None

    def set_value(self, key: str, value: any) -> None:
        if self.values is None:
            self.values = dict()
        self.values[key] = value

    def remove_key(self, key: str) -> None:
        if self.values:
            del self.values[key]


