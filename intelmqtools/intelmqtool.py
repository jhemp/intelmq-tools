# -*- coding: utf-8 -*-

"""
Created on 15.10.20
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

import argparse
import os
from argparse import Namespace
from configparser import ConfigParser
from typing import Dict, Type, Optional

from intelmqtools.classes.intelmqtoolconfig import IntelMQToolConfig
from intelmqtools.exceptions import SetupException, IntelMQToolException, IntelMQToolConfigException, \
    IncorrectArgumentException
from intelmqtools.tools.abstractbasetool import AbstractBaseTool
from intelmqtools.utils import colorize_text


class IntelMQTool:

    VERSION = '0.3'

    def __init__(self):

        self.__tools: Dict[str, AbstractBaseTool] = dict()
        self.config = None

    def register_tool(self, clazz: Type[AbstractBaseTool]) -> None:
        instance = clazz()
        if not isinstance(instance, AbstractBaseTool):
            raise IntelMQToolException(
                'Tool {} does not not implement the AbstractBaseTool class'.format(clazz.__name__)
            )
        self.__tools[instance.get_arg_parser().prog] = instance

    def __setup_argument_parser(self) -> None:
        common = argparse.ArgumentParser(add_help=False)
        common.add_argument('-f', '--full', action='store_true', help='display full', default=False)

        self.parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        self.parser.add_argument('--version',
                                 action='version',
                                 version='%(prog)s {}'.format(IntelMQTool.VERSION))
        self.parser.add_argument('-d', '--details',
                                 default=None,
                                 help='Details of intelmq and this tools',
                                 action='store_true')
        self.parser.add_argument('--bin',
                                 type=str,
                                 help='Location of the bin folder.\n'
                                      'Default is /usr/bin',
                                 default='/usr/bin')
        self.parser.add_argument('--bot',
                                 type=str,
                                 help='Location of the custom bots.\n'
                                      'Note: The bots have to be in the path of python.',
                                 default=None)
        self.parser.add_argument('--fake',
                                 type=str,
                                 help='Location of the root used for development.\n'
                                      'Note: If this set the tool is automatically in dev mode.',
                                 default=None)
        self.parser.add_argument('--config',
                                 type=str,
                                 help='Configuration file\n'
                                      'Note: The default location is ./config/config.ini',
                                 default=None)
        self.parser.add_argument('--verbose', '-v', action='count', default=0)

        sub_parsers = self.parser.add_subparsers(help='Available tools', dest='command')

        # Update parsers
        for tool in self.__tools.values():
            arg_parser = tool.get_arg_parser()
            sub_parser = sub_parsers.add_parser(
                arg_parser.prog,
                parents=[common],
                add_help=False,
                help=arg_parser.description
            )

            # noinspection PyProtectedMember
            sub_parser._add_container_actions(arg_parser)
            sub_parser.description = arg_parser.description

    def run_tool(self, key: str, args: Namespace) -> int:
        instance = self.__tools.get(key, None)
        if instance is None:
            raise IntelMQToolException('Program {} cannot be found'.format(key))
        else:
            instance.set_config(self.config)
            return instance.start(args)

    @staticmethod
    def __check_get_folder(tool_config: ConfigParser, section: str, section_key: str) -> Optional[str]:
        location = tool_config[section][section_key]
        if location:
            return location
        else:
            if 'fake' in section_key:
                return None
            raise SetupException('The configuration files is missing key {} in section {}'.format(section_key, section))

    def __set_config(self, args: Namespace) -> None:
        config_file = None
        bin_folder = args.bin
        bot_folder = args.bot
        fake_root = args.fake
        config = IntelMQToolConfig()
        config.fake_root = fake_root
        config.log_lvl = args.verbose

        try:
            intelmq_module = __import__('intelmq')
            version = getattr(getattr(intelmq_module, 'version'), '__version_info__')
            config.version = '{}.{}.{}'.format(version[0], version[1], version[len(version) - 1])
            config.config_dir = getattr(intelmq_module, 'CONFIG_DIR')
            config.intelmq_folder = os.path.dirname(intelmq_module.__file__)

        except ModuleNotFoundError:
            raise SetupException('It looks like that IntelMQ is not installed.')

        if bin_folder and bot_folder:
            config.bin_folder = bin_folder
            config.custom_bot_folder = bot_folder
        else:
            if args.config:
                config_file = args.config
            else:
                config_file = os.path.join('config', 'config.ini')

        if config_file:
            if not os.path.exists(config_file):
                raise SetupException('config file "{0}"does not exist'.format(config_file))

            # open file
            config_parser = ConfigParser()
            config_parser.read(config_file)

            config_ok = False
            if len(config_parser.sections()) == 1:
                if 'IntelMQ' in config_parser:
                    if len(config_parser['IntelMQ']) > 2:
                        config.bin_folder = self.__check_get_folder(
                            config_parser, 'IntelMQ', 'binFolder'
                        )
                        config.custom_bot_folder = self.__check_get_folder(
                            config_parser, 'IntelMQ', 'customBotFolder'
                        )
                        config.fake_root = self.__check_get_folder(
                            config_parser, 'IntelMQ', 'fakeRoot'
                        )
                        config_ok = True
            if not config_ok:
                raise SetupException(
                    'The config file "{0}" is not setup correctly use the file "config.ini_tmpl" as basis'.format(
                        config_file
                    )
                )

        try:
            config.validate()
            self.config = config
        except IntelMQToolConfigException as error:
            message = 'Error: {}'.format(error)
            message = '{}\n\n' \
                      'Configuration is not set properly.\n'\
                      'Do one the following:\n'\
                      '\t1. Specify --config\n'\
                      '\t2. Specify --bin, --bot and --intelmq\n'\
                      '\t3. Do not specify either one of 1 and 2 but have a ./config/config.ini set near this tool\n'\
                      'NOTE: for config files use config.ini_tml as basis'.format(message)
            raise SetupException(message)

    def run(self) -> int:
        self.__setup_argument_parser()
        args, argv = self.parser.parse_known_args()

        self.__set_config(args)

        if self.config.is_dev:
            print(colorize_text('Tool is in DEV mode', 'Red'))

        key = args.command
        if key:
            try:
                if argv:
                    # there are unknown commands
                    raise IncorrectArgumentException('Unknown Arguments')
                else:
                    # check if one has root access
                    try:
                        os.mknod('/etc/foo')
                    except PermissionError:
                        if not self.config.is_dev:
                            raise SetupException('You need root permissions to run this tool!')

                    return self.run_tool(key, args)
            except IncorrectArgumentException:
                sub_parser = None
                for item in getattr(getattr(self.parser, '_subparsers'), '_actions'):
                    if isinstance(item, getattr(argparse, '_SubParsersAction')):
                        sub_parser = item
                if sub_parser:
                    sub_parser = sub_parser.choices.get(key, None)
                    if sub_parser:
                        if sub_parser.prog.endswith(key):
                            sub_parser.print_help()
                            return -1
                        return -2

                raise IntelMQToolException('No Tools are defined')

        elif args.details:
            print('IntelMQ Version:                {}'.format(self.config.version))
            print('IntelMQ Installation Directory: {}'.format(self.config.intelmq_folder))
            print('Configuration Directory:        {}'.format(self.config.config_dir))
            print('running BOTS File location:     {}'.format(self.config.running_bots_file))
            print('default BOTS File location:     {}'.format(self.config.base_bots_file))
            print('defaults.conf location:         {}'.format(self.config.defaults_conf_file))
            print('runtime.conf location:          {}'.format(self.config.runtime_file))
            print('Custom IntelMQ Bots location    {}'.format(self.config.custom_bot_folder))
            return 0
        else:
            self.parser.print_help()
            return -10
