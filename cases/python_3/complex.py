ATTACKER_CODE_INFANTRY = """
from random import randint
from battle import commander
craft_client = commander.CraftClient()
craft_client.do_land_units([40,2])

def unit_landed(data):
    print('LANDED',randint(0, 100), data)
    unit_client = commander.UnitClient(data['id'])
    def search_and_destroy(data=None):
        enemy = unit_client.ask_nearest_enemy()
        unit_client.do_attack(enemy['id'])
        unit_client.when_im_idle(search_and_destroy)
    search_and_destroy()
    
craft_client.when_unit_landed(unit_landed)
"""

ATTACKER_CODE_HEAVY = """
from random import randint
from battle import commander
craft_client = commander.CraftClient()
craft_client.do_land_units([40,2])

def unit_landed(data):
    print('LANDED',randint(0, 100), data)
    unit_client = commander.UnitClient(data['id'])

    def heavy_protection(data=None):
        unit_client.do_heavy_protect()

    def search_and_destroy(data=None):
        unit_client.do_move([28,19])
        unit_client.when_im_idle(heavy_protection)

    search_and_destroy()
    
craft_client.when_unit_landed(unit_landed)
"""

ATTACKER_CODE_ROCKET = """
from random import randint
from battle import commander
craft_client = commander.CraftClient()
craft_client.do_land_units([40,0])

def unit_landed(data):
    print('LANDED',randint(0, 100), data)
    unit_client = commander.UnitClient(data['id'])
    def search_and_destroy(data=None):
        enemy = unit_client.ask_nearest_enemy()
        unit_client.do_attack(enemy['id'])
        unit_client.when_im_idle(search_and_destroy)
    search_and_destroy()
    
craft_client.when_unit_landed(unit_landed)
"""

DEF_CODE_SENTRY_GUN = """
from battle import commander
tower_client = commander.Client()

def search_next_target(data, **kwargs):
    enemies = tower_client.ask_enemy_items_in_my_firing_range()
    if enemies:
        unit_in_firing_range(enemies[0])
    else:
        tower_client.when_enemy_in_range(unit_in_firing_range)

def unit_in_firing_range(data, **kwargs):
    tower_client.do_attack(data['id'])
    tower_client.when_im_idle(search_next_target)

tower_client.when_enemy_in_range(unit_in_firing_range)
"""

DEF_CODE_MACHINE_GUN = """
import random
from battle import commander
tower_client = commander.Client()

def search_next_target(data, **kwargs):
    enemies = tower_client.ask_enemy_items_in_my_firing_range()
    if enemies:
        unit_in_firing_range(enemies[0])
    else:
        tower_client.when_enemy_in_range(unit_in_firing_range)

def unit_in_firing_range(data, **kwargs):
    # ATTACK ITEM
    tower_client.do_turn_to_fire(data['id'])
    # ATTACK ANGLE
    #tower_client.do_fire()
    tower_client.when_im_idle(search_next_target)

tower_client.do_turn(180)
tower_client.when_enemy_in_range(unit_in_firing_range)
"""

DEF_CODE_ROCKET_GUN = """
from random import randint
from battle import commander

tower_client = commander.Client()

def search_next_target(data, **kwargs):
    enemies = tower_client.ask_enemy_items_in_my_firing_range()
    if enemies:
        unit_in_firing_range(enemies[0])
    else:
        tower_client.when_enemy_in_range(unit_in_firing_range)

def unit_in_firing_range(data, **kwargs):
    # ATTACK ITEM
    tower_client.do_attack(data['id'])
    # ATTACK COORDINATES
    #tower_client.do_attack_coordinates([randint(30,32),randint(28,30)])
    tower_client.when_im_idle(search_next_target)

tower_client.when_enemy_in_range(unit_in_firing_range)
"""

PLAYERS = {
    'codes': {
        '0': {
            'def_code_sentry_gun.py': DEF_CODE_SENTRY_GUN,
            'def_code_machine_gun.py': DEF_CODE_MACHINE_GUN,
            'def_code_rocket_gun.py': DEF_CODE_ROCKET_GUN,
        },
        '1': {
            'attacker_heavy.py': ATTACKER_CODE_HEAVY,
            'attacker_infantry.py': ATTACKER_CODE_INFANTRY,
            'attacker_rocket.py': ATTACKER_CODE_ROCKET,
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
            'tile_position': [20, 13],
            'modules': [
                'u.chargingTime.lvl1',
                'b.damagePerShot.lvl1',
                'u.hitPoints.lvl1',
                'u.fireRange.lvl1',
                'freezing',
                'shotThrough',
            ],
            'type': 'sentryGun'
        },
        {
            'code': 'def_code_machine_gun.py',
            'level': 1,
            'player_id': 0,
            'status': 'idle',
            'tile_position': [27, 23],
            'modules': [
                'u.rateOfFire.lvl1',
                'u.hitPoints.lvl1',
                'incCoverRange',
            ],
            'type': 'machineGun'
        },
        {
            'code': 'def_code_rocket_gun.py',
            'level': 1,
            'player_id': 0,
            'status': 'idle',
            'tile_position': [20, 23],
            'modules': [
                'b.damagePerShot.lvl1',
                'u.hitPoints.lvl2',
                'u.fireRange.lvl2',
            ],
            'type': 'rocketGun'
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
                'u.rateOfFire.lvl1',
                'speed.lvl1',
                'extDeploy',
                'teleport',
            ],
            'unit': {
                'level': 5,
                'type': 'infantryBot'
            },
            'unit_quantity': 5
        },
        {
            'code': 'attacker_heavy.py',
            'craft_id': 2,
            'level': 1,
            'player_id': 1,
            'type': 'craft',
            'modules': [
                'u.rateOfFire.lvl1',
                'speed.lvl2',
                'extDeploy',
                'heavyProtect',
            ],
            'unit': {
                'level': 1,
                'type': 'heavyBot'
            },
            'unit_quantity': 3
        },
        {
            'code': 'attacker_rocket.py',
            'craft_id': 3,
            'level': 1,
            'player_id': 1,
            'type': 'craft',
            'modules': [
                'fasterRocket',
                'speed.lvl1',
                'extDeploy',
            ],
            'unit': {
                'level': 3,
                'type': 'rocketBot'
            },
            'unit_quantity': 2
        },

        # Obstacles

        {
            'player_id': -1,
            'status': 'idle',
            'tile_position': [
                33,
                10
            ],
            'type': 'obstacle5',
            'level': 2
        },
        {
            'player_id': -1,
            'status': 'idle',
            'tile_position': [
                33,
                5
            ],
            'type': 'obstacle5',
            'level': 2
        },
        {
            'player_id': -1,
            'status': 'idle',
            'tile_position': [
                33,
                0
            ],
            'type': 'obstacle5',
            'level': 3
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