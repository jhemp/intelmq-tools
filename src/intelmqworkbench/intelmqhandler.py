# -*- coding: utf-8 -*-

"""
Created on 29.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

import inspect
import json
import sys
import re
from importlib import import_module
from logging import Logger
from os import listdir, remove
from os.path import isfile, join, islink
from pathlib import Path
from typing import List, Type, Optional, Union

from intelmq.lib.bot import Bot, ParserBot, CollectorBot, OutputBot, SQLBot
from ruamel import yaml

from intelmqworkbench.classes.bots.bots import BOTS
from intelmqworkbench.classes.bots.botsitem import BOTSItem
from intelmqworkbench.classes.bots.botstype import BOTSType
from intelmqworkbench.classes.intelmqbot import IntelMQBot
from intelmqworkbench.classes.issues.intelmqbotinstallissue import IntelMQBotInstallIssue
from intelmqworkbench.classes.issues.intelmqbotissue import IntelMQBotIssue
from intelmqworkbench.classes.issues.intelmqbotsissue import IntelMQBotsIssue
from intelmqworkbench.classes.issues.intelmqruntimeissue import IntelMQRuntimeIssue
from intelmqworkbench.classes.issues.issues import MismatchIssue, MissingIssue, AdditionalIssue, AbsentIssue, \
    MissingExecutable, ReferenceIssue, AvailableExecutableIssue, InstallIssueLocations, NotInstalledIssue, \
    MissingDefaultConfigurationIssue, MissingDescriptionIssue, MismatchInstallIssue
from intelmqworkbench.classes.parameters import Parameters
from intelmqworkbench.classes.pipeline.pipelineitem import PipelineItem
from intelmqworkbench.classes.pipeline.pipelinie import Pipeline
from intelmqworkbench.classes.runtime.runtime import Runtime
from intelmqworkbench.classes.runtime.runtimeitem import RuntimeItem
from intelmqworkbench.exceptions import IntelMQFileNotFound, IntelMQParsingException
from intelmqworkbench.utils import get_executable_filename, get_paths, is_intelmq_2


class IntelMQHandler:
    try:
        from intelmq.lib.bot import ExpertBot
        BOT_CLASSES = (ParserBot, CollectorBot, ParserBot, OutputBot, ExpertBot, SQLBot, Bot)
    except ImportError:
        BOT_CLASSES = (ParserBot, CollectorBot, ParserBot, OutputBot, SQLBot, Bot)

    BOT_PARAMETERS = dir(Bot)
    IGNORE_KEYS = ['destination_queues', 'search_subject_like', 'username', 'password', 'search_owner']

    def __init__(self, logger: Logger):
        self.logger = logger

    def __get_data_yaml(self, file_path: str) -> dict:
        self.logger.debug('Reading Data of "{}"'.format(file_path))
        if isfile(file_path):
            data = None
            with open(file_path, 'r') as f:
                try:
                    data = yaml.load(f, Loader=yaml.Loader)
                except Exception as error:
                    message = '{}\n{}'.format(error, error.problem_mark)
                    self.logger.debug(message)
                    raise IntelMQParsingException('Error reading file "{}"\n{}'.format(file_path, message))
            if data:
                return data
            else:
                raise IntelMQParsingException('File "{}" does not contain any data'.format(file_path))
        else:
            raise IntelMQFileNotFound('File "{}" cannot be found or is not a file'.format(file_path))

    def __get_data_json(self, file_path: str) -> dict:
        self.logger.debug('Reading Data of "{}"'.format(file_path))
        if isfile(file_path):
            data = None
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                except Exception:
                    raise IntelMQParsingException('Error reading file "{}"'.format(file_path))
            if data:
                return data
            else:
                raise IntelMQParsingException('File "{}" does not contain any data'.format(file_path))
        else:
            raise IntelMQFileNotFound('File "{}" cannot be found or is not a file'.format(file_path))

    def parse_parameters(self, data: dict) -> Parameters:
        self.logger.info('Parsing Parameters')
        parameters = Parameters()
        parameters.add_values(data)
        return parameters

    def parse_bots(self, bots_path: str) -> BOTS:
        self.logger.info('Parsing BOTS - "{}"'.format(bots_path))
        data = self.__get_data_json(bots_path)
        output = BOTS()
        for type_, type_data in data.items():
            bot_type = BOTSType()
            bot_type.type_ = type_
            for name, data in type_data.items():
                bot_item = BOTSItem()
                bot_item.name = name
                bot_item.type_ = type_
                bot_item.description = data.get('description')
                bot_item.module = data.get('module')
                bot_item.parameters = self.parse_parameters(data.get('parameters', dict()))
                bot_type.bots.append(bot_item)
            output.add_type(bot_type)
        return output

    def __create_runtime(self, data: dict) -> Runtime:
        output = Runtime()
        for bot_id, item_data in data.items():
            runtime_item = RuntimeItem()
            runtime_item.bot_id = bot_id
            for key, value in item_data.items():
                if key == 'parameters':
                    runtime_item.parameters = self.parse_parameters(value)
                else:
                    setattr(runtime_item, key, value)
            output.add_item(runtime_item)
        return output

    def parse_runtime_conf(self, runtime_path: str) -> Runtime:
        self.logger.info('Parsing runtime.conf - "{}"'.format(runtime_path))
        data = self.__get_data_json(runtime_path)
        return self.__create_runtime(data)

    def parse_runtime_yaml(self, runtime_path: str) -> Runtime:
        self.logger.info('Parsing runtime.yml - "{}"'.format(runtime_path))
        data = self.__get_data_yaml(runtime_path)
        return self.__create_runtime(data)

    def parse_pipeline(self, pipeline_path: str) -> Pipeline:
        self.logger.info('Parsing pipeline.conf - "{}"'.format(pipeline_path))
        data = self.__get_data_json(pipeline_path)
        output = Pipeline()
        for bot_id, pipeline_data in data.items():
            pipeline_item = PipelineItem()
            pipeline_item.bot_id = bot_id
            for key, value in pipeline_data.items():
                if key == 'source-queue':
                    pipeline_item.source = value
                elif key == 'destination-queues':
                    pipeline_item.destinations = value
            output.add_item(pipeline_item)
        return output

    def __get_default_parameters(self, clazz: Type[Bot], file_path: str) -> Parameters:
        self.logger.info('Getting parameters')
        output = Parameters()
        variables = sorted(key for key in dir(clazz) if not key.isupper() and not key.startswith('_'))
        for key in variables:
            value = getattr(clazz, key)
            if (not inspect.ismethod(value) and not inspect.isfunction(value) and
                    not inspect.isclass(value) and not inspect.isroutine(value) and
                    not (key in IntelMQHandler.BOT_PARAMETERS and getattr(Bot, key) == value)):
                # small check to prevent usage of parent variables
                add = True
                for parent in clazz.__bases__:
                    if hasattr(parent, key):
                        add = False
                        break
                if add:
                    output.add_value(key, value)
                    self.logger.debug('Found parameter {} with value {}'.format(key, value))
        if not output.has_values():
            self.logger.info('Could not find parameters is class looking for config.json')
            # due to the fact that the old model has no default parameters the only method to detect them is if a config
            # file exits in the file path
            file_path = join(Path(file_path).parents[0], 'config.json')
            if isfile(file_path):
                with open(file_path, 'r') as f:
                    try:
                        data = json.load(f)
                        first_key = list(data.keys())[0]
                        parameters = data.get(first_key, {}).get('parameters', {})
                        for key, value in parameters.items():
                            output.add_value(key, value)
                            self.logger.debug('Found parameter {} with value {}'.format(key, value))
                        output.read_config = True
                    except Exception:
                        raise IntelMQParsingException('Error reading file "{}"'.format(file_path))
        # Note: no method found to detect default values of parameters even in text prior to intelmq 3.X

        return output

    def __get_name(self, clazz: Type[Bot]) -> str:
        self.logger.info('Getting name of bot')
        name = clazz.__name__
        for type_ in IntelMQHandler.BOT_CLASSES:
            name = name.replace(type_.__name__, '')
        # try also to replace the detection by the folder structre
        type_ = clazz.__module__.split('.')[-3].title()
        if type_.endswith('s'):
            type_ = type_[:-1]
        return name.replace(type_, '')

    def __get_type(self, clazz: Type[Bot]) -> str:
        self.logger.info('Getting type of bot')
        clazz_parents = inspect.getmro(clazz)
        for type_ in IntelMQHandler.BOT_CLASSES:
            if type_ in clazz_parents:
                if type_ == Bot or type_ == SQLBot:
                    # possible expert but can be everything
                    continue
                return type_.__name__.replace('Bot', '')
        # ok cannot be determine by types then try by folder/module structure
        type_ = clazz.__module__.split('.')[-3].title()
        if type_.endswith('s'):
            return type_[:-1]
        else:
            return type_

    def __get_description(self, clazz: Type[Bot], file_path: str) -> str:
        description = clazz.description
        if description is None:
            description = clazz.__doc__
        if description is None:
            self.logger.info('Could not find description looking in config.json')
            # due to the fact that the old model has no default parameters the only method to detect them is if a config
            # file exits in the file path
            file_path = join(Path(file_path).parents[0], 'config.json')
            if isfile(file_path):
                with open(file_path, 'r') as f:
                    try:
                        data = json.load(f)
                        first_key = list(data.keys())[0]
                        description = data.get(first_key, {}).get('description', None)
                    except Exception:
                        raise IntelMQParsingException('Error reading file "{}"'.format(file_path))
        return description

    def get_bots(self, bot_location: str, custom: bool) -> List[IntelMQBot]:
        output = list()
        self.logger.info('Searching for Bots in {}'.format(bot_location))
        path = Path(bot_location)
        # this should only be done for intelmq native files
        if custom:
            prefix = path
        else:
            prefix = path.parents[1]
        # import the modules so that __subclasses__ will work
        found_classes = list()
        for botfile in path.glob('**/*.py'):
            if botfile.is_file() and botfile.name != '__init__.py':
                file = Path(botfile.as_posix().replace(prefix.as_posix(), '')[1:])
                module_name = '.'.join(file.with_suffix('').parts)
                try:
                    module = import_module(module_name)
                    self.logger.debug('Imported module {}'.format(module_name))
                    # look for classes in module
                    for attr_name, type_ in inspect.getmembers(module):
                        if inspect.isclass(type_) and \
                                type_ not in IntelMQHandler.BOT_CLASSES and \
                                issubclass(type_, IntelMQHandler.BOT_CLASSES) and \
                                type_ not in found_classes:
                            found_classes.append(type_)

                except ImportError as error:
                    self.logger.critical('Cannot import BOT {}'.format(module_name))
                    self.logger.debug(error)
        for clazz in found_classes:
            # Check if the class is a instantiable bot
            if issubclass(clazz, IntelMQHandler.BOT_CLASSES) and \
                    clazz not in IntelMQHandler.BOT_CLASSES:
                # find the Called variable often denoted by 'BOT'
                launch_name = None
                module = sys.modules[clazz.__module__]
                for attr_name, type_ in inspect.getmembers(module):
                    if type_ == clazz and attr_name != clazz.__name__:
                        launch_name = attr_name
                        self.logger.debug('Found launch variable {} in {}'.format(launch_name, clazz.__module__))
                        break
                if launch_name:
                    # this is a bot that can be launched
                    bot = IntelMQBot()
                    bot.bot_variable = launch_name
                    bot.clazz = clazz
                    bot.file_path = module.__file__
                    bot.description = self.__get_description(clazz, bot.file_path)
                    bot.default_parameters = self.__get_default_parameters(clazz, bot.file_path)
                    bot.group = self.__get_type(clazz)
                    bot.name = self.__get_name(clazz)
                    output.append(bot)
                else:
                    self.logger.error('Bot "{}" ({}) may be missing a launch variable'.format(
                        clazz.__name__, module.__name__)
                    )
        return output

    def merge_bots_and_runtime(
            self,
            all_bots: List[IntelMQBot],
            runtime: Runtime,
            bot_location: str,
            set_install_by_path: bool = True
    ) -> None:
        self.logger.info('Merging bots an runtime')
        is_intelmq3 = not is_intelmq_2()
        for bot in all_bots:
            # refix module if intelmq 3
            module = bot.module
            if is_intelmq3 and bot.custom:
                # TODO: verify if this works!
                module = 'intelmq.bots.{}'.format(bot.module)

            runtime_items = runtime.get_runtime_items_for_module(module)
            bot.runtime_items = runtime_items
            if set_install_by_path:
                if bot_location in bot.file_path:
                    bot.installed = True

    def get_issues_for_bots(
            self,
            all_bots: List[IntelMQBot],
            bot_folder: str,
            bin_folder: str,
            runtime_bots: Optional[BOTS] = None
    ) -> List[IntelMQBotIssue]:
        output = list()
        for bot in all_bots:
            issues = self.get_issues_for_bot(bot, bin_folder, bot_folder, runtime_bots)
            if issues:
                output.append(issues)
        return output

    def __check_key(
            self,
            check_item,
            reference_item,
            key: str
    ) -> Optional[Union[MissingIssue, MismatchIssue, AdditionalIssue]]:
        self.logger.info('Checking key "{}"'.format(key))
        issue = None
        if hasattr(check_item, key):
            check_value = getattr(check_item, key)
            if hasattr(reference_item, key):
                reference_value = getattr(reference_item, key)
                if check_value != reference_value:
                    self.logger.debug('Detected mismatch for key "{}"'.format(key))
                    issue = MismatchIssue()
                    issue.has_value = check_value
                    issue.should_value = reference_value
            else:
                self.logger.debug('Detected additional for key "{}"'.format(key))
                issue = AdditionalIssue()
                issue.value = check_value
        else:
            if hasattr(reference_item, key):
                self.logger.debug('Detected missing for key "{}"'.format(key))
                reference_value = getattr(reference_item, key)
                issue = MissingIssue()
                issue.default_value = reference_value
            else:
                self.logger.debug('Detected absent for key "{}"'.format(key))
                issue = AbsentIssue()

        if issue:
            issue.key = key
        return issue

    def __check_bot_runtime(self, bot: IntelMQBot) -> List[IntelMQRuntimeIssue]:
        temp = dict()
        if bot.runtime_items:
            for runtime_item in bot.runtime_items:
                # check general bot fields
                for key in ['description', 'group', 'groupname', 'name']:
                    issue = self.__check_key(runtime_item, bot, key)
                    if issue:
                        item = temp.get(runtime_item.bot_id, None)
                        if item is None:
                            temp[runtime_item.bot_id] = IntelMQRuntimeIssue()
                            temp[runtime_item.bot_id].bot_id = runtime_item.bot_id
                            temp[runtime_item.bot_id].bot = bot
                        temp[runtime_item.bot_id].issues.append(issue)
                parameter_issues = self.__check_bot_parameters(runtime_item.parameters, bot.default_parameters)
                if parameter_issues:
                    item = temp.get(runtime_item.bot_id, None)
                    if item is None:
                        temp[runtime_item.bot_id] = IntelMQRuntimeIssue()
                        temp[runtime_item.bot_id].bot_id = runtime_item.bot_id
                        temp[runtime_item.bot_id].bot = bot
                    temp[runtime_item.bot_id].parameter_issues = parameter_issues

        else:
            # It is not possible to verify as there is no runtime configuration
            pass

        # check if there are bots in runtime which cannot be found!

        return list(temp.values())

    def __check_bot_parameters(
            self,
            check_item: Parameters,
            reference_item: Parameters
    ) -> Optional[List[Union[MissingIssue, MismatchIssue, AdditionalIssue]]]:
        self.logger.info('Checking key Parameters')
        issues = list()
        internal_reference_item = reference_item
        if internal_reference_item is None:
            internal_reference_item = Parameters()
        internal_check_item = check_item
        if internal_check_item is None:
            internal_check_item = Parameters()
        for key in internal_reference_item.get_keys():
            if key in IntelMQHandler.IGNORE_KEYS:
                self.logger.debug('Key "{}" is part of the ignored keys'.format(key))
            else:
                issue = None
                if internal_check_item.has_key(key):
                    check_value = internal_check_item.get_value(key)
                    if internal_reference_item.has_key(key):
                        reference_value = internal_reference_item.get_value(key)
                        if check_value != reference_value:
                            self.logger.debug('Detected mismatch for key "{}"'.format(key))
                            if (reference_value is None or reference_value == '' or
                                (isinstance(reference_value, str) and reference_value.startswith('<')) or
                                (isinstance(reference_value, list) and len(reference_value) == 0) or
                                (isinstance(reference_value, dict) and len(reference_value) == 0)
                            ) and check_value:
                                # basically the initial value is not set and the parameter has been set
                                self.logger.info('Possibly value for key "{}" '
                                                 'has been set manually. This will not be considered as error'.format(key))
                            else:
                                issue = MismatchIssue()
                                issue.has_value = check_value
                                issue.should_value = reference_value
                    else:
                        self.logger.debug('Detected additional for key "{}"'.format(key))
                        issue = AdditionalIssue()
                        issue.value = check_value
                else:
                    self.logger.debug('Detected missing for key "{}"'.format(key))
                    reference_value = internal_reference_item.get_value(key)
                    issue = MissingIssue()
                    issue.default_value = reference_value

                if issue:
                    issue.key = key
                    issues.append(issue)
        # Do the same just the other way round as the check may have also keys which are not present in the reference
        for key in internal_check_item.get_keys():
            if key in IntelMQHandler.IGNORE_KEYS:
                self.logger.debug('Key "{}" is part of the ignored keys'.format(key))
            else:
                if internal_reference_item.has_key(key):
                    # this have been checked above
                    pass
                else:
                    self.logger.debug('Detected additional for key "{}"'.format(key))
                    reference_value = internal_check_item.get_value(key)
                    issue = AbsentIssue()
                    issue.default_value = reference_value
                    issue.key = key
                    issues.append(issue)

        if len(issues) > 0:
            return issues
        else:
            return None

    def __check_executable_by_bot(
            self, bot: IntelMQBot, bot_folder: str, bin_folder: str
    ) -> Optional[MissingExecutable]:
        self.logger.debug('Checking if executable exits')
        executable_name = get_executable_filename(bot, bot_folder)
        if isfile(join(bin_folder, executable_name)):
            return None
        else:
            issue = MissingExecutable()
            issue.file_name = executable_name
            issue.path = bin_folder
            issue.bot = bot
            return issue

    def get_issues_for_bot(
            self,
            bot: IntelMQBot,
            bot_folder: str,
            bin_folder: str,
            runtime_bots: Optional[BOTS] = None
    ) -> Optional[IntelMQBotIssue]:
        output = IntelMQBotIssue()
        output.bot = bot
        # verify bot
        issues = self.__check_bot_runtime(bot)
        if issues:
            output.runtime_issues = issues
        issues = self.__check_bots(bot, runtime_bots)
        if issues:
            output.bots_issues = issues
        # Check if bot is installed else add an Issue
        if bot.installed:
            # Bot found but is installed check if the executable exits
            issue = self.__check_executable_by_bot(bot, bot_folder, bin_folder)
            if issue:
                output.issues.append(issue)
        # Check if there is not a strange issue e.g. missing default configuration
        if bot.default_parameters is None:
            issue = MissingDefaultConfigurationIssue()
            issue.bot = bot
            output.issues.append(issue)

        if bot.description is None:
            issue = MissingDescriptionIssue()
            issue.bot = bot
            output.issues.append(issue)

        # Issues related to the installation in intelMQ 3.x only for custom bots
        if bot.custom:
            issue = self.__check_custom_install(bot, bot_folder)
            if issue:
                output.issues.append(issue)

        if output.has_issues():
            return output
        else:
            return None

    def __check_custom_install(self, bot: IntelMQBot, bot_folder: str) -> Optional[MismatchInstallIssue]:
        if is_intelmq_2():
            return None
        else:
            self.logger.info('Checking if installation is the same')
            source, destination = get_paths(bot, bot_folder)
            # check if the files are present in the
            files = listdir(source)
            for f in files:
                file_name = join(destination, f)
                self.logger.debug('Checking if {} is a symlink'.format(file_name))
                if not islink(file_name):
                    issue = MismatchInstallIssue()
                    issue.bot = bot
                    issue.bot_folder = bot_folder
                    issue.source = source
                    issue.destination = destination
                    return issue
            return None

    def merge_bots_conf_and_bots(self, intelmq_bots: List[IntelMQBot], bots: BOTS) -> None:
        self.logger.debug('Mergin BOTS with bot')
        # the BOTS file handles all the parameters etc hence if neither config.json was read or BOTS then the
        # values set by them should not be set!
        for bot in intelmq_bots:
            bot_item = bots.get_bot_item_by_bot(bot)
            if bot_item:
                bot.description = bot_item.description
                bot.default_parameters = bot_item.parameters
            else:
                if not bot.default_parameters.read_config:
                    bot.description = None
                    bot.default_parameters = None

    def __check_bots(self, bot: IntelMQBot, runtime_bots: Optional[BOTS] = None) -> Optional[IntelMQBotsIssue]:
        if runtime_bots:
            output = IntelMQBotsIssue()
            output.bot = bot
            bots_item = runtime_bots.get_bot_item_by_bot(bot)
            if bots_item:
                issue = self.__check_key(bots_item, bot, 'description')
                if issue:
                    output.issues.append(issue)
                issues = self.__check_bot_parameters(bots_item.parameters, bot.default_parameters)
                if issues:
                    output.parameter_issues = issues

            if output.has_issues():
                return output
            else:
                return None
        else:
            return None

    def get_install_issues(self, bots: List[IntelMQBot], runtime: Runtime, bin_folder: str, bot_folder: str,
                           bots_conf: Optional[BOTS]) -> Optional[IntelMQBotInstallIssue]:
        self.logger.debug('Checking reference issues')
        # check Runtime
        output = IntelMQBotInstallIssue()
        for item in runtime.get_items():
            found = False
            for bot in bots:
                # if the module is existing so is the bot
                if item.module == bot.module:
                    found = True
                    break
            if not found:
                # there is an issue
                issue = ReferenceIssue()
                issue.module = item.module
                issue.name = item.name
                issue.reference = item.bot_id
                issue.location = InstallIssueLocations.RUNTIME
                output.issues.append(issue)
        if bots_conf:
            for item in bots_conf.get_items():
                found = False
                for bot in bots:
                    # if the module is existing so is the bot
                    if item.module == bot.module:
                        found = True
                        break
                if not found:
                    # there is an issue
                    issue = ReferenceIssue()
                    issue.module = item.module
                    issue.name = item.name
                    issue.reference = item.type_
                    issue.location = InstallIssueLocations.BOTS
                    output.issues.append(issue)
        # check bin folder
        for file in listdir(bin_folder):
            if re.match(r'.+\..+\..+\..+$', file):
                found = False
                for bot in bots:
                    # if the module is existing so is the bot
                    executable_filename = get_executable_filename(bot, bot_folder)
                    if file == executable_filename:
                        found = True
                        break
                if not found:
                    issue = AvailableExecutableIssue()
                    issue.path = bin_folder
                    issue.file_name = file
                    output.issues.append(issue)
        for bot in bots:
            if not bot.installed:
                issue = NotInstalledIssue()
                issue.bot = bot
                output.issues.append(issue)

        if output.has_issues():
            return output
        else:
            return None

    def get_issues(
            self,
            bots: List[IntelMQBot],
            bot_folder: str,
            bin_folder: str,
            runtime: Runtime,
            runtime_bots: Optional[BOTS],
    ) -> Optional[List[Union[IntelMQBotIssue, IntelMQBotInstallIssue]]]:
        output: List[Union[IntelMQBotIssue, IntelMQBotInstallIssue]] = list()
        issues = self.get_issues_for_bots(bots, bin_folder, bot_folder, runtime_bots)
        if issues:
            output = output + issues
        install_issues = self.get_install_issues(bots, runtime, bin_folder, bot_folder, runtime_bots)
        if install_issues:
            output.append(install_issues)
        if len(output) > 0:
            return output
        else:
            return None

    def remove_runtime_item_by_bot_id(
            self, bot_id: str, runtime: Runtime, pipeline: Optional[Pipeline], bin_folder: str
    ) -> bool:
        self.logger.debug('Removing Runtime Item "{}"'.format(bot_id))
        do_remove = True
        if pipeline:
            if pipeline.is_bot_id_contained(bot_id):
                do_remove = False
        if do_remove:
            runtime_item = runtime.get_item_by_id(bot_id)
            runtime.remove_by_bot_id(bot_id)
            # remove also executable
            path = join(bin_folder, runtime_item.module)
            if isfile(path):
                self.logger.debug('Executable "{}" exists'.format(path))
                remove(path)
            return True
        else:
            self.logger.error('Bot with ID "{}" cannot be deleted as it is still referenced in a pipe.'.format(bot_id))
            return False

    def remove_bots_item(
            self,
            type_: str,
            module: str,
            name: str,
            bots: BOTS,
            runtime: Runtime,
            bin_folder: str
    ) -> bool:
        if bots:
            self.logger.debug('Removing BOTS Item "{}" ({})'.format(name, module))
            do_remove = True
            runtime_items = runtime.get_runtime_items_for_module(module)
            if len(runtime_items) > 0:
                # basically the bot is referenced an cannot be removed
                do_remove = False

            if do_remove:
                bots.remove_element(type_, module, name)
                # remove also executable
                path = join(bin_folder, module)
                if isfile(path):
                    self.logger.debug('Executable "{}" exists'.format(path))
                    remove(path)
                return True
            else:
                self.logger.error(
                    'BOTS Item "{}" ({}) cannot be deleted as it is still referenced in a pipe.'.format(name, module)
                )
                return False
        else:
            self.logger.error('No BOTS provided')
            return False

    def set_install_by_bots(self, bots: List[IntelMQBot], running_bots: BOTS):
        self.logger.debug('Setting install flag via running BOTS')
        for bot in bots:
            bots_item = running_bots.get_bot_item_by_bot(bot)
            if bots_item:
                bot.installed = True


