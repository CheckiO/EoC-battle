import sys
from queue import Queue

from checkio_executor_python.client import ClientLoop, RefereeClient
from checkio_executor_python.execs import Runner

from battle import commander


def _make_id(target):
    if hasattr(target, '__func__'):
        return id(target.__self__), id(target.__func__)
    return id(target)


class PlayerRefereeClient(RefereeClient):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._signals = {}
        self._signals_calls = Queue()


    def _get_response_json(self):
        response = super()._get_response_json()
        if not response:
            return

        method = response.get('method')
        if not method:
            return response

        if method == 'signal':
            # In situation, when user code select data but received signal,
            # we mut finish select and then run signal.
            # It's can be multiple signal calls per one select, so all signals put into FIFO

            self._signals_calls.put({
                'lookup_key': response['lookup_key'],
                'data': response['data']
            })

            new_response = self._get_response_json()

            signal_kwargs = self._signals_calls.get()
            self._send_signal(**signal_kwargs)
            return new_response
        return response

    def _send_signal(self, lookup_key, data):
        callback = self._signals[lookup_key]
        callback(**data)

    def _subscribe(self, lookup_key, callback):
        self._signals[lookup_key] = callback

    def subscribe(self, event, callback, data=None):
        lookup_key = _make_id(callback)
        response = self.request({'method': 'subscribe', 'lookup_key': lookup_key, 'event': event,
                                 'data': data})
        if response.get('status') == 200:
            self._subscribe(lookup_key, callback)

    def select(self, fields):
        return self.request({'method': 'select', 'fields': fields})

    def set_action(self, action, data):
        return self.request({'method': 'set_action', 'action': action, 'data': data})


class PlayerRunner(Runner):
    ALLOWED_MODULES = Runner.ALLOWED_MODULES + ['battle', 'battle.commander']


class PlayerClientLoop(ClientLoop):
    cls_client = PlayerRefereeClient
    cls_runner = PlayerRunner

    def subscribe(self, *args, **kwargs):
        return self.client.subscribe(*args, **kwargs)

    def request(self, *args, **kwargs):
        return self.client.request(*args, **kwargs)


client = PlayerClientLoop(int(sys.argv[1]), sys.argv[2])
commander.Client.set_client(client)
client.start()
