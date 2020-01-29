# intelmq-tools
Tools for intelmq. This tool will help you to check up on your running configurations and hels you to update them.

# Features
* Installing and un installing of custom bots bots
* Checking the configurations for missconfigurations
* Fixing missconfigurations
* Listing all the bots and their configurations

# Requirements
- Installation of IntelMQ (see https://github.com/certtools/intelmq)
- Python3

# Installation
Clone this repo somewhere on the system where intel mq is installed.

# Configuration
The tool needs a configuration file to find the base paths. There is a template in the config folder:
There are only two elements which needs configuration the table below will explain both:

|TAG|Description|
|---|---|
| intelMQLocation  | The location of intelmq. Example /lib/python3.6/site-packages/intelmq/bots  |
|  entryPointsLocation | Location of the entry_point file. Example /lib/python3.6/site-packages/intelmq-2.1.1-py3.6.egg-info/entry_points.txt  |

# Custom Bots
The custom bots, need to be stored in the "bots" folder in the same directory as the tool and the setup of the internal folders should follow the same structure as of the original one from intelmq.

The only difference is that the bots require a config.json, which defines the default configuration of the bot. The configuration is the same as in intelmq.

Feel free to check see the dummy bot in the given folder as example.

# Usage examples
Here are some examples of use:

* Overview of the tools

```bash
$ ./intelmq_tools.py
usage: intelmq_tools.py [-h] [--version] [-d] [--dev]
                        {fix,install,list,check} ...

positional arguments:
  {fix,install,list,check}
                        Available tools
    fix                 Tool for fixing bot configurations
    install             Tool for installing bots
    list                Lists bots
    check               Check installation of bots is still applicable

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -d, --details         Details of intelmq and this tools
  --dev                 Development

```

* Listing of bots

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

* Installing a bot

```bash
$ ./intelmq_tools.py install -i bots/experts/dummy/expert.py 

File /usr/bin/intelmq.bots.experts.dummy.expert created
Directory /opt/intelmq/intelmq/bots/experts/dummy created
BOT Class Restena NetworK was successfully inserted
```

NOTE: This command will create all required files for the bot like executable and also update the BOTS file with the configuration given in the bot's config.json

* Checking for differences in the configurations

```bash
$ ./intelmq_tools.py check --dev -r
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

# Remarks
The tool is currently usable but not considered as final. Therefore the documentation is not complete. However the commands have help support.

# Contribute

Please do contribute! Issues and pull requests are welcome.

# LICENSE

This software is licensed under GNU Affero General Public License version 3
