import os
import time
import requests
import threading
from dotenv import load_dotenv
from flask import Flask
import sys

load_dotenv()


class WatcherState:
    def __init__(self, ping_timeout: int):
        self.last_ping_time = self._time()
        self.lock = threading.Lock()
        self.ping_timeout = ping_timeout

    # get current time in ms
    def _time(self):
        return round(time.time() * 1000)

    def ping(self):
        with self.lock:
            self.last_ping_time = self._time()

    def has_timed_out(self):
        with self.lock:
            return self._time() - self.last_ping_time > self.ping_timeout

class Discord:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_down(self):
        data = {
                'embeds': [
                    {
                        'title': 'SERVER IS UNREACHABLE',
                        'type': 'rich',
                        'description': 'The server appears to be currently unreachable',
                        'color': int('f54242', 16)
                        }
                    ]
                }

        response = requests.post(self.webhook_url, json=data)
        if response.status_code != 200:
            print("error while trying to send to discord:", response)

    def send_up(self):
        data = {
                'embeds': [
                    {
                        'title': 'SERVER IS REACHABLE AGAIN',
                        'type': 'rich',
                        'description': 'The server appears to have recovered',
                        'color': int('42f569', 16)
                        }
                    ]
                }
        response = requests.post(self.webhook_url, json=data)
        if response.status_code != 200:
            print("error while trying to send to discord:", response)

class FlaskApp:
    def __init__(self, on_ping):
        self.app = Flask(__name__)
        @self.app.route('/ping', methods=['GET'])
        def ping():
            on_ping()
            return '', 200

    def start(self):
        self.app.run(host='0.0.0.0', port=9090)

class Watcher:
    def __init__(self, state: WatcherState, on_down, on_up):
        self.state = state
        self.update_interval = 1
        self.on_down = on_down
        self.on_up = on_up

    def _start(self):
        is_down = False
        while True:
            if is_down:
                if not self.state.has_timed_out():
                    is_down = False
                    self.on_up()
                    sys.stdout.flush()
            else:
                if self.state.has_timed_out():
                    is_down = True
                    self.on_down()
                    sys.stdout.flush()

            time.sleep(self.update_interval)

    def start(self):
        threading.Thread(target=self._start, daemon=True).start()

def main():
    discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    ping_timeout_ms = os.getenv('PING_TIMEOUT_MS')
    if (discord_webhook_url is None or ping_timeout_ms is None):
        raise Exception("missing environment variable(s)")
    ping_timeout_ms = int(ping_timeout_ms)

    state = WatcherState(ping_timeout_ms)
    discord = Discord(discord_webhook_url)
    app = FlaskApp(lambda: state.ping())
    watcher = Watcher(state, lambda: discord.send_down(), lambda: discord.send_up())

    watcher.start() # does not block
    app.start() # blocks

if __name__ == '__main__':
    main()
