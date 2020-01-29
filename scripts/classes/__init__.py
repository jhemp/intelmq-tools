# -*- coding: utf-8 -*-

"""
Created on 17.01.20
"""
import configparser

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'


class CaseSensitiveConfigParser(configparser.ConfigParser):
    optionxform = staticmethod(str)