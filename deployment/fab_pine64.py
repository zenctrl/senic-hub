# coding: utf-8
from fabric import api as fab
from fabric.api import task, env


@task
def bootstrap():
    """bootstrap a freshly booted Pine64 to make it ansible ready"""
    # (temporarily) set the user to `ubuntu`
    env.host_string = 'ubuntu@%s' % env.instance.uid
    env.password = 'ubuntu'
    with fab.settings(warn_only=True):
        # enable passwordless root login via ssh
        fab.sudo("""mkdir /root/.ssh""")
        fab.sudo("""chmod 700 /root/.ssh""")
        fab.put(
            local_path='etc/authorized_keys',
            remote_path='/root/.ssh/authorized_keys',
            use_sudo=True,
            mode='0700')
        fab.sudo("""chown root:root /root/.ssh/authorized_keys""")
        fab.sudo(
            """echo 'PermitRootLogin without-password' > /etc/ssh/sshd_config""")
    fab.sudo("""/usr/local/sbin/resize_rootfs.sh""")
    fab.sudo("""/usr/local/sbin/pine64_update_uboot.sh""")
    fab.sudo("""/usr/local/sbin/pine64_update_kernel.sh""")
    fab.sudo("""apt-get install python -y""")
    fab.reboot()
