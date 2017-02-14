# coding: utf-8
from os import path
from fabric import api as fab
from fabric.api import task, env
from ploy.config import value_asbool

eth_interface = """auto {eth_iface}
iface {eth_iface} inet static
  address {eth_ip}
  netmask {eth_netmask}
  gateway {eth_gateway}
  dns-nameservers {eth_dns}
"""


@task
def bootstrap(boot_ip=None, authorized_keys='authorized_keys', static_ip=True):
    """bootstrap a freshly booted Raspberry PI 3 to make it ansible ready"""
    # (temporarily) set the user to `pi`
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
        if value_asbool(static_ip):
            fab.sudo('rm /etc/network/interfaces.d/50-cloud-init.cfg')
            fab.sudo(
                'echo """%s""" > /etc/network/interfaces.d/%s.cfg' %
                (eth_interface.format(**AV), AV['eth_iface']))
            # disable cloud init
            fab.put(
                local_path='pi3_cloud.cfg',
                remote_path='/etc/cloud/cloud.cfg',
                use_sudo=True,
                mode='0644')
        # enable passwordless root login via ssh
        fab.put(
            local_path=authorized_keys,
            remote_path='/root/.ssh/authorized_keys',
            use_sudo=True,
            mode='0700')
        fab.sudo("""chown root:root /root/.ssh/authorized_keys""")
    fab.sudo("""apt update""")
    fab.sudo("""apt upgrade -y""")
    fab.sudo("""apt install python2.7-minimal -y""")
    fab.reboot()
