# -*- coding: utf-8 -*-

"""
Created on 17.01.20
"""
from argparse import Namespace, ArgumentParser
from typing import Union

from intelmqtools.classes.generalissuedetail import GeneralIssueDetail, ParameterIssueDetail
from intelmqtools.classes.parameterissue import ParameterIssue
from intelmqtools.tools.abstractbasetool import AbstractBaseTool
from intelmqtools.exceptions import IncorrectArgumentException
from intelmqtools.utils import colorize_text

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'


class Checker(AbstractBaseTool):

    def get_arg_parser(self) -> ArgumentParser:
        arg_parse = ArgumentParser(prog='check', description='Check installation of bots is still applicable')
        arg_parse.add_argument('-b', '--bots', default=False,
                               help='Check if the running BOTS configuration and the original configuration.',
                               action='store_true')
        arg_parse.add_argument('-r', '--runtime', default=False,
                               help='Check if parameters of BOTS configuration matches the runtime one.\n'
                                    'Note: Compares Running BOTS file with running.conf.',
                               action='store_true')
        return arg_parse

    def start(self, args: Namespace) -> None:
        if args.bots:
            self.check_bots(args.full)
        elif args.runtime:
            self.check_runtime(args.full)
        else:
            raise IncorrectArgumentException()

    def get_version(self) -> str:
        return '0.2'

    def __print_issue(self, issues: GeneralIssueDetail,
                      full: bool, count: int = 0,
                      print_lines: bool = True,
                      include_params: bool = True):
        bots = 'BOTS '
        if count > 0:
            bots = 'Running Configuration'
        if print_lines:
            print('----------------------------------------')
        if issues.additional_keys:
            print(
                '    ' * count + '{} has more keys:   {}'.format(
                    bots, colorize_text('{}'.format(issues.additional_keys), 'Red')
                )
            )
        if issues.missing_keys:
            print(
                '    ' * count + '{} is missing keys: {}'.format(
                    bots, colorize_text('{}'.format(issues.missing_keys), 'Magenta')
                )
            )
        if issues.different_values and include_params:
            param = 'Parameter(s)'
            if count > 0:
                param = ' SubParameter(s)'
            print('    ' * count + '{}{} with issues:'.format(bots, param))
            for different_value in issues.different_values:
                self.print_bot_issue(different_value, full, count + 1, include_params)
        if print_lines:
            print('----------------------------------------')
        print()

    def print_bot_issue(self,
                        issue: Union[ParameterIssueDetail, ParameterIssue],
                        full: bool,
                        count: int,
                        include_params: bool
                        ) -> None:
        base = '    ' * count + 'For Parameter: {}'.format(colorize_text(issue.parameter_name, 'Yellow'))
        if isinstance(issue, ParameterIssueDetail):
            print('{} are:'.format(base))
            self.__print_issue(issue, full, count + 1, False, include_params)
        else:
            print(
                '{} has value {} but should be {}'.format(
                    base, colorize_text(issue.has_value, 'Red'), colorize_text(issue.should_be, 'Magenta')
                )
            )

    def check_bots(self, full: bool) -> None:
        bot_details = self.get_installed_bots()
        issues = self.get_different_configs(bot_details, 'BOTS')
        if issues:
            for issue in issues:
                print('BOT Class: {}'.format(colorize_text(issue.bot.class_name, 'LightYellow')))
                self.__print_issue(issue.issue, full, full)
        else:
            print('No issue found')

    def check_runtime(self, full: bool) -> None:
        bot_details = self.get_installed_bots()
        issues = self.get_different_configs(bot_details, 'runtime')
        if issues:
            for issue in issues:
                print('BOT Class:         {}'.format(colorize_text(issue.bot.class_name, 'LightYellow')))
                print('BOT Instance Name: {}'.format(colorize_text(issue.instance.name, 'Yellow')))
                self.__print_issue(issue.issue, full, 1, True,  full)
                pass
        else:
            print('No issue found')
