**NOTE:** this version works but is still a bit rough on the edges. 

# intelmq-tools
Tools for intelmq. 
This tool will help you to check up on your running configurations and 
helps you to update them. The tools also makes the necessary configurations in IntelMQ 
to be able to add custom Bots in a simple manner.

# Features
* Integrates custom bots into intelmq
* Checking the configurations for miss configurations
* Checking if the bots gotten new parameters
* Fixes discrepancies the bots configurations of IntelMQ
* Fixes missing new parameters of bots
* Listing all the bots and their configurations
* Run bots without the whole setup of intelmq, for development purposes

# Requirements
- Installation of IntelMQ (see https://github.com/certtools/intelmq)
- Python3
- The custom bots need to be referenced in the python path only required for intelmq 2.x

# Installation
Clone this repo somewhere on the system where the instance of IntelMQ resides or use a virtual environment.

Make intelmq-workbench.sh executable.

It's recommended to create a configuration file on basis of the config.ini_tmpl else the parameters have to be specified. 

# Configuration
The tool needs a configuration file to find the base paths. 
There is a template in the config folder:
There are only two elements which needs configuration the table below will explain both:

|TAG|Description|
|---|---|
| binFolder  | The location of intelmq. Example /usr/bin  |
| customBotFolder | Location of the custom bots to be referenced. Example ./bot_folder |
| fakeRoot | Location of a fake root of a system. If this value is set the tool will be in development mode.  |
| outputFolder | Location of the dump of the generated messages when using fiddler. |

# Custom Bots

## IntelMQ 2.x

The custom Bots can now be stored anywhere. The folder where the custom bots reside must have the same 
structure as the one in IntelMQ (see the bot_folder as example). The folder of custom Bots must be present in the PYTHONPATH.
This is necessary for the execution.

The custom Bots require a config.json, 
which defines the default configuration of the bot. 
The configuration is similar as in IntelMQ.

## IntelMQ 3.x

The custom Bots should be stored inside the intelmq.bots folder, else the intelmq-manager will not list them as only this bot folder is scanned.

# Usage examples
Here are some examples of use:

## Overview of the tools

```bash
$ ./intelmq-workbench.sh 
usage: intelmqworkbench.py [-h] [-d] [--runtime_conf_file RUNTIME_CONF_FILE] [--runtime_yaml_file RUNTIME_YAML_FILE] [--default_BOTS_file DEFAULT_BOTS_FILE] [--runtime_BOTS_file RUNTIME_BOTS_FILE]
                           [--custom_bot_location CUSTOM_BOT_LOCATION] [--default_bot_location DEFAULT_BOT_LOCATION] [--pipeline_file PIPELINE_FILE] [--default_logging_path DEFAULT_LOGGING_PATH]
                           [--harmonization_conf_file HARMONIZATION_CONF_FILE] [--output_folder OUTPUT_FOLDER] [--bin_folder BIN_FOLDER] [--fake FAKE] [--config CONFIG]
                           {converter,check,list,fix,botter,fiddler} ...

positional arguments:
  {converter,check,list,fix,botter,fiddler}
                        Available tools
    converter           Tool for converting 2.x to 3.x
    check               Check installation of bots is still applicable
    list                Lists bots
    fix                 Tool for fixing bot configurations
    botter              Tool for installing bots
    fiddler             Tool for installing bots

optional arguments:
  -h, --help            show this help message and exit
  -d, --details         Details of intelmq and this tools
  --runtime_conf_file RUNTIME_CONF_FILE
                        runtime.conf of 2.x
  --runtime_yaml_file RUNTIME_YAML_FILE
                        runtime.yaml of 3.x
  --default_BOTS_file DEFAULT_BOTS_FILE
                        default BOTS of 2.x
  --runtime_BOTS_file RUNTIME_BOTS_FILE
                        runtime BOTS of 2.x
  --custom_bot_location CUSTOM_BOT_LOCATION
                        Location of Custom Bots
  --default_bot_location DEFAULT_BOT_LOCATION
                        Location of IntelMQ Bots
  --pipeline_file PIPELINE_FILE
                        pipeline.conf of 2.x
  --default_logging_path DEFAULT_LOGGING_PATH
                        default logging path
  --harmonization_conf_file HARMONIZATION_CONF_FILE
                        harmonisation file
  --output_folder OUTPUT_FOLDER
                        Output folder for messages (used in fiddler)
  --bin_folder BIN_FOLDER
                        Location of bin folder
  --fake FAKE           Location of the root used for development.
                        Note: If this set the tool is automatically in dev mode.
  --config CONFIG       Configuration file
                        Note: The default location is ./config/config.ini

```

The tool will by default look for the file config/config.ini or if --config is used it uses this config file. 
If none of these is provided following parameters need to be set.
* --custom_bot_location
* --bin_folder

**Note:** Specifying any of the other parameters as for example --default_logging_path will override the values set in the config.ini.

## Listing of bots

```bash
$ ./intelmq-workbench.sh list -c
Bot "MailCollectorBot" (intelmq.bots.collectors.mail._lib) may be missing a launch variable
Bot "GithubAPICollectorBot" (intelmq.bots.collectors.github_api._collector_github_api) may be missing a launch variable

BOT Group:               Collector (Custom)
BOT Class:               OTRSCollectorBot
BOT Name:                OTRS
Description:             OTRS Collector fetches attachments from Restena's OTRS instance instance.
Module:                  collectors.otrs.collector_otrs
File:                    /workspace/intelmq-workbench/bots/bots/collectors/otrs/collector_otrs.py
Default Paramters        ['attachment_regex', 'extract_attachment', 'extract_download', 'http_password', 'http_username', 'limit', 'password', 'search_not_older_than', 'search_owner', 'search_queue', 'search_requestor', 'search_status', 'search_subject_like', 'set_status', 'ssl_client_certificate', 'take_ticket', 'uri', 'url_regex', 'user']
Installed/Strange:       False/False
Running Instances        66

```

*Note*: If th bot is not configured as expected it will not be imported. In the case above the launch variable (BOT=<class>) was not set.

## Installing a bot

```bash
$ ./intelmq-workbench.sh botter -i OTRSCollectorBot
Bot "MailCollectorBot" (intelmq.bots.collectors.mail._lib) may be missing a launch variable
Bot "GithubAPICollectorBot" (intelmq.bots.collectors.github_api._collector_github_api) may be missing a launch variable
BOT "OTRS" (collectors.otrs.collector_otrs) installed.
```
This command will create all required files for to run the bot. It will create and modify the required files to run the bot.
In intelmq 2.x for instance the BOTS file will be updated with the details specified in the config.json or as specified in the code of the bot as 
it is done in intelmq 3.x. However if the later is used in the context of intelmq 2.x, one must take care that the values will be set 
during launch manually.

For intelmq 3.x the symlinks are used to guarantee that the updated code of the custom bot is used and not an older copy.

**Note:** The bot to be installed needs to be accessible by python if used with intelmq 2.x.


 
## Removing a bot

```bash
$ ./intelmq-workbench.sh botter -u OTRSCollectorBot
Bot "MailCollectorBot" (intelmq.bots.collectors.mail._lib) may be missing a launch variable
Bot "GithubAPICollectorBot" (intelmq.bots.collectors.github_api._collector_github_api) may be missing a launch variable

```
BOT "OTRS" (collectors.otrs.collector_otrs) removed.

## Checking for differences in the configurations

```bash
$ ./intelmq-workbench.sh check -r
BOT Group:               Collector (Custom)
BOT Class:               OTRSCollectorBot
BOT Name:                OTRS
Description:             OTRS Collector fetches attachments from Restena's OTRS instance instance.
Module:                  collectors.otrs.collector_otrs
File:                    /home/jpweber/workspace/intelmq-workbench/bots/bots/collectors/otrs/collector_otrs.py
Default Paramters        ['attachment_regex', 'extract_attachment', 'extract_download', 'http_password', 'http_username', 'limit', 'password', 'search_not_older_than', 'search_owner', 'search_queue', 'search_requestor', 'search_status', 'search_subject_like', 'set_status', 'ssl_client_certificate', 'take_ticket', 'uri', 'url_regex', 'user']
Installed:               False
Running Instances        66
 - Key "attachment_regex" has value "None" but should be "\.csv\.zip$"
 - Key "extract_attachment" has value "0" but should be "True"
 - Key "extract_download" has value "0" but should be "True"
 - Key "search_queue" has value "CSIRT::Robots" but should be "CSIRT"
 - Key "set_status" has value "None" but should be "open"
 - Key "take_ticket" has value "0" but should be "True"
 - Key "search_queue" has value "None" but should be "CSIRT"

...
Other Issues were Detected
 - Bot "OTRSCloser" (intelmq.bots.experts.otrs_closer.expert) is referenced in runtime.conf (OTRS-Expert-OTRSCloser) but not installed!
```

## Fixing configurations

```bash
./intelmq-workbench.sh fix -i -a
Bot "MailCollectorBot" (intelmq.bots.collectors.mail._lib) may be missing a launch variable
Bot "GithubAPICollectorBot" (intelmq.bots.collectors.github_api._collector_github_api) may be missing a launch variable
Note: Parameter values will not be changed!

BOT "Deduplicator" (intelmq.bots.experts.deduplicator.expert) has the following issues:
 - Key "filter_keys" has value "" but should be "None"
Do you want to set the value "None" to key "filter_keys" [Y/n] Y
Fixed
 - Key "redis_cache_db" is nowhere defined with value "6"
Fixed
 - Key "redis_cache_host" is nowhere defined with value "127.0.0.1"
Fixed
 - Key "redis_cache_password" is nowhere defined with value ""
Fixed
 - Key "redis_cache_port" is nowhere defined with value "6379"
Fixed
 - Key "redis_cache_ttl" is nowhere defined with value "86400"
Fixed
BOT "Tuency" (intelmq.bots.experts.tuency.expert) has the following issues:
Major Issue: Cannot fix Bot "TuencyExpertBot" (Expert) has no description -> Skipping as manual action required.
BOT "Fireeye" (intelmq.bots.parsers.fireeye.parser) has the following issues:
Major Issue: Cannot fix Bot "FireeyeParserBot" (Parser) has no description -> Skipping as manual action required.
BOT "PostgreSQL" (intelmq.bots.outputs.postgresql.output) has the following issues:
Major Issue: Cannot fix Bot "PostgreSQLOutputBot" (Output) has no description -> Skipping as manual action required.
BOT "TemplatedSMTP" (intelmq.bots.outputs.templated_smtp.output) has the following issues:
Major Issue: Cannot fix Bot "TemplatedSMTPOutputBot" (Output) has no description -> Skipping as manual action required.
BOT "FireeyeMAS" (intelmq.bots.collectors.fireeye.collector_mas) has the following issues:
Major Issue: Cannot fix Bot "FireeyeMASCollectorBot" (Collector) has no description -> Skipping as manual action required.
```
**Note:** with the -a option the tool automatically adds/removes keys. 
Keys which different values will not be taken into account and require manual interaction.

## Converter
```bash
$ ./intelmq-workbench.sh converter -o /opt/intelmq/etc/runtime.yaml -f
No Pipeline Found fir bot "OTRS-Collector-Test"
Do you want to remove this item? [Y/n] 

Created conversion of /opt/intelmq/etc/runtime.conf and /opt/intelmq/etc/pipeline.conf. File located under /opt/intelmq/etc/runtime.yaml
```
This converts the old configurations of intelmq 2.x to the new runtime.yaml of intelmq 3.x.

**Note:** The converter was only for personal purposes. If you upgrade from 2.x to 3.x please use https://intelmq.readthedocs.io/en/maintenance/user/upgrade.html

## Fiddler
The fiddler tool, runs the bot with the given bot_id in a fake environment and outputs the generated messages in text format in the output folder.
This is to rerun messages without using the whole pipeline and also to be able to use debuggers for easier development.  

```bash
./intelmq-workbench.sh fiddler -i <bot_id>
```

**Note:** Can only run one bot at the time and is currently considered as working but buggy.

# Remarks
The tool is currently usable but not considered as final. 
Therefore the documentation is not complete. 
The commands have help support.

# Contribute

Please do contribute! Issues and pull requests are welcome.

# LICENSE

This software is licensed under GNU Affero General Public License version 3
