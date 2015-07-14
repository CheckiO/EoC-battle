"use strict";

var PARTY = {
    REQUEST_NAME: 'parties',
    MY: "my",
    ENEMY: "enemy"
};
PARTY.ALL = [PARTY.MY, PARTY.ENEMY];

var ROLE = {
    REQUEST_NAME: "roles",
    CENTER: "center",
    TOWER: "tower",
    UNIT: "unit",
    BUILDING: "building",
    OBSTACLE: "obstacle"
};
ROLE.ALL = [ROLE.CENTER, ROLE.TOWER, ROLE.UNIT, ROLE.BUILDING, ROLE.OBSTACLE];

exports.PARTY = PARTY;
exports.ROLE = ROLE;
