from random import randint

from .base import BaseItemActions, euclidean_distance
from sub_items import RocketSubItem
from .exceptions import ActionValidateError
from tools import is_coordinates


class DefenceActions(BaseItemActions):
    pass


class DefenceSentryActions(BaseItemActions):

    def _actual_shot(self, enemy):
        attacker = self._item

        damaged_ids = []
        if self._actual_hit(enemy):
            damaged_ids = enemy.get_shoted(attacker.total_damage)

        return {
            'name': 'attack',
            'firing_point': enemy.coordinates,
            'aid': enemy.id,
            'damaged': damaged_ids,  # TODO:
        }

    def _actual_hit(self, enemy):
        attacker = self._item
        enemy_range = (euclidean_distance(enemy.coordinates, attacker.coordinates) - enemy.size / 2)

        if enemy_range <= attacker.firing_range_always_hit:
            return True

        if enemy_range <= attacker.firing_range:
            relative_full_distance = attacker.firing_range - attacker.firing_range_always_hit
            relative_enemy_distance = enemy_range - attacker.firing_range_always_hit
            hit_success_percentage = 100 - int((relative_enemy_distance * 100) / relative_full_distance)

            if hit_success_percentage < 5:
                hit_success_percentage = 5
            elif hit_success_percentage > 95:
                hit_success_percentage = 95
                
            return randint(0, 100) < hit_success_percentage

        return False


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
