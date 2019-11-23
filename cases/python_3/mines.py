ATTACKER_CODE_INFANTRY = """
from battle import commander
craft_client = commander.CraftClient()
craft_client.do_land_units([40,2])

def unit_landed(data):
    unit_client = commander.UnitClient(data['id'])
    def search_and_destroy(data=None):
        enemy = unit_client.ask_nearest_enemy()
        unit_client.do_attack(enemy['id'])
        unit_client.when_im_idle(search_and_destroy)
    search_and_destroy()

craft_client.when_unit_landed(unit_landed)
"""

PLAYERS = {
    'codes': {
        '0': {

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
            'level': 2,
            'player_id': 0,
            'status': 'idle',
            'tile_position': [30, 5],
            'type': 'crystaliteFarm'
        },
        {
            'level': 1,
            'player_id': 0,
            'status': 'wait',
            'tile_position': [35, 10],
            'type': 'mine'
        },
        {
            'level': 1,
            'player_id': 0,
            'status': 'wait',
            'tile_position': [35, 9],
            'type': 'mine'
        },
        {
            'level': 1,
            'player_id': 0,
            'status': 'wait',
            'tile_position': [35, 8],
            'type': 'mine'
        },
        {
            'level': 1,
            'player_id': 0,
            'status': 'wait',
            'tile_position': [35, 7],
            'type': 'mine'
        },
        {
            'level': 1,
            'player_id': 0,
            'status': 'wait',
            'tile_position': [35, 6],
            'type': 'mine'
        },
        {
            'level': 1,
            'player_id': 0,
            'status': 'wait',
            'tile_position': [35, 5],
            'type': 'mine'
        },
        {
            'level': 1,
            'player_id': 0,
            'status': 'wait',
            'tile_position': [35, 4],
            'type': 'mine'
        },
        {
            'level': 1,
            'player_id': 0,
            'status': 'wait',
            'tile_position': [35, 3],
            'type': 'mine'
        },
        {
            'level': 1,
            'player_id': 0,
            'status': 'wait',
            'tile_position': [35, 2],
            'type': 'mine'
        },
        {
            'level': 1,
            'player_id': 0,
            'status': 'wait',
            'tile_position': [35, 1],
            'type': 'mine'
        },
        {
            'level': 1,
            'player_id': 0,
            'status': 'wait',
            'tile_position': [35, 0],
            'type': 'mine'
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
            'unit_quantity': 6
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