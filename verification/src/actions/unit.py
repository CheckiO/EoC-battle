from .base import BaseItemActions
from .exceptions import ActionValidateError

from tools.angles import angle_to_enemy, shortest_distance_between_angles
from tools.grid import is_coordinates, find_route, straighten_route
from tools.distances import euclidean_distance
from tools.terms import OPERATION, ROLE, FEATURE
from sub_items import RocketSubItem, VerticalRocketSubItem, HealSubItem, PowerSubItem


class MineActions(BaseItemActions):
    def actions_init(self):
        return {
            'wait': self.action_wait,
            'detonate': self.action_detonate,
        }

    def action_wait(self, data):
        for enemy in self._fight_handler.fighters.values():
            if enemy.is_gone:
                return

            if enemy.player_id == self._item.player_id:
                continue

            if enemy.role != ROLE.UNIT:
                continue

            distance_to_enemy = euclidean_distance(enemy.coordinates, self._item.coordinates)

            if distance_to_enemy <= self._item.firing_range:
                self._item.detonate()
                break

        return {
            'name': 'idle'
        }

    def action_detonate(self, data):
        self._item.detonator_timer()
        return {
            'name': 'detonate'
        }
        

class FlagActions(BaseItemActions):

    def actions_init(self):
        return {}

    def commands_init(self):
        return {
            'rocket': self.send_rocket,
            'heal': self.send_heal,
            'power': self.send_power,
        }

    def send_rocket(self, data):
        flagman = self._item
        if flagman.use_operation(OPERATION.ROCKET):
            flagman.add_sub_item(VerticalRocketSubItem(flagman, data['coordinates']))

    def send_heal(self, data):
        flagman = self._item
        if flagman.use_operation(OPERATION.HEAL):
            flagman.add_sub_item(HealSubItem(flagman, data['coordinates']))

    def send_power(self, data):
        flagman = self._item
        if flagman.use_operation(OPERATION.POWER):
            flagman.add_sub_item(PowerSubItem(flagman, data['coordinates']))


class CraftActions(BaseItemActions):

    def actions_init(self):
        return {
            'land_units': self.action_land_units,
        }

    def action_land_units(self, data):
        coordinates = data.get('coordinates')

        if coordinates is not None:
            if not self._item.has_feature(FEATURE.LANDING):
                return
            # elif self._item.used_feature(FEATURE.LANDING):
            #     return
            # self._item.use_feature(FEATURE.LANDING)

        if self._item.land_unit(coordinates):
            #print('LAND', self._item.craft_id, self._item.amount_units_in)
            return {
                'name': 'land_units'
            }
        else:
            #print('DONE LANDING', self._item.craft_id, self._item.amount_units_in)
            return self._idle()

    def commands_init(self):
        return {
            'attack': self.forward_by('attack'),
            'depart': self.forward_by('depart'),
            'heavy_protect': self.forward_by('heavy_protect'),
            'move': self.forward_by('move'),
            'moves': self.forward_by('moves'),
            'teleport': self.forward_command_by('teleport'),
        }

    def forward_by(self, command):
        def _forwarded(data):
            unit = self._fight_handler.fighters[data['by']]

            # TODO: check if unit from Craft
            # craft = self._item

            unit.method_set_action(command, data, from_self=False)  
        return _forwarded

    def forward_command_by(self, command):
        def _forwarded(data):
            unit = self._fight_handler.fighters[data['by']]

            # TODO: check if unit from Craft
            # craft = self._item

            unit.method_command(command, data, from_self=False)  
        return _forwarded

    def forward_do_attack(self, data):
        unit = self._fight_handler.fighters[data['by']]

        # TODO: check if unit from Craft
        # craft = self._item

        unit.method_set_action('attack', data, from_self=False)


class UnitActions(BaseItemActions):

    def __init__(self, *args, **kwargs):
        self._route = []
        self._last_map_hash = 0
        self._last_destination_point = (0, 0)
        super().__init__(*args, **kwargs)

    def actions_init(self):
        actions = super().actions_init()
        actions.update({
            'depart': self.action_depart,
            'move': self.action_move,
            'moves': self.action_moves
        })
        return actions

    def one_actions_init(self):
        return {
            'teleport': self.do_teleport,
        }

    def commands_init(self):
        return {
            'teleport': self.trans_action('teleport')
        }

    def _depart(self):
        self._fight_handler.unsubscribe(self._item)
        self._item.set_state_departed()
        return {'name': 'departed'}

    def _move(self, destination_point, stop_then=True):
        self.check_or_create_route(destination_point)
        if not self._route:
            return stop_then and self._stop()

        start_point = tuple(self._item.coordinates)
        # We on the end
        if len(self._route) == 1 and start_point == self._route[0]:
            return stop_then and self._stop()

        frame_distance = self._item.speed * self._fight_handler.GAME_FRAME_TIME
        next_point, current_point = self.process_near_turns(frame_distance)
        if not self._route:
            self._item.set_coordinates(current_point)
            # without it we will not stop
            self._route.append(current_point)
            return {'name': 'move',
                    'from': start_point,
                    'to': current_point}

        distance = euclidean_distance(current_point, next_point)
        new_point = (
            current_point[0] + (frame_distance / distance) * (next_point[0] - current_point[0]),
            current_point[1] + (frame_distance / distance) * (next_point[1] - current_point[1]))

        self._item.set_coordinates(new_point)
        return {'name': 'move',
                'from': start_point,
                'to': new_point}

    def _stop(self):
        return self._idle()

    def get_distance_to_obj(self, obj):
        return euclidean_distance(obj.coordinates, self._item.coordinates) - obj.size / 2

    def calculate_route(self, end_point):
        current_point = self._item.coordinates
        grid_scale = self._fight_handler.GRID_SCALE
        cell_shift = self._fight_handler.CELL_SHIFT
        current_cell = (int(round((current_point[0] - cell_shift) * grid_scale)),
                        int(round((current_point[1] - cell_shift) * grid_scale)))
        end_cell = (int(round((end_point[0] - cell_shift) * grid_scale)),
                    int(round((end_point[1] - cell_shift) * grid_scale)))
        # A-star search
        cell_route = find_route(self._fight_handler.map_grid,
                                self._fight_handler.map_graph,
                                current_cell, end_cell)
        cut_cell_route = straighten_route(self._fight_handler.map_grid, cell_route)
        self._route = [((c[0] / grid_scale) + cell_shift, (c[1] / grid_scale) + cell_shift)
                       for c in cut_cell_route]

    def check_or_create_route(self, destination_point):
        if (self._fight_handler.map_hash != self._last_map_hash or
                not self._route or
                self._last_destination_point != tuple(destination_point)):
            self.calculate_route(destination_point)
            self._last_map_hash = self._fight_handler.map_hash
            self._last_destination_point = tuple(destination_point)

    def process_near_turns(self, distance):
        intermediate_point = tuple(self._item.coordinates)
        next_point = self._route[0]
        while self._route and euclidean_distance(intermediate_point, next_point) < distance:
            distance -= euclidean_distance(intermediate_point, next_point)
            intermediate_point = self._route.pop(0)
            next_point = self._route[0] if self._route else next_point
        return next_point, intermediate_point

    def do_teleport(self, data):

        if not self._item.has_feature(FEATURE.TELEPORT):
            return
        if self._item.used_feature(FEATURE.TELEPORT):
            return
        self._item.use_feature(FEATURE.TELEPORT)
        coordinates = data.get('coordinates')
        self._item.set_coordinates(coordinates)

    def is_shot_possible(self, enemy):
        distance_to_enemy = self.get_distance_to_obj(enemy)
        return distance_to_enemy <= self._item.firing_range

    def _attack(self, enemy):
        prepared_to_shoot = self._get_prepared_to_shoot()
        if prepared_to_shoot:
            return prepared_to_shoot

        if self.is_shot_possible(enemy):
            return self._shot(enemy)
        return self._idle()

    def validate_attack(self, action, data):
        enemy = self._fight_handler.fighters.get(data['id'])
        if enemy.is_dead:
            raise ActionValidateError('The enemy is dead')
        elif enemy.is_departed:
            raise ActionValidateError('The enemy is departed')
        elif enemy.player['id'] == self._item.player['id']:
            raise ActionValidateError('Can not attack own item')

    def action_attack(self, data):
        self._item.departing_time = 0
        enemy = self._fight_handler.fighters.get(data['id'])
        if self.is_shot_possible(enemy):
            return self._attack(enemy)
        return self._move(enemy.coordinates)

    def validate_depart(self, action, data):
        crafts = self._fight_handler.get_crafts()
        if not crafts:
            raise ActionValidateError('No crafts to depart')

    def action_depart(self, data):
        closest_craft = None
        closest_distance = None
        for craft in self._fight_handler.get_crafts():
            craft_distance = self.get_distance_to_obj(craft)
            if closest_distance is None:
                closest_distance = craft_distance
                closest_craft = craft
            else:
                if closest_distance > craft_distance:
                    closest_distance = craft_distance
                    closest_craft = craft

        if self.get_distance_to_obj(closest_craft) > 1:
            coordinates = closest_craft.coordinates
            coordinates = self._fight_handler.adjust_coordinates(*coordinates)
            return self._move(coordinates)

        DEPARTURE_TIME = 0.5
        frame_time = DEPARTURE_TIME * self._fight_handler.GAME_FRAME_TIME
        self._item.departing_time += frame_time
        if self._item.departing_time >= DEPARTURE_TIME:
            return self._depart()
        return {'name': 'depart'}

    def validate_move(self, action, data):
        if not is_coordinates(data.get("coordinates")):
            raise ActionValidateError("Wrong coordinates {}".format(data.get("coordinates")))

    def action_move(self, data):
        self._item.departing_time = 0
        coordinates = data.get('coordinates')
        coordinates = self._fight_handler.adjust_coordinates(*coordinates)
        return self._move(coordinates)

    def validate_moves(self, action, data):
        for coordinates in data.get('steps'):
            if not is_coordinates(coordinates):
                raise ActionValidateError("Wrong coordinates {}".format(coordinates))

    def action_moves(self, data):
        self._item.departing_time = 0
        steps = data.get('steps')
        if not len(steps):
            return self._stop()
        coordinates = steps[0]
        coordinates = self._fight_handler.adjust_coordinates(*coordinates)
        ret = self._move(coordinates, stop_then=False)
        if ret:
            return ret

        data['steps'] = steps[1:]
        return self.action_moves(data)


class InfantryBotActions(UnitActions):

    def _charging(self):
        self._item.charging -= self._fight_handler.GAME_FRAME_TIME
        if self._item.charging <= 0:
            self._item.charging = 0
        return {'name': 'charge'}

    def _get_prepared_to_shoot(self):
        if self._item.charging:
            return self._charging()

    def _shot(self, enemy):
        firing_point = enemy.coordinates
        self._item.charging = self._item.charging_time
        damaged_ids = enemy.get_shot(self._item.total_damage)

        return {
            'name': 'attack',
            'firing_point': firing_point,
            'aid': enemy.id,
            'damaged': damaged_ids,
        }


class HeavyBotActions(UnitActions):

    def actions_init(self):
        actions = super().actions_init()
        actions.update({
            'heavy_protect': self.action_heavy_protect,
        })
        return actions

    def _cooldown(self):
        cooldown_time = (self._item.firing_time_limit * self._fight_handler.GAME_FRAME_TIME /
                         self._item.full_cooldown_time)
        self._item.firing_time -= cooldown_time

        if self._item.firing_time <= 0:
            self._item.firing_time = 0

        firing_percentage = (self._item.firing_time / self._item.firing_time_limit) * 100
        if firing_percentage <= self._item.min_percentage_after_overheat:
            self._item.overheated = False
        return {'name': 'cooldown'}

    def _get_prepared_to_shoot(self):
        if self._item.overheated:
            return self._cooldown()

        if self._item.firing_time > self._item.firing_time_limit:
            self._item.overheated = True
            return self._cooldown()

    def _hit(self, enemy):
        return True

    def _shot(self, enemy):
        targets = [enemy]
        damaged_ids = []
        for target in targets:
            if self._hit(target):
                damaged_ids.extend(target.get_shot(self._item.total_damage))
        self._item.firing_time += self._fight_handler.GAME_FRAME_TIME

        return {
            'name': 'attack',
            'firing_point': enemy.coordinates,
            'aid': enemy.id,
            'damaged': damaged_ids,
        }

    def _attack(self, enemy):
        prepared_to_shoot = self._get_prepared_to_shoot()
        if prepared_to_shoot:
            return prepared_to_shoot

        if self.is_shot_possible(enemy):
            return self._shot(enemy)

        if self._item.firing_time > 0:
            return self._cooldown()
        return self._idle()

    def _get_turned(self, desired_angle):
        angle_difference = shortest_distance_between_angles(desired_angle, self._item.angle)

        if angle_difference < 1:
            return

        if abs(angle_difference) < self._item.rate_of_turn:
            turn = abs(angle_difference)
        else:
            turn = self._item.rate_of_turn

        if angle_difference > 0:
            self._item.angle += turn
        else:
            self._item.angle -= turn

        if self._item.angle > 360:
            self._item.angle = self._item.angle - 360
        elif self._item.angle < 0:
            self._item.angle = 360 + self._item.angle

        return {'name': 'turn'}

    def _move(self, destination_point, stop_then=True):
        self.check_or_create_route(destination_point)
        if not self._route:
            return stop_then and self._stop()

        start_point = tuple(self._item.coordinates)
        # We on the end
        if len(self._route) == 1 and start_point == self._route[0]:
            return stop_then and self._stop()

        frame_distance = self._item.speed * self._fight_handler.GAME_FRAME_TIME
        next_point, current_point = self.process_near_turns(frame_distance)

        if not self._route:
            self._item.set_coordinates(current_point)
            # without it we will not stop
            self._route.append(current_point)
            return {'name': 'move',
                    'from': start_point,
                    'to': current_point}

        angle = angle_to_enemy(current_point, next_point)
        turned = self._get_turned(angle)
        if turned:
            return turned

        distance = euclidean_distance(current_point, next_point)
        new_point = (
            current_point[0] + (frame_distance / distance) * (next_point[0] - current_point[0]),
            current_point[1] + (frame_distance / distance) * (next_point[1] - current_point[1]))

        self._item.set_coordinates(new_point)
        return {'name': 'move',
                'from': start_point,
                'to': new_point}

    # TODO: some kind of validation?
    def validate_heavy_protect(self, action, data):
        pass

    def action_heavy_protect(self, data):
        if not self._item.has_feature(FEATURE.HEAVY_PROTECT):
            return {'name': 'idle'}
        if self._item.used_feature(FEATURE.HEAVY_PROTECT):
            return {'name': 'heavy_protect'}
        self._item.use_feature(FEATURE.HEAVY_PROTECT)

        self._item.original_speed = 0
        self._item.speed = 0

        self._state = {'name': 'heavy_protect'}
        return {'name': 'heavy_protect'}


class RocketBotActions(UnitActions):

    def _charging(self):
        self._item.charging -= self._fight_handler.GAME_FRAME_TIME
        if self._item.charging <= 0:
            self._item.charging = 0
        return {'name': 'charge'}

    def _get_prepared_to_shoot(self):
        if self._item.charging:
            return self._charging()

    def _shot(self, enemy):
        firing_point = enemy.coordinates
        self._item.add_sub_item(RocketSubItem(self._item, self._item.coordinates, firing_point))
        self._item.charging = self._item.charging_time

        return {
            'name': 'attack',
            'firing_point': firing_point,
            'aid': enemy.id,
            'damaged': [],
        }
