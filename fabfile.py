
from fabric.operations import prompt, sudo
from fabric.api import local, run, cd, env, prefix
import os 
REMOTE_WORKING_DIR = """/home/eliotberriot/savior"""
WORKING_DIR=os.path.dirname(os.path.realpath(__file__))
HOSTS = {
    "kimsufi": "176.31.98.11",
    "vps1": "62.4.11.92",
    "larcenet": "188.165.214.186:666"
    }

env.hosts = [HOSTS["larcenet"]]
env.user = 'eliotberriot'
shell = '/bin/bash'
shell_wrapper="/bin/bash -l -c "


    
def start_dev():
    local('sass --watch "{0}":"{0}"'.format(WORKING_DIR))
def switch(host="kimsufi"):
    """
        Allow you to switch between hosts
    """
    try:
        env.hosts = [HOSTS[host]]
        print("Host is now {0}".format(env.hosts))
    except KeyError:
        print("Host {0} does not exist in HOSTS setting".format(host))
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
        pull(branch, remote, False)
        
def fast_commit(message):
    local("git add .")
    local('git commit -m "{0}"'.format(message))
    sync()
    deploy()