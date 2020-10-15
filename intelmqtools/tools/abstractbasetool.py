# -*- coding: utf-8 -*-

"""
Created on 15.01.20
"""
import json
import logging
from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace

from intelmqtools.classes.intelmqtoolconfig import IntelMQToolConfig

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'


class AbstractBaseTool(ABC):

    def __init__(self, config: IntelMQToolConfig, log_level: int = None, is_dev: bool = None):
        self.logger = logging.getLogger(self.get_class_name())
        self.is_dev = is_dev
        self.config = config
        self.set_params(log_level, is_dev)

    def set_params(self, log_level: int, is_dev: bool):
        if log_level and log_level > -1:
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            self.logger.setLevel(logging.DEBUG)
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(log_format))
            console_handler.setLevel(self.__get_log_level(log_level))
            self.logger.addHandler(console_handler)

            self.logger.debug('Created instance of {}'.format(self.get_class_name()))
        if is_dev is None:
            self.is_dev = False
        else:
            self.is_dev = is_dev

    @staticmethod
    def __get_log_level(log_level: int) -> int:
        if log_level == 0:
            return logging.CRITICAL
        elif log_level == 1:
            return logging.ERROR
        elif log_level == 2:
            return logging.WARNING
        elif log_level == 3:
            return logging.INFO
        else:
            return logging.DEBUG

    def get_class_name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def get_arg_parser(self) -> ArgumentParser:
        return self._arg_parser

    @abstractmethod
    def start(self, args: Namespace) -> int:
        pass

    @abstractmethod
    def get_version(self) -> str:
        return '0.1'

    def set_default_arguments(self, arg_parser: ArgumentParser) -> None:
        arg_parser.add_argument('--version', action='version', version='%(prog)s {}'.format(self.get_version()))

    def set_config(self, config: IntelMQToolConfig) -> None:
        self.config = config
