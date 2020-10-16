# -*- coding: utf-8 -*-

"""
Created on 15.01.20
"""
import json
import logging
import os
import re
from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace

from typing import List, Optional, Tuple

from intelmqtools.classes.botissue import BotIssue
from intelmqtools.classes.generalissuedetail import ParameterIssueDetail, GeneralIssueDetail
from intelmqtools.classes.intelmqbot import IntelMQBot
from intelmqtools.classes.intelmqbotinstance import IntelMQBotInstance
from intelmqtools.classes.intelmqtoolconfig import IntelMQToolConfig

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

from intelmqtools.classes.parameterissue import ParameterIssue

from intelmqtools.exceptions import MissingConfigurationException, ConfigNotFoundException, ToolException
from intelmqtools.utils import pretty_json, colorize_text


class ExtractionException(ToolException):
    pass


class AbstractBaseTool(ABC):

    def __init__(self, config: IntelMQToolConfig = None):
        self.logger = logging.getLogger(self.get_class_name())
        self.config: IntelMQToolConfig = None
        if config:
            # No need to sel log lvl if there is no configuration
            self.set_config(config)

    def __set_logger(self, log_level: int) -> None:
        if log_level and log_level > -1:
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            self.logger.setLevel(logging.DEBUG)
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(log_format))
            console_handler.setLevel(self.__get_log_level(log_level))
            self.logger.addHandler(console_handler)

            self.logger.debug('Created instance of {}'.format(self.get_class_name()))

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
        raise NotImplemented()

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
        self.__set_logger(self.config.log_lvl)

    def __get_bots(self, bot_location: str) -> List[IntelMQBot]:
        bot_details = list()

        bot_type_folders = list()
        for bot_folder_base in IntelMQToolConfig.BOT_FOLDER_BASES:
            bot_type_folders.append(os.path.join(bot_location, bot_folder_base))

        # list all folders
        for bot_type_folder in bot_type_folders:
            for bot_folder_name in os.listdir(bot_type_folder):
                bot_folder = os.path.join(bot_type_folder, bot_folder_name)
                if os.path.isdir(bot_folder):
                    for bot_file in [f for f in os.listdir(bot_folder) if os.path.isfile(os.path.join(bot_folder, f))]:
                        if bot_file.endswith('.py'):
                            if bot_file != '__init__.py':
                                # the bot_reference is actually how it is called
                                bot_object = self.__get_bot_object(
                                    bot_folder,
                                    bot_location,
                                    bot_file,
                                )
                                if bot_object:
                                    bot_details.append(bot_object)
        return bot_details

    def __extract_data_from_file(self, file_path: str) -> Optional[Tuple[str, str, str]]:
        file_data = None
        with open(file_path, 'r') as f:
            file_data = f.read()
        if file_data:
            findings = re.search(r'^class (\w+\([^\n]+\)):', file_data, re.MULTILINE)
            if findings:
                class_string_line = findings.groups(1)[0].strip()
                # get extended class
                try:
                    bot_reference = None
                    index_of_first_parentesis = class_string_line.index('(')
                    class_name = class_string_line[0:index_of_first_parentesis]
                    parent_class = class_string_line[index_of_first_parentesis + 1:-1]
                    if 'bot' in parent_class.lower():
                        findings = re.search(r'^(\w+) = {}'.format(class_name), file_data, re.MULTILINE)
                        if findings:
                            bot_reference = findings.groups(1)[0].strip()

                        return bot_reference, class_name, parent_class
                    else:
                        self.logger.info('File {} is not a bot file, ignoring it'.format(file_path))

                except ValueError:
                    # basically the file is not usable
                    return None
            return None
        raise ExtractionException('This should not happen as this is then an empty file.')

    def __get_bot_object(self,
                         bot_folder: str,
                         bot_location: str,
                         bot_file: str
                         ) -> Optional[IntelMQBot]:
        file_name = os.path.join(bot_folder, bot_file)
        extracted_data = self.__extract_data_from_file(file_name)

        if extracted_data:
            bot_object = IntelMQBot()
            bot_object.parent_class = extracted_data[2]
            bot_object.class_name = extracted_data[1]
            bot_object.bot_alias = extracted_data[0]
            bot_object.code_file = file_name

            # Check if this is part of the installation
            bot_subpart = bot_folder.replace(bot_location, '')
            bot_module = bot_subpart.replace(os.path.sep, '.')
            if self.config.intelmq_folder in bot_folder:
                bot_module = 'intelmq.bots{}'.format(bot_module)
                bot_object.custom = False
            else:
                # this is a custom bot
                last_dir = os.path.basename(bot_location)
                bot_module = '{}{}'.format(last_dir, bot_module)
                config_path = os.path.join(bot_folder, 'config.json')
                bot_object.custom = True
                if os.path.exists(config_path):
                    with open(config_path) as f:
                        default_custom_config = json.load(f)
                    for key, values in default_custom_config.items():
                        bot_object.custom_default_parameters = values
                        bot_object.class_name = key
                else:
                    # this is a custom bot's config is missing

                    if self.config.custom_bot_folder in bot_location:
                        raise MissingConfigurationException(
                            'Configuration for bot {} is missing. Create in in file {}'.format(bot_module, config_path)
                        )

            bot_module = '{}.{}'.format(bot_module, bot_file.replace('.py', ''))
            bot_object.code_module = bot_module
            if bot_object.custom:
                bot_object.custom_default_parameters['module'] = bot_module

            return bot_object
        else:
            self.logger.info('File {} is not a bot file, ignoring it'.format(os.path.join(bot_folder, bot_file)))

    @staticmethod
    def get_config(file_path: str) -> dict:
        if os.path.exists(file_path):
            with open(file_path, 'r') as fpconfig:
                config = json.load(fpconfig)
        else:
            raise ConfigNotFoundException('File not found: {}.'.format(file_path))
        return config

    @staticmethod
    def __set_bots(default_configs: dict, bot_details: List[IntelMQBot], running_bots: bool) -> None:
        for bot_type, bot_config_object in default_configs.items():
            for bot_name, bot_config in bot_config_object.items():
                module_name = bot_config['module']
                for bot_detail in bot_details:
                    if bot_detail.code_module == module_name:
                        if running_bots:
                            bot_detail.default_parameters = bot_config
                            # if a bot is registered in the BOTS file then it is installed
                            bot_detail.installed = True
                        else:
                            bot_detail.custom_default_parameters = bot_config
                        break

    def set_default_runtime_config(self, bot_details: List[IntelMQBot]) -> None:
        default_configs = self.get_config(self.config.base_bots_file)
        # fetch default configuration in BOTS file
        self.__set_bots(default_configs, bot_details, False)

        # fetch default configuration in BOTS file
        default_configs = self.get_config(self.config.running_bots_file)
        self.__set_bots(default_configs, bot_details, True)

        # fetch running configurations
        default_configs = self.get_config(self.config.runtime_file)
        for bot_name, bot_config_object in default_configs.items():
            for bot_detail in bot_details:
                module_name = bot_config_object['module']
                if bot_detail.code_module == module_name:
                    instance = IntelMQBotInstance()
                    instance.name = bot_name
                    instance.config = bot_config_object
                    instance.bot = bot_detail
                    bot_detail.instances.append(instance)

    def set_default_options(self, bots: List[IntelMQBot]) -> None:
        defaults_config = self.get_config(self.config.defaults_conf_file)
        for bot in bots:
            bot.intelmq_defaults = defaults_config

    def get_original_bots(self) -> List[IntelMQBot]:
        # get directory structure
        bot_location = os.path.join(self.config.intelmq_folder, 'bots')
        bot_details = self.__get_bots(bot_location)
        self.set_default_runtime_config(bot_details)
        self.set_default_options(bot_details)
        bots = list()
        for bot_detail in bot_details:
            if not bot_detail.custom:
                bots.append(bot_detail)

        return bots

    def get_custom_bots(self) -> List[IntelMQBot]:
        # get directory structure
        bot_details = self.__get_bots(self.config.custom_bot_folder)
        self.set_default_runtime_config(bot_details)
        self.set_default_options(bot_details)
        return bot_details

    def get_all_bots(self) -> List[IntelMQBot]:
        bots = list()
        org_bots = self.get_original_bots()
        bot_details = self.get_custom_bots()
        # It may be possible that custom bots cannot be distinguished
        return bots + org_bots + bot_details

    @staticmethod
    def print_bot_detail(bot_detail: IntelMQBot, full: bool = False) -> None:
        type_text = bot_detail.bot_type
        if bot_detail.custom:
            type_text = '{} (Custom)'.format(type_text)
        print('BOT Type:                {}'.format(colorize_text(type_text, 'Gray')))
        print('BOT Class:               {}'.format(colorize_text(bot_detail.class_name, 'LightYellow')))
        print('Description:             {}'.format(colorize_text(bot_detail.description, 'LightGray')))
        print('Module:                  {}'.format(bot_detail.code_module))
        print('Entry Point:             {}'.format(bot_detail.entry_point))
        print('Installed:               {}'.format(bot_detail.installed))
        if full and bot_detail.installed:
            print('{}:          {}'.format(colorize_text('Default Running Config', 'Cyan'),
                                           pretty_json(bot_detail.default_parameters)))
        if full:
            print('{}:          {}'.format(colorize_text('Default Config', 'Cyan'),
                                           pretty_json(bot_detail.custom_default_parameters)))
        print('File:                    {}'.format(bot_detail.code_file))
        len_instances = len(bot_detail.instances)
        print('Running Instances        {}'.format(colorize_text('{}'.format(len_instances), 'Magenta')))
        if len_instances > 0 and full:
            print('Intances: -----------------'.format(len_instances))
            counter = 1
            for instance in bot_detail.instances:
                print('Instance {}: Name:              {}'.format(counter, instance.name))
                print('Instance {}: Parameters:        {}'.format(counter, pretty_json(instance.parameters)))
                counter = counter + 1
            if counter > 1:
                print()
        print()

    def print_bot_details(self, bot_details: List[IntelMQBot], full: bool = False) -> None:
        for bot_detail in bot_details:
            self.print_bot_detail(bot_detail, full)

    def __get_bots_by_install(self, installed: bool) -> List[IntelMQBot]:
        bot_details = self.get_all_bots()
        result = list()
        for bot_detail in bot_details:
            if bot_detail.installed is installed:
                result.append(bot_detail)
        return result

    def get_uninstalled_bots(self) -> List[IntelMQBot]:
        return self.__get_bots_by_install(False)

    def get_installed_bots(self) -> List[IntelMQBot]:
        return self.__get_bots_by_install(True)

    def get_different_configs(self, bot_details: List[IntelMQBot], type_: str) -> Optional[List[BotIssue]]:
        differences = list()

        for bot_detail in bot_details:

            # To do this the bot has to be installed
            if bot_detail.installed and type_ == 'BOTS':
                item = BotIssue()
                item.bot = bot_detail
                general_issues = self.compare_dicts(
                    bot_detail.default_parameters,
                    bot_detail.custom_default_parameters,
                    type_
                )
                if not general_issues.empty:
                    item.issue = general_issues
                    differences.append(item)
            if bot_detail.installed and type_ == 'runtime':
                for instance in bot_detail.instances:
                    if bot_detail.default_parameters:
                        parameters = bot_detail.default_parameters.get('parameters')
                        if parameters:
                            general_issues = self.compare_dicts(instance.parameters, parameters, 'parameters')
                            if not general_issues.empty:
                                item = BotIssue()
                                item.bot = bot_detail
                                item.issue = general_issues
                                item.instance = instance
                                differences.append(item)
        if len(differences) > 0:
            return differences
        else:
            return None

    def compare_dicts(self, dict1: dict, dict2: dict, type_: str,
                      previous_param_name: str = None) -> GeneralIssueDetail:
        new_bot_issue = GeneralIssueDetail()
        for key in dict1.keys():
            if key not in dict2.keys():
                new_bot_issue.additional_keys.append(key)
        for key in dict2.keys():
            if key not in dict1.keys():
                new_bot_issue.missing_keys.append(key)

        if type_ != 'parameters':
            for key, value in dict1.items():
                if previous_param_name:
                    param_name = '{}.{}'.format(previous_param_name, key)
                else:
                    param_name = key
                if param_name.startswith('.'):
                    param_name = param_name[1:]
                if isinstance(value, dict):
                    if key not in new_bot_issue.missing_keys:
                        value2 = dict2.get(key, {})
                        sub_issue = self.compare_dicts(value, value2, type_, param_name)
                        issue = ParameterIssueDetail()
                        issue.parameter_name = param_name
                        issue.additional_keys = sub_issue.additional_keys
                        issue.missing_keys = sub_issue.missing_keys
                        issue.different_values = sub_issue.different_values
                        if not issue.empty:
                            new_bot_issue.different_values.append(issue)
                else:
                    if key not in new_bot_issue.additional_keys:
                        value2 = dict2[key]
                        if value != value2:
                            param_issue = ParameterIssue()
                            param_issue.parameter_name = param_name
                            param_issue.should_be = value
                            param_issue.has_value = value2
                            new_bot_issue.different_values.append(param_issue)

        if len(new_bot_issue.missing_keys) == 0:
            new_bot_issue.missing_keys = None
        if len(new_bot_issue.additional_keys) == 0:
            new_bot_issue.additional_keys = None
        if len(new_bot_issue.different_values) == 0:
            new_bot_issue.different_values = None
        return new_bot_issue

    def update_bots_file(self, bots: List[IntelMQBot], mode_: str) -> None:
        all_bots = self.get_installed_bots()
        result_dict = {'Collector': dict(), 'Expert': dict(), 'Output': dict(), 'Parser': dict()}

        """
        for bots_bot in all_bots:
            found = False
            if mode_ in ['update', 'remove']:
                for bot in bots:
                    if bots_bot.code_module == bot.code_module:
                        parameters = bot.default_parameters
                        if parameters is None:
                            # then it is a new one
                            parameters = bot.custom_default_parameters
                        bots_bot.default_parameters = parameters
                        found = True
                        break
            if not (found and mode_ == 'remove'):
                result_dict[bots_bot.bot_type][bots_bot.class_name] = bots_bot.get_bots_config(False)
        """
        if mode_ == 'insert':
            for bot in bots:
                bot.default_parameters = bot.custom_default_parameters
                result_dict[bot.bot_type][bot.class_name] = bot.get_bots_config(False)

        content = pretty_json(result_dict)
        with open(self.config.running_bots_file, "w") as f:
            f.write(content)
