# -*- coding: utf-8 -*-

"""
Created on 31.12.21
"""

__author__ = 'Weber Jean-Paul'
__email__ = 'jean-paul.weber@restena.lu'
__copyright__ = 'Copyright 2019-present, Restena CSIRT'
__license__ = 'GPL v3+'

from argparse import ArgumentParser, Namespace
from os import remove
from os.path import join
from typing import Optional, List, Union

from intelmqworkbench import IntelMQToolException
from intelmqworkbench.abstractbasetool import AbstractBaseTool
from intelmqworkbench.classes.bots.bots import BOTS
from intelmqworkbench.classes.issues.intelmqbotinstallissue import IntelMQBotInstallIssue
from intelmqworkbench.classes.issues.intelmqbotissue import IntelMQBotIssue
from intelmqworkbench.classes.issues.intelmqbotsissue import IntelMQBotsIssue
from intelmqworkbench.classes.issues.intelmqruntimeissue import IntelMQRuntimeIssue
from intelmqworkbench.classes.issues.issues import MismatchIssue, MissingIssue, AdditionalIssue, MissingExecutable, \
    MissingDefaultConfigurationIssue, MissingDescriptionIssue, AbsentIssue, AvailableExecutableIssue, ReferenceIssue, \
    NotInstalledIssue, InstallIssueLocations, MismatchInstallIssue
from intelmqworkbench.classes.pipeline.pipelinie import Pipeline
from intelmqworkbench.classes.runtime.runtime import Runtime
from intelmqworkbench.utils import colorize_text, query_yes_no


class Fixer(AbstractBaseTool):

    def get_default_argument_description(self) -> Optional[str]:
        return 'The same as -i'

    def get_version(self) -> str:
        return '0.3'

    def get_arg_parser(self) -> ArgumentParser:
        arg_parse = ArgumentParser(prog='fix', description='Tool for fixing bot configurations')
        arg_parse.add_argument('-a', '--auto',
                               default=False,
                               help='Automatic fixing.\nNOTE: Only configuration keys are considered.',
                               action='store_true')
        arg_parse.add_argument('-i', '--issues', default=False,
                               help='Fix the detected issues.',
                               action='store_true')
        arg_parse.add_argument('--force', default=False, help='Force', action='store_true')
        return arg_parse

    def start(self, args: Namespace) -> int:
        force = args.force
        issues = self.get_issues(force)
        bots_conf = self.get_running_bots(force)
        runtime = self.get_runtime()
        pipeline = self.get_pipeline(force)
        if args.auto:
            print('{} Parameter values will not be changed!\n'.format(colorize_text('Note:', 'Red')))
        if issues:
            return self.handle_issues(issues, runtime, bots_conf, pipeline, args.auto)
        else:
            print('No issues detected')
        return 0

    def handle_issues(
            self, issues: List[Union[IntelMQBotIssue, IntelMQBotInstallIssue]],
            runtime: Runtime,
            bots_conf: Optional[BOTS],
            pipeline: Optional[Pipeline],
            auto: bool
    ) -> int:
        for issue in issues:
            if isinstance(issue, IntelMQBotIssue):
                print('BOT "{}" ({}) has the following issues:'.format(issue.bot.name, issue.bot.module))
                if issue.bots_issues:
                    self.handle_bots_issues(issue.bots_issues, bots_conf, auto)
                if issue.parameter_issues:
                    raise NotImplementedError()
                if issue.issues:
                    self.handle_bot_issues(issue.issues, bots_conf, runtime, auto)
                if issue.runtime_issues:
                    self.handle_runtime_issues(issue.runtime_issues, runtime, auto)
            elif isinstance(issue, IntelMQBotInstallIssue):
                print('Detected General Issues:')
                self.handle_general_issue(issue, bots_conf, runtime, pipeline,  auto)
            else:
                raise IntelMQToolException('Issue is not known. Stopping')
        # save changes
        self.output_handler.save_runtime(runtime)
        self.output_handler.save_bots(bots_conf)
        return 0

    def handle_general_issue(
            self,
            item: IntelMQBotInstallIssue,
            bots: BOTS,
            runtime: Runtime,
            pipeline: Optional[Pipeline],
            auto: bool
    ) -> None:
        self.logger.info('Handling Install Issues')
        for issue in item.issues:
            if isinstance(issue, AvailableExecutableIssue):
                self.output_handler.print_issue(issue)
                if auto:
                    do_fix = True
                else:
                    do_fix = query_yes_no(
                        'Do you want to remove the executable "{}" from {}'.format(issue.file_name, issue.path)
                    )
                if do_fix:
                    print(colorize_text('Fixed', 'Green'))
                    remove(join(issue.path, issue.file_name))
            elif isinstance(issue, ReferenceIssue):
                self.output_handler.print_issue(issue)
                do_fix = query_yes_no(
                    'Do you want to remove the reference "{}" from {}'.format(issue.reference, issue.location),
                    default='no'
                )
                if do_fix:
                    result = False
                    if issue.location == InstallIssueLocations.RUNTIME:
                        result = self.intelmq_handler.remove_runtime_item_by_bot_id(
                            issue.reference, runtime, pipeline, self.config.bin_folder
                        )
                    elif issue.location == InstallIssueLocations.BOTS:
                        # this one is only executed either by force or if it's intelmq 2.x
                        result = self.intelmq_handler.remove_bots_item(
                            issue.reference, issue.module, issue.name, bots, runtime, self.config.bin_folder
                        )
                    else:
                        raise IntelMQToolException('Unknown location')

                    if result:
                        print(colorize_text('Fixed', 'Green'))

            elif isinstance(issue, NotInstalledIssue):
                self.output_handler.print_issue(issue)
                do_fix = query_yes_no(
                    'Do you want to install Bot "{}" ({})'.format(issue.bot.name, issue.bot.module),
                    default='no'
                )
                if do_fix:
                    print(colorize_text('Fixed', 'Green'))
                    self.output_handler.install_bot(issue.bot, self.config.bin_folder, self.config.bot_folder, bots)

            else:
                raise IntelMQToolException('Issue is not known. Stopping')

    def handle_runtime_issues(self, issues: List[IntelMQRuntimeIssue], runtime: Runtime, auto: bool) -> None:
        self.logger.info('Handling Runtime Issues')
        for item in issues:
            runtime_item = runtime.get_item_by_id(item.bot_id)
            for issue in item.issues:
                if isinstance(issue, MismatchIssue):
                    self.output_handler.print_issue(issue)
                    do_fix = query_yes_no('Do you want to set the value "{}" to key "{}"'.format(
                        issue.should_value, issue.key)
                    )
                    if do_fix:
                        print(colorize_text('Fixed', 'Green'))
                        setattr(runtime_item, issue.key, issue.should_value)
                elif isinstance(issue, MissingIssue):
                    raise NotImplementedError()
                elif isinstance(issue, AdditionalIssue):
                    raise NotImplementedError()
                else:
                    raise IntelMQToolException('Issue is not known. Stopping')
            for issue in item.parameter_issues:
                if isinstance(issue, MismatchIssue):
                    self.output_handler.print_issue(issue)
                    do_fix = query_yes_no('Do you want to set the value "{}" to key "{}"'.format(
                        issue.should_value, issue.key)
                    )
                    if do_fix:
                        print(colorize_text('Fixed', 'Green'))
                        runtime_item.parameters.set_value(issue.key, issue.should_value)
                elif isinstance(issue, MissingIssue):
                    self.output_handler.print_issue(issue)
                    if auto:
                        do_fix = True
                    else:
                        do_fix = query_yes_no('Do you want to add the key "{}" with value "{}"'.format(
                            issue.key, issue.default_value)
                        )
                    if do_fix:
                        print(colorize_text('Fixed', 'Green'))
                        runtime_item.parameters.add_value(issue.key, issue.default_value)
                elif isinstance(issue, AdditionalIssue):
                    self.output_handler.print_issue(issue)
                    if auto:
                        do_fix = True
                    else:
                        do_fix = query_yes_no('Do you want to add the key "{}" with value "{}"'.format(
                            issue.key, issue.value)
                        )
                    if do_fix:
                        print(colorize_text('Fixed', 'Green'))
                        runtime_item.parameters.add_value(issue.key, issue.value)
                elif isinstance(issue, AbsentIssue):
                    self.output_handler.print_issue(issue)
                    if auto:
                        do_fix = True
                    else:
                        do_fix = query_yes_no('Do you want to remove the key "{}" with value "{}"'.format(
                            issue.key, issue.default_value)
                        )
                    if do_fix:
                        print(colorize_text('Fixed', 'Green'))
                        runtime_item.parameters.remove_key(issue.key)
                else:
                    raise IntelMQToolException('Issue is not known. Stopping')

    def handle_bot_issues(self, issues: List[
        Union[
            MissingIssue,
            MismatchIssue,
            AdditionalIssue,
            MissingExecutable,
            MissingDefaultConfigurationIssue,
            MissingDescriptionIssue
        ]
    ], bots: BOTS, runtime: Runtime, auto: bool):
        self.logger.info('Handling bot issues')
        for issue in issues:
            if isinstance(issue, MismatchIssue):
                raise NotImplementedError()
            elif isinstance(issue, MissingIssue):
                raise NotImplementedError()
            elif isinstance(issue, AdditionalIssue):
                raise NotImplementedError()
            elif isinstance(issue, MismatchInstallIssue):
                self.output_handler.print_issue(issue)
                if auto:
                    do_fix = True
                else:
                    do_fix = query_yes_no(
                        'Do you want to sync install of bot "{}" ({})'.format(issue.bot.class_name, issue.bot.module),
                        default='yes'
                    )
                if do_fix:
                    print(colorize_text('Fixed', 'Green'))
                    self.output_handler.sync_folders(issue.source, issue.destination)

            elif isinstance(issue, MissingExecutable):
                self.output_handler.print_issue(issue)
                if auto:
                    do_fix = True
                else:
                    do_fix = query_yes_no(
                        'Do you want to create executable {}'.format(join(issue.path, issue.file_name)),
                        default='yes'
                    )
                if do_fix:
                    print(colorize_text('Fixed', 'Green'))
                    self.output_handler.create_executable(issue.bot, self.config.bin_folder)
            elif isinstance(issue, MissingDefaultConfigurationIssue):
                message = '{}: Cannot fix {} -> Skipping as manual action required.'.format(colorize_text('Major Issue', 'Red'), issue.description)
                print(message)
            elif isinstance(issue, MissingDescriptionIssue):
                message = '{}: Cannot fix {} -> Skipping as manual action required.'.format(colorize_text('Major Issue', 'Red'), issue.description)
                print(message)
            else:
                raise IntelMQToolException('Issue is not known. Stopping')

    def handle_bots_issues(self, issues: IntelMQBotsIssue, bots: BOTS, auto: bool):
        self.logger.info('Handling issues in BOTS')
        bots_item = bots.get_bot_item_by_bot(issues.bot)
        for issue in issues.issues:
            if isinstance(issue, MismatchIssue):
                self.output_handler.print_issue(issue)
                do_fix = query_yes_no('Do you want to set the value "{}" to key "{}"'.format(
                    issue.should_value, issue.key)
                )
                if do_fix:
                    print(colorize_text('Fixed', 'Green'))
                    setattr(bots_item, issue.key, issue.should_value)
            elif isinstance(issue, MissingIssue):
                raise NotImplementedError()
            elif isinstance(issue, AdditionalIssue):
                raise NotImplementedError()
            else:
                raise IntelMQToolException('Issue is not known. Stopping')
        for issue in issues.parameter_issues:
            if isinstance(issue, MismatchIssue):
                self.output_handler.print_issue(issue)
                do_fix = query_yes_no('Do you want to set the value "{}" to key "{}"'.format(
                    issue.should_value, issue.key)
                )
                if do_fix:
                    print(colorize_text('Fixed', 'Green'))
                    bots_item.parameters.set_value(issue.key, issue.should_value)
            elif isinstance(issue, MissingIssue):
                self.output_handler.print_issue(issue)
                if auto:
                    do_fix = True
                else:
                    do_fix = query_yes_no('Do you want to add the key "{}" with value "{}"'.format(
                        issue.key, issue.default_value)
                    )
                if do_fix:
                    print(colorize_text('Fixed', 'Green'))
                    bots_item.parameters.add_value(issue.key, issue.default_value)
            elif isinstance(issue, AdditionalIssue):
                self.output_handler.print_issue(issue)
                if auto:
                    do_fix = True
                else:
                    do_fix = query_yes_no('Do you want to add the key "{}" with value "{}"'.format(
                        issue.key, issue.value)
                    )
                if do_fix:
                    print(colorize_text('Fixed', 'Green'))
                    bots_item.parameters.add_value(issue.key, issue.value)
            elif isinstance(issue, AbsentIssue):
                self.output_handler.print_issue(issue)
                if auto:
                    do_fix = True
                else:
                    do_fix = query_yes_no('Do you want to remove the key "{}" with value "{}"'.format(
                        issue.key, issue.default_value)
                    )
                if do_fix:
                    print(colorize_text('Fixed', 'Green'))
                    bots_item.parameters.remove_key(issue.key)
            else:
                raise IntelMQToolException('Issue is not known. Stopping')

