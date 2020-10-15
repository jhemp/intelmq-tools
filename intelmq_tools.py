#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""
Created on 15.01.20
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

import argparse
import sys

from intelmqtools.exceptions import IntelMQToolException
from intelmqtools.intelmqtool import IntelMQTool
from intelmqtools.tools.lister import Lister


def main() -> None:
    try:
        tools = IntelMQTool()

        # Registering available tools
        tools.register_tool(Lister)
        #self.__register_component(Updater)
        # tool_factory.register_component(Installer)
        #self.__register_component(Lister)
        #self.__register_component(Checker)

        sys.exit(tools.run())
    except IntelMQToolException as error:
        print('Error: {}'.format(error))
        sys.exit(-1)

if __name__ == '__main__':
    main()
