## How does it work in general

1. Every item on the map that can be controlled has their own environment
that can send commands to Referee

 - list of available commands can be found in FightItem.init_handlers

2. Referee every FRAME_TIME calculate how the map have changed after applying last
action from every FightItem

 - every item has a type. List of available types can be found actions.ItemActions.get_factory

 - list of available commands is different for different types. For instance list of available commands for unit can be found in actions.unit.UnitActions.actions_init

3. environment can also subscribe on actions in that case during the frame they will get an
event if it will raise

 - all type of events can be found in FightHandler.EVENTS

4. environment can get an addition information about the map.

 - list of available selections can be found in referee.FightItem.method_select


 ## Item parameters

 - "type" -- type of an item.
  * "unit" -- troop that can move and attack.
  * "center" -- main building of defenders.
  * "defender" -- static defense building, like a tower or Machine Gun.
  * "building" -- pacific building of defenders.
  * "obstacle" -- an obstacle on the map, as a rock or a tree.
 - "coordinates" -- coordinates of the center for the buildings or non-sized units.
 - "size" -- all buildings are square. Size is length of the side.
