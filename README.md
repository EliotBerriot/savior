# Presentation

[Savior](https://github.com/EliotBerriot/savior) is a tool built to automate these tasks :
- Create an archive of some files, using tar
- Create sql dumps of databases
- Send data via FTP to create a backup on a remote server
- Send a mail when the backup process is over

# Installation 

## Get savior

### via Git

    git clone https://github.com/EliotBerriot/savior.git
    
### via wget

    wget https://github.com/EliotBerriot/savior/archive/master.zip
    unzip master.zip
    mv savior-master savior
    rm master.zip
    

## Install pip
If you already have it installed, you can jump to next step. 

[Pip](http://www.pip-installer.org/en/latest/) is a handy package manager for python.
Installation process is described [here](http://www.pip-installer.org/en/latest/installing.html)

On Debian-like distributions, you generally can do :
    
    sudo apt-get install python-pip

## Install dependencies

First of all, move to savior directory:
    
    cd savior
    
Savior has a few [dependencies](requirements.txt). Install them by running:    
    
    sudo pip install -r requirements.txt
    
You're done ! You can now configure your savior instance and get it to work.

# Configuration
    
## settings.ini

Copy the provided [settings file](sample-settings.ini) and edit it with your very own informations:
    
    cp sample-settings.ini settings.ini
    nano settings.ini

All options are described in the file, read carefully ;)

## hosts.ini

Host file is used to log to FTP and database servers.
Copy the provided [hosts file](sample-hosts.ini) and edit it with your very own informations:
    
    cp sample-hosts.ini hosts.ini
    nano hosts.ini
    
All options are described in the file, read carefully ;)

As this file will contain sensitive informations, remember to secure it:
    
    chmod 750 hosts.ini
    
    
## Datasets

Savior use files under `datasets` directory to describe what need to be saved and how.
You can create your first dataset  with:
    
    cp datasets/examples/example datasets/my_first_dataset
    nano datasets/my_first_dataset
  
All options are described in the file, read carefully ;)

You can create as many datasets as you want, as long as you store them in `datasets` folder (files in subdirectories are not parsed).

# Usage

Once you're done with configuration, you can run the savior via command line. 
It's useful when you want to know if your configuration works as expected.

To get some help on available commands, just run:
    
    python savior.py --help

## Save

The save command is
    
    python savior.py save
    
It will:
    - save and backup all datasets (if needed)
    - clean old saves (if needed)
    - send a mail to admins
    
You can add options to this command:
    
    # force save process (days_between_save settings will be ignored)
    python savior.py save -f 
    
    # Save only my_dataset
    python savior.py save --datasets my_dataset 
    
    # Save my_dataset and my_other_dataset
    python savior.py save --datasets my_dataset my_other_dataset
    
    # Save my_dataset without sending mail
    python savior.py save --datasets my_dataset -nm 
    
 
## Purge

If, for some reason, you want to delete a bunch of saves, purge is the answer to your problem:
    
    # purge all datasets
    python savior.py purge
    
    # purge my_dataset
    python savior.py purge --datasets my_dataset
    
Use carefully !

## Clean

Clean will delete old saves from both local and remote server.
By default, clean is called after a successfull `save` command, so you should not need it.

Usage:
    
    # clean all datasets
    python savior.py clean

    # clean my_dataset
    python savior.py clean --datasets my_dataset
    
# Automating save process

The point of savior is to automate things. Command line is nice, but in most case, you'll want to use a crontab to save your datasets.
When you have checked via command line that your configuration works, you can add the following to your crontab:
    
    crontab -e 
    
    # add the following lines to save your datasets everyday, on midnight :
    # Savior
    * 0 * * * python /path/to/savior/savior.py save

# Contact and bug report

Feel free to send me any question or suggestion relative to savior via [Git repository](https://github.com/EliotBerriot/savior).

