# -*- coding: utf-8 -*-

"""
Created on 29.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'
from argparse import ArgumentParser, Namespace
from typing import Optional

from intelmqworkbench import AbstractBaseTool, IncorrectArgumentException
from intelmqworkbench.classes.issues.intelmqbotinstallissue import IntelMQBotInstallIssue
from intelmqworkbench.classes.issues.intelmqbotissue import IntelMQBotIssue
from intelmqworkbench.classes.issues.issues import InstallIssueLocations, ReferenceIssue, AvailableExecutableIssue, \
    MissingExecutable, NotInstalledIssue, MismatchInstallIssue, MissingDescriptionIssue, \
    MissingDefaultConfigurationIssue
from intelmqworkbench.exceptions import IntelMQToolException


class Checker(AbstractBaseTool):

    def get_version(self) -> str:
        return '0.3'

    def get_arg_parser(self) -> ArgumentParser:
        arg_parse = ArgumentParser(prog='check', description='Check installation of bots is still applicable')
        arg_parse.add_argument('-b', '--bots', default=False,
                               help='Check if the running BOTS configuration and the original configuration.',
                               action='store_true')
        arg_parse.add_argument('-r', '--runtime', default=False,
                               help='Check if parameters of BOTS configuration matches the runtime one.\n'
                                    'Note: Compares Running BOTS file with running.conf.',
                               action='store_true')
        arg_parse.add_argument('-s', '--strange', default=False,
                               help='Check if there are strange BOTS or configurations',
                               action='store_true')
        arg_parse.add_argument('--force', default=False, help='Force', action='store_true')
        self.set_default_arguments(arg_parse)
        return arg_parse

    def start(self, args: Namespace) -> int:
        if args.bots:
            return self.check_bots(args.force)
        elif args.runtime:
            return self.check_runtime(args.force)
        elif args.strange:
            return self.check_strange(args.force)
        else:
            raise IncorrectArgumentException()

    def get_default_argument_description(self) -> Optional[str]:
        return None

    def check_bots(self, force: bool) -> int:
        # check BOTS File which do not match their config e.g. parameters and are referenced in BOTS but do not have BOT
        if self.config.version.startswith('3') and not force:
            print('BOTS cannot be checked as IntelMQ Version > 3.0.0 or use --force.')
        else:
            issues = self.get_issues(force)
            if issues:
                general_issues = list()
                for issue in issues:
                    output_issues = list()
                    # print('BOT "{}" has issues:'.format(issue.bot.name))
                    if isinstance(issue, IntelMQBotInstallIssue):
                        for item in issue.issues:
                            if isinstance(item, ReferenceIssue):
                                if item.location == InstallIssueLocations.BOTS:
                                    output_issues.append(item)
                    elif isinstance(issue, IntelMQBotIssue):
                        if issue.bots_issues:
                            for item in issue.bots_issues.issues:
                                output_issues.append(item)
                        if issue.parameter_issues:
                            for item in issue.parameter_issues:
                                output_issues.append(item)
                    if len(output_issues) > 0:
                        if isinstance(issue, IntelMQBotInstallIssue):
                            general_issues += output_issues
                        else:
                            self.output_handler.print_bot_detail(issue.bot, False)
                            for item in output_issues:
                                self.output_handler.print_issue(item)
                if len(general_issues) > 0:
                    print('\nOther Issues were Detected')
                    for item in general_issues:
                        self.output_handler.print_issue(item)
        return 0

    def check_runtime(self, force: bool) -> int:
        # Bots which do not match their config e.g. parameters and references in runtime.conf which have no BOT
        issues = self.get_issues(force)
        if issues:
            general_issues = list()
            for issue in issues:
                output_issues = list()
                # print('BOT "{}" has issues:'.format(issue.bot.name))
                if isinstance(issue, IntelMQBotInstallIssue):
                    for item in issue.issues:
                        if isinstance(item, ReferenceIssue):
                            if item.location == InstallIssueLocations.RUNTIME:
                                output_issues.append(item)
                elif isinstance(issue, IntelMQBotIssue):
                    if issue.runtime_issues:
                        for item in issue.runtime_issues:
                            for sub_item in item.issues:
                                output_issues.append(sub_item)
                            for sub_item in item.parameter_issues:
                                output_issues.append(sub_item)
                if len(output_issues) > 0:
                    if isinstance(issue, IntelMQBotInstallIssue):
                        general_issues += output_issues
                    else:
                        self.output_handler.print_bot_detail(issue.bot, False)
                        for item in output_issues:
                            self.output_handler.print_issue(item)
            if len(general_issues) > 0:
                print('\nOther Issues were Detected')
                for item in general_issues:
                    self.output_handler.print_issue(item)
        return 0

    def check_strange(self, force: bool) -> int:
        # Bots either not installed or fragments left e.g. executable references in runtime.conf or BOTS
        issues = self.get_issues(force)
        if issues:
            general_issues = list()
            for issue in issues:
                output_issues = list()
                # print('BOT "{}" has issues:'.format(issue.bot.name))
                if isinstance(issue, IntelMQBotInstallIssue):
                    for item in issue.issues:
                        if isinstance(item, AvailableExecutableIssue):
                            output_issues.append(item)
                        elif isinstance(item, NotInstalledIssue):
                            output_issues.append(item)
                        elif isinstance(item, ReferenceIssue):
                            output_issues.append(item)
                elif isinstance(issue, IntelMQBotIssue):
                    if issue.issues:
                        for item in issue.issues:
                            if isinstance(item, MissingExecutable):
                                output_issues.append(item)
                            elif isinstance(item, MismatchInstallIssue):
                                output_issues.append(item)
                            elif isinstance(item, MissingDescriptionIssue):
                                output_issues.append(item)
                            elif isinstance(item, AvailableExecutableIssue):
                                output_issues.append(item)
                            elif isinstance(item, MissingDefaultConfigurationIssue):
                                output_issues.append(item)
                            else:
                                raise IntelMQToolException('Unknown Issue')
                if len(output_issues) > 0:
                    if isinstance(issue, IntelMQBotInstallIssue):
                        general_issues += output_issues
                    else:
                        if issue.bot.installed:
                            self.output_handler.print_bot_detail(issue.bot, False)
                            print('Issues Detected:')
                            for item in output_issues:
                                self.output_handler.print_issue(item)
                            print()
            if len(general_issues) > 0:
                print('\nOther Issues were Detected')
                for item in general_issues:
                    self.output_handler.print_issue(item)
        return 0

