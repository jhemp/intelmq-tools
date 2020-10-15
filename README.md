# intelmq-tools
Tools for intelmq. 
This tool will help you to check up on your running configurations and 
helps you to update them.

# Features
* Integrates custom bots into intelmq
* Checking the configurations for miss configurations
* Checking if the bots gotten new parameters
* Fixes discrepancies the bots configurations of IntelMQ
* Fixes missing new parameters of bots
* Listing all the bots and their configurations

# Requirements
- Installation of IntelMQ (see https://github.com/certtools/intelmq)
- Python3
- The custom bots need to be referenced in the python path

# Installation
Clone this repo somewhere on the system where the instance of IntelMQ resides.

Make intelmq_tools.py executable

**Optional:** Create a configuration file on basis of the config.ini_tmpl 

# Configuration
The tool needs a configuration file to find the base paths. 
There is a template in the config folder:
There are only two elements which needs configuration the table below will explain both:

|TAG|Description|
|---|---|
| binFolder  | The location of intelmq. Example /usr/bin  |
| customBotFolder | Location of the custom bots to be referenced. Example ./bot_folder |
| fakeRoot | Location of a fake root of a system. If this value is set the tool will be in development mode.  |

# Custom Bots
The custom Bots can now be stored anywhere. The folder where the custom bots reside must have the same 
structure as the one in IntelMQ (see the bot_folder as example). The folder of custom Bots must be present in the PYTHONPATH.
This is necessary for the execution.

The custom Bots require a config.json, 
which defines the default configuration of the bot. 
The configuration is similar as in IntelMQ.

# Usage examples
Here are some examples of use:

## Overview of the tools

```bash
$ ./intelmq_tools.py
usage: intelmq_tools.py [-h] [--version] [-d] [--bin BIN] [--bot BOT] [--fake FAKE] [--config CONFIG] [--verbose] {list,check,fix,install} ...

positional arguments:
  {list,check,fix,install}
                        Available tools
    list                Lists bots
    check               Check installation of bots is still applicable
    fix                 Tool for fixing bot configurations
    install             Tool for installing bots

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -d, --details         Details of intelmq and this tools
  --bin BIN             Location of the bin folder.
                        Default is /usr/bin
  --bot BOT             Location of the custom bots.
                        Note: The bots have to be in the path of python.
  --fake FAKE           Location of the root used for development.
                        Note: If this set the tool is automatically in dev mode.
  --config CONFIG       Optional configuration file
                        Note: The default location is ./config/config.ini
  --verbose, -v

```

**Note:**: If the config/config.ini is present the tool takes this file. 
The arguments --config or --bin and --bot are optional. However if one is set they take
priority.

## Listing of bots

```bash
$ ./intelmq_tools.py list -o

BOT Type:                Output
BOT Class:               UDP
Description:             UDP is a simple UDP bot responsible to send events to a udp port (e.g.: syslog daemon). For more explanations about the parameters field, checkout out the README.md
Module:                  intelmq.bots.outputs.udp.output
Entry Point:             intelmq.bots.outputs.udp.output:BOT.run
File:                    /opt/intelmq/intelmq/bots/outputs/udp/output.py
Running Instances        0

```

## Installing a bot

```bash
$ ./intelmq_tools.py install -i bots/experts/dummy/expert.py 

File /usr/bin/intelmq.bots.experts.dummy.expert created
Directory /opt/intelmq/intelmq/bots/experts/dummy created
BOT Class Restena NetworK was successfully inserted
```

**Note:** This command will create all required files for the bot like executable and also update the BOTS file with the configuration given in the bot's config.json

## Checking for differences in the configurations

```bash
$ ./intelmq_tools.py check -r
BOT Class:         Deduplicator
BOT Instance Name: deduplicator-expert
----------------------------------------
    Running Configuration is missing keys: ['redis_cache_password']
----------------------------------------

BOT Class:         Cymru Whois
BOT Instance Name: cymru-whois-expert
----------------------------------------
    Running Configuration is missing keys: ['overwrite']
----------------------------------------

BOT Class:         url2fqdn
BOT Instance Name: url2fqdn-expert
----------------------------------------
    Running Configuration has more keys:   ['load_balance']
----------------------------------------

BOT Class:         File
BOT Instance Name: file-output
----------------------------------------
    Running Configuration is missing keys: ['encoding_errors_mode', 'format_filename', 'keep_raw_field', 'message_jsondict_as_string', 'message_with_type']
----------------------------------------

```
## Fixing configurations

```bash
./intelmq_tools.py fix -r
Fixing runtime.conf File
Fixing deduplicator-expert:
Do you want to add Key redis_cache_password to Parameter parameters with default value None [y/N] y
Fixing cymru-whois-expert:
Do you want to add Key overwrite to Parameter parameters with default value False [y/N] y
Fixing url2fqdn-expert:
Do you want to remove Key load_balance from Parameter parameters [y/N] y
Fixing file-output:
Do you want to add Key encoding_errors_mode to Parameter parameters with default value strict [y/N] y
Do you want to add Key format_filename to Parameter parameters with default value False [y/N] y
Do you want to add Key keep_raw_field to Parameter parameters with default value False [y/N] y
Do you want to add Key message_jsondict_as_string to Parameter parameters with default value False [y/N] y
Do you want to add Key message_with_type to Parameter parameters with default value False [y/N] y
```
**Note:** with the -a option the tool automatically adds/removes keys. 
Keys which different values will not be taken into account. 

# Remarks
The tool is currently usable but not considered as final. 
Therefore the documentation is not complete. 
However the commands have help support.

# Contribute

Please do contribute! Issues and pull requests are welcome.

# LICENSE

This software is licensed under GNU Affero General Public License version 3
