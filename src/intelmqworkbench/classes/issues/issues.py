# -*- coding: utf-8 -*-

"""
Created on 29.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

from enum import Enum
from typing import Optional, Union

from intelmqworkbench.classes.intelmqbot import IntelMQBot
from intelmqworkbench.classes.issues import Issue


class MissingIssue(Issue):

    def __init__(self):
        super(MissingIssue, self).__init__()
        self.key: Optional[str] = None
        self.default_value: Optional[Union[list, bool, str, int, dict]] = None

    @property
    def description(self) -> str:
        return 'Key "{}" with default value "{}" is missing'.format(
            self.key, self.default_value
        )


class MismatchIssue(Issue):

    def __init__(self):
        super(MismatchIssue, self).__init__()
        self.key: Optional[str] = None
        self.has_value: Optional[Union[list, bool, str, int, dict]] = None
        self.should_value: Optional[Union[list, bool, str, int, dict]] = None

    @property
    def description(self) -> str:
        return 'Key "{}" has value "{}" but should be "{}"'.format(
            self.key, self.has_value, self.should_value
        )


class AdditionalIssue(Issue):

    def __init__(self):
        super(AdditionalIssue, self).__init__()
        self.key: Optional[str] = None
        self.value: Optional[Union[list, bool, str, int, dict]] = None

    @property
    def description(self) -> str:
        return 'Key "{}" with default value "{}" is not part of the configuration anymore'.format(
            self.key, self.value
        )


class AbsentIssue(Issue):

    def __init__(self):
        super(AbsentIssue, self).__init__()
        self.key: Optional[str] = None
        self.default_value: Optional[Union[list, bool, str, int, dict]] = None

    @property
    def description(self) -> str:
        return 'Key "{}" is nowhere defined with value "{}"'.format(
            self.key,
            self.default_value
        )


class MissingExecutable(Issue):

    def __init__(self):
        super(MissingExecutable, self).__init__()
        self.path: Optional[str] = None
        self.file_name: Optional[str] = None
        self.bot: Optional[IntelMQBot] = None

    @property
    def description(self) -> str:
        return 'Executable "{}" is missing in "{}" for Bot "{}" ({})'.format(
            self.file_name,
            self.path,
            self.bot.name,
            self.bot.module
        )


class AvailableExecutableIssue(Issue):

    def __init__(self):
        super(AvailableExecutableIssue, self).__init__()
        self.path: Optional[str] = None
        self.file_name: Optional[str] = None

    @property
    def description(self) -> str:
        return 'Executable "{}" is available in "{}" but no Bot for it.'.format(
            self.file_name,
            self.path
        )


class NotInstalledIssue(Issue):

    def __init__(self):
        super(NotInstalledIssue, self).__init__()
        self.bot: Optional[IntelMQBot] = None

    @property
    def description(self) -> str:
        return 'Bot "{}" ({}) is not installed'.format(
            self.bot.class_name,
            self.bot.group
        )


class MissingDefaultConfigurationIssue(Issue):

    def __init__(self):
        super(MissingDefaultConfigurationIssue, self).__init__()
        self.bot: Optional[IntelMQBot] = None

    @property
    def description(self) -> str:
        return 'Bot "{}" ({}) has no default configuration'.format(
            self.bot.class_name,
            self.bot.group
        )


class MissingDescriptionIssue(Issue):

    def __init__(self):
        super(MissingDescriptionIssue, self).__init__()
        self.bot: Optional[IntelMQBot] = None

    @property
    def description(self) -> str:
        return 'Bot "{}" ({}) has no description'.format(
            self.bot.class_name,
            self.bot.group
        )


class InstallIssueLocations(Enum):
    BOTS = 'BOTS'
    RUNTIME = 'runtime.conf'


class ReferenceIssue(Issue):

    def __init__(self):
        super(ReferenceIssue, self).__init__()
        self.name: Optional[str] = None
        self.module: Optional[str] = None
        # runtime.conf, BOTS
        self.location: Optional[InstallIssueLocations] = None
        self.reference: Optional[str] = None

    @property
    def description(self) -> str:
        return 'Bot "{}" ({}) is referenced in {} ({}) but not installed!'.format(
            self.name,
            self.module,
            self.location.value,
            self.reference
        )


class MismatchInstallIssue(Issue):

    def __init__(self):
        super(MismatchInstallIssue, self).__init__()
        self.bot: Optional[IntelMQBot] = None
        self.bot_folder: Optional[str] = None
        self.source: Optional[str] = None
        self.destination: Optional[str] = None

    @property
    def description(self) -> str:
        return 'Bot "{}" ({}) in location does not match setup of custom folder'.format(
            self.bot.name,
            self.bot.module,
            self.bot_folder
        )
