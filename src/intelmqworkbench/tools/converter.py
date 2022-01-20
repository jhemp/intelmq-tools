# -*- coding: utf-8 -*-

"""
Created on 27.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

from argparse import ArgumentParser, Namespace
from os.path import join
from pathlib import Path
from typing import Optional

from ruamel import yaml

from intelmqworkbench import AbstractBaseTool
from intelmqworkbench.classes.parameters import Parameters
from intelmqworkbench.classes.pipeline.pipelinie import Pipeline
from intelmqworkbench.classes.runtime.runtime import Runtime
from intelmqworkbench.exceptions import IntelMQToolException, IntelMQParsingException
from intelmqworkbench.utils import query_yes_no


class Converter(AbstractBaseTool):

    def get_version(self) -> str:
        return '0.2'

    def get_arg_parser(self) -> ArgumentParser:
        arg_parse = ArgumentParser(prog='converter', description='Tool for converting 2.x to 3.x')
        arg_parse.add_argument('-o', '--output', default=None, help='Output runtime.conf of 2.x', type=str, required=True)
        arg_parse.add_argument('--force', default=False, help='Force', action='store_true')
        self.set_default_arguments(arg_parse)
        return arg_parse

    def convert_to_new_runtime(self, pipeline: Pipeline, runtime: Runtime) -> Runtime:
        self.logger.info('Converting pipeline.conf and runtime.conf to new setup')
        # modify runtime to fit the new pattern
        runtime_items_to_remove = list()
        for runtime_item in runtime.get_items():
            pipeline_item = pipeline.get_item_for(runtime_item.bot_id)
            if pipeline_item:
                parameter = Parameters()
                parameter.add_values({
                    'destination_queues': {
                        '_default': pipeline_item.destinations
                    }
                })
                runtime_item.parameters.merge_parameters(parameter)
            else:
                if runtime_item.group in ['Collector']:
                    message = 'No Pipeline Found fir bot "{}"'.format(runtime_item.bot_id)
                    self.logger.error(message)
                    result = query_yes_no('Do you want to remove this item?')
                    if result:
                        runtime_items_to_remove.append(runtime_item)
                    else:
                        raise IntelMQParsingException('Manual Action required to solve the issue.')
                elif runtime_item.group in ['Output']:
                    self.logger.debug('Output Bot "{}" found. Taking no action'.format(runtime_item.bot_id))
                else:
                    self.logger.critical('Non Collector bot found with no Pipeline. Removing "{}"'.format(runtime_item.bot_id))
                    runtime_items_to_remove.append(runtime_item)

        for item in runtime_items_to_remove:
            runtime.remove_by_bot_id(item.bot_id)

        return runtime

    def start(self, args: Namespace) -> int:
        runtime_path = self.config.runtime_conf_file
        pipeline_path = self.config.pipeline_conf_file
        runtime = self.intelmq_handler.parse_runtime_conf(runtime_path)
        pipeline = self.intelmq_handler.parse_pipeline(pipeline_path)

        output = args.output
        if output:
            if not output.startswith('/'):
                path = Path(__file__).parents[3]
                output = join(path, output)
            if pipeline:
                runtime_new = self.convert_to_new_runtime(pipeline, runtime)
                self.logger.debug('Saving to {}'.format(output))
                with open(output, 'w+') as f:
                    yaml.dump(runtime_new.to_json(), f)
                print('Created conversion of {} and {}. File located under {}'.format(
                        self.config.runtime_conf_file, self.config.pipeline_conf_file, output
                    )
                )
                return 0
            else:
                print('IntelMQ is of Version > 3.0.0 and runtime should be already converted use with --force')
                return -1
        else:
            raise IntelMQToolException('No output file specified')

    def get_default_argument_description(self) -> Optional[str]:
        return None
