from .exceptions import ActionValidateError, ActionSkip
from tools.distances import euclidean_distance
from tools import is_coordinates


class BaseItemActions(object):
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
            'attack': self.action_attack,
            'message': None
        }

    def _idle(self):
        self._fight_handler.send_im_idle(self._item.id)
        return {'action': 'idle'}

    def action_attack(self, data):
        enemy = self._fight_handler.fighters.get(data['id'])
        if enemy is None:
            raise Exception("No enemy")
            return  # WTF

        return self._shot(enemy)

    def _shot(self, enemy):
        attacker = self._item
        attacker.charging += self._fight_handler.GAME_FRAME_TIME * attacker.rate_of_fire
        if attacker.charging < 1:
            return {
                'action': 'charge',
                'firing_point': enemy.coordinates,
                'aid': enemy.id
            }

        enemy.hit_points -= attacker.damage_per_shot
        if enemy.hit_points <= 0:
            self._dead(enemy)

        attacker.charging -= 1
        return {
            'action': 'attack',
            'firing_point': enemy.coordinates,
            'aid': enemy.id,
            'damaged': [enemy.id],  # TODO:
        }

    def _dead(self, enemy):
        enemy.set_state_dead()
        self._fight_handler.send_death_event(enemy.id)
        self._fight_handler.unsubscribe(enemy)

    def parse_action_data(self, action, data):
        if action not in self._actions:
            raise NotImplementedError  # TODO: custom exception

        validator = getattr(self, 'validate_{}'.format(action), None)
        if validator is not None:
            validator(action, data)
        return {
            'name': action,
            'data': data,
        }

    def validate_attack(self, action, data):
        enemy = self._fight_handler.fighters.get(data['id'])
        if enemy.is_dead:
            raise ActionValidateError("The enemy is dead")
        if enemy.player['id'] == self._item.player['id']:
            raise ActionValidateError("Can not attack own item")

        distance_to_enemy = euclidean_distance(enemy.coordinates, self._item.coordinates)
        item_firing_range = self._item.firing_range
        if distance_to_enemy - enemy.size / 2 > item_firing_range:
            raise ActionValidateError("Can not attack item, it's big distance")

    def validate_move(self, action, data):
        if not is_coordinates(data.get("coordinates")):
            raise ActionValidateError("Wrong coordinates")

    def validate_message(self, action, data):
        self._fight_handler.add_messages_to(data['message'], map(int, data['ids']), self._item.id)
        raise ActionSkip

    def do_action(self, action_data):
        validator = getattr(self, 'validate_{}'.format(action_data['name']))
        if validator is not None:
            validator(action_data['name'], action_data["data"])
        action_handler = self._actions[action_data['name']]
        return action_handler(action_data['data'])
