ATTACKER_CODE_INFANTRY = """
from battle import commander
craft_client = commander.CraftClient()
craft_client.do_land_units([40,2])

def unit_depart(data):
    unit_client = commander.UnitClient(data['id'])
    unit_client.do_depart()

def unit_travel(data):
    unit_client = commander.UnitClient(data['id'])
    unit_client.do_move([36,6])
    #unit_client.when_im_idle(unit_depart)

craft_client.when_unit_landed(unit_travel)
"""

DEF_CODE_SENTRY_GUN = """
from battle import commander
tower_client = commander.Client()

def unit_in_firing_range(data):
    tower_client.do_attack(data['id'])

tower_client.when_enemy_in_range(unit_in_firing_range)
"""

PLAYERS = {
    'codes': {
        '0': {
            'def_code_sentry_gun.py': DEF_CODE_SENTRY_GUN,
        },
        '1': {
            'attacker_infantry.py': ATTACKER_CODE_INFANTRY,
        },
    },
    'interface': {
        'player_id': 0
    },
    'is_stream': True,
    'map_elements': [
        {
            'level': 1,
            'player_id': 0,
            'status': 'idle',
            'tile_position': [20, 18],
            'type': 'commandCenter'
        },
        {
            'code': 'def_code_sentry_gun.py',
            'level': 5,
            'player_id': 0,
            'status': 'idle',
            'tile_position': [32, 12],
            'modules': [
            ],
            'type': 'sentryGun'
        },
        {
            'level': 2,
            'player_id': 0,
            'status': 'idle',
            'tile_position': [35, 19],
            'type': 'crystaliteFarm'
        },
        {
            'code': 'attacker_infantry.py',
            'craft_id': 1,
            'level': 5,
            'player_id': 1,
            'type': 'craft',
            'modules': [
                'extDeploy',
            ],
            'unit': {
                'level': 5,
                'type': 'infantryBot'
            },
            'unit_quantity': 3
        },

    ],
    'map_size': [40, 40],
    'players': [
        {'defeat': ['center'], 'env_name': 'python_3', 'id': 0, 'user_id': 14},
        {'defeat': ['units', 'time'], 'env_name': 'python_3', 'id': 1, 'user_id': 24}
    ],
    'rewards': {
        'resources': {
            'adamantite': 400,
            'crystalite': 150,
        }
    },
    'time_limit': 30
}