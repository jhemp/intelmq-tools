# -*- coding: utf-8 -*-

"""
Created on 27.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'


class IntelMQWorkbenchException(Exception):
    pass


class IntelMQWorkbenchValueException(IntelMQWorkbenchException):
    pass


class IntelMQToolFactoryException(IntelMQWorkbenchException):
    pass


class IntelMQWorkbenchConfigException(IntelMQWorkbenchException):
    pass


class IntelMQToolException(IntelMQWorkbenchException):
    pass


class IncorrectArgumentException(IntelMQToolException):
    pass


class IntelMQParsingException(IntelMQWorkbenchException):
    pass


class IntelMQFileNotFound(IntelMQWorkbenchException):
    pass
