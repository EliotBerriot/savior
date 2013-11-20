# Presentation

Autosave is a tool built to automate these tasks :
- Create an archive of some files, using tar
- Create sql dumps of databases
- Send data via FTP to create a backup on a remote server
- Send a mail when the backup process is over

# Installation 

## Get the archive

## Install pip
If you already have it installed, you can jump to next step. 

[Pip](http://www.pip-installer.org/en/latest/) is a handy package manager for python.
Installation process is described [here](http://www.pip-installer.org/en/latest/installing.html)

On Debian-like distributions, you generally can do :
    sudo apt-get install python-pip

## Install dependencies

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

    

Once you're done, you can use autosave as follows:
cd path/to/autosave/folder
sudo fab autosave

This command will iterate through all your datasets and save them to a new directory (using current datestamp as name). 
Then, it will put this whole directory on your FTP server, and send you an email once it's done.

You can also save a specific dataset :
sudo fab save:another_dataset

It will only save another_dataset.

Autosave has an autosave.sh script you can use in your crontab : 
sudo crontab -e
And add the following lines to save your datasets everyday, on midnight :

# autosave
* 0 * * * /path/to/autosave/autosave.sh 

Contact and bug report
===========================
You can contact me for any question at contact@eliotberriot.com

