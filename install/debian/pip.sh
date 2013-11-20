#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )" 

echo "Installing PIP..."
sudo apt-get install python-pip

echo "downloading python dependencies..."
pip install -r $DIR/../python_requirements.txt