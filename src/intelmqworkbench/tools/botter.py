# -*- coding: utf-8 -*-

"""
Created on 31.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

from argparse import ArgumentParser, Namespace
from os import remove
from os.path import join, isfile
from shutil import rmtree
from typing import Optional

from intelmqworkbench import AbstractBaseTool, IncorrectArgumentException, IntelMQToolException
from intelmqworkbench.classes.bots.bots import BOTS
from intelmqworkbench.classes.intelmqbot import IntelMQBot
from intelmqworkbench.classes.runtime.runtime import Runtime


class Botter(AbstractBaseTool):

    def get_default_argument_description(self) -> Optional[str]:
        return None

    def get_version(self) -> str:
        return '0.2'

    def get_arg_parser(self) -> ArgumentParser:
        arg_parse = ArgumentParser(prog='botter', description='Tool for installing bots')
        arg_parse.add_argument('-i', '--install', default=None,
                               help='Class name or Name of the BOT to be installed e.g. ExampleParserBot, Example',
                               type=str)
        arg_parse.add_argument('-u', '--uninstall', default=None,
                               help='Class name or Name of the BOT to be installed e.g. ExampleParserBot, Example',
                               type=str)
        arg_parse.add_argument('--force', default=False, help='Force', action='store_true')
        return arg_parse

    def __get_bot(self, class_name: str, force: bool) -> Optional[IntelMQBot]:
        bots = self.get_all_bots(force)
        for bot in bots:
            if bot.name == class_name or bot.class_name == class_name:
                return bot
        return None

    def start(self, args: Namespace) -> int:
        bots_conf = self.get_running_bots(args.force)
        force = args.force
        if args.install:
            class_name = args.install
            bot = self.__get_bot(class_name, force)
            if bot:
                if not (bot.description or bot.default_parameters):
                    raise IntelMQToolException('Bot "{}" ({}) is faulty. Verify manually'.format(bot.name, bot.module))
                return self.output_handler.install_bot(bot, self.config.bin_folder, self.config.bot_folder, bots_conf)
            else:
                raise IntelMQToolException('Bot "{}" cannot be found verify if it is listed.')
        elif args.uninstall:
            class_name = args.uninstall
            bot = self.__get_bot(class_name, force)
            if bot:
                if not (bot.description or bot.default_parameters):
                    raise IntelMQToolException('Bot "{}" ({}) is faulty. Verify manually'.format(bot.name, bot.module))
                runtime = self.get_runtime()
                return self.remove_bot(bot, bots_conf, runtime)
            else:
                raise IntelMQToolException('Bot "{}" cannot be found verify if it is listed.')
        else:
            raise IncorrectArgumentException()

    def remove_bot(
            self,
            bot: IntelMQBot,
            bots_conf: BOTS,
            runtime: Runtime
    ) -> int:
        self.logger.info('Removing "{}" ({})'.format(bot.name, bot.module))
        if not bot.installed:
            raise IntelMQToolException('Bot "{}" ({}) is not installed'.format(bot.name, bot.module))

        removed = False

        runtime_items = runtime.get_runtime_items_for_module(bot.module)
        for item in runtime_items:
            result = self.intelmq_handler.remove_runtime_item_by_bot_id(item.bot_id)
            if result:
                self.logger.info('Removed BOT "{}" from runtime'.format(item.bot_id))
                removed = True
            else:
                raise IntelMQToolException(
                    'Cannot removed BOT "{}" from runtime as it is still referenced'.format(item.bot_id)
                )

        if removed:
            # can occur if the bot is not part of any pipeline
            self.output_handler.save_runtime(runtime)

        if bots_conf:
            self.logger.debug('IntelMQ 2.x uninstallation')
            removed = self.intelmq_handler.remove_bots_item(
                bot.group, bot.module, bot.name, bots_conf, runtime, self.config.bin_folder
            )
            if removed:
                self.output_handler.save_bots(bots_conf)
                self.logger.info('Removed from BOTS')

        else:
            self.logger.debug('IntelMQ 3.x uninstallation')
            # removal for IntelMQ > 3.0
            destination = self.output_handler.get_paths(bot, self.config.bot_folder)[1]
            rmtree(destination)

        # Remove executable
        file_name = self.output_handler.get_executable_filename(bot, self.config.bin_folder)
        path = join(self.config.bin_folder, file_name)
        if isfile(path):
            self.logger.debug('Executable "{}" exists'.format(path))
            remove(path)

        print('BOT "{}" ({}) removed.'.format(bot.name, bot.module))
        return 0

