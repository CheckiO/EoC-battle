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

ATTACKER_CODE_HEAVY = """
var commander = require("battle/commander.js");
var craftClient = new commander.CraftClient();
craftClient.doLandUnits([40,2]);

function unitLanded(data) {
    var unitClient = new commander.UnitClient(data['id']);

    function heavyProtection() {
        unitClient.doHeavyProtect();
    };
    
    function searchAndDestroy() {
        unitClient.doMove([28,19]);
        unitClient.whenImIdle().then(heavyProtection);
    };

    searchAndDestroy();
}

craftClient.whenUnitLanded(unitLanded);
"""

ATTACKER_CODE_ROCKET = """
var commander = require("battle/commander.js");
var craftClient = new commander.CraftClient();
craftClient.doLandUnits([40,0]);

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

DEF_CODE_SENTRY_GUN = """
var commander = require("battle/commander.js");
var towerClient = new commander.Client();

function searchNextTarget(data) {
    var enemies = towerClient.askEnemyItemsInMyFiringRange();
    if (typeof enemies !== 'undefined') {
        unitInFiringRange(enemies[0]);
    } else {
        towerClient.whenEnemyInRange().then(unitInFiringRange);    
    };
};

function unitInFiringRange(data) {
    towerClient.doAttack(data['id']);
    towerClient.whenImIdle().then(searchNextTarget);
};

towerClient.whenEnemyInRange().then(unitInFiringRange);
"""

DEF_CODE_MACHINE_GUN = """
var commander = require("battle/commander.js");
var towerClient = new commander.Client();

function searchNextTarget(data) {
    var enemies = towerClient.askEnemyItemsInMyFiringRange();
    if (typeof enemies !== 'undefined') {
        unitInFiringRange(enemies[0]);
    } else {
        towerClient.whenEnemyInRange().then(unitInFiringRange);    
    };
};
function unitInFiringRange(data) {
    // ATTACK ITEM
    towerClient.doTurnToFire(data['id']);
    //ATTACK ANGLE
    //towerClient.doFire();
    
    towerClient.whenImIdle().then(searchNextTarget);
};

towerClient.whenEnemyInRange().then(unitInFiringRange);
"""

DEF_CODE_ROCKET_GUN = """
var commander = require("battle/commander.js");
var towerClient = new commander.Client();

function searchNextTarget(data) {
    var enemies = towerClient.askEnemyItemsInMyFiringRange();
    if (typeof enemies !== 'undefined') {
        unitInFiringRange(enemies[0]);
    } else {
        towerClient.whenEnemyInRange().then(unitInFiringRange);    
    };
};
function unitInFiringRange(data) {
    // ATTACK ITEM
    towerClient.doAttack(data['id']);
    //ATTACK COORDINATES
    //towerClient.doAttackCoordinates([Math.floor(Math.random() * 11), Math.floor(Math.random() * 11)]);

    towerClient.whenImIdle().then(searchNextTarget);
};

towerClient.whenEnemyInRange().then(unitInFiringRange);
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