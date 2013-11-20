# Presentation

[Savior](https://github.com/EliotBerriot/savior) is a tool built to automate these tasks :
- Create an archive of some files, using tar
- Create sql dumps of databases
- Send data via FTP to create a backup on a remote server
- Send a mail when the backup process is done

As I did not found a simple tool to achieve these tasks the way I want, I created it.

# Philosophy

Savior works as follow:
    1. You define your settings : save recurrency, number of save to keep, etc.
    2. You define your hosts:
        - FTP servers on which you want to backup your files
        - Database server you want to save
    3. You define some datasets. A dataset is a collection of files and/or databases you want to save together
    
Savior is designed to be as flexible as possible. This mean you can override most global settings in datasets configuration.

This allow you to have two datasets with different save settings, for exemple:
    - "important_website" dataset, collecting production MySQL database and website PHP files, that saves every day, keeping 10 last saves on 3 different FTP servers
    - "apache_configuration" dataset that saves your apache config every week, keeping 2 saves on 2 different FTP servers
    
You can save as many datasets as you want, the only limit is available space on your hard drives.
On FTP servers, datasets will be stored  like this :
    
    /your/save/path
    |-- important_website
    |   |-- 2013-11-19--17h54
    |   |   |-- application.tar
    |   |   |-- base_prod.sql
    |   |   `-- base_test.sql
    |   `-- 2013-11-20--17h54
    |       |-- application.tar
    |       |-- base_prod.sql
    |       `-- base_test.sql
    `-- apache_configuration
        `-- 2013-11-19--17h54
            `-- files.tar
        `-- 2013-11-20--17h54
            `-- files.tar
# Installation 

## Get savior

### via Git

    git clone https://github.com/EliotBerriot/savior.git
    
### via wget

    wget https://github.com/EliotBerriot/savior/archive/master.zip
    unzip master.zip
    mv savior-master savior
    rm master.zip
    
You got it ! Remember to cd in this directory :
    
    cd savior
    
## Prepare your system

Depending on your needs, you will have to install [some packages](install/system_requirements.md) on your machine.

### The easy way

To install all dependencies, on Debian-like distributions, you can run:
    
    bash install/debian/full.sh
    
This will install both system packages and python packages
    
### The precise way

If you want to install only the packages you will need, have a look at scripts inside `install/yourdistribution`:
    
    bash install/yourdistribution/pip.sh    # to install only pip and python packages
    bash install/yourdistribution/mysql.sh  # to install only mysql libraries
    # etc...
    
If you only need to install [python packages](install/requirements.txt), just run :
    
    pip install -r install/python_requirements.txt
    
### The 'my distribution is not listed' way

In this case, you're on your own. Requirements are listed under [install/system_requirements.md](install/system_requirements.md)
If you want to help, you're welcome !
    
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
    
    # add the following lines at the end to save your datasets everyday, on midnight :
    # Savior
    * 0 * * * python /path/to/savior/savior.py save /dev/null 2>&1

Sometimes, you may meet permissions problems when backing up files from local system.
In this case, one solution is to run the save process as root :
    
    sudo crontab -e
    
    # add the following lines at the end to save your datasets everyday, on midnight :
    # Savior
    * 0 * * * python /path/to/savior/savior.py save /dev/null 2>&1
    

# Contact, help and bug report

If you want to improve savior, your help is welcome.
Feel free to send me any question or suggestion relative to savior via [Git repository](https://github.com/EliotBerriot/savior). 
If you don't have a github account, we can't get in contact via email : contact@eliotberriot.com.



