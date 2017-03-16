import xmlrpc.client


SUPERVISOR_URL = "http://127.0.0.1:9001"


_proxy = None


def get_supervisor_rpc_client():
    global _proxy

    if _proxy is None:
        _proxy = xmlrpc.client.ServerProxy("{0}/RPC2".format(SUPERVISOR_URL))

    return _proxy.supervisor


def restart_program(name):
    supervisor = get_supervisor_rpc_client()
    supervisor.stopProcess(name)
    supervisor.startProcess(name)
