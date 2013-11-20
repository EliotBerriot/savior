#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )" 

echo "Installing all savior dependencies..."

bash $DIR/pip.sh
bash $DIR/filesystem.sh
bash $DIR/postgresql.sh
bash $DIR/mysql.sh
