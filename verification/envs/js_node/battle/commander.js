/*jshint node: true */
/*jslint node: true */

"use strict";
var BattleClientLoop = require("../battle_client.js").BattleClientLoop;
var Terms = require('./terms.js');
var util = require('util');
var PARTY = Terms.PARTY;
var ROLE = Terms.ROLE;
var _ = require("underscore");

var ERR_ID_TYPE = "%s ID must be an integer",
    ERR_ARRAY_TYPE = "%s must be a list/tuple",
    ERR_COORDINATES_TYPE = "%s must be an array with two numbers.",
    ERR_CALLABLE_TYPE = "%s must be callable (function)",
    ERR_STR_TYPE = "%s must be a string",
    ERR_NUMBER_TYPE = "%s must be a number.",
    ERR_NUMBER_POSITIVE_VALUE = "%s must be a positive.",
    ERR_NUMBER_PERCENTAGE_VALUE = "%s must be a percentage.",
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

function checkDistance(number) {
    if (number is undefined) {
        return
    }
    if (isNaN(number)) {
        throw new TypeError(util.format(ERR_NUMBER_TYPE, "Distance"));
    }
    if (number <= 0) {
        throw new Error(util.format(ERR_NUMBER_POSITIVE_VALUE, "Distance"));
    }
}

function checkPercentage(number) {
    if (number is undefined) {
        return
    }
    if (isNaN(number)) {
        throw new TypeError(util.format(ERR_NUMBER_TYPE, "Percentage"));
    }
    if (number < 0) {
        throw new Error(util.format(ERR_NUMBER_PERCENTAGE_VALUE, "Percentage"));
    }
    if (number > 100) {
        throw new Error(util.format(ERR_NUMBER_PERCENTAGE_VALUE, "Percentage"));
    }
}

function Client() {
    this.loop = BattleClientLoop.lastLoop;
}

Client.prototype.myData = function () {
    return this.loop.myData;
};

Client.prototype.envData = function () {
    return this.loop.envData;
};

Client.prototype.envMap = function () {
    return this.envData().map;
};

Client.prototype.myInfo = function () {
    return this.envMap()[this.myData().id];
};

var MapMath = {
    euclideanDistance: function(point1, point2){
        return Math.sqrt(Math.pow(point1[0] - point2[0], 2) + Math.pow(point1[1] - point2[1], 2));
    }
};

var Filters = {
    enemy: function(client, item){
        return client.myInfo().player_id != item.player_id && item.player_id != -1;
    },
    my: function(client, item){
        return client.myInfo().player_id == item.player_id;
    },
    roles: function(roles){
        var _filter = function(client, item){
            return roles.indexOf(item.role) + 1;
        };
        return _filter;
    },
    inMyRange: function(client, item){
        var distance = MapMath.euclideanDistance(item.coordinates, client.myInfo().coordinates);
        return distance - item.size/2 <= client.myInfo().firing_range;
    }
};

Client.prototype.mapFilter = function (filters) {
    var _filter_passed = function(item){
        return typeof _.find(filters, function(_filter){
            if (!_filter(this, item)) {
                return true;
            }
        }, this) === 'undefined';
    }.bind(this);
    return _.filter(_.values(this.envMap()), function(item){
        return !item.is_dead && _filter_passed(item);
    }, this);
};


// ASK


Client.prototype.askCurTime = function() {
    return this.envData()['game']['time'];
};

Client.prototype.askMyInfo = function () {
    return this.myInfo();
};
Client.prototype.start = Client.prototype.askMyInfo;

Client.prototype.askItemInfo = function (id) {
    checkItemId(id);
    return this.envMap()[id];
};

Client.prototype.askNearestEnemy = function (roles) {
    var minLen = 1000,
        nearest,
        fighter = this.myInfo(),
        filters = [Filters.enemy];

    if (roles) {
        filters.push(Filters.roles(roles));
    }
    _.each(this.mapFilter(filters), function(item){
        var length = MapMath.euclideanDistance(item.coordinates, fighter.coordinates);
        if (length < minLen) {
            minLen = length;
            nearest = item;
        }
    });
    return nearest;
};

Client.prototype.askItems = function (parties, roles) {
    roles = roles || ROLE.ALL;
    roles = _.uniq(roles);
    parties = parties || PARTY.ALL;
    parties = _.uniq(parties);
    checkArray(parties, PARTY.ALL, "Parties");
    checkArray(roles, ROLE.ALL, "Roles");
    var filters = [];
    if (parties.length === 1) {
        if (parties[0] === PARTY.ENEMY) {
            filters.push(Filters.enemy);
        } else if (parties[0] === PARTY.MY) {
            filters.push(Filters.my);
        }
    }
    filters.push(Filters.roles(roles));
    return this.mapFilter(filters)
};

Client.prototype.askEnemyItems = function () {
    return this.askItems([PARTY.ENEMY], undefined);
};

Client.prototype.askMyItems = function () {
    return this.askItems([PARTY.MY], undefined);
};

Client.prototype.askBuildings = function () {
    return this.askItems(undefined, [ROLE.CENTER, ROLE.BUILDING]);
};

Client.prototype.askTowers = function () {
    return this.askItems(undefined, [ROLE.TOWER]);
};

Client.prototype.askCenter = function () {
    var ret = this.askItems(undefined, [ROLE.CENTER]);
    if (ret.length === 0) {
        return
    } else {
        return ret[0];
    }
};

Client.prototype.askUnits = function () {
    return this.askItems(undefined, [ROLE.UNIT]);
};

Client.prototype.askMyRangeEnemyItems = function () {
    return this.mapFilter([Filters.enemy, Filters.inMyRange]);
};

// IDs

Client.prototype.idsMyCraft = function () {
    var ret = [];
    var myInfo = this.myInfo();
    _.each(this.envMap(), function(item, id){
        if (id != myInfo.id && item.craft_id === myInfo.craft_id) {
            ret.push(id);
        }
    });
    return ret;
};

Client.prototype.idsMyTeam = function () {
    var ret = [];
    var myInfo = this.myInfo();
    _.each(this.envMap(), function(item, id){
        if (id != myInfo.id && item.player_id === myInfo.player_id) {
            ret.push(id);
        }
    });
    return ret;
};

// DO

Client.prototype.do = function (action, data) {
    return this.loop.setAction(action, data);
};

Client.prototype.doAttack = function (id) {
    checkItemId(id);
    return this.do('attack', {'id': id});
};

Client.prototype.doMove = function (coordinates) {
    checkCoordinates(coordinates, "Coordinates");
    return this.do('move', {'coordinates': coordinates});
};

Client.prototype.doMoves = function (steps) {
    _.each(steps, function(coordinates) {
        checkCoordinates(coordinates, "Coordinates");
    });
    
    return this.do('moves', {'steps': steps});
};

Client.prototype.doAttackCoordinates = function (coordinates) {
    checkCoordinates(coordinates, "Coordinates");
    return this.do('attack_coor', {'coordinates': coordinates});
};

Client.prototype.doAttackCoordinated = Client.prototype.doAttackCoordinates; // Used to have a typo, kept to prevent breakage

Client.prototype.doMessage = function (message, ids) {
    return this.do('message', {'message': message, 'ids': ids});
};

Client.prototype.doMessageToId = function (message, id) {
    return this.doMessage(message, [id]);
};

Client.prototype.doMessageToCraft = function (message) {
    return this.doMessage(message, this.idsMyCraft());
};

Client.prototype.doMessageToTeam = function (message) {
    return this.doMessage(message, this.idsMyTeam());
};

// SUBSCRIBE

Client.prototype.when = function (action, data) {
    return this.loop.subscribe(action, data);
};

Client.prototype.unSubscribeAll = function () {
    return this.when('unsubscribe_all', undefined);
};

Client.prototype.whenInArea = function (center, radius) {
    checkCoordinates(center, "Center coordinates");
    checkRadius(radius);
    return this.when('im_in_area', {
        'coordinates': center,
        'radius': radius
    });
};

Client.prototype.whenItemInArea = function (center, radius) {
    checkCoordinates(center, "Center coordinates");
    return this.when('any_item_in_area', {
        'coordinates': center,
        'radius': radius
    });
};

Client.prototype.whenStoped = function () {
    console.warn("'whenStoped' is deprecated. Please use 'whenIdle' instaed");
    return new Promise(function(resolve){});
};

Client.prototype.whenIdle = function () {
    return this.when('im_idle', {});
};

Client.prototype.whenEnemyInRange = function (distance, percentage) {
    checkDistance(distance);
    checkPercentage(percentage);
    return this.when('enemy_in_my_firing_range', {
        'distance': distance,
        'percentage': percentage
    });
};

Client.prototype.whenEnemyOutRange = function () {
    console.warn("'whenEnemyOutRange' is deprecated");
    return new Promise(function(resolve){});
};

Client.prototype.whenItemDestroyed = function (id) {
    checkItemId(id);
    return this.when('death', {'id': id});
};

Client.prototype.whenTime = function(atTime) {
    return this.when('time', {'time': atTime});
};

Client.prototype.whenMessage = function() {
    return this.when('message', {});
};

exports.Client = Client;
