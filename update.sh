#!/bin/bash

echo "Updating main repo"
git pull > /dev/null
source venv/bin/activate
pip3 install -r requirements.txt 2>/dev/null > /dev/null
