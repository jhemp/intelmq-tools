# -*- coding: utf-8 -*-

"""
Created on 15.01.20
"""
import json
import os
import shutil
from argparse import Namespace, ArgumentParser
from typing import Union, List

from intelmqtools.classes.botissue import BotIssue
from intelmqtools.classes.generalissuedetail import ParameterIssueDetail, GeneralIssueDetail
from intelmqtools.classes.intelmqbot import IntelMQBot
from intelmqtools.classes.intelmqbotinstance import IntelMQBotInstance
from intelmqtools.classes.parameterissue import ParameterIssue
from intelmqtools.tools.abstractbasetool import AbstractBaseTool
from intelmqtools.exceptions import IncorrectArgumentException
from intelmqtools.utils import colorize_text, get_value, set_value, query_yes_no, pretty_json, create_executable

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'


class Updater(AbstractBaseTool):

    def get_arg_parser(self) -> ArgumentParser:
        arg_parse = ArgumentParser(prog='fix', description='Tool for fixing bot configurations')
        arg_parse.add_argument('-a', '--auto',
                               default=False,
                               help='Automatic fixing.\nNOTE: Only configuration keys are considered.',
                               action='store_true')
        arg_parse.add_argument('-b', '--bots', default=False,
                               help='Check if the running BOTS configuration and the original configuration.',
                               action='store_true')
        arg_parse.add_argument('-r', '--runtime', default=False,
                               help='Fixes parameters of BOTS configuration matches the runtime one.\n'
                                    'Note: Compares Running BOTS file with running.conf.',
                               action='store_true')
        arg_parse.add_argument('-s', '--strange', default=False,
                               help='Fixes strange BOTS',
                               action='store_true')
        self.set_default_arguments(arg_parse)
        return arg_parse

    def start(self, args: Namespace) -> int:

        if args.auto:
            print('{} Parameter values will not be changed!\n'.format(colorize_text('Note:', 'Red')))

        bot_details = self.get_all_bots()
        if args.bots:
            default_issues = self.get_issues(bot_details, 'BOTS')
            if default_issues:
                print(
                    'Found {} issues in BOTS file\n'.format(
                        colorize_text('{}'.format(len(default_issues)), 'Magenta')
                    )
                )
                print(colorize_text('Fixing BOTS File', 'Underlined'))
                fixed_bots = self.handle_bots_issues(default_issues, args.auto)
                self.update_bots_file(fixed_bots, 'update')
                return 0
            else:
                print('There are not issues! Don\'t fix stuff which is not broken!')
                return -10

        elif args.runtime:
            runtime_issues = self.get_issues(bot_details, 'runtime')
            print(colorize_text('Fixing runtime.conf File', 'Underlined'))
            fixed_bots = self.handle_runtime_issues(runtime_issues, args.auto)
            if fixed_bots:
                # save runtime.conf
                runtime_cfg = dict()
                with open(self.config.runtime_file, 'r') as f:
                    runtime_cfg = json.loads(f.read())
                for bot_instance in fixed_bots:
                    config = runtime_cfg.get(bot_instance.bot_id)
                    if config:
                        runtime_cfg[bot_instance.bot_id] = bot_instance.to_dict(bot_instance.bot.module)
                with open(self.config.runtime_file, 'w') as f:
                    f.write(pretty_json(runtime_cfg))
                return 0
            else:
                print('There are not issues! Don\'t fix stuff which is not broken!')
                return -10
        elif args.strange:

            strange_bots = self.get_strange_bots(False)
            for strange_bot in strange_bots:
                text = '{}'.format(strange_bot.bot.class_name)
                if strange_bot.bot.executable_exists and not strange_bot.bot.has_running_config:
                    print('Bot {} is not referenced in BOTS but has an executable.'.format(text))
                    if len(strange_bot.bot.instances) > 0:
                        # not in bots but in instances then it is a strange one but still ok
                        print('However it is referenced in the running.conf hence this works.')
                    else:
                        if args.auto:
                            print('Removing executable for BOT {}'.format(text))
                            do_remove = True
                        else:
                            do_remove = query_yes_no('Do you want to remove executable for BOT {}'.format(text), default='no')
                        if do_remove:
                            self.manipulate_execution_file(strange_bot.bot, False)

                if not strange_bot.bot.executable_exists and strange_bot.bot.has_running_config:
                    # referenced in bots but has not an executable
                    print('Bot {} has no default configuration but an executable'.format(text))
                    text = '{} to {}'.format(strange_bot.bot.module, self.config.bin_folder)
                    if args.auto:
                        print('Adding executable {}'.format(text))
                        do_add = True
                    else:
                        do_add = query_yes_no('Do you want to add {}'.format(text), default='no')
                    if do_add:
                        self.manipulate_execution_file(strange_bot.bot, True)

        else:
            raise IncorrectArgumentException()

    def get_version(self) -> str:
        return '0.2'

    def handle_runtime_issues(self, issues: List[BotIssue], auto: bool) -> List[Union[IntelMQBotInstance]]:
        result = list()
        if issues:
            for item in issues:
                # Note: the items are instances of bots!
                print('Fixing {}:'.format(colorize_text(item.instance.bot_id, 'LightYellow')))
                self.__handle_issue(item, True, auto)
                result.append(item.instance)
            return result
        return result

    def handle_bots_issues(self, issues: List[BotIssue], auto: bool) -> List[IntelMQBot]:
        result = list()
        for item in issues:
            print('Fixing {}:'.format(colorize_text(item.bot.class_name, 'LightYellow')))
            self.__handle_issue(item, False, auto)
            result.append(item.bot)
        return result

    def __handle_issue(self, bot_issue: BotIssue, is_runtime: bool, auto: bool):
        internal_instance = bot_issue.bot.bots_config
        if is_runtime:
            internal_instance = bot_issue.instance

        for issue in bot_issue.issues:
            if issue.additional_keys:
                # basically add keys with their default value
                for key in issue.additional_keys:
                    default_value = bot_issue.bot.default_bots.parameters.get(key, 'MissingKey')
                    text = 'Parameter {} with value {} is missing from running configuration'.format(
                        colorize_text('parameters.{}'.format(key), 'Yellow'),
                        colorize_text(default_value, 'Blue')
                    )
                    print(text)
                    if auto:
                        do_add = True
                        print('Automatically added.')
                    else:
                        do_add = query_yes_no('Do you want to add this parameter?', default='yes')
                    if do_add:
                        internal_instance.parameters[key] = default_value

            if issue.missing_keys:
                for key in issue.missing_keys:
                    text = 'Parameter {} with value {} is not present in default configuration'.format(
                        colorize_text('parameters.{}'.format(key), 'Yellow'),
                        colorize_text(internal_instance.parameters.get(key, 'MissingKey'), 'Blue')
                    )
                    print(text)
                    if auto:
                        do_remove = True
                        print('Automatically removed.')
                    else:
                        do_remove = query_yes_no('Do you want to remove this parameter?', default='yes')
                    if do_remove:
                        del internal_instance.parameters[key]

            if issue.different_values:
                for different_value in issue.different_values:
                    if different_value.parameter_name in vars(internal_instance).keys():
                        is_parameter = False
                        param_name = different_value.parameter_name
                    else:
                        is_parameter = True
                        param_name = 'parameter.{}'.format(different_value.parameter_name)

                    text = 'Parameter {} has value {} but differs from default {}.'.format(
                        colorize_text(param_name, 'Red'),
                        colorize_text(different_value.has_value, 'Magenta'),
                        colorize_text(different_value.should_be, 'Green')
                    )
                    print(text)
                    if auto:
                        do_change = different_value.parameter_name in ['name', 'description']
                        print('Change will not be applied use Manual Processing instead.')
                    else:
                        do_change = query_yes_no('Do you want to apply default value?', default='no')
                    if do_change:
                        if is_parameter:
                            internal_instance.parameters[different_value.parameter_name] = different_value.should_be
                        else:
                            setattr(internal_instance, different_value.parameter_name, different_value.should_be)
        # check if exe needs fixing
        self.__fix_executable(bot_issue.bot, auto)

    def __fix_executable(self, bot: IntelMQBot, auto: bool) -> None:
        # check if the executable has not been fixed in the meanwhile
        executable_path = os.path.join(self.config.bin_folder, bot.module)
        if not os.path.exists(executable_path):
            if auto:
                create = True
            else:
                create = query_yes_no('Do you want to create executable ' + executable_path, default='yes')
            if create:
                file_path = os.path.join(self.config.bin_folder, bot.module)
                create_executable(bot, file_path)
                print('Recreated {} in {}'.format(bot.executable_name, file_path))
            else:
                self.logger.debug('User decided to not create the executable')
        else:
            self.logger.debug('File {} was created in the meanwhile'.format(executable_path))





















    def __fix_decider(self,
                      bot: Union[IntelMQBot, IntelMQBotInstance],
                      parameter_name, issue: Union[ParameterIssue, ParameterIssueDetail, GeneralIssueDetail],
                      auto: bool) -> None:
        if isinstance(issue, GeneralIssueDetail) or isinstance(issue, ParameterIssueDetail):

            if issue.additional_keys:
                for additional_key in issue.additional_keys:


                    text = 'Key {} from to Parameters {}'.format(colorize_text(
                        additional_key, 'Yellow'),
                        colorize_text(parameter_name, 'Yellow'))

                    if auto:
                        print('Adding ' + text)
                        do_add = True
                    else:
                        do_add = query_yes_no('Do you want to add ' + text, default='no')

                    if do_add:
                        if isinstance(bot, IntelMQBot):
                            if parameter_name is None:
                                bot.bots_config.parameters[additional_key] = bot.default_bots.parameters.get(additional_key)
                                # del bot.bots_config.parameters[additional_key]
                            else:
                                del get_value(parameter_name, bot.bots_config.parameters)[additional_key]
                        else:
                            del bot.config[parameter_name][additional_key]

            if issue.missing_keys:
                # and set their value
                for missing_key in issue.missing_keys:
                    if parameter_name is None:
                        check_key = missing_key
                    else:
                        check_key = '{}.{}'.format(parameter_name, missing_key)
                    if isinstance(bot, IntelMQBot):
                        desired_value = get_value(check_key, bot.custom_default_parameters)
                    else:
                        desired_value = get_value(check_key, bot.bot.default_bots_parameters)

                    text = 'Key {} to Parameter {} with default value {}'.format(colorize_text(
                        missing_key, 'Yellow'),
                        colorize_text(parameter_name, 'Yellow'),
                        colorize_text(desired_value, 'Blue')
                        )

                    if auto:
                        print('Adding ' + text)
                        do_add = True
                    else:
                        do_add = query_yes_no('Do you want to add ' + text, default='no')

                    if do_add:
                        if isinstance(bot, IntelMQBot):
                            if parameter_name is None:
                                bot.default_bots_parameters[missing_key] = desired_value
                            else:
                                get_value(parameter_name, bot.default_bots_parameters)[missing_key] = desired_value
                        else:
                            bot.config[parameter_name][missing_key] = desired_value

            if issue.different_values:
                for different_value in issue.different_values:
                    self.__fix_decider(bot, different_value.parameter_name, different_value, auto)
        if isinstance(issue, ParameterIssue):
            self.__fix_parameter_issue(bot, parameter_name, issue, auto)

    @staticmethod
    def __fix_parameter_issue(
            bot: [IntelMQBot, IntelMQBotInstance],
            parameter_name: str,
            issue: ParameterIssue,
            auto: bool) -> None:
        text = 'Parameter {} with Value: {} was {}.'.format(
            colorize_text(parameter_name, 'Red'),
            colorize_text(issue.should_be, 'Magenta'),
            colorize_text(issue.has_value, 'Gray'))
        if auto:
            print(text + ' Use Manual Processing for changing.')
        else:
            if query_yes_no('Do you want to replace ' + text, default='no'):
                if isinstance(bot, IntelMQBot):
                    field = issue.parameter_name
                    if field in vars(bot.bots_config):
                        setattr(bot.bots_config, issue.parameter_name, issue.should_be)
                    else:
                        bot.bots_config.parameters[issue.parameter_name] = issue.should_be


                else:
                    set_value(issue.parameter_name, bot.config, issue.should_be)


