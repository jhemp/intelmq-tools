# -*- coding: utf-8 -*-

"""
Created on 31.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

from argparse import ArgumentParser, Namespace
from typing import List, Optional, Union

from intelmqworkbench import AbstractBaseTool, IncorrectArgumentException
from intelmqworkbench.classes.intelmqbot import IntelMQBot
from intelmqworkbench.classes.issues.intelmqbotinstallissue import IntelMQBotInstallIssue
from intelmqworkbench.classes.issues.intelmqbotissue import IntelMQBotIssue
from intelmqworkbench.classes.issues.issues import MissingExecutable, MissingDefaultConfigurationIssue, \
    MissingDescriptionIssue


class Lister(AbstractBaseTool):

    def get_version(self) -> str:
        return '0.3'

    def get_arg_parser(self) -> ArgumentParser:
        arg_parse = ArgumentParser(prog='list', description='Lists bots')
        arg_parse.add_argument('-o', '--original', default=False, help='List all original BOTS', action='store_true')
        arg_parse.add_argument('-i', '--installed', default=False, help='List all installed BOTS', action='store_true')
        arg_parse.add_argument('-c', '--customs', default=False, help='List all custom BOTS', action='store_true')
        arg_parse.add_argument('-u', '--uninstalled',
                               default=False, help='List all not installed BOTS', action='store_true')
        arg_parse.add_argument('-a', '--all', default=False, help='List all BOTS', action='store_true')
        arg_parse.add_argument('-s', '--strange', default=False, help='List strange BOTS', action='store_true')
        arg_parse.add_argument('--force', default=False, help='Force', action='store_true')
        return arg_parse

    def start(self, args: Namespace) -> int:
        strange_bots = self.get_strange_bots(args)
        force = args.force
        if args.installed:
            bots = self.get_bots_by_install(True, force)

            return self.output(bots, strange_bots, args.full)
        elif args.customs:
            bots = self.get_bots_by_genre(True, force)

            return self.output(bots, strange_bots, args.full)
        elif args.uninstalled:
            bots = self.get_bots_by_install(False, force)

            return self.output(bots, strange_bots, args.full)
        elif args.all:
            bots = self.get_all_bots(force)

            return self.output(bots, strange_bots, args.full)
        elif args.original:
            bots = self.get_bots_by_genre(False, force)

            return self.output(bots, strange_bots, args.full)
        elif args.strange:
            issues = self.get_issues(force)
            return self.output_strange(strange_bots, issues, args.full)
        else:
            raise IncorrectArgumentException()

    def get_bots_by_install(self, installed: bool,force: bool) -> List[IntelMQBot]:
        output = list()
        bots = self.get_all_bots(force)
        for bot in bots:
            if bot.installed == installed:
                output.append(bot)
        return output

    def get_bots_by_genre(self, custom: bool, force: bool) -> List[IntelMQBot]:
        output = list()
        bots = self.get_all_bots(force)
        for bot in bots:
            if bot.custom == custom:
                output.append(bot)
        return output

    def get_strange_bots(self, args: Namespace) -> Optional[List[IntelMQBot]]:
        issues = self.get_issues(args.force)
        self.logger.info('Searching for strange bots')
        temp = dict()
        if issues:
            for issue in issues:
                if isinstance(issue, IntelMQBotIssue):
                    if issue.issues:
                        for item in issue.issues:
                            if isinstance(item,
                                          (MissingExecutable, MissingDefaultConfigurationIssue, MissingDescriptionIssue)
                                          ):
                                key = issue.bot.module
                                if key not in temp.keys():
                                    temp[key] = issue.bot
        if len(temp.values()) > 0:
            return list(temp.values())
        return None

    def output(self, bots: List[IntelMQBot], strange_bots: Optional[List[IntelMQBot]], full: bool) -> int:
        internal_strange_bots = strange_bots
        if internal_strange_bots is None:
            internal_strange_bots = []
        if len(bots) > 0:
            for bot in bots:
                strange = False
                for strange_bot in internal_strange_bots:
                    if bot.module == strange_bot.module:
                        strange = True
                        break

                self.output_handler.print_bot_detail(bot, full, strange)
                print()
        else:
            print('No bots found')

        return 0

    def output_strange(
            self,
            bots: List[IntelMQBot],
            issues: List[Union[IntelMQBotIssue, IntelMQBotInstallIssue]],
            full: bool
    ) -> int:
        if bots:
            for bot in bots:
                self.output_handler.print_bot_detail(bot, full, True)
                # get issue of bot
                print('Issues Detected:')
                for issue in issues:
                    if isinstance(issue, IntelMQBotIssue):
                        if issue.bot.module == bot.module:
                            for item in issue.issues:
                                if isinstance(item,
                                              (
                                                      MissingExecutable,
                                                      MissingDefaultConfigurationIssue,
                                                      MissingDescriptionIssue
                                              )
                                              ):
                                    self.output_handler.print_issue(item)
                print()
        else:
            print('No Strange Bots detected')
        return 0

    def get_default_argument_description(self) -> Optional[str]:
        return None



