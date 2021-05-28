CHANGELOG
==========

0.4
----------
- Adapted code to work with intelmq 2.3.2 and the new dev format
  - Remark: IntelMQ 3.0.0 does not have a BOTS, runtime.conf, aso anymore
- Custom Bot configuration parameters can be specified in config.json or in the class itself.
  - Remark: The parameters specified in the class have priority over the config.json or default BOTS
- Added possibility to install and uninstall default intelmq bots
- Fixing elements works on all fields of BOTS
- Fixer removes double definition of the same bot module in BOTS
- Removed python3.6 for execution script

0.3
----------
- Fixed had coded version
- Refactored code
- Bots are not integrated into intelmq anymore, but only referenced in the configurations
- Added new parameters for configuration purposes
- "module" in config.json is not used anymore
- Installer will not install bots code files into intelmq they must be kept separately

0.2
----------
- Added example bot folder
- Fixed location issue

0.1
----------
- Initial Release