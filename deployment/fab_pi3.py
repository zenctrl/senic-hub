# coding: utf-8
from os import path
from fabric import api as fab
from fabric.api import task, env
from ploy.common import shjoin

AV = None

eth_interface = """
auto {eth_iface}
iface {eth_iface} inet static
  address {eth_ip}
  netmask {eth_netmask}
  gateway {eth_gateway}
"""


@task
def bootstrap(boot_ip=None, authorized_keys='authorized_keys', configure_ethernet="yes"):
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
    fab.sudo("""apt update""")
    fab.sudo("""apt upgrade -y""")
    AV = env.instance.get_ansible_variables()
    # TODO: Move defaults into ploy.conf
    AV.setdefault('eth_ip', final_ip)
    AV.setdefault('eth_iface', 'eth0')
    AV.setdefault('eth_netmask', '255.255.255.0')
    AV.setdefault('eth_gateway', '192.168.1.1')
    AV.setdefault('eth_dns', '8.8.8.8')
    with fab.settings(warn_only=True):
        fab.sudo("systemctl stop dhcpcd")
        fab.sudo("systemctl disable dhcpcd")
        if configure_ethernet == "yes":
            eth_config = eth_interface.format(**AV)
            fab.sudo('echo """%s""" > /etc/network/interfaces.d/%s' %
                (eth_config, AV['eth_iface']))
            fab.sudo('echo "source-directory /etc/network/interfaces.d" > /etc/network/interfaces')
            fab.sudo('echo "nameserver %s" | resolvconf -a %s' %
                (AV['eth_gateway'], AV['eth_iface']))
        # enable passwordless root login via ssh
        fab.sudo("""mkdir -p /root/.ssh""")
        fab.sudo("""chmod 700 /root/.ssh""")
        fab.put(
            local_path=authorized_keys,
            remote_path='/root/.ssh/authorized_keys',
            use_sudo=True,
            mode='0700')
        fab.sudo("""chown root:root /root/.ssh/authorized_keys""")
    fab.reboot()


def get_vars():
    global AV
    if AV is None:
        hostname = env.host_string.split('@')[-1].split('-')[1]
        AV = dict(hostname=hostname, **env.instances[hostname].get_ansible_variables())
    return AV


@task
def rsync(*args, **kwargs):
    """ wrapper around the rsync command.
        the ssh connection arguments are set automatically.
        any args are just passed directly to rsync.
        you can use {host_string} in place of the server.
        the kwargs are passed on the 'local' fabric command.
        if not set, 'capture' is set to False.
        example usage:
        rsync('-pthrvz', "{host_string}:/some/src/directory", "some/destination/")
    """
    kwargs.setdefault('capture', False)
    replacements = dict(
        host_string="{user}@{host}".format(
            user=env.instance.config.get('user', 'root'),
            host=env.instance.config.get(
                'host', env.instance.config.get(
                    'ip', env.instance.uid))))
    args = [x.format(**replacements) for x in args]
    ssh_info = env.instance.init_ssh_key()
    ssh_info.pop('host')
    ssh_info.pop('user')
    ssh_args = env.instance.ssh_args_from_info(ssh_info)
    cmd_parts = ['rsync']
    cmd_parts.extend(['-e', "ssh %s" % shjoin(ssh_args)])
    cmd_parts.extend(args)
    cmd = shjoin(cmd_parts)
    return fab.local(cmd, **kwargs)


@task
def sync_src():
    get_vars()
    with fab.lcd('..'):
        destination = '/home/%s/senic-hub' % AV['build_user']
        fab.sudo('mkdir -p %s' % destination, user=AV['build_user'])
        rsync(
            '-rlptvD',
            '--exclude', '.tox',
            '--exclude', '*.egg-info',
            '--exclude', '__pycache__',
            '--exclude', 'node_modules',
            '--exclude', '/build',
            '--exclude', '/deployment',
            '--exclude', '/dist',
            '--exclude', '/docs',
            '--exclude', '/venv',
            '.',
            '{host_string}:%s' % destination)

@task
def sync_ha_src():
    get_vars()
    with fab.lcd('../../home-assistant'):
        destination = '/home/%s/home-assistant' % AV['build_user']
        fab.sudo('mkdir -p %s' % destination, user=AV['build_user'])
        rsync(
            '-rlptvD',
            '--exclude', '.*',
            '--exclude', '*.egg-info',
            '--exclude', '__pycache__',
            '--exclude', '/dist',
            '--exclude', '/docs',
            '--exclude', '/venv',
            '.',
            '{host_string}:%s' % destination)

@task
def sync_soco_src():
    get_vars()
    with fab.lcd('../../SoCo'):
        destination = '/home/%s/SoCo' % AV['build_user']
        fab.sudo('mkdir -p %s' % destination, user=AV['build_user'])
        rsync(
            '-rlptvD',
            '--exclude', '.*',
            '--exclude', '*.egg-info',
            '--exclude', '__pycache__',
            '--exclude', '/dist',
            '--exclude', '/docs',
            '--exclude', '/venv',
            '.',
            '{host_string}:%s' % destination)
