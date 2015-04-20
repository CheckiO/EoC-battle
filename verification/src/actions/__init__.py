from .defence import DefenceActions
from .exceptions import ActionValidateError
from .unit import UnitActions


def distance_to_point(point1, point2):
    return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5


class ItemActions(object):

    def __new__(cls, item, *args, **kwargs):
        if cls is ItemActions:
            if item['type'] == 'unit':
                return super(ItemActions, cls).__new__(UnitActions, item, *args, **kwargs)
            if item['type'] == 'defence':
                return super(ItemActions, cls).__new__(DefenceActions, item, *args, **kwargs)
        else:
            return super(ItemActions, cls).__new__(cls, item, *args, **kwargs)

    def __init__(self, item, fight_handler):
        self._item = item
        self._fight_handler = fight_handler
        self._actions = self.actions_init()

    def actions_init(self):
        """
        add actions for custom class
        :return:
        """
        return {
            'attack': self.action_attack
        }

    def action_attack(self, data):
        enemy = self._fight_handler.fighters.get(data['item_id'])
        if enemy is None:
            return  # WTF

        return self._shot(enemy)

    def _shot(self, enemy):
        attacker = self._item
        attacker.charging += self._fight_handler.GAME_FRAME_TIME * attacker.fire_speed
        if attacker.charging < 1:
            return {'action': 'charging'}

        enemy.health -= attacker.damage
        if enemy.health <= 0:
            self._dead(enemy)

        attacker.charging -= 1
        return {
            'action': 'attack',
            'aid': enemy.id,
            'damaged': [enemy.id],  # TODO:
        }

    def _dead(self, enemy):
        self._fight_handler.unsubscribe(enemy)
        self._fight_handler.send_death_event(enemy.id)

    def parse_action_data(self, action, data):
        if action not in self._actions:
            raise NotImplementedError  # TODO: custom exception

        validator = getattr(self, 'validate_{}'.format(action))
        if validator is not None:
            validator(action, data)

        return {
            'name': action,
            'data': data,
        }

    def validate_attack(self, action, data):
        enemy = self._fight_handler.fighters.get(data['item_id'])
        if enemy.player['id'] == self._item.player['id']:
            raise ActionValidateError("Can not attack own item")

        distance_to_enemy = distance_to_point(enemy.coordinates, self._item.coordinates)
        item_range = self._item.range
        if distance_to_enemy > item_range:
            raise ActionValidateError("Can not attack item, it's big distance")

    def do_action(self, action_data):
        action_handler = self._actions[action_data['name']]
        action_handler(action_data['data'])
