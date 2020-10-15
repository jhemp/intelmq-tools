# -*- coding: utf-8 -*-

"""
Created on 17.01.20
"""
from typing import Union

from scripts.classes.generalissuedetail import ParameterIssueDetail, GeneralIssueDetail
from scripts.classes.intelmqbot import IntelMQBot
from scripts.classes.intelmqbotinstance import IntelMQBotInstance
from scripts.classes.parameterissue import ParameterIssue

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'


class BotIssue:
    def __init__(self):
        self.bot: IntelMQBot = None
        self.issue: Union[ParameterIssueDetail, ParameterIssue, GeneralIssueDetail] = None
        self.instance: IntelMQBotInstance = None
