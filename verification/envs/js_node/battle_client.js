"use strict";
var ClientLoop = require('./client.js').ClientLoop;

function makeId() {
    return String(Math.random()).split('.')[1];
}

function BattleClientLoop(port, environment_id) {
    this.connection_port = port;
    this.environment_id = environment_id;
    this.waitEvents = {};
    this.requestQueue = [];
    this.currentRequest = undefined;
    this.currentCallBack = undefined;
    this.myData = {};
    this.envData = {};
    BattleClientLoop.lastLoop = this;
}

BattleClientLoop.prototype = new ClientLoop();
BattleClientLoop.prototype.parent = ClientLoop.prototype;

BattleClientLoop.prototype.actionRunCode = function (data) {
    data = this.grabEnvData(data);
    ClientLoop.prototype.actionRunCode.apply(this, [data]);
};

BattleClientLoop.prototype.grabEnvData = function (data) {
    this.myData = data.__my_data;
    this.envData = data.__env_data;
    delete data.__my_data;
    delete data.__env_data;
    return data;
};

BattleClientLoop.prototype.pushRequestQueue = function (data, callBack) {
    this.requestQueue.push([data, callBack]);
};

BattleClientLoop.prototype.actualRequest = function (data) {
    return new Promise(function(resolve, reject){
        if (this.currentRequest) {
            this.pushRequestQueue(data, resolve);
            return;
        }
        this.currentRequest = data;
        this.currentCallBack = resolve;
        data.status = 'success';
        this.connection.write(JSON.stringify(data) + '\u0000');
    }.bind(this));
};

BattleClientLoop.prototype.getCallActions = function () {
    var actions = this.parent.getCallActions.call(this);
    actions.event = this.actionEvent.bind(this);
    return actions;
};

BattleClientLoop.prototype.actionEvent = function (data) {
    console.log('QQQQQQQQQQQQQQQQQQQQQQQQQQQ');
    console.log(data);
    var callBack = this.waitEvents[data.lookup_key];
    delete this.waitEvents[data.lookup_key];
    callBack(data.data);
};

BattleClientLoop.prototype.onClientData = function (data) {
    var result, currentCallBack, nextInQueue;
    if (data.action && this.callActions[data.action]) {
        result = this.callActions[data.action](data);
        if (result) {
            this.clientWrite(result);
        }
    } else {
        currentCallBack = this.currentCallBack;
        this.currentRequest = undefined;
        this.currentCallBack = undefined;
        if (currentCallBack) {
            currentCallBack(data.data);
        }
        if (this.requestQueue.length) {
            nextInQueue = this.requestQueue.shift();
            this.actualRequest(nextInQueue[0], nextInQueue[1]);
        }
    }
};

BattleClientLoop.prototype.setAction = function (action, data) {
    return this.actualRequest({'method': 'set_action', 'action': action, 'data': data});
};

BattleClientLoop.prototype.sendCommand = function (action, data) {
    return this.actualRequest({'method': 'command', 'action': action, 'data': data});
};


BattleClientLoop.prototype.subscribeCallback = function (action, data, callback, infinity=false) {
    var key = makeId();
    this.actualRequest({'method': 'subscribe', 'lookup_key': key, 'event': action, 'data': data});
    this.waitEvents[key] = function(data){
        data = this.grabEnvData(data);
        callback(data);
        if (infinity === true) {
            this.subscribeCallback(action, data, callback, infinity);
        };
    }.bind(this);
};

BattleClientLoop.prototype.subscribe = function (action, data, infinity=false) {
    return new Promise(function(resolve, reject){
        this.subscribeCallback(action, data, resolve, infinity);
    }.bind(this));
};

exports.BattleClientLoop = BattleClientLoop;