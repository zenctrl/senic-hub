# coding: utf-8
from os import path
from fabric import api as fab
from fabric.api import task, env

eth_interface = """auto {eth_iface}
iface {eth_iface} inet static
  address {eth_ip}
  netmask {eth_netmask}
  gateway {eth_gateway}
"""

eth_resolvconf = """nameserver {eth_dns}
"""


@task
def bootstrap(boot_ip=None, authorized_keys='authorized_keys'):
    """bootstrap a freshly booted Pine64 to make it ansible ready"""
    # (temporarily) set the user to `ubuntu`
    if not path.isabs(authorized_keys):
        authorized_keys = path.join(
            env['config_base'],
            '..',
            authorized_keys)
    final_ip = env.instance.config['ip']
    if boot_ip:
        env.instance.config['ip'] = boot_ip
    hostname = env.instance.uid
    env.host_string = 'ubuntu@%s' % hostname
    env.password = 'ubuntu'
    AV = env.instance.get_ansible_variables()
    AV.setdefault('eth_ip', final_ip)
    AV.setdefault('eth_iface', 'eth0')
    AV.setdefault('eth_netmask', '255.255.255.0')
    AV.setdefault('eth_gateway', '192.168.1.1')
    AV.setdefault('eth_dns', '8.8.8.8')
    with fab.settings(warn_only=True):
        fab.sudo(
            'echo """%s""" > /etc/network/interfaces.d/%s' %
            (eth_interface.format(**AV), AV['eth_iface']))
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
    fab.sudo("""/usr/local/sbin/resize_rootfs.sh""")
    fab.sudo("""/usr/local/sbin/pine64_update_uboot.sh""")
    fab.sudo("""/usr/local/sbin/pine64_update_kernel.sh""")
    fab.sudo("""apt-get install python -y""")
    # finally override DNS
    fab.sudo('echo """%s""" > /etc/resolvconf/resolv.conf.d/tail' % eth_resolvconf.format(**AV))
    fab.reboot()
