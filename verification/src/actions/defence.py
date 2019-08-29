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


class DefenceMachineActions(BaseItemActions):

    def actions_init(self):
        actions = super().actions_init()
        actions.update({
            'turn': self.action_turn,
            'turn_to_fire': self.action_turn_to_fire,
            'turn_aggressive': self.action_turn_aggressive,
        })
        return actions

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

    def validate_turn_aggressive(self, action, data):
        if not is_angle(data.get('angle')):
            raise ActionValidateError('Wrong angle')

    # TODO dev-118 aggresive-turn
    def action_turn_aggressive(self, data):
        angle = data.get('angle')

    def is_shot_possible(self, enemy_coordinates):
        distance_to_enemy = euclidean_distance(enemy_coordinates, self._item.coordinates)
        if distance_to_enemy > self._item.firing_range:
            return False

        angle = angle_between_center_vision_and_enemy(self._item.coordinates, self._item.angle, enemy_coordinates)
        if angle > self._item.field_of_view / 2:
            return False

        return True

    def _cooldown(self):
        self._item.firing_time -= self._fight_handler.GAME_FRAME_TIME
        if self._item.firing_time <= 0:
            self._item.firing_time = 0
            self._item.on_firing_cooldown = False
        return {'name': 'cooldown'}

    def _get_prepared_to_shoot(self):
        if self._item.on_firing_cooldown:
            return self._cooldown()
        if self._item.firing_time > self._item.firing_time_limit:
            self._item.on_firing_cooldown = True
            return self._cooldown()

    def _actual_shot(self, enemy):
        targets = [enemy]

        for event_item in self._fight_handler.get_battle_fighters():
            if event_item.is_dead:
                continue
            if self._item == event_item:
                continue
            if enemy == event_item:
                continue
            if not event_item.coordinates:
                continue
            if self.is_shot_possible(event_item.coordinates):
                targets.append(event_item)

        damaged_ids = []
        for target in targets:
            if self._actual_hit(target):
                damaged_ids.extend(target.get_shot(self._item.total_damage))
        self._item.firing_time += self._fight_handler.GAME_FRAME_TIME

        return {
            'name': 'attack',
            'firing_point': enemy.coordinates,
            'aid': enemy.id,
            'damaged': damaged_ids,
        }

    def _shot(self, enemy):
        prepared_to_shoot = self._get_prepared_to_shoot()
        if prepared_to_shoot:
            return prepared_to_shoot

        if self.is_shot_possible(enemy.coordinates):
            return self._actual_shot(enemy)

        if self._item.firing_time > 0:
            return self._cooldown()

        return self._idle()


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
