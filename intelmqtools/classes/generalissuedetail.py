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

    @property
    def empty(self):
        return self.different_values is None and self.missing_keys is None and self.additional_keys is None


class ParameterIssueDetail(GeneralIssueDetail):

    def __init__(self):
        self.parameter_name: str = None
