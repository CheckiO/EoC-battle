from .exceptions import ActionValidateError, ActionSkip
from tools.distances import euclidean_distance
from tools import is_coordinates


class BaseItemActions(object):

    def __init__(self, item, fight_handler):
        self._item = item
        self._fight_handler = fight_handler
        self._actions = self.actions_init()
        self._commands = self.commands_init()
        self._one_actions = self.one_actions_init()

    def actions_init(self):
        """
        add actions for custom class
        :return:
        """
        return {
            'attack': self.action_attack,
            'message': None
        }

    def action_attack(self):
        pass

    def commands_init(self):
        return {}

    def one_actions_init(self):
        return {}

    def trans_action(self, name):
        def add_one_time(data):
            return self._item.add_one_action(name, data)
        return add_one_time

    def _idle(self):
        return {'name': 'idle'}

    def parse_action_data(self, action, data):
        if action not in self._actions:
            raise ActionValidateError("Unknown action {}".format(action))

        validator = getattr(self, 'validate_{}'.format(action), None)
        if validator is not None:
            validator(action, data)
        return {
            'name': action,
            'data': data,
        }

    def parse_command_data(self, action, data):
        if action not in self._commands:
            raise ActionValidateError("Unknown command {}".format(action))

        self._commands[action](data)

    def parse_one_action_data(self, action, data):
        self._one_actions[action](data)

    def validate_attack(self, action, data):
        enemy = self._fight_handler.fighters.get(data['id'])
        if enemy.is_dead:
            raise ActionValidateError('The enemy is dead')
        elif enemy.is_departed:
            raise ActionValidateError('The enemy is departed')
        elif enemy.player['id'] == self._item.player['id']:
            raise ActionValidateError('Can not attack own item')

        distance_to_enemy = euclidean_distance(enemy.coordinates, self._item.coordinates) - enemy.size / 2
        item_firing_range = self._item.firing_range
        if distance_to_enemy > item_firing_range:
            raise ActionValidateError("Can not attack item, it's big distance")

    def validate_move(self, action, data):
        if not is_coordinates(data.get("coordinates")):
            raise ActionValidateError("Wrong coordinates")

    def validate_message(self, action, data):
        if self._item.level < 4:
            raise ActionValidateError("Unit level should be at least 4 to use message commands")

        self._fight_handler.add_messages_to(data['message'], map(int, data['ids']), self._item.id)
        raise ActionSkip

    def do_action(self, action_data):
        validator = getattr(self, 'validate_{}'.format(action_data['name']), None)
        if validator is not None:
            validator(action_data['name'], action_data["data"])
        action_handler = self._actions[action_data['name']]
        return action_handler(action_data['data'])
