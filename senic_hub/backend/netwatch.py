#!/usr/bin/python3

import click
import dbus
import dbus.mainloop.glib
import logging
import time
import xmlrpc.client

import NetworkManager
try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject

from .supervisor import start_program, stop_program

logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
@click.option('--wlan', '-w', required=False, help="WLAN device (default = wlan0)")
def netwatch_cli(ctx, wlan):
    if not wlan:
        wlan = 'wlan0'
    ctx.obj = NetwatchSupervisor(wlan)


@netwatch_cli.command(name='start', help="start Netwatch supervisor")
@click.option('--verbose', '-v', count=True, help="Print info messages (-vv for debug messages)")
@click.pass_context
def netwatch_start(ctx, verbose):
    log_format = '%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s'
    if verbose >= 2:
        logging.basicConfig(level=logging.DEBUG, format=log_format)
    elif verbose >= 1:
        logging.basicConfig(level=logging.INFO, format=log_format)
    else:
        logging.basicConfig(level=logging.WARNING, format=log_format)
    ctx.obj.run()


class NetwatchSupervisor(object):
    """
    Watches for changes in the network connection.
    If the connection is down, Bluenet will be started to be able to use the setup app
    to configure the Wifi connection and nuimo_app will be stopped because the setup app can
    only connect if there are no Nuimos connected.
    If the connection is back up, the nuimo_app will be restarted.
    """

    def __init__(self, wlan_adapter):
        """
        Initializes the object. It can then be started with run().
        :param wlan_adapter: name of the WLAN adapter (i.e. 'wlan0')
        """
        self._wlan_adapter = wlan_adapter
        self._bluenet_is_running = False
        self._nuimo_app_is_running = False
        self._bluenet_rpc = xmlrpc.client.ServerProxy('http://127.0.0.1:6459')

    def run(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        # check initial status:
        state = NetworkManager.NetworkManager.State
        self._on_state_changed(None, state)

        # listen for changes:
        NetworkManager.NetworkManager.OnStateChanged(self._on_state_changed)
        logger.debug("Start listening to network status changes")
        loop = GObject.MainLoop()
        loop.run()

    def _on_state_changed(self, nm, state, **kwargs):
        logger.info("State changed to %d: %s" % (state, NetworkManager.const('STATE', state)))
        if state >= NetworkManager.NM_STATE_CONNECTED_GLOBAL:
            self._switch_to_normal_mode()
        elif state <= NetworkManager.NM_STATE_DISCONNECTED:
            self._switch_to_provisioning_mode()

    def _switch_to_normal_mode(self):
        while (self._bluenet_is_connected() and
                NetworkManager.NetworkManager.State >= NetworkManager.NM_STATE_CONNECTED_LOCAL):
            logger.debug("Waiting before leaving provisioning mode till setup app is disconnected...")
            time.sleep(5)

        if NetworkManager.NetworkManager.State < NetworkManager.NM_STATE_CONNECTED_LOCAL:
            logger.debug("Staying in provisioning mode because connection is lost again")
            return

        logger.debug("Normal mode: Stopping Bluenet and starting nuimo_app")
        try:
            stop_program('bluenet')
        except xmlrpc.client.Fault as e:
            logger.warning("Error while stopping Bluenet: %s" % str(e))

        try:
            start_program('nuimo_app')
        except xmlrpc.client.Fault as e:
            if e.faultCode == 60:
                logger.debug("nuimo_app is already running")
                pass
            else:
                logger.warning("Error while starting nuimo_app: %s" % str(e))

    def _switch_to_provisioning_mode(self):
        logger.debug("Provisioning mode:  Stopping nuimo_app and starting Bluenet")
        try:
            stop_program('nuimo_app')
        except xmlrpc.client.Fault as e:
            logger.warning("Error while stopping nuimo_app: %s" % str(e))

        try:
            start_program('bluenet')
        except xmlrpc.client.Fault as e:
            if e.faultCode == 60:
                logger.debug("Bluenet is already running")
            else:
                logger.warning("Error while starting bluenet: %s" % str(e))

    def _bluenet_is_connected(self):
        try:
            return self._bluenet_rpc.bluenet_is_connected()
        except OSError:
            # -> connection refused because bluenet is not even running
            return False
        except (xmlrpc.client.Fault, OSError) as e:
            logger.warning("Couldn't check if Bluenet is connected: %s" % str(e))
        return False


if __name__ == '__main__':
    netwatch_cli()
