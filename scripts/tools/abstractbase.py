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
from configparser import ConfigParser
from typing import List, Tuple
import sys

from intelmqtools.classes.botissue import BotIssue
from intelmqtools.classes.generalissuedetail import GeneralIssueDetail, ParameterIssueDetail
from intelmqtools.classes.intelmqbot import IntelMQBot
from intelmqtools.classes.intelmqbotinstance import IntelMQBotInstance
from intelmqtools.classes.intelmqdetails import IntelMQDetails
from intelmqtools.classes.parameterissue import ParameterIssue
from intelmqtools.exceptions import ToolException
from intelmqtools.utils import colorize_text, pretty_json

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'


class AbstractBaseTool(ABC):

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

    def __init__(self, config: ConfigParser = None, log_level: int = None, is_dev: bool = None) -> None:
        self.is_dev = None
        self._arg_parser = None
        self.logger = logging.getLogger(self.get_class_name())
        self.set_params(log_level, is_dev)
        self.config = config
        self.bot_location = os.path.dirname(os.path.abspath(__file__)).replace('/scripts/libs', '/bots')
        sys.path.insert(0, self.bot_location.replace('/bots', ''))



    def set_config(self, config: ConfigParser):
        self.config = config

    @abstractmethod
    def get_arg_parser(self) -> ArgumentParser:
        return self._arg_parser

    @abstractmethod
    def start(self, args: Namespace) -> None:
        pass

    @abstractmethod
    def get_version(self) -> str:
        return '0.1'

    def set_default_arguments(self, arg_parser: ArgumentParser) -> None:
        arg_parser.add_argument('--version', action='version', version='%(prog)s {}'.format(self.get_version()))

    @staticmethod
    def __extract_data_from_text(file_data: str) -> str:
        bot_reference = None

        if file_data:
            findings = re.search(r'^class (\w+\([^\n]+\)):', file_data, re.MULTILINE)
            if findings:
                class_string_line = findings.groups(1)[0].strip()
                for bot_type in ['Bot', 'CollectorBot', 'ParserBot', 'SQLBot', 'OutputBot']:
                    extends_str = '({})'.format(bot_type)
                    if class_string_line.endswith(extends_str):
                        # this is a bot

                        class_name = class_string_line.replace(extends_str, '')
                        findings = re.search(r'^(\w+) = {}'.format(class_name), file_data, re.MULTILINE)
                        if findings:
                            bot_reference = findings.groups(1)[0].strip()

        return bot_reference

    def __get_bot_object(self,
                         bot_reference: str,
                         bot_folder: str,
                         bot_location: str,
                         bot_file: str
                         ) -> IntelMQBot:
        if bot_reference:
            bot_object = IntelMQBot()
            bot_module = 'intelmq.bots{}'.format(bot_folder.replace(bot_location, ''))
            if bot_location == self.bot_location:
                bot_module = 'bots{}'.format(bot_folder.replace(bot_location, ''))
            bot_module = bot_module.replace(os.path.sep, '.')
            bot_module = '{}.{}'.format(bot_module, bot_file.replace('.py', ''))
            bot_object.code_module = bot_module
            bot_object.bot_alias = bot_reference

            # check if it is a custom bot
            config_path = os.path.join(bot_folder, 'config.json')
            if os.path.exists(config_path):
                with open(config_path) as f:
                    default_custom_config = json.load(f)
                for key, values in default_custom_config.items():
                    bot_object.custom_default_parameters = values
                    bot_object.class_name = key
                    bot_object.custom = True
                return bot_object
            else:
                if self.bot_location in bot_location:
                    print('Configuration for bot {} is missing. Create in in file {}'.format(bot_module, config_path))
            return bot_object

    def __populate_intelmq_details(self, module: any, details: IntelMQDetails, dev: bool) -> None:
        details.config_dir = getattr(module, 'CONFIG_DIR')
        version = getattr(getattr(module, 'version'), '__version_info__')
        details.version = '{}.{}.{}'.format(version[0], version[1], version[len(version) - 1])
        details.intelmq_location = self.config['IntelMQ']['intelMQLocation']
        details.entry_point_location = self.config['IntelMQ']['entryPointsLocation']
        details.bin_folder = self.config['IntelMQ']['binFolder']

        if dev:
            base = self.config['IntelMQ']['fakeRoot']
            details.config_dir = os.path.join(base, details.config_dir[1:])
            details.intelmq_location = os.path.join(base, details.intelmq_location[1:])
            details.entry_point_location = os.path.join(base, details.entry_point_location[1:])
            details.bin_folder = os.path.join(base, details.bin_folder[1:])

    def __get_bots(self, bot_location: str) -> List[IntelMQBot]:
        bot_details = list()

        bot_type_folders = list()
        for bot_folder_base in IntelMQDetails.BOT_FOLDER_BASES:
            bot_type_folders.append(os.path.join(bot_location, bot_folder_base))

        # list all folders
        for bot_type_folder in bot_type_folders:
            for bot_folder_name in os.listdir(bot_type_folder):
                bot_folder = os.path.join(bot_type_folder, bot_folder_name)
                if os.path.isdir(bot_folder):
                    for bot_file in [f for f in os.listdir(bot_folder) if os.path.isfile(os.path.join(bot_folder, f))]:
                        if bot_file.endswith('.py'):
                            if bot_file != '__init__.py':
                                file_name = os.path.join(bot_folder, bot_file)
                                with open(file_name, 'r') as f:
                                    file_data = f.read()
                                bot_reference = self.__extract_data_from_text(file_data)
                                bot_object = self.__get_bot_object(
                                    bot_reference,
                                    bot_folder,
                                    bot_location,
                                    bot_file,
                                )
                                if bot_object:
                                    bot_details.append(bot_object)
        return bot_details

    def set_default_options(self, intelmq_details: IntelMQDetails, bots: List[IntelMQBot]) -> None:
        defaults_config = self.get_config(intelmq_details.defaults_conf_file)
        for bot in bots:
            bot.intelmq_defaults = defaults_config

    def get_intelmq_details(self, dev: bool) -> IntelMQDetails:
        intelmq_details = IntelMQDetails()
        command_module = __import__('intelmq.bots')

        self.__populate_intelmq_details(command_module, intelmq_details, dev)
        return intelmq_details

    def __set_BOTS(self, default_configs: dict, intelmq_details: IntelMQDetails, bot_details: List[IntelMQBot], running_bots: bool) -> None:
        for bot_type, bot_config_object in default_configs.items():
            for bot_name, bot_config in bot_config_object.items():
                module_name = bot_config['module']
                for bot_detail in bot_details:
                    if bot_detail.code_module == module_name:
                        if bot_detail.code_file is None:
                            code_file = os.path.join(intelmq_details.intelmq_location,
                                                     bot_detail.code_module.replace('.', os.path.sep))
                            bot_detail.code_file = '{}.py'.format(code_file)
                        if running_bots:
                            bot_detail.default_parameters = bot_config
                        else:
                            bot_detail.custom_default_parameters = bot_config
                        bot_detail.installed = running_bots
                        if not bot_detail.class_name:
                            bot_detail.class_name = bot_name
                        bot_detail.custom = False

                        break

    def set_default_runtime_config(self, intelmq_details: IntelMQDetails, bot_details: List[IntelMQBot]) -> None:
        default_configs = self.get_config(intelmq_details.base_bots_file)
        # fetch default configuration in BOTS file
        self.__set_BOTS(default_configs, intelmq_details, bot_details, False)

        default_configs = self.get_config(intelmq_details.base_bots_file)
        # fetch default configuration in BOTS file

        default_configs = self.get_config(intelmq_details.running_bots_file)
        self.__set_BOTS(default_configs, intelmq_details, bot_details, True)

        # fetch running configurations
        default_configs = self.get_config(intelmq_details.runtime_file)
        for bot_name, bot_config_object in default_configs.items():
            for bot_detail in bot_details:
                module_name = bot_config_object['module']
                if bot_detail.code_module == module_name:
                    instance = IntelMQBotInstance()
                    instance.name = bot_name
                    instance.config = bot_config_object
                    instance.bot = bot_detail
                    bot_detail.instances.append(instance)

    @staticmethod
    def get_config(file_path: str) -> dict:
        if os.path.exists(file_path):
            with open(file_path, 'r') as fpconfig:
                config = json.load(fpconfig)
        else:
            raise ToolException('File not found: {}.'.format(file_path))
        return config

    def get_original_bots(self, dev: bool) -> Tuple[IntelMQDetails, List[IntelMQBot]]:
        # get directory structure
        intelmq_details = self.get_intelmq_details(dev)
        bot_location = os.path.join(intelmq_details.intelmq_location, 'bots')
        bot_details = self.__get_bots(bot_location)
        self.set_default_runtime_config(intelmq_details, bot_details)
        self.set_default_options(intelmq_details, bot_details)
        bots = list()
        for bot_detail in bot_details:
            if not bot_detail.custom:
                bots.append(bot_detail)

        return intelmq_details, bots

    def get_custom_bots(self, dev: bool) -> Tuple[IntelMQDetails, List[IntelMQBot]]:
        # get directory structure
        bot_details = self.__get_bots(self.bot_location)
        intelmq_details = self.get_intelmq_details(dev)
        for bot_detail in bot_details:
            # set path right
            code_file = os.path.join(self.bot_location, bot_detail.code_module.replace('.', os.path.sep))
            file_path = '{}.py'.format(code_file)
            # TODO: find out why? but it works
            bot_detail.code_file = file_path.replace('/bots/', '/')
            # set module right
            bot_detail.code_module = 'intelmq.{}'.format(bot_detail.code_module)
            # determine type
        self.set_default_runtime_config(intelmq_details, bot_details)
        self.set_default_options(intelmq_details, bot_details)
        return intelmq_details, bot_details

    @staticmethod
    def print_bot_detail(bot_detail: IntelMQBot, full: bool = False) -> None:
        print('BOT Type:                {}'.format(colorize_text(bot_detail.bot_type, 'Gray')))
        print('BOT Class:               {}'.format(colorize_text(bot_detail.class_name, 'LightYellow')))
        print('Description:             {}'.format(colorize_text(bot_detail.description, 'White')))
        print('Module:                  {}'.format(bot_detail.code_module))
        print('Entry Point:             {}'.format(bot_detail.entry_point))
        if full and bot_detail.installed:
            print('{}:          {}'.format(colorize_text('Default Running Config', 'Cyan'),
                                           pretty_json(bot_detail.default_parameters)))
        if full:
            print('{}:   {}'.format(colorize_text('Default Config', 'Cyan'),
                                    pretty_json(bot_detail.custom_default_parameters)))
        print('File:                    {}'.format(bot_detail.code_file))
        len_instances = len(bot_detail.instances)
        print('Running Instances        {}'.format(colorize_text(len_instances, 'Magenta')))
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
                param_name = ''
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

    def __get_bots_by_install(self, installed: bool, dev: bool) -> Tuple[IntelMQDetails, List[IntelMQBot]]:
        intelmq_details, bot_details = self.get_all_bots(dev)
        result = list()
        for bot_detail in bot_details:
            if bot_detail.installed is installed:
                result.append(bot_detail)
        return intelmq_details, result

    def get_uninstalled_bots(self, dev: bool) -> Tuple[IntelMQDetails, List[IntelMQBot]]:
        return self.__get_bots_by_install(False, dev)

    def get_installed_bots(self, dev: bool) -> Tuple[IntelMQDetails, List[IntelMQBot]]:
        return self.__get_bots_by_install(True, dev)

    def get_different_configs(self, bot_details: List[IntelMQBot], type_: str) -> List[BotIssue]:
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

    def get_all_bots(self, dev: bool) -> Tuple[IntelMQDetails, List[IntelMQBot]]:
        bots = list()
        intelmq_details, org_bots = self.get_original_bots(dev)
        intelmq_details, bot_details = self.get_custom_bots(dev)
        # It may be possible that custom bots cannot be distinguished
        for org_bot in org_bots:
            not_found = True
            for bot in bot_details:
                if org_bot.code_module == bot.code_module:
                    not_found = False
                    bots.append(bot)
            if not_found:
                bots.append(org_bot)
        return intelmq_details, bots

    def update_bots_file(self, bots: List[IntelMQBot], mode_: str, dev: bool) -> None:
        intelmq_details, all_bots = self.get_installed_bots(dev)
        result_dict = {'Collector': dict(), 'Expert': dict(), 'Output': dict(), 'Parser': dict()}

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
        if mode_ == 'insert':
            for bot in bots:
                bot.default_parameters = bot.custom_default_parameters
                result_dict[bot.bot_type][bot.class_name] = bot.get_bots_config(False)

        with open(intelmq_details.running_bots_file, "w") as f:
            f.write(pretty_json(result_dict))
