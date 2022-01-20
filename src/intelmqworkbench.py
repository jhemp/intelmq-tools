#!/usr/bin/env python

# -*- coding: utf-8 -*-

"""
Created on 27.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

import sys

from intelmqworkbench import IntelMQWorkbench, IntelMQWorkbenchException
from intelmqworkbench.tools.checker import Checker
from intelmqworkbench.tools.converter import Converter
from intelmqworkbench.tools.fiddler import Fiddler
from intelmqworkbench.tools.fixer import Fixer
from intelmqworkbench.tools.botter import Botter
from intelmqworkbench.tools.lister import Lister


def main() -> None:
    try:
        workbench = IntelMQWorkbench()
        workbench.register_tool(Converter)
        workbench.register_tool(Checker)
        workbench.register_tool(Lister)
        workbench.register_tool(Fixer)
        workbench.register_tool(Botter)
        workbench.register_tool(Fiddler)
        sys.exit(workbench.start())
    except IntelMQWorkbenchException as error:
        print('HIGH ERROR: {}'.format(error))
        sys.exit(-1)


if __name__ == '__main__':
    main()
