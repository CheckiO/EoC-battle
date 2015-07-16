var optimist = require('optimist');
var BattleClientLoop = require('./battle_client.js').BattleClientLoop;

var argv = optimist.argv._;
var client = new BattleClientLoop(argv[0], argv[1]);
client.start();
