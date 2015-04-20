from checkio_referee.environment.controller import EnvironmentsController
from checkio_referee.environment.client import EnvironmentClient


class BattleEnvironmentClient(EnvironmentClient):

    def select_result(self, data):
        self.write({
            'method': 'select_result',
            'data': data
        })

    def confirm(self):
        self.write({
            'method': 'confirm',
            'status': 200
        })

    def bad_action(self):
        self.write({
            'method': 'confirm',
            'status': 400
        })

    def send_event(self, lookup_key, data):
        self.write({
            'method': 'event',
            'lookup_key': lookup_key,
            'data': data
        })


class BattleEnvironmentsController(EnvironmentsController):
    ENVIRONMENT_CLIENT_CLS = BattleEnvironmentClient
