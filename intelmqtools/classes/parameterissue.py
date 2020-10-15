# -*- coding: utf-8 -*-

"""
Created on 17.01.20
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'


class ParameterIssue:

    def __init__(self):
        self.parameter_name: str = None
        self.should_be: any = None
        self.has_value: any = None

