#!/bin/bash
if [ ! -d "intelmqworkbench" ]; then
  ln -s src/intelmqworkbench .
  ./update.sh
fi

source venv/bin/activate
cd src
python3 intelmqworkbench.py "$@"
cd ..
