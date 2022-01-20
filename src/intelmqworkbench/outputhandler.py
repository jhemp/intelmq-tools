# -*- coding: utf-8 -*-

"""
Created on 31.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

from logging import Logger
from os import chmod, makedirs, symlink, listdir
from os.path import join, exists
from pathlib import Path
from shutil import rmtree
from typing import Optional, Tuple

from intelmqworkbench.classes.bots.bots import BOTS
from intelmqworkbench.classes.bots.botsitem import BOTSItem
from intelmqworkbench.classes.intelmqbot import IntelMQBot
from intelmqworkbench.classes.issues.intelmqbotissue import IntelMQBotIssue
from intelmqworkbench.classes.runtime.runtime import Runtime
from intelmqworkbench.exceptions import IntelMQToolException
from intelmqworkbench.utils import colorize_text, pretty_json, get_executable_filename, get_paths


class OutPutHandler:

    def __init__(self, logger: Logger):
        self.logger = logger

    def print_bot_meta(self, bot_detail: IntelMQBot) -> None:
        self.logger.debug('OutPut Bot Meta')
        internal_detail = bot_detail
        type_text = internal_detail.group
        if internal_detail.custom:
            type_text = '{} (Custom)'.format(type_text)
        print('BOT Group:               {}'.format(colorize_text(type_text, 'Gray')))
        print('BOT Class:               {}'.format(colorize_text(internal_detail.class_name, 'LightYellow')))
        print('BOT Name:                {}'.format(colorize_text(internal_detail.name, 'LightGreen')))
        print('Description:             {}'.format(colorize_text(internal_detail.description, 'LightGray')))
        print('Module:                  {}'.format(internal_detail.module))
        print('File:                    {}'.format(internal_detail.file_path))
        if internal_detail.default_parameters:
            print('Default Paramters        {}'.format(internal_detail.default_parameters.get_keys()))

    def print_bot_detail(self, bot: IntelMQBot, full: bool, strange: Optional[bool] = None) -> None:
        self.print_bot_meta(bot)
        if strange is None:
            print('Installed:               {}'.format(bot.installed))
        else:
            print('Installed/Strange:       {}/{}'.format(bot.installed, strange))
        if full:
            print('{}:          {}'.format(colorize_text('Default Config', 'Cyan'),
                                           pretty_json(bot.default_parameters.to_json())))
        len_instances = len(bot.runtime_items)
        print('Running Instances        {}'.format(colorize_text('{}'.format(len_instances), 'Magenta')))
        if len_instances > 0 and full:
            print('Instances: -----------------'.format(len_instances))
            counter = 1
            for runtime_item in bot.runtime_items:
                print('Instance {}: Name:              {}'.format(counter, runtime_item.name))
                print('Instance {}: Parameters:        {}'.format(counter, pretty_json(runtime_item.parameters.to_json())))
                counter = counter + 1
            if counter > 1:
                print()

    def print_issue(self, issue: IntelMQBotIssue) -> None:
        self.logger.debug('OutPut Issue')
        print(' - {}'.format(issue.description))

    def create_executable(self, bot: IntelMQBot, bin_folder: str) -> None:
        file_name = self.get_executable_filename(bot, bin_folder)
        self.logger.info('Creating file {} in {}'.format(file_name, bin_folder))
        executable_path = join(bin_folder, file_name)
        text = "#!/bin/python3\n" \
               "import {0}\n" \
               "import sys\n" \
               "sys.exit(\n" \
               "    {0}.{1}.run()\n" \
               ")".format(bot.module, bot.bot_variable)
        with open(executable_path, 'w+') as f:
            f.write(text)
        # Note: must be in octal (771_8 = 457_10)
        chmod(executable_path, 493)

    def save_runtime(self, runtime: Runtime) -> None:
        output = pretty_json(runtime.to_json())
        location = runtime.location
        with open(location, 'w') as f:
            f.write(output)
        self.logger.info('Saved Runtime to {}'.format(location))

    def save_bots(self, bots: BOTS) -> None:
        if bots:
            output = pretty_json(bots.to_json())
            location = bots.location
            with open(location, 'w') as f:
                f.write(output)
            self.logger.info('Saved BOTS to {}'.format(location))

    def install_bot(
            self,
            bot: IntelMQBot,
            bin_folder: str,
            bot_folder: str,
            bots_conf: BOTS
    ) -> int:
        self.logger.info('Installing "{}" ({})'.format(bot.name, bot.module))
        if bot.installed:
            raise IntelMQToolException('Bot "{}" ({}) is already installed'.format(bot.name, bot.module))
        module = bot.module
        if bots_conf:
            self.logger.debug('IntelMQ 2.x installation')
            # register in bots
            bot_item = BOTSItem()
            bot_item.module = bot.module
            bot_item.type_ = bot.group
            bot_item.name = bot.name
            bot_item.parameters = bot.default_parameters
            bot_item.description = bot.description
            bots_conf.add_bot(bot_item)
            self.save_bots(bots_conf)

        else:
            # make intelMQ > 3.0 setup
            self.logger.debug('IntelMQ 3.x installation')

            # intelmq-manager requires the bot to be present in IntelMQ's bot folder
            # as there is no more BOTS file the python file needs to be inside this specific folder
            # however the bot also needs to be in the pyhton path as for 2.x therefore only the main file of the bot is
            # required to be there

            source, destination = self.get_paths(bot, bot_folder)
            self.sync_folders(source, destination)

            # Note: The executable name is different during calls due it's location which in intelmq/bots!!!

        self.create_executable(bot, bin_folder)
        print('BOT "{}" ({}) installed.'.format(bot.name, bot.module))
        return 0

    def get_executable_filename(self, bot: IntelMQBot, bot_folder: str) -> str:
        file_name = get_executable_filename(bot, bot_folder)
        self.logger.debug('"{}" generated'.format(file_name))
        return file_name

    def get_paths(self, bot: IntelMQBot, bot_folder: str) -> Tuple[Path, Path]:
        self.logger.debug('Getting paths for bots')
        return get_paths(bot, bot_folder)

    def sync_folders(self, source: str, destination: str) -> None:
        if exists(destination):
            rmtree(destination)
        # Note: Must be a folder else it will not be recognised
        makedirs(destination, exist_ok=True)
        self.logger.debug('Create symlinks from {} to {}'.format(source, destination))

        # Creating symlinks to simplify bot updates as one has not to fiddle inside the intelmq/bots folder

        files = listdir(source)
        for f in files:
            file_name = join(destination, f)
            self.logger.debug('Created symlink to {}'.format(file_name))
            symlink(join(source, f), file_name)