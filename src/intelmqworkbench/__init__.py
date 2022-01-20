# -*- coding: utf-8 -*-

"""
Created on 27.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

import logging
import os
import pathlib
import sys
import argparse
from configparser import ConfigParser
from os.path import isfile
from typing import Dict, List, Type, Optional

from intelmqworkbench.abstractbasetool import AbstractBaseTool
from intelmqworkbench.classes.intelmqworkbenchconfig import IntelMQWorkbenchConfig
from intelmqworkbench.exceptions import IntelMQToolFactoryException, IncorrectArgumentException, \
    IntelMQWorkbenchException, IntelMQToolException, IntelMQWorkbenchConfigException


class ToolFactory:

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.__components: Dict[str, AbstractBaseTool] = dict()
        self.intelmq_config = None
        self.config = None

    def __setup_config_file(self, config_file: Optional[str]) -> None:
        internal_config = config_file
        if internal_config is None:
            path = pathlib.Path().resolve()
            internal_config = os.path.join(path, '..', 'config', 'config.ini')
            if not isfile(internal_config):
                internal_config = os.path.join(path, 'config', 'config.ini')

        if internal_config and os.path.isfile(internal_config) and self.config:
            # open file
            config_parser = ConfigParser()
            config_parser.read(internal_config)
            if len(config_parser.sections()) == 1:
                if 'IntelMQ' in config_parser:
                    if len(config_parser['IntelMQ']) > 2:
                        self.config.bin_folder = config_parser['IntelMQ']['binFolder']
                        self.config.custom_bot_folder = config_parser['IntelMQ']['customBotFolder']
                        self.config.fake_root = config_parser['IntelMQ']['fakeRoot']
                        self.config.output_folder = config_parser['IntelMQ']['outputFolder']

    def set_config(self, args: Optional[argparse.Namespace]) -> None:
        self.config = IntelMQWorkbenchConfig()
        # set values defined by intelmq
        intelmq_module = __import__('intelmq')
        version = getattr(getattr(intelmq_module, 'version'), '__version_info__')
        self.config.version = '{}.{}.{}'.format(version[0], version[1], version[len(version) - 1])
        self.config.config_dir = getattr(intelmq_module, 'CONFIG_DIR')
        self.config.default_logging_path = getattr(intelmq_module, 'DEFAULT_LOGGING_PATH')
        self.config.intelmq_folder = os.path.dirname(intelmq_module.__file__)
        self.config.harmonization_conf_file = getattr(intelmq_module, 'HARMONIZATION_CONF_FILE')
        if self.config.version.startswith('2'):
            self.config.pipeline_conf_file = getattr(intelmq_module, 'PIPELINE_CONF_FILE')

        self.__setup_config_file(args.config)
        del args.config

        # override or set
        if args.output_folder:
            self.config.output_folder = args.output_folder
            del args.output_folder

        if args.runtime_conf_file:
            self.config.runtime_conf_file = args.runtime_conf_file
            del args.runtime_conf_file

        if args.runtime_yaml_file:
            self.config.runtime_yaml_file = args.runtime_yaml_file
            del args.runtime_yaml_file

        if args.default_BOTS_file:
            self.config.default_BOTS_file = args.default_BOTS_file
            del args.default_BOTS_file

        if args.runtime_BOTS_file:
            self.config.runtime_BOTS_file = args.runtime_BOTS_file
            del args.runtime_BOTS_file

        if args.default_logging_path:
            self.config.default_logging_path = args.default_logging_path
            del args.default_logging_path

        if args.harmonization_conf_file:
            self.config.harmonization_conf_file = args.harmonization_conf_file
            del args.harmonization_conf_file

        if args.custom_bot_location:
            self.config.custom_bot_location = args.custom_bot_location
            del args.custom_bot_location

        if args.default_bot_location:
            self.config.default_bot_location = args.default_bot_location
            del args.default_bot_location

        if args.pipeline_file:
            self.config.pipeline_conf_file = args.pipeline_file
            del args.pipeline_file

        if args.bin_folder:
            self.config.bin_folder = args.bin_folder
            del args.bin_folder

        if args.fake:
            self.config.fake_root = args.fake
            del args.fake
        try:
            self.config.validate()
        except IntelMQWorkbenchConfigException as error:
            message = 'Error: {}'.format(error)
            message = '{}\n\n' \
                      'Configuration is not set properly.\n' \
                      'Do one the following:\n' \
                      '\t1. Specify --config\n' \
                      '\t2. Specify --bin, --bot and --intelmq\n' \
                      '\t3. Do not specify either one of 1 and 2 but have a ./config/config.ini set near this tool\n' \
                      'NOTE: for config files use config.ini_tml as basis'.format(message)
            raise IntelMQWorkbenchException(message)

    @property
    def components(self) -> List[AbstractBaseTool]:
        output = list()
        for item in self.__components.values():
            output.append(item)
        return output

    def register_component(self, clazz: Type[AbstractBaseTool]) -> None:
        instance = clazz(self.logger, self.config)
        tool_id = instance.get_arg_parser().prog
        if tool_id in self.__components.keys():
            raise IntelMQToolFactoryException('Tool id "{}" is already existing. It is defined in "{}"'.format(
                tool_id,
                clazz.__name__
                )
            )
        self.__components[tool_id] = instance

    def run_application(self, key: str, args: argparse.Namespace) -> int:
        instance = self.__components.get(key, None)
        # is not set by registration as it may vary
        instance.config = self.config
        if instance is None:
            raise IntelMQToolFactoryException('Tool {} cannot be found'.format(key))
        else:
            if hasattr(args, 'version'):
                if args.version:
                    print('Version: {}', instance.get_version())
                    return 0
                else:
                    del args.version
            return instance.start(args)


class IntelMQWorkbench:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__tool_factory = ToolFactory(self.logger)
        self.__parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        self.__subparsers = self.__parser.add_subparsers(help='Available tools', dest='command')
        self.__common = argparse.ArgumentParser(add_help=False)
        self.__common.add_argument('--verbose', '-v', action='count', default=0)
        self.__common.add_argument('-f', '--full', action='store_true', help='display full', default=False)
        self.__parser.add_argument('-d', '--details',
                                   default=None,
                                   help='Details of intelmq and this tools',
                                   action='store_true')

        self.__parser.add_argument('--runtime_conf_file', default=None, help='runtime.conf of 2.x', type=str)
        self.__parser.add_argument('--runtime_yaml_file', default=None, help='runtime.yaml of 3.x', type=str)
        self.__parser.add_argument('--default_BOTS_file', default=None, help='default BOTS of 2.x', type=str)
        self.__parser.add_argument('--runtime_BOTS_file', default=None, help='runtime BOTS of 2.x', type=str)
        self.__parser.add_argument('--custom_bot_location', default=None, help='Location of Custom Bots', type=str)
        self.__parser.add_argument('--default_bot_location', default=None, help='Location of IntelMQ Bots', type=str)
        self.__parser.add_argument('--pipeline_file', default=None, help='pipeline.conf of 2.x', type=str)
        self.__parser.add_argument('--default_logging_path', default=None, help='default logging path', type=str)
        self.__parser.add_argument('--harmonization_conf_file', default=None, help='harmonisation file', type=str)
        self.__parser.add_argument('--intelmq_location', default=None, help='Location of the intelmq installation', type=str)
        self.__parser.add_argument('--output_folder',
                                   default=None,
                                   help='Output folder for messages (used in fiddler)',
                                   type=str)
        self.__parser.add_argument('--bin_folder', default=None, help='Location of bin folder', type=str)

        self.__parser.add_argument('--fake',
                                   type=str,
                                   help='Location of the root used for development.\n'
                                        'Note: If this set the tool is automatically in dev mode.',
                                   default=None)
        self.__parser.add_argument('--config',
                                   type=str,
                                   help='Configuration file\n'
                                        'Note: The default location is ./config/config.ini',
                                   default=None)

    def register_tool(self, clazz: Type[AbstractBaseTool]):
        self.__tool_factory.register_component(clazz)

    @staticmethod
    def __get_log_level(log_level: int) -> int:
        if log_level == 0:
            return logging.CRITICAL
        elif log_level == 1:
            return logging.ERROR
        elif log_level == 2:
            return logging.WARNING
        elif log_level == 3:
            return logging.INFO
        else:
            return logging.DEBUG

    def __set_logger_parameters(self, log_level: int) -> None:
        if log_level and log_level > -1:
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            self.logger.setLevel(logging.DEBUG)
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(log_format))
            console_handler.setLevel(self.__get_log_level(log_level))
            self.logger.addHandler(console_handler)

    def start(self) -> int:

        for tool in self.__tool_factory.components:
            arg_parser = tool.get_arg_parser()
            sub_parser = self.__subparsers.add_parser(
                arg_parser.prog,
                parents=[self.__common],
                add_help=False,
                help=arg_parser.description
            )

            # noinspection PyProtectedMember
            sub_parser._add_container_actions(arg_parser)
            sub_parser.description = arg_parser.description

        args, argv = self.__parser.parse_known_args()
        self.__tool_factory.set_config(args)
        # be sure that the custom bots are in the path
        sys.path.append(self.__tool_factory.config.custom_bot_folder)
        key = args.command
        if key:
            try:
                # check if there are unknown commands
                if argv:
                    # there are unknown commands
                    raise IntelMQToolException('Command {} is not defined'.format(argv))
                else:

                    del args.command
                    # set logger configuration
                    self.__set_logger_parameters(args.verbose)

                    # check if environment is setup as expected
                    return self.__tool_factory.run_application(key, args)
            except IncorrectArgumentException:
                sub_parser = None
                for item in getattr(getattr(self.__parser, '_subparsers'), '_actions'):
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
            except IntelMQToolException as error:
                print(error)
                return -3
            except IntelMQWorkbenchException as error:
                print(error)
                return -4
        elif args.details:
            print('IntelMQ Version:                {}'.format(self.__tool_factory.config.version))
            print('IntelMQ Installation Directory: {}'.format(self.__tool_factory.config.intelmq_folder))
            print('Configuration Directory:        {}'.format(self.__tool_factory.config.config_dir))
            if self.__tool_factory.config.version.startswith('3'):
                print('runtime.yml location:           {}'.format(self.__tool_factory.config.runtime_yaml_file))
            else:
                print('running BOTS File location:     {}'.format(self.__tool_factory.config.running_BOTS))
                print('default BOTS File location:     {}'.format(self.__tool_factory.config.default_BOTS))
                print('pipeline.conf File location:     {}'.format(self.__tool_factory.config.pipeline_conf_file))
                print('runtime.conf location:          {}'.format(self.__tool_factory.config.runtime_conf_file))
            print('Custom IntelMQ Bots location:   {}'.format(self.__tool_factory.config.custom_bot_folder))
            print('Bin Folder location:            {}'.format(self.__tool_factory.config.bin_folder))
            return 0
        else:
            self.__parser.print_help()
            return -10

