# -*- coding: utf-8 -*-

"""
Created on 15.01.20
"""
import os
import shutil
from argparse import ArgumentParser, Namespace
from typing import List, Dict, Optional

from intelmqtools.classes.intelmqbot import IntelMQBot
from intelmqtools.classes.pipelinedetail import PipelineDetail
from intelmqtools.tools.abstractbasetool import AbstractBaseTool
from intelmqtools.exceptions import IncorrectArgumentException, ToolException, BotFileNotFoundException, \
    MissingConfigurationException, BotAlreadyInstalledException, BotNotInstalledException
from intelmqtools.utils import pretty_json

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'


class Installer(AbstractBaseTool):

    def get_arg_parser(self) -> ArgumentParser:
        arg_parse = ArgumentParser(prog='install', description='Tool for installing bots')
        arg_parse.add_argument('-i', '--install', default=None,
                               help='Path of the bot to install (Note: Module Folder only)', type=str)
        arg_parse.add_argument('-u', '--uninstall', default=None,
                               help='Path of the bot to uninstall (Note: Module Folder only)', type=str)
        self.set_default_arguments(arg_parse)
        return arg_parse

    def __get_bot_details(self, bot_path: str) -> Optional[IntelMQBot]:
        full_path = os.path.abspath(bot_path)
        # bots = self.get_custom_bots()
        bots = self.get_all_bots()
        for bot in bots:
            if bot.code_file == full_path:
                return bot
        return None

    def manipulate_bots_file(self, bot: IntelMQBot, install: bool) -> None:
        if install:
            installed_bots = self.get_installed_bots()
            installed_bots.append(bot)
            self.update_bots_file(installed_bots, 'insert')
        else:
            self.update_bots_file([bot], 'remove')

    def start(self, args: Namespace) -> int:

        if args.install:
            bot_path = args.install
            bot = self.__get_bot_details(bot_path)
            if bot:
                if bot.installed:
                    raise BotAlreadyInstalledException('Bot in file {} is already installed'.format(bot_path))
                else:
                    self.manipulate_execution_file(bot, True)
                    self.manipulate_bots_file(bot, True)
                    print('Bot {} successfully installed'.format(bot.class_name))
                    return 0
            else:
                raise ToolException('File {} is not part of the custom bot location'.format(bot_path))

        elif args.uninstall:
            bot_path = args.uninstall
            bot = self.__get_bot_details(bot_path)
            if bot:
                if bot.installed:
                    raise BotNotInstalledException('Bot in file {} is not installed'.format(bot_path))
                else:
                    pipeline_map = self.check_pipeline([bot])
                    self.remove_runtime(pipeline_map, [bot])
                    self.manipulate_execution_file(bot, False)
                    self.manipulate_bots_file(bot, False)
                    print('BOT Class {} was successfully uninstalled'.format(bot.class_name))
                    return 0
            else:
                raise ToolException('File {} is not part of the custom bot location'.format(bot_path))

        else:
            raise IncorrectArgumentException()

    def get_version(self) -> str:
        return '0.1'

    @staticmethod
    def build_pipeline_map(pipeline: dict) -> Dict[str, PipelineDetail]:
        seen_details = dict()
        for instance_name, details in pipeline.items():
            if instance_name not in seen_details.keys():
                seen_details[instance_name] = PipelineDetail()
                seen_details[instance_name].bot_instance_name = instance_name
        for instance_name, details in pipeline.items():
            source_queue = details.get('source-queue')
            if source_queue:
                queue_instance_name = source_queue.replace('-queue', '')
                if queue_instance_name in seen_details.keys():
                    seen_details[queue_instance_name].source = seen_details[queue_instance_name]

            for destination in details.get('destination-queues', []):
                queue_instance_name = destination.replace('-queue', '')
                if queue_instance_name in seen_details.keys():
                    seen_details[instance_name].destinations.append(seen_details[queue_instance_name])
        return seen_details

    def check_pipeline(self, bots: List[IntelMQBot]) -> Dict[str, PipelineDetail]:
        pipeline = self.get_config(self.config.pipeline_file)
        pipeline_map = self.build_pipeline_map(pipeline)
        for bot in bots:
            for instance in bot.instances:
                item = pipeline_map.get(instance.name)
                if item:
                    if item.destinations or item.source:
                        # the bot is still used!
                        raise ToolException('The Bot {} is still used in the pipes. Remove pipes first.'.format(bot.code_file))
        return pipeline_map

    def remove_runtime(self, pipeline_map: Dict[str, PipelineDetail],
                       bots: List[IntelMQBot]) -> None:
        runtime = self.get_config(self.config.runtime_file)
        for bot in bots:
            can_be_removed = True
            if bot.instances:
                for instance in bot.instances:
                    item = pipeline_map.get(instance.name)
                    if item:
                        can_be_removed = False
                    if can_be_removed:
                        del runtime[instance.name]
        with open(self.config.runtime_file, 'w') as f:
            f.write(pretty_json(runtime))

