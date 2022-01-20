# -*- coding: utf-8 -*-

"""
Created on 03.01.22
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

import base64
import json
from importlib import import_module
from logging import Logger
from os import listdir, makedirs, remove, rmdir
from os.path import join, isfile, isdir
from shutil import move, rmtree

from typing import List, Optional

from intelmqworkbench.classes.intelmqbot import IntelMQBot
from intelmqworkbench.classes.intelmqworkbenchconfig import IntelMQWorkbenchConfig

import intelmq
try:
    import intelmq.lib.utils as utils
except ImportError:
    utils = None

from intelmq.lib.message import Report, Event

from intelmqworkbench.exceptions import IntelMQToolException
from intelmqworkbench.utils import pretty_json


class FiddleHandler:

    FILE_NAME = 'message'
    OLD_MESSAGES = 'old'

    def __init__(self, logger: Logger):
        self.logger = logger
        self.config = None
        self.bots = None
        self.__message_count = 0
        self.__current_send_message = 0
        self.__current_load_message = 0
        self.old_messages_path = None

    def init(self, bots: List[IntelMQBot], config: IntelMQWorkbenchConfig) -> None:
        self.bots = bots
        self.config = config
        self.__set_up()
        self.old_messages_path = join(self.config.output_folder, FiddleHandler.OLD_MESSAGES)
        self.__message_count = self.__get_message_count()
        self.__current_send_message = 0
        self.__current_load_message = 0

    def __get_files_in_dir(self, directory: str) -> List[str]:
        self.logger.debug('Scanning for files in {}'.format(directory))
        message_files = [f for f in listdir(directory) if isfile(join(directory, f))]
        return message_files

    def __get_message_count(self) -> int:
        message_files = self.__get_files_in_dir(self.config.output_folder)
        count = -1
        for message_file in message_files:
            if message_file.startswith(FiddleHandler.FILE_NAME):
                count += 1
        # move the files to an other directory so that files are not being overridden
        makedirs(self.old_messages_path, exist_ok=True)
        for message_file in message_files:
            source_file = join(self.config.output_folder, message_file)
            destination_file = join(self.old_messages_path, message_file)
            move(source_file, destination_file)
        if count >= 0:
            count += 1
        return count

    def __set_up(self) -> None:
        setattr(intelmq, 'CONFIG_DIR', self.config.config_dir)
        setattr(intelmq, 'DEFAULT_LOGGING_PATH', self.config.default_logging_path)
        if self.config.version.startswith('2'):
            setattr(intelmq, 'RUNTIME_CONF_FILE', self.config.runtime_conf_file)
        else:
            setattr(intelmq, 'RUNTIME_CONF_FILE', self.config.runtime_yaml_file)
        setattr(intelmq, 'PIPELINE_CONF_FILE', self.config.pipeline_conf_file)
        setattr(intelmq, 'HARMONIZATION_CONF_FILE', self.config.harmonization_conf_file)
        # set part in utils
        if utils:
            setattr(utils, 'RUNTIME_CONF_FILE', self.config.runtime_yaml_file)
            setattr(getattr(utils, 'intelmq'), 'DEFAULT_LOGGING_PATH', self.config.default_logging_path)

        # fiddle with bot
        setattr(getattr(intelmq.lib, 'bot'), 'DEFAULT_LOGGING_PATH', self.config.default_logging_path)
        setattr(getattr(intelmq.lib, 'bot'), 'HARMONIZATION_CONF_FILE', self.config.harmonization_conf_file)
        if self.config.version.startswith('2'):
            setattr(getattr(intelmq.lib, 'bot'), 'RUNTIME_CONF_FILE', self.config.runtime_conf_file)
        else:
            setattr(getattr(intelmq.lib, 'bot'), 'RUNTIME_CONF_FILE', self.config.runtime_yaml_file)

        setattr(getattr(intelmq.lib, 'message'), 'HARMONIZATION_CONF_FILE', self.config.harmonization_conf_file)

        if self.config.output_folder is None:
            raise IntelMQToolException('Output Folder is not set either specify it in config or use --output folder')

    def print_configuration(self) -> int:
        print('Config Dir:           {}'.format(intelmq.CONFIG_DIR))
        print('Default logging Path: {}'.format(intelmq.DEFAULT_LOGGING_PATH))
        if self.config.version.startswith('2'):
            print('Pipeline Conf:    {}'.format(intelmq.DEFAULT_LOGGING_PATH))
        print('Runtime Conf:         {}'.format(intelmq.RUNTIME_CONF_FILE))
        print('Harmonization Conf:   {}'.format(intelmq.HARMONIZATION_CONF_FILE))
        print('Output folder:        {}'.format(self.config.output_folder))
        return 0

    def __get_bot_by_id(self, bot_id: str) -> IntelMQBot:
        if self.bots:
            self.logger.debug('Getting BOT for "{}"'.format(bot_id))
            for bot in self.bots:
                if bot.runtime_items:
                    for run_item in bot.runtime_items:
                        if run_item.bot_id == bot_id:
                            return bot
            raise IntelMQToolException('Cannot find Bot with ID "{}"'.format(bot_id))
        else:
            raise IntelMQToolException('Fiddler Handler Not initialized. Call init first')

    def launch_bot(self, bot_id: str) -> None:
        # import bot
        bot = self.__get_bot_by_id(bot_id)
        module = import_module(bot.module)
        clazz = getattr(module, bot.class_name)
        setattr(clazz, 'logging_path', self.config.default_logging_path)
        instance = clazz(bot_id)
        setattr(instance, 'send_message', self.__send_message)
        setattr(instance, 'acknowledge_message', self.__acknowledge_message)
        if bot.group in ['Collector']:
            if self.__message_count == -1:
                self.__message_count = 0
            setattr(instance, 'receive_message', None)
        else:
            if self.__message_count == -1:
                raise IntelMQToolException('You are running a tool on non existing messages!')
            setattr(instance, 'receive_message', self.__receive_message_event)
        # boot up
        instance.init()
        if instance.group == 'Collector':
            self.logger.debug('Running Collector bot {}'.format(bot.class_name))
            try:
                instance.process()
            except Exception as error:
                self.__reset_messages()
                raise error
        else:
            for count in range(0, self.__message_count, 1):
                self.logger.debug('Running {} time of {}'.format(count, self.__message_count))
                try:
                    instance.process()
                except Exception as error:
                    self.__reset_messages()
                    raise error

        if isdir(self.old_messages_path):
            rmtree(self.old_messages_path)

    def __reset_messages(self):
        # clear files in base
        message_files = self.__get_files_in_dir(self.config.output_folder)
        for message_file in message_files:
            file_name = join(self.config.output_folder, message_file)
            remove(file_name)
        # move files back from old
        message_files = self.__get_files_in_dir(self.old_messages_path)
        for message_file in message_files:
            destination_file = join(self.config.output_folder, message_file)
            source_file = join(self.old_messages_path, message_file)
            move(source_file, destination_file)
        # directory must be empty remove it
        rmdir(self.old_messages_path)

    def __acknowledge_message(self):
        self.logger.debug('ACK Message')

    def __send_message(self, *messages, path: str = "_default", auto_add=None, path_permissive: bool = False) -> None:
        self.logger.info('Sending Message')
        counter = self.__current_send_message
        for message in messages:
            if not message:
                self.logger.warning("Ignoring empty message at sending. Possible bug in bot.")
                continue
            file_name = join(self.config.output_folder, '{}-{}.json'.format(FiddleHandler.FILE_NAME, counter))
            self.logger.debug('Saving Message to {}'.format(file_name))
            with open(file_name, 'w+') as f:
                f.write(pretty_json(message.to_dict()))
            counter += 1
        self.__current_send_message = counter

    def __get_file_data(self) -> Optional[dict]:
        file_name = join(self.old_messages_path, '{}-{}.json'.format(FiddleHandler.FILE_NAME, self.__current_load_message))
        self.logger.debug('Loading data from {}'.format(file_name))
        with open(file_name, 'r') as f:
            data = json.loads(f.read())
        self.__current_load_message += 1
        return data

    def __receive_message_report(self) -> Report:
        self.logger.info('Receive Message')
        report = Report()
        data = self.__get_file_data()
        for key, value in data.items():
            if key == 'raw':
                decoded = base64.b64decode(value).decode('utf-8')
                report.add(key, decoded, overwrite=True)
            else:
                report.add(key, value, overwrite=True)
        self.logger.debug('Sending Message')
        return report

    def __receive_message_event(self) -> Event:
        self.logger.info('Receive Message (Event)')
        event = Event()
        data = self.__get_file_data()
        for key, value in data.items():
            if key == 'raw':
                decoded = base64.b64decode(value).decode('utf-8')
                event.add(key, decoded, overwrite=True)
            else:
                event.add(key, value, overwrite=True)
        self.logger.debug('Sending Message')
        return event



