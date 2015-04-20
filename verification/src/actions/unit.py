from .base import BaseItemActions, distance_to_point
from .exceptions import ActionValidateError


class UnitActions(BaseItemActions):

    def actions_init(self):
        actions = super().actions_init()
        actions.update({
            'move': self.action_move
        })
        return actions

    def action_attack(self, data):
        enemy = self._fight_handler.fighters.get(data['id'])
        if enemy is None:
            return  # WTF
        distance_to_enemy = distance_to_point(enemy.coordinates, self._item.coordinates)
        item_range = self._item.range
        if distance_to_enemy > item_range:
            return self._move(enemy.coordinates)
        return self._shot(enemy)

    def action_move(self, data):
        target_coordinates = data['coordinates']
        return self._move(target_coordinates)

    def _move(self, target_coordinates):
        speed = self._item.speed * self._fight_handler.GAME_FRAME_TIME
        current_coordinates = self._item.coordinates
        distance = distance_to_point(current_coordinates, target_coordinates)

        new_coordinates = (
            current_coordinates[0] + (speed * (target_coordinates[0] - current_coordinates[0])
                                      / distance),
            current_coordinates[1] + (speed * (target_coordinates[1] - current_coordinates[1])
                                      / distance)
        )
        self._item.set_coordinates(new_coordinates)

        return {
            'action': 'move',
            'from': current_coordinates,
            'to': new_coordinates
        }

    def validate_attack(self, action, data):
        enemy = self._fight_handler.fighters.get(data['id'])
        if enemy.player['id'] == self._item.player['id']:
            raise ActionValidateError("Can not attack own item")
