from tornado import gen

from checkio_referee.environment.controller import EnvironmentsController
from checkio_referee.environment.client import EnvironmentClient

from tools.terms import ENV


class BattleEnvironmentClient(EnvironmentClient):

    @gen.coroutine
    def run_code(self, code, env_data, my_data):
        # this function is from checkio_referee.environment.client.py
        # it is better to rewrite it in that module so parents can pass some addidion
        # arguments
        result = yield self._request({
            'action': 'run_code',
            'code': code,
            ENV.DATA: env_data,
            ENV.MY_DATA: my_data
        })
        return result

    def confirm(self):
        self.write({
            'status': 200
        })

    def bad_action(self, description=""):
        self.write({
            'status': 400,
            'description': description
        })

    def send_event(self, lookup_key, data):
        self.write({
            'action': 'event',
            'lookup_key': lookup_key,
            'data': data
        })

    @gen.coroutine
    def _request(self, data):
        yield self.write(data)
        response = yield self.read_message()
        return response


class BattleEnvironmentsController(EnvironmentsController):
    ENVIRONMENT_CLIENT_CLS = BattleEnvironmentClient
