import sys
from queue import Queue

from checkio_executor_python.client import ClientLoop, RefereeClient
from checkio_executor_python.execs import Runner

from battle import commander

Runner.ALLOWED_MODULES += ['battle', 'battle.commander']  # OMFG


def _make_id(target):
    if hasattr(target, '__func__'):
        return id(target.__self__), id(target.__func__)
    return id(target)


class PlayerRefereeClient(RefereeClient):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._events = {}
        self.events_call = Queue()
        self.runner = None

    def set_runner(self, runner):
        self.runner = runner

    def _request(self, data, skipp_result=None):
        data['status'] = 'success'
        return self.request(data, skipp_result, do_not_clean_up=True)

    def request(self, *args, **kwargs):
        do_not_clean_up = kwargs.pop('do_not_clean_up')

        if not do_not_clean_up:
            self.clean_up()

        return super().request(*args, **kwargs)

    def clean_up(self):
        while not self.events_call.empty():
            response = self.events_call.get()
            self._send_event(response['lookup_key'], response['data'])

    def _send_event(self, lookup_key, data):
        callback = self._events[lookup_key]
        callback(data=data)

    def _subscribe(self, lookup_key, callback):
        self._events[lookup_key] = callback

    def wait_actual_response(self, response):
        if response.get('method') != 'event':
            return response

        self.events_call.put(response)
        return self.wait_actual_response(self._get_response_json())

    def actual_request(self, *args, **kwargs):
        response = self._request(*args, **kwargs)
        return self.wait_actual_response(response)

    def subscribe(self, event, callback, data=None):
        lookup_key = _make_id(callback)
        response = self.actual_request({'method': 'subscribe', 'lookup_key': lookup_key,
                                        'event': event, 'data': data})
        if response.get('status') == 200:
            self._subscribe(lookup_key, callback)
            return True
        return False

    def select(self, fields):
        response = self.actual_request({'method': 'select', 'fields': fields})
        return response['data']

    def set_action(self, action, data):
        return self.actual_request({'method': 'set_action', 'action': action, 'data': data})


class PlayerClientLoop(ClientLoop):
    cls_client = PlayerRefereeClient

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client.set_runner(self.runner)


client_loop = PlayerClientLoop(int(sys.argv[1]), sys.argv[2])
commander.Client.set_client(client_loop.client)
client_loop.start()
