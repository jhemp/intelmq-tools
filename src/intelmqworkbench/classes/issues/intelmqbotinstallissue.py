# -*- coding: utf-8 -*-

"""
Created on 30.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'


from typing import List, Union

from intelmqworkbench.classes.issues import Issue
from intelmqworkbench.classes.issues.issues import AvailableExecutableIssue, ReferenceIssue, NotInstalledIssue


class IntelMQBotInstallIssue(Issue):

    @property
    def description(self) -> str:
        return 'Issues Detected on Runtime.conf'

    def __init__(self):
        super(IntelMQBotInstallIssue, self).__init__()
        self.issues: List[Union[AvailableExecutableIssue, ReferenceIssue, NotInstalledIssue]] = list()

    def has_issues(self) -> bool:
        return len(self.issues) > 0
