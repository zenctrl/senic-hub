# coding: utf-8
from os import path
from fabric import api as fab
from fabric.api import task, env


@task
def bootstrap(
        username='root',
        password='fooberific',
        authorized_keys='authorized_keys',
        **kw):
    """bootstrap a freshly booted nanopi NEO Air to make it ansible ready"""
    # (temporarily) set the user to the user set up during bootstrapping
    hostname = env.instance.uid
    env.host_string = '%s@%s' % (username, hostname)
    env.password = password
    if not path.isabs(authorized_keys):
        authorized_keys = path.join(
            env['config_base'],
            '..',
            authorized_keys)
    with fab.settings(warn_only=True):
        # enable passwordless root login via ssh
        fab.sudo("""mkdir /root/.ssh""")
        fab.sudo("""chmod 700 /root/.ssh""")
        fab.put(
            local_path=authorized_keys,
            remote_path='/root/.ssh/authorized_keys',
            use_sudo=True,
            mode='0700')
        fab.sudo("""chown root:root /root/.ssh/authorized_keys""")
        fab.sudo(
            """echo 'PermitRootLogin without-password' > /etc/ssh/sshd_config""")
        fab.sudo("""apt update""")
        fab.sudo("""apt upgrade -y""")
    fab.reboot()
