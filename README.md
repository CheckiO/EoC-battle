Battle is part of the project Empire of Code. This battle algorithm is using to tun a battle in the game.

## How to run the battle?

In order to run the buttle you should do the following steps

 - **Install** checkio-client

    pip install checkio-client

 - **Configure** it for domain epy (In case you will be asked about "key" just put a random numer in it. It is not important at this stage)

    checkio --domain epy config

 - The next step is to **build buttle** using checkio client. In order to do so you will need a docker installed.

    checkio eoc-get-git /path/to/battle/folder battle

you can also use github path

    checkio eoc-get-git https://github.com/CheckiO/EoC-battle battle

- The last step is actually **run the battle**. Running buttle requires battle configuration file. It describes what kind of troops and buildings are on the battle now and source code they are using to run the battle. The configuration file is .py file with dict PLAYERS in it.

    checkio eoc-battle battle /path/to/config/file/battle.py

or you can use a generated default battle file in your solutions folder

    checkio eoc-battle battle


## Balance

Battle configuration file contains information about units and buildings on the battle field. For example it says that we have a Sentry Gun level 5 on the battle field. But in order to run the battle we need to know what stats level 5 has, how many hit-points Sentry  Gun level 5 has etc..

Information about all stats of all buildings, units, modules atc we called *balace* and it includes into the battle docker image during your battle build. Building process using repository https://github.com/CheckiO/eoc-balance . The same repository is Empire of Code is using.

If balance is changed you need to rebuild your battle using command `checkio eoc-get-git`

But one more option here is to link a balance folder during the run process

    checkio eoc-battle --balance /path/to/eoc-balance/ battle /path/to/battle.py



## Folder Structure

 - *interfaces* - folder is responsable for showing battle result 
 - *interfaces/checkio_cli* - showing battle result for checkio-client
 - *verification* - running the battle
 - *envs* - every building has a source code. This folder is using for running this source code for different interpretators
 - *envs/python_3/main.py* - script that runs users code
 - *envs/python_3/battle* - battle module that can be improted from users source-code in order to send commands to verification server
 - *verification/src* - referee. All verefication process starts here.
 - *verification/src/referee.py* - verification proccess starts in this module
 - *verification/src/enviroment.py* - this file is using for network protocol
 - *verification/src/fight_handler.py* - the main handler which is using in referee for controlling battle
 - *verification/src/fight_item.py* - items are participatiung on the battle. Flagman, Unit, CoommandCenter those are Items on the battle
 - *verification/src/fight_logger.py* - module that responsable for sending battle results to use
 - *verification/src/sub_items.py* - items, during the battle, can generate subitem. For example - rocket is an subitem of RocketTower.
 - *verification/src/modules.py* - describe modules that can be used by items.
 - *verification/src/actions/* - items that can be controlled by code are using actions module 

## Step by step running a battle verification process (referee)

Let's take as an example the following config

	ATTACKER_CODE = """
	from battle import commander
	craft_client = commander.CraftClient()
	craft_client.do_land_units()
	def unit_landed(data):
	    unit_client = commander.UnitClient(data['id'])
	    #unit_client.do_teleport([30, 24])
	    def search_and_destroy(data=None):
	        enemy = unit_client.ask_nearest_enemy()
	        unit_client.do_attack(enemy['id'])
	        unit_client.when_im_idle(search_and_destroy)
	    search_and_destroy()
	craft_client.when_unit_landed(unit_landed)
	"""
	DEF_CODE_01 = """
	from battle import commander
	tower_client = commander.Client()
	def search_next_target(data, **kwargs):
	    enemies = tower_client.ask_enemy_items_in_my_firing_range()
	    if enemies:
	        unit_in_firing_range(enemies[0])
	    else:
	        tower_client.when_enemy_in_range(unit_in_firing_range)
	def unit_in_firing_range(data, **kwargs):
	    tower_client.attack_item(data['id'])
	    tower_client.when_im_idle(search_next_target)
	tower_client.when_enemy_in_range(unit_in_firing_range)
	"""
	PLAYERS = {'codes':{
	    '0': {
	      'def_code.py': DEF_CODE_01,
	      },
	    '1': {
	      'attacker.py':ATTACKER_CODE,
	      },
	  },
	 'is_stream': True,
	 'map_elements': [{'level': 1,
	                   'player_id': 0,
	                   'status': 'idle',
	                   'tile_position': [20, 18],
	                   'type': 'commandCenter'},
	                  {'code': 'def_code.py',
	                   'level': 5,
	                   'player_id': 0,
	                   'status': 'idle',
	                   'tile_position': [21, 23],
	                   'type': 'sentryGun'},
	                  {'code': 'def_code.py',
	                   'level': 5,
	                   'player_id': 0,
	                   'status': 'idle',
	                   'tile_position': [25, 23],
	                   'modules': [
	                      'u.rateOfFire.lvl1',
	                      'u.fireRange.lvl1'
	                   ],
	                   'type': 'sentryGun'},
	                  {'level': 2,
	                   'player_id': 0,
	                   'status': 'idle',
	                   'tile_position': [25, 19],
	                   'type': 'crystaliteFarm'},
	                  {'code': 'attacker.py',
	                   'craft_id': 1,
	                   'level': 1,
	                   'player_id': 1,
	                   'type': 'craft',
	                   'modules': [],
	                   'unit': {'level': 3,
	                            'type': 'infantryBot'},
	                   'unit_quantity': 3},
	                  {'code': 'attacker.py',
	                   'craft_id': 2,
	                   'level': 1,
	                   'player_id': 1,
	                   'type': 'craft',
	                   'unit': {'level': 1,
	                            'type': 'heavyBot'},
	                   'unit_quantity': 1},
	                  {'code': 'attacker.py',
	                   'craft_id': 3,
	                   'level': 1,
	                   'player_id': 1,
	                   'type': 'craft',
	                   'unit': {'level': 3,
	                            'type': 'rocketBot'},
	                   'unit_quantity': 2},
	                   ],
	 'map_size': [40, 40],
	 'players': [{'defeat': ['center'], 'env_name': 'python_3', 'id': 0},
	             {'defeat': ['units', 'time'], 'env_name': 'python_3', 'id': 1}],
	 'rewards': {'adamantite': 400, 'crystalite': 150},
	 'time_limit': 30}

One important key I would like to point right away is "is_stream" key. If it is True - then you will see the results in real time, if False - all the results will be saved in one file

Running process of any missions for EoC (including Battle) starts with launching two containers. One is for referee and another one is for interface

*interfaces/checkio_cli/src/interface.py FightHandler* receives a source code of your config file, extracts dicts PLAYERS from it and pass it to referee using API.

*verification/src/referee.py Referee* is the main referee class, which also includes handlers. In our case we have only once handler battle.

*verification/src/fight_handler.py FightHandler* is main handler for battle. In the handler you can find the whole information of the current battle. The battle starts with method *FightHandler.start*

The main goal of method *start* is to generate dict *self.fighters* {object.id: FightItem} and starts all generated FightItems.

*verification/src/fight_item.py FightItem.start* is for executable Items (It means Items that has code). It launches the code using *BattleEnvironmentsController* and store it in *self._env*

*verification/src/environment.py BattleEnvironmentsController* is responsible for reading stdin and stdout from the clients code, sending commands to client and receiving commands from it.

*verification/src/fight_item.py FightItem.handle_result* FightItem.starts starts endles loop the receives commands from clients code and use it in this function.

*verification/src/fight_item.py FightItem.init_handlers* Client can send only 3 kinds of commands:

 - set_action - set command to a unit. For Example 'attack' - a command, that will be set for unit, and unit will do everything for attacking (moving to a target, charging and fire). Action is usually something that takes several frames to finish. 
 - subscribe - subscribe to a specific event in the FightHandler. 
 - command - send a specific command to a unit. Command is something that executes right away and on the current frame.

*verification/src/actions/* ItemActions is responsable for actions and commands. When FightItem initiates it also creates object `self._actions_handlers` for different type of FightItem we create different ItemActions. All the available actions are listed in *verification/src/actions/*

Actions and commands are working in pretty much the same way. The only difference between action and command is that result of parsing action will be saved to attribute `self.action` for FightItem, and when the same object of ItemActions will be process data from `self.action` during frame calculation. The result of this processing will be stored in `self._state` of FightItem and later this data will be shown to user in order to animate unit (or building)

Subscription. Since we covered first two, let's describe subscriptions as well.

*verification/src/fight_handler.py FightHandler.subscribe(event_name, item_id, lookup_key, data)* is responsable for subscription. lookup_key is a unique key for client. This key is needed to recognize event on the senrver side when it raise.

Every new subscription will be added into dict EVENTS of object FightHandler. It is dict of list {event name : list of subscriptions}. That is pretty much it. Usually in the end on frame calculation we have list of function which starts with `_send` those functions are using function `_send_event_` in order to raise an event to the subscribers

*verification/src/fight_handler.py FightHandler._send_event(event_name, check_function, data_function)* the function simply go through all the subscriptions for event name, if check_function returns True - data function generates data for the receiver and send it back. check_function and data_function receive two argumants - event (dict with data that was setted up during event setup) receiver (fight item for testing)

One important thing. Every time when system sends event data it also send information about the map and units on the map. And detail information about reveiver.

*verification/src/fight_handler.py FightHandler.compute_frame* - when the battle started FightHandler starts calculating frames by perodically calling function compute_frame. It goes through all the available fighters and executes their current action, It also goes through the all waiting events. As the last step system tries to figure if we have a winner already.

## Step by step running a battle client-code.

As you can see in our example we have 2 defending building with the same code

	{'code': 'def_code.py',
	'level': 5,
	'player_id': 0,
	'status': 'idle',
	'tile_position': [21, 23],
	'type': 'sentryGun'},

and

	{'code': 'def_code.py',
	'level': 5,
	'player_id': 0,
	'status': 'idle',
	'tile_position': [25, 23],
	'modules': [
	  'u.rateOfFire.lvl1',
	  'u.fireRange.lvl1'
	],
	'type': 'sentryGun'},

They both have the same code `def_code.py`. And we have three crafts (attackers)

	{'code': 'attacker.py',
	'craft_id': 1,
	'level': 1,
	'player_id': 1,
	'type': 'craft',
	'modules': [],
	'unit': {'level': 3,
	        'type': 'infantryBot'},
	'unit_quantity': 3},
	{'code': 'attacker.py',
	'craft_id': 2,
	'level': 1,
	'player_id': 1,
	'type': 'craft',
	'unit': {'level': 1,
	        'type': 'heavyBot'},
	'unit_quantity': 1},
	{'code': 'attacker.py',
	'craft_id': 3,
	'level': 1,
	'player_id': 1,
	'type': 'craft',
	'unit': {'level': 3,
	        'type': 'rocketBot'},
	'unit_quantity': 2},

all of the crafts has the same code `attacker.py`.

The actual source code of thouse scrips can be found in key "codes". All the players strategies are listes in the dict "codes", because one strategy can import any other strategies.

Let's start with defence source code

	from battle import commander
	tower_client = commander.Client()
	def search_next_target(data, **kwargs):
	    enemies = tower_client.ask_enemy_items_in_my_firing_range()
	    if enemies:
	        unit_in_firing_range(enemies[0])
	    else:
	        tower_client.when_enemy_in_range(unit_in_firing_range)
	def unit_in_firing_range(data, **kwargs):
	    tower_client.attack_item(data['id'])
	    tower_client.when_im_idle(search_next_target)
	tower_client.when_enemy_in_range(unit_in_firing_range)

*verification/envs/python_3/main.py* script that is using to launch a Python client code. 

*verification/envs/python_3/battle/commander.py* module that is using in strategy.

*verification/envs/python_3/battle/commander.py Client* is a base class that is using in users code. It contains all of the commands that can be used 

*verification/envs/python_3/battle/main.py PlayerRefereeClient* Client has an attribute self.CLIENT - it is an object of PlayerRefereeClient. This object is using for sending and receiving commands from referee.

(One important point about dialog between client and referee - **Every request should have a response**.)

As you can see PlayerRefereeClient has all of the commands we have described in referee section set_action, send_command, subscribe. Those methods are translated into Client object with methods "do", "command" and "when" (why they were renamed? I don't know, but I'm sure it should be a reason for that).

On top of that Client has a set of methods that starts with `ask_` . Those methods are using for extracting specific information from env_data and my_data (information that is passed to script with every event and run)

Client also has two methods set_opts and get_opt. When user assign a strategy to a craft or a building. Extra options can be added. That allows user to customize their strategies by simply using extra options.

Now the defence source code looks pretty straight forward. At the very beginning we subscribe on "when_enemy_in_range" then attack enemy by it's ID, then subscribe on "idle" event.

### Crafts and defPlatform.

Every building with code starts as a separate client *verification/envs/python_3/main.py* but some buildings can generate generate units and those units can have their own commands and their own events. System doesn't use indiviual script for each unit but use the same script. It allows you to control your units as a group.

Let's check craft code.

	from battle import commander
	craft_client = commander.CraftClient()
	craft_client.do_land_units()
	def unit_landed(data):
	    unit_client = commander.UnitClient(data['id'])
	    #unit_client.do_teleport([30, 24])
	    def search_and_destroy(data=None):
	        enemy = unit_client.ask_nearest_enemy()
	        unit_client.do_attack(enemy['id'])
	        unit_client.when_im_idle(search_and_destroy)
	    search_and_destroy()
	craft_client.when_unit_landed(unit_landed)

it uses two clients. CraftClient and UnitClient. Snce they have one script they will share one `self.CLIENT`.

## Golosary

 - **battle** - one execution of the referee.
 - **player** - group of units and buildings can be controled by player. Usualy two players can be in the battle
 - **interface** - scripts responcable for visualisation process of running referee.
 - **referee** - the main script for controlling and verefication battle
 - **executable item** - FightItem that has a code assigned to it
 - **frame** - is like a move, but computed in a real time. 
 - **battle configuration file** - .py file with PLAYERS dict in it. The dict contains all the information about battle. This script is using by interface in order to launch a ballte