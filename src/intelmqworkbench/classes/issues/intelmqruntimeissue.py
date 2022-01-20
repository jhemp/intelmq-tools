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
from intelmqworkbench.classes.issues.issues import MissingIssue, MismatchIssue, AdditionalIssue


class IntelMQRuntimeIssue(Issue):

    @property
    def description(self) -> str:
        return 'Issues Detected on Runtime.conf'

    def __init__(self):
        super(IntelMQRuntimeIssue, self).__init__()
        self.bot_id: Optional[str] = None
        self.bot: Optional[IntelMQBot] = None
        self.issues: List[Union[MissingIssue, MismatchIssue, AdditionalIssue]] = list()
        self.parameter_issues: List[Union[MissingIssue, MismatchIssue, AdditionalIssue]] = list()

