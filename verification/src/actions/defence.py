from random import randint

from .base import BaseItemActions
from .exceptions import ActionValidateError

from tools.angles import angle_between_center_vision_and_enemy, angle_to_enemy, shortest_distance_between_angles
from tools.grid import is_angle, is_coordinates
from tools.distances import euclidean_distance
from tools.terms import FEATURE

from effects import gen_effects
from sub_items import RocketSubItem


class DefenceTowerActions(BaseItemActions):

    def _distance_to_enemy(self, enemy):
        return euclidean_distance(enemy.coordinates, self._item.coordinates) - enemy.size / 2

    def _distance_to_coordinates(self, coordinates):
        return euclidean_distance(coordinates, self._item.coordinates)

    def is_shot_possible(self, obj):
        distance_to_obj = self._distance_to_enemy(obj)
        return distance_to_obj <= self._item.firing_range

    def action_attack(self, data):
        enemy = self._fight_handler.fighters.get(data['id'])
        return self._attack(enemy)


class DefenceSentryActions(DefenceTowerActions):

    def _charging(self):
        self._item.charging -= self._fight_handler.GAME_FRAME_TIME
        if self._item.charging <= 0:
            self._item.charging = 0
        return {'name': 'charge'}

    def _get_prepared_to_shoot(self):
        if self._item.charging:
            return self._charging()

    def is_pierce_shot_possible(self, coordinates, angle, obj):

        distance_to_obj = self._distance_to_enemy(obj)
        if distance_to_obj > self._item.firing_range:
            return False

        enemy_angle = angle_between_center_vision_and_enemy(coordinates, angle, obj.coordinates)
        if enemy_angle > 2:
            return False
        return True

    def _find_targets(self, enemy):

        if not self._item.has_feature(FEATURE.PIERCE_SHOT):
            return [enemy]
        targets = [enemy]
        angle = angle_to_enemy(self._item.coordinates, enemy.coordinates)

        for event_item in self._fight_handler.get_active_battle_fighters():
            if enemy == event_item:
                continue
            if self._item.player_id == event_item.player_id:
                continue
            if not event_item.coordinates:
                continue

            if self.is_pierce_shot_possible(self._item.coordinates, angle, event_item):
                targets.append(event_item)

        return targets

    def _shot(self, enemy):
        damaged_ids = []
        if self._hit(enemy):
            effects = gen_effects(self._item.features)
            enemies = self._find_targets(enemy)

            for enemy in enemies:
                enemy_ids = enemy.get_shot(self._item.total_damage, effects)
                damaged_ids.extend(enemy_ids)

        self._item.charging = self._item.charging_time
        return {
            'name': 'attack',
            'firing_point': enemy.coordinates,
            'aid': enemy.id,
            'damaged': damaged_ids,
        }

    def _hit(self, enemy):
        attacker = self._item
        distance_to_enemy = self._distance_to_enemy(enemy)

        if distance_to_enemy <= attacker.firing_range_always_hit:
            return True

        if distance_to_enemy <= attacker.firing_range:
            normalized_full_distance = attacker.firing_range - attacker.firing_range_always_hit
            normalized_enemy_distance = distance_to_enemy - attacker.firing_range_always_hit
            hit_success_percentage = 100 - int(
                normalized_enemy_distance * (100 - attacker.start_chance) / normalized_full_distance)
            return randint(0, 100) < hit_success_percentage

        return False

    def _attack(self, enemy):
        prepared_to_shoot = self._get_prepared_to_shoot()
        if prepared_to_shoot:
            return prepared_to_shoot

        if self.is_shot_possible(enemy):
            return self._shot(enemy)
        return self._idle()


class DefenceMachineActions(DefenceTowerActions):

    def is_shot_possible(self, obj):
        distance_to_obj = self._distance_to_enemy(obj)
        if distance_to_obj > self._item.firing_range:
            return False
        angle = angle_between_center_vision_and_enemy(self._item.coordinates, self._item.angle, obj.coordinates)

        if angle > self._item.field_of_view / 2:
            return False
        return True

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

    def _shot(self, enemy=None):
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
            damaged_ids.extend(target.get_shot(self._item.total_damage))
        self._item.firing_time += self._fight_handler.GAME_FRAME_TIME

        return {
            'name': 'attack',
            'firing_point': firing_point,
            'aid': aid,
            'damaged': damaged_ids,
        }

    def _find_targets(self, excluded_targets=None):
        targets = []
        if excluded_targets is None:
            excluded_targets = []
        for event_item in self._fight_handler.get_active_battle_fighters():
            if self._item == event_item:
                continue
            if not event_item.coordinates:
                continue
            if event_item in excluded_targets:
                continue
            if self.is_shot_possible(event_item):
                targets.append(event_item)

        return targets

    def _attack(self, enemy=None):
        prepared_to_shoot = self._get_prepared_to_shoot()
        if prepared_to_shoot:
            return prepared_to_shoot

        if enemy is not None:
            if self.is_shot_possible(enemy):
                return self._shot(enemy)
        else:
            return self._shot()

        if self._item.firing_time > 0:
            return self._cooldown()
        return self._idle()

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
        return self._idle()

    def validate_turn_to_fire(self, action, data):
        enemy = self._fight_handler.fighters.get(data['id'])
        if not is_coordinates(enemy.coordinates):
            raise ActionValidateError('Wrong coordinates')

    def action_turn_to_fire(self, data):

        enemy = self._fight_handler.fighters.get(data['id'])
        if self.is_shot_possible(enemy):
            return self._attack(enemy)

        angle = angle_to_enemy(self._item.coordinates, enemy.coordinates)
        turned = self._get_turned(angle)
        if turned:
            return turned
        return self._idle()

    def validate_fire(self, action, data):
        pass

    def action_fire(self, data):
        return self._attack()


class DefenceRocketActions(DefenceTowerActions):

    def is_shot_to_coordinates_possible(self, coordinates):
        distance_to_coordinates = self._distance_to_coordinates(coordinates)
        return distance_to_coordinates <= self._item.firing_range

    def _charging(self):
        self._item.charging -= self._fight_handler.GAME_FRAME_TIME
        if self._item.charging <= 0:
            self._item.charging = 0
        return {'name': 'charge'}

    def _get_prepared_to_shoot(self):
        if self._item.charging:
            return self._charging()

    def _shot(self, enemy=None, coordinates=None):
        if enemy is not None:
            aid = enemy.id
            firing_point = enemy.coordinates
        elif coordinates is not None:
            aid = None
            firing_point = coordinates
        else:
            raise ActionValidateError('Wrong attack data')

        self._item.add_sub_item(RocketSubItem(self._item, firing_point))
        self._item.charging = self._item.charging_time

        return {
            'name': 'attack',
            'firing_point': firing_point,
            'aid': aid,
            'damaged': [],
        }

    def _attack(self, enemy):
        prepared_to_shoot = self._get_prepared_to_shoot()
        if prepared_to_shoot:
            return prepared_to_shoot

        if self.is_shot_possible(enemy):
            return self._shot(enemy=enemy)
        return self._idle()

    def actions_init(self):
        actions = super().actions_init()
        actions.update({
            'attack_coordinates': self.action_attack_coordinates
        })
        return actions

    def validate_attack_coordinates(self, action, data):
        if not is_coordinates(data.get('coordinates')):
            raise ActionValidateError('Wrong coordinates')

    def action_attack_coordinates(self, data):
        coordinates = data.get('coordinates')

        prepared_to_shoot = self._get_prepared_to_shoot()
        if prepared_to_shoot:
            return prepared_to_shoot

        if self.is_shot_to_coordinates_possible(coordinates):
            return self._shot(coordinates=coordinates)
        return self._idle()
