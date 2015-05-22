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
  * "tower" -- static defense building, like a tower or Machine Gun.
  * "building" -- pacific building of defenders.
  * "obstacle" -- an obstacle on the map, as a rock or a tree.
  
 - "coordinates" -- coordinates of the center for the buildings or non-sized units
 - "size" -- all buildings are square. Size is length of the side. Units don't have size (== 0)
 - "hit_points" -- health point (hp)
 - "damage_per_shot" -- how many hp are reduced for one shot
 - "rate_of_fire" -- shots per second
 - "firing_range" -- the distance for shooting (radius)
 - "speed" -- for units. Speed in titles per second.
 - "area_damage_per_shot" -- if a fighter attack by area, than reduce hp of all items in the circle
 - "area_damage_radius" -- radius of area where items are damaged (if area_damage_per_shot != 0) 
 - "code" -- the code name (file) for this unit
 