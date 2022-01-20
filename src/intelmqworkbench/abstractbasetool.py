# -*- coding: utf-8 -*-

"""
Created on 15.01.20
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

import logging
from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
from typing import Optional, List, Union

from intelmqworkbench.classes.bots.bots import BOTS
from intelmqworkbench.classes.intelmqbot import IntelMQBot
from intelmqworkbench.classes.intelmqworkbenchconfig import IntelMQWorkbenchConfig
from intelmqworkbench.classes.issues.intelmqbotinstallissue import IntelMQBotInstallIssue
from intelmqworkbench.classes.issues.intelmqbotissue import IntelMQBotIssue
from intelmqworkbench.classes.pipeline.pipelinie import Pipeline
from intelmqworkbench.classes.runtime.runtime import Runtime
from intelmqworkbench.outputhandler import OutPutHandler
from intelmqworkbench.intelmqhandler import IntelMQHandler


class AbstractBaseTool(ABC):

    def __init__(self, logger: logging.Logger, config: IntelMQWorkbenchConfig):
        self.logger = logger
        self.config = config
        self.intelmq_handler = IntelMQHandler(logger)
        self.output_handler = OutPutHandler(logger)
        self.__bots: List[IntelMQBot] = list()

    @abstractmethod
    def get_arg_parser(self) -> ArgumentParser:
        raise NotImplementedError()

    def get_classname(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def start(self, args: Namespace) -> int:
        raise NotImplementedError()

    @abstractmethod
    def get_version(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def get_default_argument_description(self) -> Optional[str]:
        return 'lorem ipsum'

    def set_default_arguments(self, arg_parser: ArgumentParser):
        arg_parser.add_argument('--version', action='version', version='%(prog)s {}'.format(self.get_version()))
        default_description = self.get_default_argument_description()
        if default_description:
            arg_parser.add_argument(
                'default_operation',
                nargs='?',
                type=str,
                help='The default argument. {}'.format(default_description)
            )

    def get_all_bots(self, force: bool) -> List[IntelMQBot]:
        if len(self.__bots) == 0:
            self.__bots = self.fetch_bots(force)
        return self.__bots

    def fetch_bots(self, force):
        intelmq_bots = self.intelmq_handler.get_bots(self.config.bot_folder, False)
        bots = self.get_default_bots(force)
        if bots:
            self.intelmq_handler.merge_bots_conf_and_bots(intelmq_bots, bots)
        custom_bots = self.intelmq_handler.get_bots(self.config.custom_bot_folder, True)
        # Mark bots as custom
        for custom_bot in custom_bots:
            custom_bot.custom = True
        # mark custom bots and also remove them from the ones installed in the intelmq bots folder
        all_bots = list()
        for bot in intelmq_bots:
            found = False
            for custom_bot in custom_bots:
                # the common denominator
                if bot.class_name == custom_bot.class_name:
                    found = True
                    # if the bot can be found inside the installed ones then it is installed (only for IntelMQ 3.x)
                    custom_bot.installed = True
                    break
            if not found:
                all_bots.append(bot)
        all_bots = all_bots + custom_bots
        running_bots = self.get_running_bots(force)
        if running_bots:
            self.intelmq_handler.set_install_by_bots(all_bots, running_bots)
        set_install_by_path = bots is None
        runtime = self.get_runtime()
        self.intelmq_handler.merge_bots_and_runtime(all_bots, runtime, self.config.bot_folder, set_install_by_path)
        return all_bots

    def get_runtime(self) -> Runtime:
        if self.config.version.startswith('3'):
            path = self.config.runtime_yaml_file
            runtime = self.intelmq_handler.parse_runtime_yaml(path)
        else:
            path = self.config.runtime_conf_file
            runtime = self.intelmq_handler.parse_runtime_conf(path)
        runtime.location = path
        return runtime

    def get_pipeline(self, force: bool = False) -> Optional[Pipeline]:
        if self.config.version.startswith('3') and not force:
            return None
        pipeline = self.intelmq_handler.parse_pipeline(self.config.pipeline_conf_file)
        return pipeline

    def get_running_bots(self, force: bool = False) -> Optional[BOTS]:
        if self.config.version.startswith('3') and not force:
            return None
        path = self.config.running_BOTS
        bots = self.intelmq_handler.parse_bots(path)
        bots.location = path
        return bots

    def get_default_bots(self, force: bool = False) -> Optional[BOTS]:
        if self.config.version.startswith('3') and not force:
            return None
        path = self.config.default_BOTS
        bots = self.intelmq_handler.parse_bots(path)
        bots.location = path
        return bots

    def get_issues(self, force: bool = False) -> Optional[List[Union[IntelMQBotIssue, IntelMQBotInstallIssue]]]:
        runtime = self.get_runtime()
        bots = self.get_all_bots(force)
        runtime_bots = self.get_running_bots(force)
        issues = self.intelmq_handler.get_issues(
            bots, self.config.bot_folder, self.config.bin_folder, runtime, runtime_bots
        )
        return issues
