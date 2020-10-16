# -*- coding: utf-8 -*-

"""
Created on 17.01.20
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'


class IntelMQToolException(Exception):
    pass


class IntelMQToolConfigException(IntelMQToolException):
    pass


class SetupException(IntelMQToolException):
    pass


class ToolException(IntelMQToolException):
    pass


class BotFileNotFoundException(ToolException):
    pass


class MissingConfigurationException(ToolException):
    pass


class BotAlreadyInstalledException(ToolException):
    pass


class BotNotInstalledException(ToolException):
    pass


class ConfigNotFoundException(ToolException):
    pass


class IncorrectArgumentException(ToolException):
    pass
