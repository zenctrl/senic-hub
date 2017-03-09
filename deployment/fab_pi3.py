# coding: utf-8
from os import path
from fabric import api as fab
from fabric.api import task, env
from ploy.common import shjoin

AV = None

eth_interface = """auto {eth_iface}
interface {eth_iface}
static ip_address={eth_ip}/{eth_netmask}
static routers={eth_gateway}
static domain_name_servers={eth_dns}
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
    env.host_string = 'pi@%s' % hostname
    env.password = 'raspberry'
    fab.sudo("""apt update""")
    fab.sudo("""apt upgrade -y""")
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
def sync_app_src():
    get_vars()
    with fab.lcd('../application'):
        env.instance.config['user'] = AV['build_user']
        target = '/home/{build_user}/nuimo-hub-backend/application'.format(**AV)
        rsync('-rlptD', '--exclude', '.*', '--exclude', 'venv', '.', '{host_string}:%s' % target)

@task
def sync_frontend_src():
    get_vars()
    with fab.lcd('../frontend'):
        env.instance.config['user'] = AV['build_user']
        target = '/home/{build_user}/nuimo-hub-backend/frontend'.format(**AV)
        rsync('-rlptD', '--exclude', '.*', '--exclude', 'node_modules', '.', '{host_string}:%s' % target)
