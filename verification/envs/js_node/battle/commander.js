/*jshint node: true */
/*jslint node: true */

"use strict";
var BattleClientLoop = require("../battle_client.js").BattleClientLoop;
var Terms = require('./terms.js');
var util = require('util');
var PARTY = Terms.PARTY;
var ROLE = Terms.ROLE;

var ERR_ID_TYPE = "%s ID must be an integer",
    ERR_ARRAY_TYPE = "%s must be a list/tuple",
    ERR_COORDINATES_TYPE = "%s must be an array with two numbers.",
    ERR_CALLABLE_TYPE = "%s must be callable (function)",
    ERR_STR_TYPE = "%s must be a string",
    ERR_NUMBER_TYPE = "%s must be a number.",
    ERR_NUMBER_POSITIVE_VALUE = "%s must be a positive.",
    ERR_ARRAY_VALUE = "%s must contains only correct values",
    ERR_CALLBACK_DEPRECATED = "[WARNING][DEPRECATED] " +
        "Callbacks for 'do' (action) commands are deprecated. " +
        "They will be disabled soon." +
        " Be careful - callback for 'do' is called after command sending," +
        " not after end of the action";


// Type and values check functions

function checkCallable(func, name) {
    if (typeof(func) !== 'function') {
        throw new TypeError(util.format(ERR_CALLABLE_TYPE, name));
    }
}

function checkItemId(itemId) {
    if (isNaN(itemId) || parseInt(itemId, 10) !== itemId) {
        throw new TypeError(util.format(ERR_ID_TYPE, "Item"));
    }
}

function checkCoordinates(coordinates, name) {
    if (!Array.isArray(coordinates) || coordinates.length !== 2 ||
        isNaN(coordinates[0]) || isNaN(coordinates[1])) {
        throw new TypeError(util.format(ERR_COORDINATES_TYPE, name));
    }
}

function checkArray(array, correctValues, name) {
    if (!Array.isArray(array)) {
        throw new TypeError(util.format(ERR_ARRAY_TYPE, name));
    }
    for (var i = 0, l = array.length; i < l; i++) {
        if (correctValues.indexOf(array[i]) === -1) {
            throw new Error(util.format(ERR_ARRAY_VALUE, name));
        }
    }
}

function checkRadius(number) {
    if (isNaN(number)) {
        throw new TypeError(util.format(ERR_NUMBER_TYPE, "Radius"));
    }
    if (number <= 0) {
        throw new Error(util.format(ERR_NUMBER_POSITIVE_VALUE, "Radius"));
    }
}

function Client() {
    this.loop = BattleClientLoop.lastLoop;
}


// ASK

Client.prototype.ask = function (fields, callBack) {
    if (callBack) {
        checkCallable(callBack, "Callback");
    }
    if (typeof(callBack) !== 'function') {
        throw new TypeError(util.format(ERR_CALLABLE_TYPE, "Callback"));
    }
    return this.loop.select([fields], function (data) {
        callBack(data[0]);
    });
};

Client.prototype.askMyInfo = function (callBack) {
    return this.ask({
        'field': 'my_info'
    }, callBack);
};
Client.prototype.start = Client.prototype.askMyInfo;

Client.prototype.askItemInfo = function (id, callBack) {
    checkItemId(id);
    return this.ask({
        'field': 'item_info',
        'data': {
            'id': id
        }
    }, callBack);
};

Client.prototype.askNearestEnemy = function (callBack) {
    return this.ask({
        'field': 'nearest_enemy'
    }, callBack);
};

Client.prototype.askItems = function (parties, roles, callBack) {
    roles = roles || ROLE.ALL;
    parties = parties || PARTY.ALL;
    checkArray(parties, PARTY.ALL, "Parties");
    checkArray(roles, ROLE.ALL, "Roles");
    var data = {};
    data[PARTY.REQUEST_NAME] = parties;
    data[ROLE.REQUEST_NAME] = roles;
    return this.ask({
        'field': 'items',
        'data': data
    }, callBack);
};

Client.prototype.askEnemyItems = function (callBack) {
    return this.askItems([PARTY.ENEMY], undefined, callBack);
};

Client.prototype.askMyItems = function (callBack) {
    return this.askItems([PARTY.MY], undefined, callBack);
};

Client.prototype.askBuildings = function (callBack) {
    return this.askItems(undefined, [ROLE.CENTER, ROLE.BUILDING], callBack);
};

Client.prototype.askTowers = function (callBack) {
    return this.askItems(undefined, [ROLE.TOWER], callBack);
};

Client.prototype.askCenter = function (callBack) {
    function setMeUp(data) {
        if (data.length === 0) {
            callBack(undefined);
        } else {
            callBack(data[0]);
        }
    }
    return this.askItems(undefined, [ROLE.CENTER], setMeUp);
};

Client.prototype.askUnits = function (callBack) {
    return this.askItems([PARTY.UNIT], undefined, callBack);
};

Client.prototype.askPlayers = function (parties, callBack) {
    parties = parties || PARTY.ALL;
    checkArray(parties, PARTY.ALL, "Parties");
    var data = {};
    data[PARTY.REQUEST_NAME] = parties;
    return this.select({
        'field': 'players',
        'data': data
    }, callBack);
};

Client.prototype.askEnemyPlayers = function (callBack) {
    return this.askItems([PARTY.ENEMY], undefined, callBack);
};

Client.prototype.askMyRangeEnemyItems = function (callBack) {
    return this.ask({
        'field': 'enemy_items_in_my_firing_range'
    }, callBack);
};

// DO

Client.prototype.do = function (action, data, callBack) {
    if (callBack) {
        checkCallable(callBack, "Callback");
        console.log(ERR_CALLBACK_DEPRECATED);
    }
    return this.loop.setAction(action, data, callBack);
};

Client.prototype.doAttack = function (id, callBack) {
    checkItemId(id);
    this.do('attack', {'id': id}, callBack);
};

Client.prototype.doMove = function (coordinates, callBack) {
    checkCoordinates(coordinates, "Coordinates");
    this.do('move', {'coordinates': coordinates}, callBack);
};

// SUBSCRIBE

Client.prototype.when = function (action, data, callBack) {
    if (callBack) {
        checkCallable(callBack, "Callback");
    }
    this.loop.subscribe(action, data, callBack);
};

Client.prototype.unSubscribeAll = function (callBack) {
    if (callBack) {
        checkCallable(callBack, "Callback");
    }
    this.when('unsubscribe_all', undefined, callBack);
};

Client.prototype.whenInArea = function (center, radius, callBack) {
    checkCoordinates(center, "Center coordinates");
    checkRadius(radius);
    this.when('im_in_area', {
        'coordinates': center,
        'radius': radius
    }, callBack);
};

Client.prototype.whenItemInArea = function (center, radius, callBack) {
    checkCoordinates(center, "Center coordinates");
    this.when('any_item_in_area', {
        'coordinates': center,
        'radius': radius
    }, callBack);
};

Client.prototype.whenStoped = function (callBack) {
    this.when('im_stop', {}, callBack);
};

Client.prototype.whenIdle = function (callBack) {
    this.when('im_idle', {}, callBack);
};

Client.prototype.whenEnemyInRange = function (callBack) {
    this.when('enemy_in_my_firing_range', {}, callBack);
};

Client.prototype.whenEnemyOutRange = function (callBack) {
    this.when('the_item_out_my_firing_range', {}, callBack);
};

Client.prototype.whenItemDestroyed = function (id, callBack) {
    checkItemId(id);
    this.when('death', {'id': id}, callBack);
};

exports.Client = Client;
