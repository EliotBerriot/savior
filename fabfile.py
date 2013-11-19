 # -*- coding: utf-8 -*-
import sys, os

from main import Savior, ParseConfigError
from fabric.api import local, run, cd, env, prefix
import logging
import env_settings
REMOTE_WORKING_DIR = env_settings.REMOTE_WORKING_DIR

env.hosts = env_settings.HOSTS
env.user = env_settings.USER

logger = logging.getLogger('savior')
logger.setLevel(logging.DEBUG)
def autosave(datasets="all", force_save=False):
    try:
        a = Savior(datasets, force_save)
        a.save()
    except ParseConfigError, e:
        logger.critical("Could not save datasets {0}".format(datasets))
        
def clean(datasets="all", force_save=False): # remove saves that are too old
    try:
        a = Savior(datasets, force_save)
        a.clean()
    except ParseConfigError, e:
        logger.critical("Could not save datasets {0}".format(datasets))

def purge(datasets="all", force_save=False): # remove all saves
    try:
        a = Savior(datasets, force_save)
        a.purge()
    except ParseConfigError, e:
        logger.critical("Could not save datasets {0}".format(datasets))

def push(branch='master', remote='origin', runlocal=True):
    if runlocal:
        # lance la commande en local
        local("git push %s %s" % (remote, branch))
    else:
        # lance la commande sur les serveurs de la liste eng.hosts
        run("git push %s %s" % (remote, branch))
 
def pull(branch='master', remote='origin', runlocal=True):
    if runlocal:
        local("git pull %s %s" % (remote, branch))
    else:
        run("git pull %s %s" % (remote, branch))
 
def sync(branch='master', remote='origin', runlocal=True):
    pull(branch, remote, runlocal)
    push(branch, remote, runlocal)
 
def deploy(branch='master', remote='origin'):
    # execute toutes les commandes dans ce dossier
    with cd(REMOTE_WORKING_DIR):
        # excute toutes les commandes avec celle-ci avant
        pull(branch, remote, False)