# -*- coding: utf-8 -*-

"""
Created on 17.01.20
"""
from typing import List, Union

from intelmqtools.classes.parameterissue import ParameterIssue

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'


class GeneralIssueDetail:

    def __init__(self):
        self.additional_keys: List[str] = list()
        self.missing_keys: List[str] = list()
        self.different_values: List[Union[ParameterIssueDetail, ParameterIssue]] = list()
        self.referenced_bots: bool = True
        self.referenced_running_bots: bool = True

    @property
    def empty(self):
        return len(self.different_values) == 0 and len(self.missing_keys) == 0 and len(self.additional_keys) == 0 and self.referenced_bots and self.referenced_running_bots

    @property
    def bots_issues(self) -> List[str]:
        output = list()
        if self.referenced_bots is False:
            output.append('Bot is not referenced in default BOTS file')
        if self.referenced_running_bots is False:
            output.append('Bot is not referenced in running BOTS file')
        return output


class ParameterIssueDetail(GeneralIssueDetail):

    def __init__(self):
        self.parameter_name: str = None
