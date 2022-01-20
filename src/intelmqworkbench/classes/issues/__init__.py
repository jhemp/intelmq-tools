# -*- coding: utf-8 -*-

"""
Created on 29.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

from abc import ABC, abstractmethod


class Issue(ABC):

    def __init__(self):
        self.parent = None

    @property
    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError()
