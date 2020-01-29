# -*- coding: utf-8 -*-

"""
Created on 17.01.20
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'


class IntelMQTool(Exception):
    pass


class SetupException(IntelMQTool):
    pass


class ToolException(IntelMQTool):
    pass


class IncorrectArgumentException(ToolException):
    pass