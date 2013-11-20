 # -*- coding: utf-8 -*-

from fabric.api import local, run, cd, env, prefix
import env_settings
REMOTE_WORKING_DIR = env_settings.REMOTE_WORKING_DIR

env.hosts = env_settings.HOSTS
env.user = env_settings.USER


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