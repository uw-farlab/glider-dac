from fabric.api import *
from fabric.contrib.files import *
import os
from copy import copy
import time

"""
    Call this with fab -c .fab TASK to pick up deploy variables
    Required variables in .fab file:
        mail_server = x
        mail_port = x
        mail_username = x
        mail_password = x
        mail_default_sender = x
        mailer_debug = x
        mail_default_to = x
        mail_default_list = x
        webpass = x
        secret_key = x
        data_root = x
        rsync_ssh_user = x
        rsync_to_host = x
        rsync_to_path = x
"""

env.user = "gliderweb"
code_dir = "/home/gliderweb/glider-mission"
env.hosts = ['ftp.gliders.ioos.us']

def admin():
    env.user = "dfoster"
def gliderweb():
    env.user = "gliderweb"

def deploy():
    stop_supervisord()

    gliderweb()
    with cd(code_dir):
        run("git pull origin master")
        update_supervisord()
        update_libs()
        start_supervisord()
        run("supervisorctl -c ~/supervisord.conf start all")

        update_supervisord_perms_monitor()
        update_libs_perms_monitor()
        start_supervisord_perms_monitor()
        with prefix("workon root-monitor"):
            sudo("supervisorctl -c /root/supervisord-perms-monitor.conf start all")

    restart_nginx()

def update_supervisord():
    gliderweb()
    run("pip install supervisor")
    upload_template('deploy/supervisord.conf', '/home/gliderweb/supervisord.conf', context=copy(env), use_jinja=True, use_sudo=False, backup=False, mirror_local_mode=True)

def update_supervisord_perms_monitor():
    admin()
    with prefix("workon root-monitor"):
        sudo("pip install supervisor")
        upload_template("deploy/supervisord-perms-monitor.conf",
                        "/root/supervisord-perms-monitor.conf",
                        context=copy(env),
                        use_jinja=True,
                        use_sudo=True,
                        backup=False,
                        mirror_local_mode=True)

def update_libs():
    gliderweb()
    with cd(code_dir):
        with settings(warn_only=True):
            run("pip install -r requirements.txt")

def update_libs_perms_monitor():
    admin()
    with cd(code_dir):
        with settings(warn_only=True):
            with prefix("workon root-monitor"):
                sudo("pip install -r requirements.txt")

def restart_nginx():
    admin()
    sudo("/etc/init.d/nginx restart")

def supervisord_restart():
    stop_supervisord()
    start_supervisord()

def supervisord_perms_monitor_restart():
    stop_supervisord_perms_monitor()
    start_supervisord_perms_monitor()

def stop_supervisord():
    gliderweb()
    with cd(code_dir):
        with settings(warn_only=True):
            run("supervisorctl -c ~/supervisord.conf stop all")
            run("kill -QUIT $(ps aux | grep supervisord | grep -v grep | awk '{print $2}')")

    kill_pythons()

def kill_pythons():
    admin()
    with settings(warn_only=True):
        sudo("kill -QUIT $(ps aux | grep python | grep -v supervisord | awk '{print $2}')")

def stop_supervisord_perms_monitor():
    admin()
    with settings(warn_only=True):
        with prefix("workon root-monitor"):
            sudo("supervisorctl -c /root/supervisord-perms-monitor.conf stop all")
            sudo("kill -QUIT $(ps aux | grep supervisord | grep -v grep | awk '{print $2}')")

def start_supervisord():
    gliderweb()
    with cd(code_dir):
        with settings(warn_only=True):
            run("supervisord -c ~/supervisord.conf")

def start_supervisord_perms_monitor():
    admin()
    with settings(warn_only=True):
        with prefix("workon root-monitor"):
            sudo("supervisord -c /root/supervisord-perms-monitor.conf")

