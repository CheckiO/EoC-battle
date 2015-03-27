import sys
from checkio_executor_python.client import ClientLoop, RefereeClient
from checkio_executor_python.execs import Runner
from battle import commander


Runner.ALLOWED_MODULES += ['battle', 'battle.commander']  # OMFG


class PlayerRefereeClient(RefereeClient):
    next_subscription_key = 1
    subscriptions = {}

    def _get_response_json(self):
        resp = super()._get_response_json()
        if not resp:
            return resp
        if 'action' not in resp:
            return resp
        attr_name = 'action_' + resp['action']
        if hasattr(self, attr_name):
            getattr(self, attr_name)(resp)
            return self._get_response_json()
        else:
            return resp

    def action_raise(self, data):
        func, w_data = self.subscriptions[data['key']]
        call_data = {
            'data': data['data']
        }
        call_data.update(w_data)
        func(**call_data)

    def _subscribe(self, key, function, data):
        self.subscriptions[key] = (function, data)

    def subscribe(self, what, function, call_data=None, back_data=None):
        key = str(self.next_subscription_key)
        result = self.request({'do': 'subscribe', 'data': call_data, 'key': key, 'what': what})
        if result['ok'] == 'ok':
            self._subscribe(key, function, {
                'what': what,
                'call_data': call_data,
                'back_data': back_data
            })
            self.next_subscription_key += 1


class PlayerRunner(Runner):
    pass


class PlayerClientLoop(ClientLoop):
    cls_client = PlayerRefereeClient
    cls_runner = PlayerRunner

    def subscribe(self, *args, **kwargs):
        return self.client.subscribe(*args, **kwargs)

    def request(self, *args, **kwargs):
        return self.client.request(*args, **kwargs)


client = PlayerClientLoop(int(sys.argv[1]), sys.argv[2])
commander.set_client(client)
client.start()
