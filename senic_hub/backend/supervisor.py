import xmlrpc.client


SUPERVISOR_URL = "http://127.0.0.1:9001"


_proxy = None


def get_supervisor_rpc_client():
    global _proxy

    if _proxy is None:
        _proxy = xmlrpc.client.ServerProxy("{0}/RPC2".format(SUPERVISOR_URL))

    return _proxy.supervisor


def restart_program(name):
    stop_program(name)
    start_program(name)


def program_status(name):
    return get_supervisor_rpc_client().getProcessInfo(name)['statename']


def stop_program(name):
    try:
        get_supervisor_rpc_client().stopProcess(name)
    except xmlrpc.client.Fault as e:
        # list of possible faults https://github.com/Supervisor/supervisor/blob/master/supervisor/xmlrpc.py#L27
        if e.faultCode in (40, 70):
            pass
        else:
            raise


def start_program(name):
    get_supervisor_rpc_client().startProcess(name)
