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

function retCall(data, callBack) {
    if (callBack){
        setTimeout(function(){callBack(data);}, 1);
    }
    return data;
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
        return client.myInfo().player_id != item.player_id;
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
        if (item.is_dead) {
            return false;
        }
        if (_filter_passed(item)) {
            return true;
        }
    }, this);
};


// ASK

Client.prototype.askMyInfo = function (callBack) {
    return retCall(this.myInfo(), callBack);
};
Client.prototype.start = Client.prototype.askMyInfo;

Client.prototype.askItemInfo = function (id, callBack) {
    checkItemId(id);
    return retCall(this.envMap()[id], callBack);
};

Client.prototype.askNearestEnemy = function (callBack) {
    var minLen = 1000,
        nearest,
        fighter = this.myInfo();

    _.each(this.mapFilter([Filters.enemy]), function(item){
        var length = MapMath.euclideanDistance(item.coordinates, fighter.coordinates);
        if (length < minLen) {
            minLen = length;
            nearest = item;
        }
    });
    return retCall(nearest, callBack);
};

Client.prototype.askItems = function (parties, roles, callBack) {
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
    return retCall(this.mapFilter(filters), callBack);
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
    var ret = this.askItems(undefined, [ROLE.CENTER]);
    if (ret.length === 0) {
        ret = undefined;
    } else {
        ret = ret[0];
    }
    return retCall(ret, callBack);
};

Client.prototype.askUnits = function (callBack) {
    return this.askItems([PARTY.UNIT], undefined, callBack);
};

Client.prototype.askMyRangeEnemyItems = function (callBack) {
    return retCall(this.mapFilter([Filters.inMyRange]), callBack);
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
