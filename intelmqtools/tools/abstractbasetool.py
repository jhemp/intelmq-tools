# -*- coding: utf-8 -*-

"""
Created on 15.01.20
"""
import importlib
import inspect
import json
import logging
import os
import re
from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
from os.path import basename
from types import FunctionType

from typing import List, Optional, Tuple, Union

from intelmq.lib.bot import Bot

from intelmqtools.classes.botissue import BotIssue
from intelmqtools.classes.generalissuedetail import GeneralIssueDetail
from intelmqtools.classes.intelmqbot import IntelMQBot, IntelMQBotConfig
from intelmqtools.classes.intelmqbotinstance import IntelMQBotInstance
from intelmqtools.classes.intelmqtoolconfig import IntelMQToolConfig
from intelmqtools.classes.strangebot import StrangeBot


__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

from intelmqtools.classes.parameterissue import ParameterIssue

from intelmqtools.exceptions import MissingConfigurationException, ConfigNotFoundException, ToolException
from intelmqtools.utils import pretty_json, colorize_text, create_executable


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
        self.logger.debug('Setting Config for Tool {}'.format(self.get_class_name()))
        self.config = config
        self.__set_logger(self.config.log_lvl)

    def __get_bots(self, bot_location: str) -> List[IntelMQBot]:
        bot_details = list()

        # collect possible bot types
        possible_main_classes = list()
        for subclass in Bot.__subclasses__():
            possible_main_classes.append(subclass.__name__)
        possible_main_classes.append('Bot')
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
                            # the bot_reference is actually how it is called
                            bot_object = self.__get_bot_object(
                                bot_folder,
                                bot_location,
                                bot_file,
                                possible_main_classes
                            )
                            if bot_object:
                                bot_details.append(bot_object)
        return bot_details

    def __extract_data_from_file(self, file_path: str, possible_main_classes: List[str]) -> Optional[Tuple[str, str, str]]:
        file_data = None
        self.logger.debug('Opening "{}"'.format(file_path))
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
                    if ',' in parent_class:
                        # this is multiple inheritance
                        for item in possible_main_classes:
                            if item in parent_class:
                                # if the base class is found then return this as parent as the other inheritance is
                                # considered as a part of the bot package
                                parent_class = item
                                break
                    if parent_class in possible_main_classes:
                        # this is a bot class
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
        else:
            self.logger.debug('File "" is empty, ignoring'.format(file_path))

    def __get_bot_object(self,
                         bot_folder: str,
                         bot_location: str,
                         bot_file: str,
                         possible_main_classes: List[str]
                         ) -> Optional[IntelMQBot]:
        file_name = os.path.join(bot_folder, bot_file)
        # extracted_data = bot_reference, class_name, parent_class
        extracted_data = self.__extract_data_from_file(file_name, possible_main_classes)

        if extracted_data:
            bot_object = IntelMQBot()
            bot_object.parent_class = extracted_data[2]
            bot_object.class_name = extracted_data[1]
            bot_object.bot_alias = extracted_data[0]
            bot_object.file_path = file_name

            # Check if this is part of the installation
            bot_subpart = bot_folder.replace(bot_location, '')
            bot_module = bot_subpart.replace(os.path.sep, '.')
            bot_module = '{}.{}'.format(bot_module, bot_file.replace('.py', ''))

            if self.config.intelmq_folder in bot_folder:
                bot_module = 'intelmq.bots{}'.format(bot_module)
                bot_object.module = bot_module
                bot_object.custom = False
            else:
                # this is a custom bot
                last_dir = os.path.basename(bot_location)
                bot_module = '{}{}'.format(last_dir, bot_module)
                config_path = os.path.join(bot_folder, 'config.json')
                bot_object.custom = True
                if os.path.exists(config_path):
                    self.logger.debug('Using config.json for bot {}'.format(bot_module))
                    with open(config_path) as f:
                        default_custom_config = json.load(f)
                else:
                    self.logger.debug('Configuration file config.json is not existing for bot {}'.format(bot_module))
                    default_custom_config = (bot_object.class_name, {'module': bot_module, 'description': 'NotSet'})

                # setting the configuration
                configuration_element = default_custom_config.popitem()
                config = IntelMQBotConfig()
                config.name = configuration_element[0]
                config.description = configuration_element[1].get('description', 'NotSet')
                config.parameters = configuration_element[1].get('parameters', {})
                bot_object.default_bots = config
                bot_object.module = bot_module

            self.logger.debug(
                'Created BotObject for Bot {} Bots in Tool {}'.format(bot_object.class_name, self.get_class_name())
            )

            # Check if the executable exists
            path = os.path.join(self.config.bin_folder, bot_object.executable_name)
            bot_object.executable_exists = os.path.exists(path)

            # check check also in the instance as there may be configuration details after intelmq 2.3.2
            # this is basically also a verification if they match the bots config
            # Note: This does not work for self.parameters fields!
            # Note2: The class parameters have priority
            spec = importlib.util.spec_from_file_location(bot_object.module, bot_object.file_path)
            bot_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(bot_module)
            bot_class = getattr(bot_module, bot_object.class_name)
            parent_class = getattr(bot_module, bot_object.parent_class)
            parent_fields = self.get_fields(parent_class)
            fields = list()
            class_fields = self.get_fields(bot_class)
            for item in class_fields:
                if item not in parent_fields:
                    fields.append(item)
            if fields:
                if bot_object.default_bots is None:
                    bot_object.default_bots = IntelMQBotConfig()

                for field in fields:
                    bot_object.default_bots.parameters[field] = getattr(bot_class, field)

                # set default values if set in the file itself
                name = getattr(bot_class, 'name')
                if name:
                    bot_object.default_bots.name = name
                description = getattr(bot_class, 'description')
                if description:
                    bot_object.default_bots.description = description

            return bot_object
        else:
            self.logger.info('File {} is not a bot file, ignoring it'.format(os.path.join(bot_folder, bot_file)))

    @staticmethod
    def get_fields(clazz: Bot) -> List[str]:
        output = list()
        for i in inspect.getmembers(clazz):
            if not i[0].startswith('_'):
                if not isinstance(i[1], FunctionType):
                    output.append(i[0])
        return output

    def get_config(self, file_path: str) -> dict:
        self.logger.debug('Loading configuration {}'.format(file_path))
        if os.path.exists(file_path):
            with open(file_path, 'r') as fpconfig:
                config = json.load(fpconfig)
        else:
            raise ConfigNotFoundException('File not found: {}.'.format(file_path))
        return config

    def __get_intelmq_bot_config(self, bot_name: str, data: dict) -> IntelMQBotConfig:
        self.logger.debug('Creating bot config for bot {}'.format(bot_name))
        output = IntelMQBotConfig()
        output.name = bot_name
        output.description = data.get('description', 'NotSet')
        output.parameters = data.get('parameters', {})
        return output

    def __set_bots(self, default_configs: dict, bot_details: List[IntelMQBot], running_bots: bool) -> None:
        self.logger.debug('Setting default config for bot objects')
        for bot_type, bot_config_object in default_configs.items():
            for bot_name, bot_config in bot_config_object.items():
                module_name = bot_config['module']
                for bot_detail in bot_details:
                    if bot_detail.module == module_name:
                        if running_bots:
                            bot_detail.bots_config = self.__get_intelmq_bot_config(bot_name, bot_config)
                        else:
                            bot_detail.default_bots = self.__get_intelmq_bot_config(bot_name, bot_config)
                        break

    def __get_intelmq_instance(self, bot_name: str, bot_detail: IntelMQBot, data: dict) -> IntelMQBotInstance:
        self.logger.debug('Creating instance object for {}'.format(bot_name))
        instance = IntelMQBotInstance()
        instance.name = data['name']
        instance.description = data['description']
        instance.bot_id = data['bot_id']
        instance.group = data['group']
        instance.groupname = data['groupname']
        instance.module = data['module']
        instance.run_mode = data['run_mode']
        instance.parameters = data['parameters']
        instance.enabled = data['enabled']
        instance.bot = bot_detail
        return instance

    def set_bots_runtime_config(self, bot_details: List[IntelMQBot]) -> None:
        self.logger.debug('Setting default runtime config for bots')
        default_configs = self.get_config(self.config.base_bots_file)
        # fetch default configuration in BOTS file
        self.__set_bots(default_configs, bot_details, False)

        # fetch running configuration in BOTS file
        default_configs = self.get_config(self.config.running_bots_file)
        self.__set_bots(default_configs, bot_details, True)

        # fetch runtime configurations
        default_configs = self.get_config(self.config.runtime_file)
        for bot_name, bot_config_object in default_configs.items():
            for bot_detail in bot_details:
                module_name = bot_config_object['module']
                if bot_detail.module == module_name:
                    instance = self.__get_intelmq_instance(bot_name, bot_detail, bot_config_object)
                    bot_detail.instances.append(instance)

    def set_bot_defaults(self, bots: List[IntelMQBot]) -> None:
        self.logger.debug('Setting default options for bots')
        defaults_config = self.get_config(self.config.defaults_conf_file)
        for bot in bots:
            bot.default_parameters = defaults_config

    def get_original_bots(self) -> List[IntelMQBot]:
        self.logger.debug('Getting original bots for Tool {}'.format(self.get_class_name()))
        # get directory structure
        bot_location = os.path.join(self.config.intelmq_folder, 'bots')
        bot_details = self.__get_bots(bot_location)
        # set defaults.conf
        self.set_bot_defaults(bot_details)
        # set runtime.conf and BOTS details
        self.set_bots_runtime_config(bot_details)
        # self BOTS details

        bots = list()
        for bot_detail in bot_details:
            if not bot_detail.custom:
                bots.append(bot_detail)
        return bots

    def get_custom_bots(self) -> List[IntelMQBot]:
        self.logger.debug('Getting custom bots for Tool {}'.format(self.get_class_name()))
        # get directory structure
        bot_details = self.__get_bots(self.config.custom_bot_folder)
        self.set_bots_runtime_config(bot_details)
        self.set_bot_defaults(bot_details)
        return bot_details

    def get_all_bots(self) -> List[IntelMQBot]:
        self.logger.debug('Getting all bots for Tool {}'.format(self.get_class_name()))
        bots = list()
        org_bots = self.get_original_bots()
        bot_details = self.get_custom_bots()
        # It may be possible that custom bots cannot be distinguished
        return bots + org_bots + bot_details

    @staticmethod
    def print_bot_meta(bot_detail: IntelMQBot) -> None:
        internal_detail = bot_detail
        if isinstance(bot_detail, StrangeBot):
            internal_detail = internal_detail.bot

        type_text = internal_detail.bot_type
        if internal_detail.custom:
            type_text = '{} (Custom)'.format(type_text)
        print('BOT Type:                {}'.format(colorize_text(type_text, 'Gray')))
        print('BOT Class:               {}'.format(colorize_text(internal_detail.class_name, 'LightYellow')))
        print('Description:             {}'.format(colorize_text(internal_detail.description, 'LightGray')))
        print('Module:                  {}'.format(internal_detail.module))
        print('File:                    {}'.format(internal_detail.file_path))

    def print_bot_detail(self, bot_detail: IntelMQBot, full: bool = False) -> None:
        self.print_bot_meta(bot_detail)
        strange = bot_detail.strange
        if strange:
            strange = colorize_text(strange, 'Red')
        print('Installed/Strange:       {}/{}'.format(bot_detail.installed, strange))
        self.print_bot_full(bot_detail, full)

    @staticmethod
    def print_bot_full(bot_detail: IntelMQBot, full: bool = False) -> None:
        internal_detail = bot_detail
        if isinstance(bot_detail, StrangeBot):
            internal_detail = internal_detail.bot

        if full and internal_detail.installed:
            print('{}:          {}'.format(colorize_text('Default Running Config', 'Cyan'),
                                           pretty_json(internal_detail.default_bots_parameters)))
        if full:
            print('{}:          {}'.format(colorize_text('Default Config', 'Cyan'),
                                           pretty_json(internal_detail.custom_default_parameters)))
        len_instances = len(internal_detail.instances)
        print('Running Instances        {}'.format(colorize_text('{}'.format(len_instances), 'Magenta')))
        if len_instances > 0 and full:
            print('Intances: -----------------'.format(len_instances))
            counter = 1
            for instance in internal_detail.instances:
                print('Instance {}: Name:              {}'.format(counter, instance.name))
                print('Instance {}: Parameters:        {}'.format(counter, pretty_json(instance.parameters)))
                counter = counter + 1
            if counter > 1:
                print()

    def print_bot_strange(self, bot_detail: IntelMQBot) -> None:
        internal_detail = bot_detail
        if isinstance(bot_detail, StrangeBot):
            internal_detail = internal_detail.bot

        if internal_detail.strange:
            print(colorize_text('Errors:', 'Red'))
        if not internal_detail.executable_exists and (internal_detail.bots_config or internal_detail.has_running_config):
            print('- Executable "{}" does not exist in {}'.format(internal_detail.module, self.config.bin_folder))
        if not internal_detail.default_bots:
            if bot_detail.custom:
                path = bot_detail.file_path.replace(basename(bot_detail.file_path), '')
                print('- BOT has no config.json in {}, or nothing was specified in the class'.format(path))
            else:
                path = self.config.base_bots_file
                print('- BOT has no default configuration in {}'.format(path))
        if internal_detail.executable_exists and not (internal_detail.bots_config or internal_detail.has_running_config):
            print('- BOT has an executable but is not installed')

    def print_bot_details(self, bot_details: List[IntelMQBot], full: bool = False) -> None:
        for bot_detail in bot_details:
            self.print_bot_detail(bot_detail, full)
            print()

    def __get_bots_by_install(self, installed: bool) -> List[IntelMQBot]:
        self.logger.debug('Getting bots by installed = {} for Tool {}'.format(installed, self.get_class_name()))
        bot_details = self.get_all_bots()
        result = list()
        for bot_detail in bot_details:
            if bot_detail.installed is installed:
                result.append(bot_detail)
        return result

    def get_strange_bots(self, with_issues: bool) -> List[StrangeBot]:
        self.logger.debug('Fetching strange bots')
        bot_details = self.get_all_bots()
        strange_bots = dict()
        for bot_detail in bot_details:
            if bot_detail.strange:
                strange_bots[bot_detail.module] = {
                        'bot': bot_detail,
                        'issues': list()
                    }

        if with_issues:
            issues = self.get_issues(strange_bots, 'BOTS')
            if issues:
                # this command takes only into account installed bot
                for issue in issues:
                    strange_bots[issue.bot.module]['issues'].append(issue)

        return_values = list()
        for item in strange_bots.values():
            bot = item['bot']
            issues = item['issues']
            if bot.has_issues is False:
                bot.has_issues = len(issues) > 0
            if bot.strange:
                return_values.append(StrangeBot(bot, issues))
        return return_values

    def get_uninstalled_bots(self) -> List[IntelMQBot]:
        return self.__get_bots_by_install(False)

    def get_installed_bots(self) -> List[IntelMQBot]:
        return self.__get_bots_by_install(True)

    def get_issues(self, bot_details: List[IntelMQBot], type_: str) -> Optional[List[BotIssue]]:
        self.logger.debug(
            'Getting differences in configuration of type {} for Tool {}'.format(type_, self.get_class_name())
        )
        differences = list()

        for bot_detail in bot_details:
            if bot_detail.installed:
                general_issues = GeneralIssueDetail()

                # To do this the bot has to be installed
                if bot_detail.default_bots and type_ == 'BOTS':
                    if bot_detail.bots_config:
                        # basically check only if the bot is installed
                        if bot_detail.default_bots:
                            self.compare_configs(
                                general_issues,
                                bot_detail.bots_config,
                                bot_detail.default_bots,
                            )

                    # if the bot is present in file bot not in default BOTS not in BOTS there is an issue

                    general_issues.referenced_bots = bot_detail.default_bots is not None
                    general_issues.referenced_running_bots = bot_detail.bots_config is not None

                    if not general_issues.empty:
                        item = BotIssue()
                        item.bot = bot_detail
                        item.issues.append(general_issues)
                        differences.append(item)

                # for the runtime part it is considered that the BOTS is up to date
                if bot_detail.bots_config and type_ == 'runtime':
                    differences = differences + self.compare_runtime_parameters(bot_detail)

        if len(differences) > 0:
            for item in differences:
                item.bot.has_issues = True
            return differences
        else:
            return None

    def compare_meta(self,
                     general_issues: GeneralIssueDetail,
                     is_config: Union[IntelMQBotConfig, IntelMQBotInstance],
                     should_config: IntelMQBotConfig,
                     ) -> None:
        self.logger.debug('Checking meta information')
        # check name and description
        if is_config.name != should_config.name:
            param_issue = ParameterIssue()
            param_issue.parameter_name = 'name'
            param_issue.should_be = should_config.name
            param_issue.has_value = is_config.name
            general_issues.different_values.append(param_issue)
        if is_config.description != should_config.description:
            param_issue = ParameterIssue()
            param_issue.parameter_name = 'description'
            param_issue.should_be = should_config.description
            param_issue.has_value = is_config.description
            general_issues.different_values.append(param_issue)

    def compare_configs(self,
                        general_issues: GeneralIssueDetail,
                        is_config: IntelMQBotConfig,
                        should_config: IntelMQBotConfig,
                        ) -> None:
        if is_config is None:
            is_config = IntelMQBotConfig()
        self.compare_meta(general_issues, is_config, should_config)
        self.compare_bots_parameters(general_issues, is_config.parameters, should_config.parameters)

    def compare_bots_parameters(self, new_bot_issue: GeneralIssueDetail, is_parameters: dict, should_parameters: dict) -> None:
        self.logger.debug('Checking parameter mismatches')
        for key in should_parameters.keys():
            if key not in is_parameters.keys():
                new_bot_issue.additional_keys.append(key)
        for key in is_parameters.keys():
            if key not in should_parameters.keys():
                new_bot_issue.missing_keys.append(key)
        for key, value in is_parameters.items():
            if key not in new_bot_issue.additional_keys and key not in new_bot_issue.missing_keys:
                if '{}'.format(value) != '{}'.format(should_parameters[key]):
                    issue = ParameterIssue()
                    issue.has_value = value
                    issue.should_be = should_parameters[key]
                    issue.parameter_name = key
                    new_bot_issue.different_values.append(issue)

    def compare_runtime_parameters(self,
                                   bot_detail: IntelMQBot
                                   ) -> List[BotIssue]:
        output = list()
        for instance in bot_detail.instances:
            item = BotIssue()
            item.bot = bot_detail
            item.instance = instance
            general_issues = GeneralIssueDetail()
            self.compare_meta(general_issues, instance, bot_detail.bots_config)

            temp = bot_detail.bots_config.parameters.copy()
            temp.update(bot_detail.default_parameters)
            self.compare_bots_parameters(general_issues, instance.parameters, bot_detail.bots_config.parameters)
            if not general_issues.empty:
                item.issues.append(general_issues)
                output.append(item)
        return output

    def update_bots_file(self, fixed_bots: List[IntelMQBot], mode_: str) -> None:
        # load running bots file
        json_str = '{}'
        with open(self.config.running_bots_file, 'r') as f:
            json_str = f.read()
        running_bots = json.loads(json_str)
        for bot in fixed_bots:

            if mode_ == 'insert':
                running_bots[bot.bot_type][bot.bots_config.name] = bot.bots_config.to_dict(bot.module)
            elif mode_ == 'update':
                keys_to_delete = list()
                for name, values in running_bots[bot.bot_type].items():
                    if values.get('module') == bot.module:
                        keys_to_delete.append(name)

                for key_to_delete in keys_to_delete:
                    del running_bots[bot.bot_type][key_to_delete]

                running_bots[bot.bot_type][bot.bots_config.name] = bot.bots_config.to_dict(bot.module)
            elif mode_ == 'remove':
                if running_bots[bot.bot_type].get(bot.bots_config.name):
                    del running_bots[bot.bot_type][bot.bots_config.name]
            else:
                raise ToolException('Mode {} is not supported'.format(mode_))

        content = pretty_json(running_bots)
        with open(self.config.running_bots_file, "w") as f:
            f.write(content)

    def manipulate_execution_file(self, bot: IntelMQBot, install: bool) -> None:
        file_path = os.path.join(self.config.bin_folder, bot.module)
        if install:
            if os.path.exists(file_path):
                raise ToolException(
                    'Bot {} is not installed but file {} already exists. Please Remove it first'.format(
                        bot.class_name, file_path
                    )
                )
            else:
                create_executable(bot, file_path)
                print('File {} created'.format(file_path))
        else:
            if os.path.exists(file_path):
                print('Removed file {}'.format(file_path))
                os.remove(file_path)
            else:
                print('Will not remove {} as it does not exist'.format(file_path))
