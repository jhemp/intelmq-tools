# -*- coding: utf-8 -*-

"""
Created on 15.01.20
"""
from argparse import Namespace
from configparser import ConfigParser
from typing import Dict, List, Type

from scripts.libs.abstractbase import AbstractBaseTool

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'


class FactoryException(Exception):
    pass


class Factory:

    def __init__(self):
        self.__components: Dict[str, AbstractBaseTool] = dict()

    @property
    def components(self) -> List[AbstractBaseTool]:
        return self.__components.values()

    def register_component(self, clazz: Type[AbstractBaseTool]) -> None:
        instance = clazz()
        self.__components[instance.get_arg_parser().prog] = instance

    def run_application(self, key: str, args: Namespace, config: ConfigParser) -> None:
        instance = self.__components.get(key, None)
        if instance is None:
            raise FactoryException('Program {} cannot be found'.format(key))
        else:
            log_level = args.verbose
            instance.set_params(log_level, False)
            instance.set_config(config)
            instance.start(args)
