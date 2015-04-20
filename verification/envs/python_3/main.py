import sys
from queue import Queue
from functools import partial

from checkio_executor_python.client import ClientLoop, RefereeClient
from checkio_executor_python.execs import Runner

from battle import commander

EVENTS_CALLS = Queue()
Runner.ALLOWED_MODULES += ['battle', 'battle.commander']  # OMFG


def _make_id(target):
    if hasattr(target, '__func__'):
        return id(target.__self__), id(target.__func__)
    return id(target)


def run_events():
    while not EVENTS_CALLS.empty():
        send_event = EVENTS_CALLS.get()
        send_event()


class PlayerRunner(Runner):

    def __init__(self):
        super().__init__()
        self._is_executing = False

    @property
    def is_executing(self):
        return self._is_executing

    def execute(self, execution_data):
        self._is_executing = True
        return super().execute(execution_data)

    def post_execute(self):
        self._is_executing = False
        run_events()


class PlayerRefereeClient(RefereeClient):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._events = {}
        self.runner = None

    def set_runner(self, runner):
        self.runner = runner

    def _get_response_json(self):
        response = super()._get_response_json()
        if not response:
            return

        method = response.get('method')
        if not method:
            return response

        if method == 'event':
            # In situation, when user code select data but received event,
            # we mut finish select and then run event.
            # It's can be multiple event calls per one select, so all events put into FIFO
            lookup_key, data = response['lookup_key'], response['data']
            send_event = partial(self._send_event, lookup_key=lookup_key, data=data)
            EVENTS_CALLS.put(send_event)
            if not self.runner.is_executing:
                run_events()
            return self._get_response_json()
        return response

    def _request(self, data, skipp_result=None):
        data['status'] = 'success'
        return self.request(data, skipp_result)

    def _send_event(self, lookup_key, data):
        callback = self._events[lookup_key]
        callback(data=data)

    def _subscribe(self, lookup_key, callback):
        self._events[lookup_key] = callback

    def subscribe(self, event, callback, data=None):
        lookup_key = _make_id(callback)
        response = self._request({'method': 'subscribe', 'lookup_key': lookup_key, 'event': event,
                                 'data': data})
        if response.get('status') == 200:
            self._subscribe(lookup_key, callback)
            return True
        return False

    def select(self, fields):
        response = self._request({'method': 'select', 'fields': fields})
        return response['data']

    def set_action(self, action, data):
        return self._request({'method': 'set_action', 'action': action, 'data': data})


class PlayerClientLoop(ClientLoop):
    cls_client = PlayerRefereeClient
    cls_runner = PlayerRunner

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client.set_runner(self.runner)


client_loop = PlayerClientLoop(int(sys.argv[1]), sys.argv[2])
commander.Client.set_client(client_loop.client)
client_loop.start()
