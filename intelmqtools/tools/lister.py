# -*- coding: utf-8 -*-

"""
Created on 17.01.20
"""
from argparse import Namespace, ArgumentParser
from typing import List

from intelmqtools.classes.intelmqbot import IntelMQBot
from intelmqtools.tools.abstractbasetool import AbstractBaseTool
from intelmqtools.exceptions import IncorrectArgumentException

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
        arg_parse.add_argument('-u', '--uninstalled', default=False, help='List all not installed BOTS', action='store_true')
        arg_parse.add_argument('-l', '--list', default=False, help='List all BOTS', action='store_true')
        return arg_parse

    def start(self, args: Namespace) -> None:
        if args.installed:
            bot_details = self.get_installed_bots()
            self.output(bot_details, args.full)
        elif args.customs:
            bot_details = self.get_custom_bots()
            self.output(bot_details, args.full)
        elif args.uninstalled:
            bot_details = self.get_uninstalled_bots()
            self.output(bot_details, args.full)
        elif args.list:
            bot_details = self.get_all_bots()
            self.output(bot_details, args.full)
        elif args.original:
            bot_details = self.get_original_bots()
            self.output(bot_details, args.full)
        else:
            raise IncorrectArgumentException()

    def get_version(self) -> str:
        return '0.0.1'

    def output(self, bot_details: List[IntelMQBot], full: bool) -> None:
        if bot_details:
            self.print_bot_details(bot_details, full)
        else:
            print('No bots found.')
