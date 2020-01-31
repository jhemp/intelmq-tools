#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""
Created on 15.01.20
"""
import argparse
import errno
import sys
from configparser import ConfigParser
import os
import os.path

from scripts.libs.exceptions import SetupException, IntelMQTool, IncorrectArgumentException
from scripts.libs.factory import Factory
from scripts.tools.checker import Checker
from scripts.tools.installer import Installer
from scripts.tools.lister import Lister
from scripts.tools.fixer import Updater

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILE = '{}/config/config.ini'.format(CURRENT_DIR)
VERSION = '0.2'

def check_if_root() -> None:
    try:
        os.rename('/etc/foo', '/etc/bar')
    except IOError as error:
        if error[0] == errno.EPERM:
            raise SetupException('You need root permissions to do this!')


def check_if_configfile() -> None:
    if not os.path.exists(CONFIG_FILE):
        raise SetupException('config file "{0}"does not exist, use the file "{0}_tmpl" as basis'.format(CONFIG_FILE))


def check_get_key(tool_config: ConfigParser, section: str, section_key: str, dev: bool) -> str:
    location = tool_config[section][section_key]
    if location:
        location = get_folder(location, dev)
        if os.path.exists(location):
            return location
        else:
            raise SetupException('The File "{}" for key {} does not exist'.format(location, 'botCodeLocation'))
    else:
        raise SetupException('The configuration files is missing key {} in section {}'.format(section_key, section))

def get_folder(location: str, dev: bool) -> str:
    if dev:
        return os.path.join(tool_config['IntelMQ']['fakeRoot'], check_location)
    return location

def check_bot_folders(location: str, dev) -> None:
    expected_folders = ['collectors', 'experts', 'parsers', 'outputs']
    for expected_folder in expected_folders:
        location_folder = get_folder(location, dev)
        if not (os.path.exists(location)):
            raise SetupException('Folder "{}" does not exist in "{}"'.format(expected_folder, location))


def check_config(config: ConfigParser, dev: bool) -> None:
    config_ok = False
    if len(config.sections()) == 1:
        if 'IntelMQ' in config:
            if dev:
                # Well it's ok :P
                config_ok = True
            elif len(config['IntelMQ']) > 3:
                location = check_get_key(config, 'IntelMQ', 'intelMQLocation', dev)
                bot_code_location = os.path.join(location, 'bots')
                check_bot_folders(bot_code_location, dev)
                check_get_key(config, 'IntelMQ', 'entryPointsLocation', dev)
                check_get_key(config, 'IntelMQ', 'binFolder', dev)
                config_ok = True
    if not config_ok:
        raise SetupException(
            'The config file "{0}" is not setup correctly use the file "{0}_tmpl" as basis'.format(CONFIG_FILE)
        )


def setup(dev: bool) -> ConfigParser:
    # check_if_root()
    check_if_configfile()
    config = ConfigParser()
    config.read(CONFIG_FILE)
    check_config(config, dev)
    return config


tool_factory = Factory()
tool_factory.register_component(Updater)
tool_factory.register_component(Installer)
tool_factory.register_component(Lister)
tool_factory.register_component(Checker)

common = argparse.ArgumentParser(add_help=False)
common.add_argument('--verbose', '-v', action='count', default=0)
common.add_argument('-f', '--full', action='store_true', help='display full', default=False)
common.add_argument('--dev', action='store_true', help='Development', default=False)

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--version', action='version', version='%(prog)s {}'.format(VERSION))
parser.add_argument('-d', '--details', default=None, help='Details of intelmq and this tools', action='store_true')
parser.add_argument('--dev', action='store_true', help='Development', default=False)

subparsers = parser.add_subparsers(help='Available tools', dest='command')

# Update parsers
for component in tool_factory.components:
    arg_parser = component.get_arg_parser()
    subparser = subparsers.add_parser(
        arg_parser.prog,
        parents=[common],
        add_help=False,
        help=arg_parser.description
    )

    # noinspection PyProtectedMember
    subparser._add_container_actions(arg_parser)
    subparser.description = arg_parser.description

args, argv = parser.parse_known_args()
config = setup(args.dev)
key = args.command
if key:
    try:
        # check if there are unknown commands
        if argv:
            # there are unknown commands
            raise IncorrectArgumentException()
        else:

            del args.command
            # check if environment is setup as expected
            tool_factory.run_application(key, args, config)

            sys.exit(0)
    except IncorrectArgumentException:
        sub_parser = None
        for item in getattr(getattr(parser, '_subparsers'), '_actions'):
            if isinstance(item, getattr(argparse, '_SubParsersAction')):
                sub_parser = item
        if sub_parser:
            sub_parser = sub_parser.choices.get(key, None)
            if sub_parser:
                if sub_parser.prog.endswith(key):
                    sub_parser.print_help()
                    sys.exit(-1)
                sys.exit(-2)

        print('No Tools are defined')
        sys.exit(-40)
    except IntelMQTool as error:
        print('Error: {}'.format(error))
        sys.exit(-3)
elif args.details:
    if len(tool_factory.components) > 0:
        value = next(iter(tool_factory.components))
        value.set_config(config)
        intelmq_details = value.get_intelmq_details(args.dev)
        print('IntelMQ Installation Directory: {}'.format(intelmq_details.intelmq_location))
        print('IntelMQ Version:                {}'.format(intelmq_details.version))
        print('Configuration Directory:        {}'.format(intelmq_details.config_dir))
        print('running BOTS File location:     {}'.format(intelmq_details.running_bots_file))
        print('default BOTS File location:     {}'.format(intelmq_details.base_bots_file))
        print('defaults.conf location:         {}'.format(intelmq_details.defaults_conf_file))
        print('runtime.conf location:          {}'.format(intelmq_details.runtime_file))
        print('Custom IntelMQ Bots location    {}'.format(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bots')))
    else:
        print('Error no component defined')
        sys.exit(-20)
else:
    parser.print_help()
    sys.exit(-10)
