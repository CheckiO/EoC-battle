ATTACKER_CODE_INFANTRY = """
var commander = require("battle/commander.js");
var craftClient = new commander.CraftClient();
craftClient.doLandUnits([40,2]);

function unitDepart(data) {
    var unitClient = new commander.UnitClient(data['id']);
    unitClient.doDepart();
}

function unitTravel(data) {
    var unitClient = new commander.UnitClient(data['id']);
    unitClient.doMove([36,6]);
    unitClient.whenImIdle().then(unitDepart);
}

craftClient.whenUnitLanded(unitTravel);
"""

DEF_CODE_SENTRY_GUN = """
var commander = require("battle/commander.js");
var towerClient = new commander.Client();

function unitInFiringRange(data) {
    towerClient.doAttack(data['id'])
}
towerClient.whenEnemyInRange().then(unitInFiringRange);
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
        {'defeat': ['center'], 'env_name': 'js_node', 'id': 0, 'user_id': 14},
        {'defeat': ['units', 'time'], 'env_name': 'js_node', 'id': 1, 'user_id': 24}
    ],
    'rewards': {
        'resources': {
            'adamantite': 400,
            'crystalite': 150,
        }
    },
    'time_limit': 30
}