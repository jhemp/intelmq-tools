# -*- coding: utf-8 -*-

"""
Created on 30.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

from typing import Optional, List, Union

from intelmqworkbench.classes.intelmqbot import IntelMQBot
from intelmqworkbench.classes.issues import Issue
from intelmqworkbench.classes.issues.issues import MissingIssue, MismatchIssue, AdditionalIssue


class IntelMQBotsIssue(Issue):

    @property
    def description(self) -> str:
        return 'Issues detected on BOTS'

    def __init__(self):
        super(IntelMQBotsIssue, self).__init__()
        self.bot: Optional[IntelMQBot] = None
        self.issues: List[Union[MissingIssue, MismatchIssue, AdditionalIssue]] = list()
        self.parameter_issues: List[Union[MissingIssue, MismatchIssue, AdditionalIssue]] = list()

    def has_issues(self) -> bool:
        return len(self.issues) > 0 or \
               len(self.parameter_issues) > 0

