import json

BALANCE_FILE = '/opt/balance/balance.json'
BALANCE = json.load(open(BALANCE_FILE))

class UNIT:
    INFANTRY = 'infantryBot'
    ROCKET = 'rocketBot'
    HEAVY = 'heavyBot'

def players(
        elements,
        is_stream=False,
        is_attack=True,
        def_codes=None,
        attack_codes=None,
        ):

    if not def_codes:
        def_codes = {}
    if not attack_codes:
        attack_codes = {}

    return {
        'codes': {
            '0': def_codes,
            '1': attack_codes,
        },
        'interface': {
            'player_id': int(is_attack)
        },
        'is_stream': is_stream,
        'map_elements': elements,
        'map_size': [40, 40],
        'players': [
            {'defeat': ['center'], 'env_name': 'python_3', 'id': 0, 'user_id': 14},
            {'defeat': ['units', 'time'], 'env_name': 'python_3', 'id': 1, 'user_id': 24}
        ],
        'rewards': {
            'resources': {
                'adamantite':  100,
                'crystalite': 100,
            }
        },
        'time_limit': 30
    }

def building(
        b_type,
        position,
        level=1,
        ):
    return {
        'level': level,
        'player_id': 0,
        'status': 'idle',
        'tile_position': position,
        'type': b_type,
    }

def def_building(code, *args, **kwargs):
    modules = kwargs.pop('modules', [])
    data = building(*args, **kwargs)
    data.update({
        'code': code,
        'modules': modules,
    })
    return data

def attack_craft(
        craft_id,
        code,
        unit_type=UNIT.INFANTRY,
        unit_level=1,
        unit_quantity=1,
        modules=None,
        craft_level=1,
        ):
    if not modules:
        modules = []

    return {
        'code': code,
        'craft_id': craft_id,
        'level': craft_level,
        'player_id': 1,
        'type': 'craft',
        'modules': modules,
        'unit': {
            'level': unit_level,
            'type': unit_type
        },
        'unit_quantity': unit_quantity,
    }

def command_center(*args, **kwargs):
    return building('commandCenter', *args, **kwargs)

def crystalite_silo(*args, **kwargs):
    return building('crystaliteSilo', *args, **kwargs)

def crystalite_farm(*args, **kwargs):
    return building('crystaliteFarm', *args, **kwargs)

def adamantite_storage(*args, **kwargs):
    return building('adamantiteStorage', *args, **kwargs)

def flex_storage(*args, **kwargs):
    return building('titaniumStorage', *args, **kwargs)

def flex_lab(*args, **kwargs):
    return building('titaniumLab', *args, **kwargs)

def vault(*args, **kwargs):
    return building('vault', *args, **kwargs)

def electronic(*args, **kwargs):
    return building('electronic', *args, **kwargs)

def laboratory(*args, **kwargs):
    return building('laboratory', *args, **kwargs)

def bots(*args, **kwargs):
    return building('bots', *args, **kwargs)

def radar(*args, **kwargs):
    return building('radar', *args, **kwargs)

def garbage(*args, **kwargs):
    return building('garbage', *args, **kwargs)

def flagman(*args, **kwargs):
    return building('flagman', *args, **kwargs)

def sentry_gun(code, *args, **kwargs):
    return def_building(code, 'sentryGun', *args, **kwargs)

def machine_gun(code, *args, **kwargs):
    return def_building(code, 'machineGun', *args, **kwargs)

def rocket_gun(code, *args, **kwargs):
    return def_building(code, 'rocketGun', *args, **kwargs)

