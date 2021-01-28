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
from intelmqtools.utils import colorize_text, get_value, set_value, query_yes_no, pretty_json

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
            default_issues = self.get_different_configs(bot_details, 'BOTS')
            if default_issues:
                print(
                    'Found {} issues in BOTS file\n'.format(
                        colorize_text('{}'.format(len(default_issues)), 'Magenta')
                    )
                )
                if default_issues:
                    print(colorize_text('Fixing BOTS File', 'Underlined'))
                    fixed_bots = self.handle_issues(default_issues, args.auto)
                    self.update_bots_file(fixed_bots, 'update')
                    return 0
            else:
                print('There are not issues! Don\'t fix stuff which is not broken!')
                return -10

        elif args.runtime:
            runtime_issues = self.get_different_configs(bot_details, 'runtime')
            print(colorize_text('Fixing runtime.conf File', 'Underlined'))
            fixed_bots = self.handle_runtime_issues(runtime_issues, args.auto)
            if fixed_bots:
                # save runtime.conf
                runtime_cfg = dict()
                with open(self.config.runtime_file, 'r') as f:
                    runtime_cfg = json.loads(f.read())
                for bot_instance in fixed_bots:
                    config = runtime_cfg.get(bot_instance.name)
                    if config:
                        runtime_cfg[bot_instance.name] = bot_instance.config
                with open(self.config.runtime_file, 'w') as f:
                    f.write(pretty_json(runtime_cfg))
                return 0
            else:
                print('There are not issues! Don\'t fix stuff which is not broken!')
                return -10
        elif args.strange:

            strange_bots = self.get_strange_bots(False)
            for strange_bot in strange_bots:

                if not strange_bot.bot.executable_exists and strange_bot.bot.running_config_exists:
                    # create executable
                    do_add = False
                    text = '{} to {}'.format(strange_bot.bot.code_module, self.config.bin_folder)
                    if args.auto:
                        print('Adding executable {}'.format(text))
                        do_add = True
                    else:
                        do_add = query_yes_no('Do you want to add {}'.format(text), default='no')
                    if do_add:
                        self.manipulate_execution_file(strange_bot.bot, True)

                if not strange_bot.bot.default_config_exists:
                    # add default config to BOTS
                    if strange_bot.bot.custom_default_parameters:
                        # there is a config present somewhere
                        strange_bot.bot.default_parameters = strange_bot.bot.custom_default_parameters
                        self.update_bots_file([strange_bot.bot], 'insert')

                    else:
                        do_remove = False
                        # there is no config ask if you want to remove the bot
                        text = '{}'.format(strange_bot.bot.class_name)
                        print('Bot {} has no default configuration and is not registered in intelMQ'.format(text))
                        do_remove = query_yes_no('Do you want to remove BOT {}'.format(text), default='no')
                        if do_remove:
                            self.update_bots_file([strange_bot.bot], 'remove')
                            self.manipulate_execution_file(strange_bot.bot, False)
                            # remove code of the bot
                            directory = os.path.dirname(strange_bot.bot.code_file)
                            shutil.rmtree(directory)
                            print('Removed {}'.format(directory))
                if strange_bot.bot.executable_exists and not strange_bot.bot.installed:
                    # the bot has an executable but is not installed
                    do_remove = False
                    # there is no config ask if you want to remove the bot
                    text = '{}'.format(strange_bot.bot.class_name)
                    print('Bot {} has no default configuration but an executable'.format(text))
                    if args.auto:
                        print('Removing executable for BOT {}'.format(text))
                        do_remove = True
                    else:
                        do_remove = query_yes_no('Do you want to remove executable for BOT {}'.format(text), default='no')
                    if do_remove:
                        self.manipulate_execution_file(strange_bot.bot, False)

        else:
            raise IncorrectArgumentException()

    def get_version(self) -> str:
        return '0.2'

    def handle_runtime_issues(self, issues: List[BotIssue], auto: bool) -> List[Union[IntelMQBotInstance]]:
        result = list()
        if issues:
            for item in issues:
                # Note: the items are instances of bots!
                print('Fixing {}:'.format(colorize_text(item.instance.name, 'LightYellow')))
                setattr(item.issue, 'parameter_name', 'parameters')
                self.__fix_issue(item.instance, item.issue, auto)
                result.append(item.instance)
            return result
        return result

    def handle_issues(self, issues: List[BotIssue], auto: bool) -> List[IntelMQBot]:
        result = list()
        for item in issues:
            print('Fixing {}:'.format(colorize_text(item.bot.class_name, 'LightYellow')))
            self.__fix_issue(item.bot, item.issue, auto)
            result.append(item.bot)
        return result

    def __fix_issue(self,
                    bot: Union[IntelMQBot, IntelMQBotInstance],
                    issue: Union[ParameterIssue, ParameterIssueDetail, GeneralIssueDetail],
                    auto: bool) -> None:
        parameter_name = None
        if hasattr(issue, 'parameter_name'):
            parameter_name = issue.parameter_name
        self.__fix_decider(bot, parameter_name, issue, auto)

    def __fix_decider(self,
                      bot: Union[IntelMQBot, IntelMQBotInstance],
                      parameter_name, issue: Union[ParameterIssue, ParameterIssueDetail, GeneralIssueDetail],
                      auto: bool) -> None:
        if isinstance(issue, GeneralIssueDetail) or isinstance(issue, ParameterIssueDetail):

            if issue.additional_keys:
                for additional_key in issue.additional_keys:
                    text = 'Key {} from Parameter {}'.format(colorize_text(
                        additional_key, 'Yellow'),
                        colorize_text(parameter_name, 'Yellow'))

                    if auto:
                        print('Removing ' + text)
                        do_remove = True
                    else:
                        do_remove = query_yes_no('Do you want to remove ' + text, default='no')

                    if do_remove:
                        if isinstance(bot, IntelMQBot):
                            if parameter_name is None:
                                del bot.default_parameters[additional_key]
                            else:
                                del get_value(parameter_name, bot.default_parameters)[additional_key]
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
                        desired_value = get_value(check_key, bot.bot.default_parameters)

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
                                bot.default_parameters[missing_key] = desired_value
                            else:
                                get_value(parameter_name, bot.default_parameters)[missing_key] = desired_value
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
                    set_value(issue.parameter_name, bot.default_parameters, issue.should_be)
                else:
                    set_value(issue.parameter_name, bot.config, issue.should_be)
