# coding: utf-8
from os import path
from fabric import api as fab
from fabric.api import task, env

eth_interface = """auto {eth_iface}
interface {eth_iface}
static ip_address={eth_ip}/{eth_netmask}
static routers={eth_gateway}
static domain_name_servers={eth_dns}
"""


@task
def bootstrap(boot_ip=None, authorized_keys='authorized_keys', static_ip=False):
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
    env.host_string = 'pi@%s' % hostname
    env.password = 'raspberry'
    AV = env.instance.get_ansible_variables()
    AV.setdefault('eth_ip', final_ip)
    AV.setdefault('eth_iface', 'eth0')
    AV.setdefault('eth_netmask', '24')
    AV.setdefault('eth_gateway', '192.168.1.1')
    AV.setdefault('eth_dns', '8.8.8.8')
    with fab.settings(warn_only=True):
        if static_ip:
            fab.sudo(
                'echo """%s""" >> /etc/dhcpcd.conf' %
                eth_interface.format(**AV))
        # enable passwordless root login via ssh
        fab.sudo("""mkdir /root/.ssh""")
        fab.sudo("""chmod 700 /root/.ssh""")
        fab.put(
            local_path=authorized_keys,
            remote_path='/root/.ssh/authorized_keys',
            use_sudo=True,
            mode='0700')
        fab.sudo("""chown root:root /root/.ssh/authorized_keys""")
    fab.sudo("""apt update""")
    fab.sudo("""apt upgrade -y""")
    fab.reboot()
