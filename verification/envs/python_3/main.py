import os
import sys
import logging
from queue import Queue

from checkio_executor_python.client import ClientLoop, RefereeClient
from checkio_executor_python.execs import Runner, StopExecuting

from battle import commander

Runner.ALLOWED_MODULES += ['battle', 'battle.commander']  # OMFG


# WTF ?!?
def _make_id(target):
    if hasattr(target, '__func__'):
        return id(target.__self__), id(target.__func__)
    return id(target), None


class PlayerRefereeRunner(Runner):
    def __init__(self, *args, **kwargs):
        self._events = {}
        super().__init__(*args, **kwargs)

    def action_event(self, data):
        lookup_key = tuple(data['lookup_key'])
        callback = self._events[lookup_key]
        try:
            callback(data['data'])
        except Exception as e:
            logging.error(e, exc_info=True)

    def subscribe(self, lookup_key, callback):
        self._events[lookup_key] = callback


class PlayerRefereeClient(RefereeClient):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._events = {}
        self.events_call = Queue()
        self.runner = None
        self._env_data = {}
        self._my_data = {}

    def grab_env_data(self, response):
        try:
            self._env_data = response.pop('__env_data')
        except KeyError:
            pass

        try:
            self._my_data = response.pop('__my_data')
        except KeyError:
            pass

        return response

    def set_runner(self, runner):
        self.runner = runner

    def request(self, *args, skip_clean_up=None, **kwargs):
        if not skip_clean_up:
            self.clean_up()

        return super().request(*args, **kwargs)

    def clean_up(self):
        while not self.events_call.empty():
            response = self.events_call.get()
            self.runner.action_event(response)

    def wait_actual_response(self, response):
        if response.get('action') != 'event':
            return response

        self.events_call.put(response)
        return self.wait_actual_response(self._get_response_json())

    def actual_request(self, data, *args, **kwargs):
        data['status'] = 'success'  # hack because of backward requesting
        response = self.request(data, *args, **kwargs)
        return self.wait_actual_response(response)

    def subscribe(self, event, callback, data=None):
        def _grab_call_back(data):
            data = self.grab_env_data(data)
            return callback(data)
        lookup_key = _make_id(_grab_call_back)
        response = self.actual_request({'method': 'subscribe', 'lookup_key': lookup_key,
                                        'event': event, 'data': data})
        if response.get('status') == 200:
            self.runner.subscribe(lookup_key, _grab_call_back)
            return True
        return False

    def select(self, fields):
        response = self.actual_request({'method': 'select', 'fields': fields})
        return response['data']

    def set_action(self, action, data):
        return self.actual_request({'method': 'set_action', 'action': action, 'data': data})

    def send_command(self, action, data):
        return self.actual_request({'method': 'command', 'action': action, 'data': data})


class PlayerClientLoop(ClientLoop):
    cls_client = PlayerRefereeClient
    cls_runner = PlayerRefereeRunner

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client.set_runner(self.runner)

    def start(self):
        self.set_os_permissions()
        execution_data = self.client.request({
            'status': 'connected',
            'environment_id': self.environment_id,
            'pid': os.getpid(),
        })
        execution_data = self.client.grab_env_data(execution_data)
        while True:
            try:
                results = self.runner.execute(execution_data)
            except StopExecuting:
                results = None
            execution_data = self.client.request(results)


client_loop = PlayerClientLoop(int(sys.argv[1]), sys.argv[2])
commander.Client.set_client(client_loop.client)
client_loop.start()
