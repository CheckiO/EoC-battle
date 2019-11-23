ATTACKER_CODE_INFANTRY = """
var commander = require("battle/commander.js");
var craftClient = new commander.CraftClient();
craftClient.doLandUnits([40,2]);

function unitLanded(data) {
    var unitClient = new commander.UnitClient(data['id']);
    
    function searchAndDestroy() {
        var enemy = unitClient.askNearestEnemy();
        unitClient.doAttack(enemy['id']);
        unitClient.whenImIdle().then(searchAndDestroy);
    };
    
    searchAndDestroy();
}

craftClient.whenUnitLanded(unitLanded);
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