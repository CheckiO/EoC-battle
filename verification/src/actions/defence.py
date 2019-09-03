from random import randint

from .base import BaseItemActions, euclidean_distance
from .exceptions import ActionValidateError

from tools import (is_angle, is_coordinates, shortest_distance_between_angles,
                   angle_to_enemy, angle_between_center_vision_and_enemy)
from sub_items import RocketSubItem


class DefenceSentryActions(BaseItemActions):

    def _actual_hit(self, enemy):
        attacker = self._item
        distance_to_enemy = (euclidean_distance(enemy.coordinates, attacker.coordinates) - enemy.size / 2)

        if distance_to_enemy <= attacker.firing_range_always_hit:
            return True

        if distance_to_enemy <= attacker.firing_range:
            normalized_full_distance = attacker.firing_range - attacker.firing_range_always_hit
            normalized_enemy_distance = distance_to_enemy - attacker.firing_range_always_hit
            hit_success_percentage = 100 - int(
                normalized_enemy_distance * (100 - attacker.start_chance) / normalized_full_distance)
            return randint(0, 100) < hit_success_percentage

        return False

    def _charging(self):
        self._item.charging -= self._fight_handler.GAME_FRAME_TIME
        if self._item.charging <= 0:
            self._item.charging = 0
        return {'name': 'charge'}

    def _get_prepared_to_shoot(self):
        if self._item.charging:
            return self._charging()

    def _actual_shot(self, enemy):
        damaged_ids = []
        if self._actual_hit(enemy):
            damaged_ids.extend(enemy.get_shot(self._item.total_damage))

        self._item.charging = self._item.charging_time
        return {
            'name': 'attack',
            'firing_point': enemy.coordinates,
            'aid': enemy.id,
            'damaged': damaged_ids,
        }

    def is_shot_possible(self, enemy_coordinates):
        distance_to_enemy = euclidean_distance(enemy_coordinates, self._item.coordinates)
        if distance_to_enemy > self._item.firing_range:
            return False
        return True

    def _shot(self, enemy):
        prepared_to_shoot = self._get_prepared_to_shoot()
        if prepared_to_shoot:
            return prepared_to_shoot

        if self.is_shot_possible(enemy.coordinates):
            return self._actual_shot(enemy)

        return self._idle()


class DefenceMachineActions(BaseItemActions):

    def _actual_hit(self, enemy):
        return True

    def _shot(self, enemy=None):
        prepared_to_shoot = self._get_prepared_to_shoot()
        if prepared_to_shoot:
            return prepared_to_shoot

        if enemy is not None:
            if self.is_shot_possible(enemy.coordinates):
                return self._actual_shot(enemy)
        else:
            return self._actual_shot()

        if self._item.firing_time > 0:
            return self._cooldown()

        return self._idle()

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

    def _find_targets(self, excluded_targets=None):
        targets = []
        if excluded_targets is None:
            excluded_targets = []
        for event_item in self._fight_handler.get_battle_fighters():
            if event_item.is_dead:
                continue
            if self._item == event_item:
                continue
            if not event_item.coordinates:
                continue
            if event_item in excluded_targets:
                continue
            if self.is_shot_possible(event_item.coordinates):
                targets.append(event_item)

        return targets

    def _actual_shot(self, enemy=None):
        if enemy is None:
            aid = None
            firing_point = None
            targets = self._find_targets()
        else:
            aid = enemy.id
            firing_point = enemy.coordinates
            targets = [enemy]
            targets.extend(self._find_targets(excluded_targets=[enemy]))

        damaged_ids = []
        for target in targets:
            if self._actual_hit(target):
                damaged_ids.extend(target.get_shot(self._item.total_damage))
        self._item.firing_time += self._fight_handler.GAME_FRAME_TIME

        return {
            'name': 'attack',
            'firing_point': firing_point,
            'aid': aid,
            'damaged': damaged_ids,
        }

    def is_shot_possible(self, enemy_coordinates):
        distance_to_enemy = euclidean_distance(enemy_coordinates, self._item.coordinates)
        if distance_to_enemy > self._item.firing_range:
            return False

        angle = angle_between_center_vision_and_enemy(self._item.coordinates, self._item.angle, enemy_coordinates)
        if angle > self._item.field_of_view / 2:
            return False

        return True

    def _get_turned(self, desired_angle):
        angle_difference = shortest_distance_between_angles(desired_angle, self._item.angle)

        if angle_difference == 0:
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

    def actions_init(self):
        actions = super().actions_init()
        actions.update({
            'fire': self.action_fire,
            'turn': self.action_turn,
            'turn_to_fire': self.action_turn_to_fire,
        })
        return actions

    def validate_turn(self, action, data):
        if not is_angle(data.get('angle')):
            raise ActionValidateError('Wrong angle')

    def action_turn(self, data):
        angle = data.get('angle')
        turned = self._get_turned(angle)
        if turned:
            return turned
        return {'name': 'idle'}

    def validate_turn_to_fire(self, action, data):
        enemy = self._fight_handler.fighters.get(data['id'])
        if not is_coordinates(enemy.coordinates):
            raise ActionValidateError('Wrong coordinates')

    def action_turn_to_fire(self, data):
        enemy = self._fight_handler.fighters.get(data['id'])
        if self.is_shot_possible(enemy.coordinates):
            return self._shot(enemy)

        angle = angle_to_enemy(self._item.coordinates, enemy.coordinates)
        turned = self._get_turned(angle)
        if turned:
            return turned
        return {'name': 'idle'}

    def validate_fire(self, action, data):
        pass

    def action_fire(self, data):
        return self._shot()


class DefenceRocketActions(BaseItemActions):

    def _actual_shot(self, enemy):
        attacker = self._item
        attacker.add_sub_item(RocketSubItem(attacker, attacker.coordinates, enemy.coordinates))
        return {
            'name': 'attack',
            'firing_point': enemy.coordinates,
            'aid': enemy.id,
            'damaged': []
        }

    def actions_init(self):
        actions = super().actions_init()
        actions.update({
            'attack_coor': self.action_attack_coor
        })
        return actions

    def validate_attack_coor(self, action, data):
        if not is_coordinates(data.get("coordinates")):
            raise ActionValidateError("Wrong coordinates")

    def action_attack_coor(self, data):
        coordinates = data.get('coordinates')

        charged = self._get_charged(coordinates)
        if charged:
            return charged

        distance_to_enemy = euclidean_distance(coordinates, self._item.coordinates)
        item_firing_range = self._item.firing_range
        if distance_to_enemy > item_firing_range:
            return {'name': 'idle'}
        return self._actual_coor_shot(coordinates)

    def _actual_coor_shot(self, coordinates):
        attacker = self._item
        attacker.add_sub_item(RocketSubItem(attacker, attacker.coordinates, coordinates))

        return {
            'name': 'attack',
            'firing_point': coordinates,
            'aid': None,
            'damaged': []  # TODO:
        }
