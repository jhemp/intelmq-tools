#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""
Created on 15.01.20
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

import sys

from intelmqtools.exceptions import IntelMQToolException
from intelmqtools.intelmqtool import IntelMQTool
from intelmqtools.tools.checker import Checker
from intelmqtools.tools.installer import Installer
from intelmqtools.tools.lister import Lister
from intelmqtools.tools.updater import Updater


def main() -> None:
    try:
        tools = IntelMQTool()

        # Registering available tools
        tools.register_tool(Lister)
        tools.register_tool(Checker)
        tools.register_tool(Updater)
        tools.register_tool(Installer)

        sys.exit(tools.run())
    except IntelMQToolException as error:
        print('Error: {}'.format(error))
        sys.exit(-1)

if __name__ == '__main__':
    main()
