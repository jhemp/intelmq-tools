# -*- coding: utf-8 -*-

"""
Created on 15.01.20
"""
import json
import sys

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

TYPES = {
    'ENDC': '\033[0m',
    'ResetAll': '\033[0m',
    'Bold': '\033[1m',
    'Dim': '\033[2m',
    'Underlined': '\033[4m',
    'Blink': '\033[5m',
    'Reverse': '\033[7m',
    'Hidden': '\033[8m',

    'ResetBold': '\033[21m',
    'ResetDim': '\033[22m',
    'ResetUnderlined': '\033[24m',
    'ResetBlink': '\033[25m',
    'ResetReverse': '\033[27m',
    'ResetHidden': '\033[28m',

    'Default': '\033[39m',
    'Black': '\033[30m',
    'Red': '\033[31m',
    'Green': '\033[32m',
    'Yellow': '\033[33m',
    'Blue': '\033[34m',
    'Magenta': '\033[35m',
    'Cyan': '\033[36m',
    'LightGray': '\033[37m',
    'DarkGray': '\033[90m',
    'LightRed': '\033[91m',
    'LightGreen': '\033[92m',
    'LightYellow': '\033[93m',
    'LightBlue': '\033[94m',
    'LightMagenta': '\033[95m',
    'LightCyan': '\033[96m',
    'White': '\033[97m',

    'BackgroundDefault': '\033[49m',
    'BackgroundBlack': '\033[40m',
    'BackgroundRed': '\033[41m',
    'BackgroundGreen': '\033[42m',
    'BackgroundYellow': '\033[43m',
    'BackgroundBlue': '\033[44m',
    'BackgroundMagenta': '\033[45m',
    'BackgroundCyan': '\033[46m',
    'BackgroundLightGray': '\033[47m',
    'BackgroundDarkGray': '\033[100m',
    'BackgroundLightRed': '\033[101m',
    'BackgroundLightGreen': '\033[102m',
    'BackgroundLightYellow': '\033[103m',
    'BackgroundLightBlue': '\033[104m',
    'BackgroundLightMagenta': '\033[105m',
    'BackgroundLightCyan': '\033[106m',
    'BackgroundWhite': '\033[107m'
}


def colorize_text(text: str, type_: str)-> str:
    color = TYPES.get(type_)
    output = text
    if color:
        output = '{}{}{}'.format(color, text, TYPES.get('ENDC'))
    return output


def pretty_json(data: dict) -> str:
    return json.dumps(data, indent=4, sort_keys=True)


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    Source: https://stackoverflow.com/questions/3041986/apt-command-line-interface-like-yes-no-inp
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def get_value(key: str, dictionary: dict) -> any:
    result = dictionary
    keys = key.split('.')
    for item in keys[:-1]:
        result = result[item]
    return result.get(keys[-1], None)


def set_value(key: str, dictionary: dict, value: any) -> any:
    result = dictionary
    keys = key.split('.')
    for item in keys[:-1]:
        result = result[item]
    result[keys[-1]] = value