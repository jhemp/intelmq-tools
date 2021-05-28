# -*- coding: utf-8 -*-

"""
Created on 17.01.20
"""
from typing import Union, Optional, List

from intelmqtools.classes.generalissuedetail import ParameterIssueDetail, GeneralIssueDetail
from intelmqtools.classes.intelmqbot import IntelMQBot
from intelmqtools.classes.intelmqbotinstance import IntelMQBotInstance
from intelmqtools.classes.parameterissue import ParameterIssue

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'


class BotIssue:
    def __init__(self):
        self.bot: Optional[IntelMQBot] = None
        self.issues: List[GeneralIssueDetail] = list()
        self.instance: Optional[IntelMQBotInstance] = None
