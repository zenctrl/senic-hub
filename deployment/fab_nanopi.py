# coding: utf-8
from fabric import api as fab
from fabric.api import task, env
from ploy.common import shjoin

AV = None



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
            '--exclude', '.*',
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

