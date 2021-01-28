# -*- coding: utf-8 -*-

"""
Created on 17.01.20
"""
from argparse import Namespace, ArgumentParser
from typing import List

from intelmqtools.classes.intelmqbot import IntelMQBot
from intelmqtools.classes.strangebot import StrangeBot
from intelmqtools.tools.abstractbasetool import AbstractBaseTool
from intelmqtools.exceptions import IncorrectArgumentException
from intelmqtools.utils import colorize_text

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'


class Lister(AbstractBaseTool):

    def get_arg_parser(self) -> ArgumentParser:
        arg_parse = ArgumentParser(prog='list', description='Lists bots')
        arg_parse.add_argument('-o', '--original', default=False, help='List all original BOTS', action='store_true')
        arg_parse.add_argument('-i', '--installed', default=False, help='List all installed BOTS', action='store_true')
        arg_parse.add_argument('-c', '--customs', default=False, help='List all custom BOTS', action='store_true')
        arg_parse.add_argument('-u', '--uninstalled',
                               default=False, help='List all not installed BOTS', action='store_true')
        arg_parse.add_argument('-a', '--all', default=False, help='List all BOTS', action='store_true')
        arg_parse.add_argument('-s', '--strange', default=False, help='List strange BOTS', action='store_true')
        return arg_parse

    def start(self, args: Namespace) -> int:
        if args.installed:
            bot_details = self.get_installed_bots()
            return self.output(bot_details, args.full)
        elif args.customs:
            bot_details = self.get_custom_bots()
            return self.output(bot_details, args.full)
        elif args.uninstalled:
            bot_details = self.get_uninstalled_bots()
            return self.output(bot_details, args.full)
        elif args.all:
            bot_details = self.get_all_bots()
            return self.output(bot_details, args.full)
        elif args.original:
            bot_details = self.get_original_bots()
            return self.output(bot_details, args.full)
        elif args.strange:
            strange_bots = self.get_strange_bots(False)
            return self.output_strange(strange_bots, args.full)
        else:
            raise IncorrectArgumentException()

    def get_version(self) -> str:
        return '0.2'

    def output_strange(self, strange_bots: List[StrangeBot], full: bool) -> int:
        for item in strange_bots:
            bot_detail = item.bot
            self.print_bot_meta(bot_detail)
            self.print_bot_strange(bot_detail)
            self.print_bot_full(bot_detail, full)
            print()
        return 0

    def output(self, bot_details: List[IntelMQBot], full: bool) -> int:
        if bot_details:
            self.print_bot_details(bot_details, full)
            return 0
        else:
            print('No bots found.')
            return -10
