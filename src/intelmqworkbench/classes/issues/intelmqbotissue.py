# -*- coding: utf-8 -*-

"""
Created on 29.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

from typing import List, Union, Optional

from intelmqworkbench.classes.intelmqbot import IntelMQBot
from intelmqworkbench.classes.issues import Issue
from intelmqworkbench.classes.issues.intelmqbotsissue import IntelMQBotsIssue
from intelmqworkbench.classes.issues.intelmqruntimeissue import IntelMQRuntimeIssue
from intelmqworkbench.classes.issues.issues import MissingIssue, MismatchIssue, AdditionalIssue, MissingExecutable, \
    MissingDefaultConfigurationIssue, MissingDescriptionIssue, MismatchInstallIssue


class IntelMQBotIssue(Issue):

    @property
    def description(self) -> str:
        raise
        return 'Issues on the bots and their configuration'

    def __init__(self):
        super(IntelMQBotIssue, self).__init__()
        self.issues: List[
            Union[
                MissingIssue,
                MismatchIssue,
                AdditionalIssue,
                MissingExecutable,
                MissingDefaultConfigurationIssue,
                MissingDescriptionIssue,
                MismatchInstallIssue
            ]
        ] = list()
        self.parameter_issues: List[Union[MissingIssue, MismatchIssue, AdditionalIssue]] = list()
        self.bots_issues: Optional[IntelMQBotsIssue] = None
        self.runtime_issues: List[IntelMQRuntimeIssue] = list()
        self.bot: Optional[IntelMQBot] = None

    def has_issues(self) -> bool:
        return len(self.issues) > 0 or \
               len(self.parameter_issues) > 0 or \
               len(self.runtime_issues) > 0 or \
               self.bots_issues is not None

