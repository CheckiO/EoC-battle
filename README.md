Battle is part of the project Empire of Code. The same code is using to run battle in the game.

## How to run the battle?

In order to run the buttle you should do the following steps

 - *Install* checkio-client

    pip install checkio-client

 - *Configure* it for domain epy (In case you will be asked about "key" just put a random numer in it. It is not important at this stage)

    checkio --domain epy config

 - The next step is to *build buttle* using checkio client. In order to do so you will need a docker installed.

    checkio eoc-get-git /path/to/battle/folder battle

you can also use github path

    checkio eoc-get-git https://github.com/CheckiO/EoC-battle battle

- The last step is actually *run the battle*. Running buttle requires configuration file for the battle (or battle setup). It describes what kind of troops and buildings are on the battle now and source code they are using to run the battle. The configuration file is .py file with dict PLAYERS in it.

    checkio eoc-battle battle /path/to/config/file/battle.py

or you can use a generated default battle file in your solutions folder

    checkio eoc-battle battle


## Balance

Configuration file contains information about units and buildings on the battle field. For example it says that we have a Sentry Gun level 5 on the battle field. But in order to run the battle we need to know what stats level 5 has, how many hit-points Sentry  Gun level 5 has etc..

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
 - *verification/src/sub_items.py* - items, during the battle, can generate subitem. For example - rocket is an subitem of RocketTower.
 - *verification/src/modules.py* - describe modules that can be used by items.
 - *verification/src/actions/* - items that can be controlled by code are using actions module 


## Golosary

 - *battle* - one execution of the referee.
 - *player* - group of units and buildings can be controled by player. Usualy two players can be in the battle