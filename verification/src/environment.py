from checkio_referee.environment.controller import EnvironmentsController
from checkio_referee.environment.client import EnvironmentClient


class BattleEnvironmentClient(EnvironmentClient):

    def select_result(self, data):
        self.write({
            'status': 200,
            'data': data
        })

    def confirm(self):
        self.write({
            'status': 200
        })

    def bad_action(self):
        self.write({
            'status': 400
        })

    def send_event(self, lookup_key, data):
        self.write({
            'action': 'event',
            'lookup_key': lookup_key,
            'data': data
        })


class BattleEnvironmentsController(EnvironmentsController):
    ENVIRONMENT_CLIENT_CLS = BattleEnvironmentClient
