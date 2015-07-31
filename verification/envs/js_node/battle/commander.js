"use strict";
var BattleClientLoop = require("../battle_client.js").BattleClientLoop;
var Terms = require('./terms.js');
var PARTY = Terms.PARTY;
var ROLE = Terms.ROLE;

function Client() {
    this.loop = BattleClientLoop.lastLoop;
    this.myInfo = undefined;
}

// ASK

Client.prototype.ask = function (fields, callBack) {
    return this.loop.select([fields], function (data) {
        callBack(data[0]);
    });
};

Client.prototype.askMyInfo = function (callBack) {
    function setMeUp(data) {
        this.myInfo = data;
        if (callBack) {
            callBack(data);
        }
    }
    return this.ask({
        'field': 'my_info'
    }, setMeUp.bind(this));
};
Client.prototype.start = Client.prototype.askMyInfo;

Client.prototype.askItemInfo = function (id, callBack) {
    return this.ask({
        'field': 'item_info',
        'data': {
            'id': id
        }
    }, callBack);
};

Client.prototype.askNearestEnemy = function (callBack) {
    return this.ask({
        'field': 'nearest_enemy',
        'data': {
            'id': this.myInfo.id
        }
    }, callBack);
};

Client.prototype.askItems = function (parties, roles, callBack) {
    if (!parties) {
        parties = PARTY.ALL;
    }
    if (!roles) {
        roles = ROLE.ALL;
    }
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
    return this.askItems(undefined, [ROLE.TOWERS], callBack);
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
    if (!parties) {
        parties = PARTY.ALL;
    }
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
        'field': 'enemy_items_in_my_firing_range',
        'data': {
            'id': this.myInfo.id
        }
    }, callBack);
};

// DO

Client.prototype.do = function (action, data, callBack) {
    return this.loop.setAction(action, data, callBack);
};

Client.prototype.doAttack = function (id, callBack) {
    this.do('attack', {'id': id}, callBack);
};

Client.prototype.doMove = function (coordinates, callBack) {
    this.do('move', {'coordinates': coordinates}, callBack);
};

// SUBSCRIBE

Client.prototype.when = function (action, data, callBack) {
    this.loop.subscribe(action, data, callBack);
};

Client.prototype.unSubscribeAll = function (callBack) {
    this.when('unsubscribe_all', undefined, callBack);
};

Client.prototype.whenInArea = function (center, radius, callBack) {
    this.when('im_in_area', {
        'coordinates': center,
        'radius': radius
    }, callBack);
};

Client.prototype.whenItemInArea = function (center, radius, callBack) {
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
    this.when('death', {'id': id}, callBack);
};

exports.Client = Client;