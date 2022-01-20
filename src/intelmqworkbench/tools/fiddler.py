# -*- coding: utf-8 -*-

"""
Created on 03.01.22
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'


from logging import Logger

from intelmqworkbench.exceptions import IntelMQToolException
from intelmqworkbench.fiddlehandler import FiddleHandler
from intelmqworkbench import AbstractBaseTool, IncorrectArgumentException, IntelMQWorkbenchConfig
from argparse import ArgumentParser, Namespace
from typing import Optional


class Fiddler(AbstractBaseTool):

    def __init__(self, logger: Logger, config: IntelMQWorkbenchConfig):
        super().__init__(logger, config)
        self.fiddle_handler = FiddleHandler(logger)

    def get_default_argument_description(self) -> Optional[str]:
        return None

    def get_version(self) -> str:
        return '0.2'

    def get_arg_parser(self) -> ArgumentParser:
        arg_parse = ArgumentParser(prog='fiddler', description='Tool for developing/debugging bots')
        arg_parse.add_argument('-i', '--bot_id', default=None,
                               help='bot_id of the bot to be executed',
                               type=str)
        arg_parse.add_argument('--fixes', default=False, help='Show Fixed Configuration', action='store_true')
        return arg_parse

    def start(self, args: Namespace) -> int:
        if self.config.output_folder:
            self.fiddle_handler.init(self.get_all_bots(False), self.config)
            if args.fixes:
                return self.fiddle_handler.print_configuration()
            elif args.bot_id:
                bot_name = args.bot_id
                self.fiddle_handler.launch_bot(bot_name)
            else:
                raise IncorrectArgumentException()
        else:
            raise IntelMQToolException(
                'Not output Folder Specified use with parameter --output_folder or specify it in config.'
            )

