from .base import BaseItemActions, euclidean_distance
from sub_items import RocketSubItem
from .exceptions import ActionValidateError
from tools import is_coordinates


class DefenceActions(BaseItemActions):
    pass


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
