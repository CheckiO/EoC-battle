
CLIENT = None


def set_client(client):
    global CLIENT
    CLIENT = client


def client_request(data):
    if CLIENT is None:
        return {}
    data['status'] = 'success'  # OMFG
    return CLIENT.request(data)

# ASKS


def ask(what, data=None):
    return client_request({'do': 'ask', 'what': what, 'data': data})


def ask_initials():
    return ask('initial')


def ask_nearest_enemy():
    return ask('nearest_enemy')

# SUBSCRIBTIONS

SUBSCRIBTIONS = {}
NEXT_SUBSCRIBE_ID = 1


def subscribe(what, function, data=None):
    return CLIENT.subscribe(what, function, data)


def subscribe_unit_in_my_range(radius, function):
    return subscribe('unit_in_my_range', function, {'radius': radius})


def subscribe_death_sysid(sysid, function):
    return subscribe('death_sysid', function, {'sysid': sysid})


# DOs

def do(what, data=None):
    return client_request({'do': 'do', 'what': what, 'data': data})


def do_attack_sysid(sysid):
    return do('attack', {'sysid': sysid})
