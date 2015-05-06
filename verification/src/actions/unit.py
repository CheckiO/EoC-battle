from .base import BaseItemActions, euclidean_distance
from .exceptions import ActionValidateError
from tools import find_route


class UnitActions(BaseItemActions):
    def __init__(self, *args, **kwargs):
        self._route = []
        self._last_map_hash = 0
        self._last_destination_point = (0, 0)

        super().__init__(*args, **kwargs)

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
        distance_to_enemy = euclidean_distance(enemy.coordinates, self._item.coordinates)
        item_range = self._item.range
        if distance_to_enemy > item_range:
            return self._move(enemy.coordinates)
        return self._shot(enemy)

    def action_move(self, data):
        target_coordinates = data['coordinates']
        return self._move(target_coordinates)

    def _move(self, destination_point):
        if (self._fight_handler.map_hash != self._last_map_hash or not self._route or
                self._last_destination_point != tuple(destination_point)):
            self.calculate_route(destination_point)
            self._last_map_hash = self._fight_handler.map_hash
            self._last_destination_point = tuple(destination_point)
        if not self._route:
            return {
                'action': 'stand',
            }
        frame_distance = self._item.speed * self._fight_handler.GAME_FRAME_TIME
        start_point = temp_point = tuple(self._item.coordinates)
        next_point = self._route[0]
        if start_point == next_point:
            return {
                'action': 'stand',
            }
        while self._route and euclidean_distance(temp_point, next_point) < frame_distance:
            frame_distance -= euclidean_distance(temp_point, next_point)
            temp_point = self._route.pop(0)
            next_point = self._route[0] if self._route else next_point

        if not self._route:
            self._item.set_coordinates(temp_point)
            return {
                'action': 'move',
                'from': start_point,
                'to': temp_point
            }
        distance = euclidean_distance(temp_point, next_point)
        new_point = (
            temp_point[0] + (frame_distance / distance) * (next_point[0] - temp_point[0]),
            temp_point[1] + (frame_distance / distance) * (next_point[1] - temp_point[1]))
        self._item.set_coordinates(new_point)

        return {
            'action': 'move',
            'from': start_point,
            'to': new_point
        }

    def calculate_route(self, end_point):
        current_point = self._item.coordinates
        grid_scale = self._fight_handler.GRID_SCALE
        cell_shift = self._fight_handler.CELL_SHIFT
        current_cell = (int(round((current_point[0] - cell_shift) * grid_scale)),
                        int(round((current_point[1] - cell_shift) * grid_scale)))
        end_cell = (int(round((end_point[0] - cell_shift) * grid_scale)),
                    int(round((end_point[1] - cell_shift) * grid_scale)))
        # A-star search
        cell_route = find_route(self._fight_handler.map_grid, current_cell, end_cell)
        self._route = [((c[0] / grid_scale) + cell_shift, (c[1] / grid_scale) + cell_shift)
                       for c in cell_route]

    def validate_attack(self, action, data):
        enemy = self._fight_handler.fighters.get(data['id'])
        if enemy.player['id'] == self._item.player['id']:
            raise ActionValidateError("Can not attack own item")
