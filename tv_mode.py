#!/usr/bin/env python3
"""Controller-first TV launcher.

All controller input is read through SDL.  Web services receive one keyboard-only bridge through local Chrome DevTools;
Netflix then handles that keyboard input in its content script.  No pointer input is synthesized.
"""
import ctypes as C
import json
import os
import signal
import socket
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import gi
from websockets.sync.client import connect as websocket_connect
gi.require_version('Gdk', '4.0')
gi.require_version('Gtk', '4.0')
from gi.repository import Gdk, GLib, Gtk

APP_ID = 'rocks.shy.VacuumTube'
LOG = Path.home() / '.local' / 'state' / 'tv-mode' / 'launcher.log'
STEAM_LOG = Path.home() / '.local' / 'share' / 'Steam' / 'logs' / 'console_log.txt'
EMBY_URL = 'https://kotflix.local'
ROOT = Path(__file__).resolve().parent
CONFIG = Path(os.environ.get(
    'TV_MODE_CONFIG',
    Path.home() / '.config' / 'tv-mode' / 'services.json',
))
DEFAULT_SERVICES = [
    {
        'name': 'YouTube', 'source': 'VacuumTube', 'tag': 'YOUTUBE',
        'badge': 'badge-youtube', 'description': 'Odtwarzacz YouTube dla TV',
        'kind': 'vacuumtube',
    },
    {
        'name': 'Emby', 'source': 'kotflix.local', 'tag': 'EMBY',
        'badge': 'badge-emby', 'description': 'Domowa biblioteka wideo',
        'kind': 'browser', 'url': EMBY_URL, 'profile': 'emby', 'port': 9223,
        'runtime_name': 'Emby', 'host_resolver': 'MAP kotflix.local 127.0.0.1',
        'ignore_certificate_errors': True,
    },
    {
        'name': 'Netflix', 'source': 'netflix.com', 'tag': 'NETFLIX',
        'badge': 'badge-netflix', 'description': 'Filmy, seriale i programy',
        'kind': 'browser', 'url': 'https://www.netflix.com/browse',
        'profile': 'netflix', 'port': 9224,
        'runtime_name': 'Netflix',
    },
    {
        'name': 'Apple TV+', 'source': 'tv.apple.com', 'tag': 'APPLE TV+',
        'badge': 'badge-apple', 'description': 'Katalog premium i seriale',
        'kind': 'browser', 'url': 'https://tv.apple.com/',
        'profile': 'apple', 'port': 9225,
        'runtime_name': 'AppleTV',
    },
    {
        'name': 'Canal+', 'source': 'canalplus.com', 'tag': 'CANAL+',
        'badge': 'badge-canal', 'description': 'TV i seriale w jednym pakiecie',
        'kind': 'browser', 'url': 'https://www.canalplus.com/pl/',
        'profile': 'canal', 'port': 9226,
        'runtime_name': 'CanalPlus',
    },
    {
        'name': 'Xbox Cloud', 'source': 'xbox.com/play', 'tag': 'XBOX',
        'badge': 'badge-xbox', 'description': 'Gry z chmury na telewizorze',
        'kind': 'browser', 'url': 'https://www.xbox.com/play',
        'profile': 'xbox-cloud', 'port': 9227,
        'runtime_name': 'XboxCloud',
    },
]


def log(message):
    line = f"{datetime.now().astimezone().isoformat(timespec='seconds')} — TV mode: {message}\n"
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open('a') as output:
        output.write(line)


def load_services():
    value = DEFAULT_SERVICES
    if CONFIG.exists():
        try:
            value = json.loads(CONFIG.read_text())
        except (OSError, json.JSONDecodeError) as error:
            log(f'nie udało się odczytać konfiguracji usług: {error}; używam domyślnej listy')
        if not isinstance(value, list) or not value:
            log('konfiguracja usług jest pusta lub niepoprawna; używam domyślnej listy')
            value = DEFAULT_SERVICES
    for index, service in enumerate(value):
        if service.get('kind') == 'browser':
            service.setdefault('runtime_name', service['profile'].replace('-', '').title())
            service.setdefault('port', 9223 + index)
    return value


def browser_command(service, profile):
    browser = shutil.which('google-chrome') or shutil.which('google-chrome-stable')
    if not browser:
        browser = shutil.which('chromium') or shutil.which('chromium-browser')
    if browser:
        command = [browser]
    elif shutil.which('flatpak'):
        command = [
            '/usr/bin/flatpak', 'run', '--nosocket=wayland', '--socket=x11',
            '--command=chrome', 'com.google.Chrome',
        ]
    else:
        raise RuntimeError('Nie znaleziono Google Chrome/Chromium ani Flatpaka')
    command.extend([
        f'--user-data-dir={profile}', '--ozone-platform=x11', '--kiosk',
        '--no-first-run', '--no-default-browser-check',
        '--remote-debugging-address=127.0.0.1',
        f"--remote-debugging-port={service['port']}",
        '--remote-allow-origins=http://localhost',
    ])
    if service.get('host_resolver'):
        resolver = service['host_resolver']
        if resolver.endswith('127.0.0.1'):
            resolver = f"MAP kotflix.local {socket.gethostbyname('kotflix.local')}"
        command.append(f'--host-resolver-rules={resolver}')
    if service.get('ignore_certificate_errors'):
        command.append('--ignore-certificate-errors')
    command.append(service['url'])
    return command


class Controllers:
    """Poll all SDL GameController devices and merge their pressed buttons."""
    BUTTONS = {
        0: 'a', 1: 'b', 2: 'x', 3: 'y',
        4: 'view', 6: 'menu', 9: 'lb', 10: 'rb',
        11: 'up', 12: 'down', 13: 'left', 14: 'right',
    }

    def __init__(self):
        self.sdl = C.CDLL('libSDL2-2.0.so.0')
        declarations = [
            ('SDL_SetHint', C.c_int, [C.c_char_p, C.c_char_p]),
            ('SDL_Init', C.c_int, [C.c_uint]),
            ('SDL_NumJoysticks', C.c_int, []),
            ('SDL_IsGameController', C.c_int, [C.c_int]),
            ('SDL_GameControllerOpen', C.c_void_p, [C.c_int]),
            ('SDL_GameControllerGetAttached', C.c_int, [C.c_void_p]),
            ('SDL_GameControllerClose', None, [C.c_void_p]),
            ('SDL_GameControllerGetButton', C.c_ubyte, [C.c_void_p, C.c_int]),
            ('SDL_GameControllerGetAxis', C.c_short, [C.c_void_p, C.c_int]),
            ('SDL_GameControllerUpdate', None, []),
            ('SDL_PumpEvents', None, []),
        ]
        for name, result, args in declarations:
            function = getattr(self.sdl, name)
            function.restype, function.argtypes = result, args
        self.sdl.SDL_SetHint(b'SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS', b'1')
        if self.sdl.SDL_Init(0x2000 | 0x0200 | 0x4000) != 0:
            raise RuntimeError('SDL could not initialize controller support')
        self.pads = []
        self.next_scan = 0
        self.last_count = None

    def scan(self):
        for pad in self.pads:
            self.sdl.SDL_GameControllerClose(pad)
        self.pads = []
        for index in range(self.sdl.SDL_NumJoysticks()):
            if self.sdl.SDL_IsGameController(index):
                pad = self.sdl.SDL_GameControllerOpen(index)
                if pad:
                    self.pads.append(pad)
        if len(self.pads) != self.last_count:
            log(f'wykryte kontrolery SDL: {len(self.pads)}')
            self.last_count = len(self.pads)

    def pressed(self):
        self.sdl.SDL_PumpEvents()
        self.sdl.SDL_GameControllerUpdate()
        if time.monotonic() >= self.next_scan:
            self.next_scan = time.monotonic() + 1
            self.scan()
        keys = set()
        for pad in self.pads:
            if not self.sdl.SDL_GameControllerGetAttached(pad):
                continue
            for number, key in self.BUTTONS.items():
                if self.sdl.SDL_GameControllerGetButton(pad, number):
                    keys.add(key)
            horizontal = self.sdl.SDL_GameControllerGetAxis(pad, 0)
            vertical = self.sdl.SDL_GameControllerGetAxis(pad, 1)
            if horizontal < -16000:
                keys.add('left')
            elif horizontal > 16000:
                keys.add('right')
            if vertical < -16000:
                keys.add('up')
            elif vertical > 16000:
                keys.add('down')
        return keys

    def close(self):
        for pad in self.pads:
            self.sdl.SDL_GameControllerClose(pad)
        self.pads = []


class ChromeKeyboard:
    """Deliver keyboard events to the locally launched Chrome instance.

    Chrome's X11 focus handling in Game Mode discards uinput keyboard events.
    The local DevTools endpoint is limited to the isolated Chrome process and
    lets TV mode deliver the same keyboard events directly to its page.  It
    never sends pointer events or reads page content.
    """
    KEYS = {
        'up': ('ArrowUp', 'ArrowUp', 38), 'down': ('ArrowDown', 'ArrowDown', 40),
        'left': ('ArrowLeft', 'ArrowLeft', 37), 'right': ('ArrowRight', 'ArrowRight', 39),
        'lb': ('F7', 'F7', 118), 'rb': ('F8', 'F8', 119),
        'a': ('Enter', 'Enter', 13), 'b': ('Escape', 'Escape', 27),
        'Space': (' ', 'Space', 32), 'KeyM': ('m', 'KeyM', 77),
        'TimelineLeft': ('ArrowLeft', 'ArrowLeft', 37),
        'TimelineRight': ('ArrowRight', 'ArrowRight', 39),
    }

    def __init__(self, services):
        self.ports = {
            service['runtime_name']: service['port']
            for service in services if service.get('kind') == 'browser'
        }
        self.netflix_source = (
            ROOT / 'scripts' / 'netflix-focus.js'
        ).read_text()
        self.browser_source = (
            ROOT / 'scripts' / 'browser-focus.js'
        ).read_text()

    def endpoint(self, service, browser=False):
        port = self.ports[service]
        path = 'json/version' if browser else 'json/list'
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/{path}', timeout=1) as response:
            data = json.load(response)
        if browser:
            return data['webSocketDebuggerUrl']
        for target in data:
            if target.get('type') != 'page':
                continue
            url = target.get('url', '')
            if service == 'Netflix' and not url.startswith('https://www.netflix.com/'):
                continue
            if service == 'AppleTV' and not ('tv.apple.com' in url or 'apple.com' in url):
                continue
            if service == 'CanalPlus' and not ('canalplus' in url or 'canal' in url):
                continue
            if service == 'XboxCloud' and not ('xbox.com/play' in url or 'xbox.com' in url or 'cloud' in url):
                continue
            return target['webSocketDebuggerUrl']
        raise RuntimeError(f'{service} Chrome has no matching page target')

    @staticmethod
    def command(websocket, method, params=None):
        request_id = 1
        websocket.send(json.dumps({'id': request_id, 'method': method, 'params': params or {}}))
        while True:
            response = json.loads(websocket.recv(timeout=1))
            if response.get('id') == request_id:
                break
        if 'error' in response:
            raise RuntimeError(response['error'].get('message', method))
        return response

    def click_element(self, websocket, selector):
        result = self.command(websocket, 'Runtime.evaluate', {
            'expression': (
                f"""(() => {{
                    const element = document.querySelector({json.dumps(selector)});
                    if (!element) return null;
                    const box = element.getBoundingClientRect();
                    return {{x: box.left + box.width / 2, y: box.top + box.height / 2}};
                }})()"""
            ),
            'returnByValue': True,
        })
        point = result.get('result', {}).get('result', {}).get('value')
        if not point:
            return False
        for event_type in ('mousePressed', 'mouseReleased'):
            self.command(websocket, 'Input.dispatchMouseEvent', {
                'type': event_type,
                'x': point['x'],
                'y': point['y'],
                'button': 'left',
                'clickCount': 1,
            })
        return True

    def click_point(self, websocket, x, y):
        for event_type in ('mousePressed', 'mouseReleased'):
            self.command(websocket, 'Input.dispatchMouseEvent', {
                'type': event_type,
                'x': float(x),
                'y': float(y),
                'button': 'left',
                'clickCount': 1,
            })

    def tap(self, service, action, held_ms=0):
        if action == 'quit':
            with websocket_connect(self.endpoint(service, browser=True), origin='http://localhost', open_timeout=1, close_timeout=1) as websocket:
                self.command(websocket, 'Browser.close')
            return
        if service == 'Netflix':
            expression = (
                f'window.__tvModeNetflixFocus?.handle('
                f'{json.dumps(action)}, {int(held_ms)})'
            )
            with websocket_connect(self.endpoint(service), origin='http://localhost', open_timeout=1, close_timeout=1) as websocket:
                # Netflix only mounts its native player controls after pointer activity.
                # Wake that layer before resolving the gamepad focus target.
                for x, y in ((10, 10), (960, 900)):
                    self.command(websocket, 'Input.dispatchMouseEvent', {
                        'type': 'mouseMoved', 'x': x, 'y': y,
                    })
                time.sleep(0.08)
                result = self.command(websocket, 'Runtime.evaluate', {
                    'expression': expression, 'returnByValue': True,
                })
                value = result.get('result', {}).get('result', {}).get('value')
                if value == 'PlayButton':
                    if not self.click_element(websocket, '[data-uia="player-blocked-play"]'):
                        raise RuntimeError('Netflix play control not found')
                    return
                if value == 'PlayerPause':
                    if not self.click_element(websocket, '[data-uia^="control-play-pause"]'):
                        raise RuntimeError('Netflix play/pause control not found')
                    return
                if isinstance(value, str) and value.startswith('TimelineClick:'):
                    _, x, y = value.split(':', 2)
                    self.click_point(websocket, x, y)
                    return
                if value == 'PlayerBack':
                    if not self.click_element(websocket, '[data-uia="nfplayer-exit"]'):
                        self.command(websocket, 'Page.goBack')
                    return
                if value is not True and not isinstance(value, str):
                    self.install_script_on_connection(websocket, self.netflix_source)
                    result = self.command(websocket, 'Runtime.evaluate', {
                        'expression': expression, 'returnByValue': True,
                    })
                    value = result.get('result', {}).get('result', {}).get('value')
                    if value == 'PlayButton':
                        if not self.click_element(websocket, '[data-uia="player-blocked-play"]'):
                            raise RuntimeError('Netflix play control not found')
                        return
                    if value == 'PlayerPause':
                        if not self.click_element(websocket, '[data-uia^="control-play-pause"]'):
                            raise RuntimeError('Netflix play/pause control not found')
                        return
                    if isinstance(value, str) and value.startswith('TimelineClick:'):
                        _, x, y = value.split(':', 2)
                        self.click_point(websocket, x, y)
                        return
                    if value == 'PlayerBack':
                        if not self.click_element(websocket, '[data-uia="nfplayer-exit"]'):
                            self.command(websocket, 'Page.goBack')
                        return
                if isinstance(value, str):
                    key, code, virtual_key = self.KEYS[value]
                    params = {'key': key, 'code': code, 'windowsVirtualKeyCode': virtual_key,
                              'nativeVirtualKeyCode': virtual_key}
                    self.command(websocket, 'Input.dispatchKeyEvent', {'type': 'keyDown', **params})
                    self.command(websocket, 'Input.dispatchKeyEvent', {'type': 'keyUp', **params})
            if value is not True and not isinstance(value, str):
                raise RuntimeError('Netflix focus script handled no matching element')
            return
        if service != 'Emby':
            expression = (
                f'window.__tvModeBrowserFocus?.handle('
                f'{json.dumps(action)}, {int(held_ms)})'
            )
            with websocket_connect(self.endpoint(service), origin='http://localhost', open_timeout=1, close_timeout=1) as websocket:
                result = self.command(websocket, 'Runtime.evaluate', {
                    'expression': expression, 'returnByValue': True,
                })
                value = result.get('result', {}).get('result', {}).get('value')
                if value is None:
                    self.install_script_on_connection(websocket, self.browser_source, 'window.__tvModeBrowserFocus')
                    result = self.command(websocket, 'Runtime.evaluate', {
                        'expression': expression, 'returnByValue': True,
                    })
                    value = result.get('result', {}).get('result', {}).get('value')
                if value is not True and not isinstance(value, str):
                    raise RuntimeError(f'{service} browser focus script handled no matching element')
            return
        key, code, virtual_key = self.KEYS[action]
        params = {'key': key, 'code': code, 'windowsVirtualKeyCode': virtual_key,
                  'nativeVirtualKeyCode': virtual_key}
        with websocket_connect(self.endpoint(service), origin='http://localhost', open_timeout=1, close_timeout=1) as websocket:
            self.command(websocket, 'Input.dispatchKeyEvent', {'type': 'keyDown', **params})
            self.command(websocket, 'Input.dispatchKeyEvent', {'type': 'keyUp', **params})

    def install_script(self, service, source):
        """Install a content script for this isolated browser session."""
        with websocket_connect(self.endpoint(service), origin='http://localhost', open_timeout=1, close_timeout=1) as websocket:
            ready = 'typeof window.__tvModeNetflixFocus' if service == 'Netflix' else 'typeof window.__tvModeBrowserFocus'
            self.install_script_on_connection(websocket, source, ready)

    def install_script_on_connection(self, websocket, source, ready_expression='typeof window.__tvModeNetflixFocus'):
        self.command(websocket, 'Page.addScriptToEvaluateOnNewDocument', {'source': source})
        result = self.command(websocket, 'Runtime.evaluate', {'expression': source})
        if 'exceptionDetails' in result.get('result', {}):
            raise RuntimeError('Netflix focus script raised an exception')
        ready = self.command(websocket, 'Runtime.evaluate', {
            'expression': ready_expression, 'returnByValue': True,
        })
        if ready.get('result', {}).get('result', {}).get('value') != 'object':
            raise RuntimeError('browser focus script did not expose its handler')


class TvMode(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='local.niusia.TvMode')
        self.window = None
        self.previous = set()
        self.controllers = None
        self.status = 'A uruchamia VacuumTube'
        self.focus_deadline = 0.0
        self.child = None
        self.child_name = None
        self.services = load_services()
        self.chrome_keyboard = ChromeKeyboard(self.services)
        self.selected = 0
        self.browser_repeat = 0.0
        self.browser_hold_button = None
        self.browser_hold_started = 0.0
        self.return_started = 0.0
        self.script_deadline = 0.0
        self.steam_log_position = STEAM_LOG.stat().st_size if STEAM_LOG.exists() else 0
        self.tiles = []
        signal.signal(signal.SIGTERM, self.on_stop_signal)
        signal.signal(signal.SIGHUP, self.on_stop_signal)

    def on_stop_signal(self, signum, _frame):
        """Let Steam stop the child before it considers this shortcut closed."""
        log(f'otrzymano sygnał zatrzymania {signum} od Steam')
        GLib.idle_add(self.quit)

    def do_activate(self):
        if self.window:
            self.window.present()
            return
        self.window = Gtk.ApplicationWindow(application=self, title='TV mode')
        self.window.set_decorated(False)
        self.window.fullscreen()
        self.window.add_css_class('tv-window')
        self.window.connect('close-request', self.close_request)
        keyboard = Gtk.EventControllerKey()
        keyboard.connect('key-pressed', self.on_key)
        self.window.add_controller(keyboard)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content.set_valign(Gtk.Align.CENTER)
        content.set_halign(Gtk.Align.CENTER)

        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        title = Gtk.Label(label='TV mode')
        title.add_css_class('title')
        title.set_halign(Gtk.Align.START)
        header.append(title)
        subtitle = Gtk.Label(label='Wybierz aplikację do uruchomienia na telewizorze')
        subtitle.add_css_class('subtitle')
        subtitle.set_halign(Gtk.Align.START)
        header.append(subtitle)
        content.append(header)

        tile_grid = Gtk.Grid(column_spacing=24, row_spacing=24)
        tile_grid.set_column_homogeneous(True)
        tile_grid.set_row_homogeneous(True)
        columns = min(3, max(1, len(self.services)))
        tile_grid.set_margin_top(40)
        tile_grid.set_margin_bottom(40)
        for index, service in enumerate(self.services):
            name_text = service['name']
            source_text = service['source']
            tag_text = service['tag']
            tag_class = service['badge']
            desc_text = service['description']
            tile = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            tile.add_css_class('tile')
            tile.set_size_request(340, 190)

            top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            badge = Gtk.Label(label=tag_text)
            badge.add_css_class('service-badge')
            badge.add_css_class(tag_class)
            badge.set_halign(Gtk.Align.START)
            top_row.append(badge)
            tile.append(top_row)

            name = Gtk.Label(label=name_text)
            name.add_css_class('tile-title')
            name.set_halign(Gtk.Align.START)
            tile.append(name)

            desc = Gtk.Label(label=desc_text)
            desc.add_css_class('tile-detail')
            desc.set_halign(Gtk.Align.START)
            tile.append(desc)

            source = Gtk.Label(label=source_text)
            source.add_css_class('tile-source')
            source.set_halign(Gtk.Align.START)
            tile.append(source)

            tile_grid.attach(tile, index % columns, index // columns, 1, 1)
            self.tiles.append(tile)
        content.append(tile_grid)

        legend = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=28)
        legend.add_css_class('legend-bar')
        legend.set_halign(Gtk.Align.START)

        # A action
        a_item = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        a_badge = Gtk.Label(label='A')
        a_badge.add_css_class('btn-badge')
        a_badge.add_css_class('btn-a')
        self.action_label = Gtk.Label(label=f"Uruchom {self.services[self.selected]['name']}")
        self.action_label.add_css_class('legend-label')
        a_item.append(a_badge)
        a_item.append(self.action_label)
        legend.append(a_item)

        # Navigation
        nav_item = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        nav_badge = Gtk.Label(label='◄  ►')
        nav_badge.add_css_class('btn-badge')
        nav_badge.add_css_class('btn-nav')
        nav_label = Gtk.Label(label='Wybór')
        nav_label.add_css_class('legend-label-subtle')
        nav_item.append(nav_badge)
        nav_item.append(nav_label)
        legend.append(nav_item)

        # B quit
        b_item = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        b_badge = Gtk.Label(label='B')
        b_badge.add_css_class('btn-badge')
        b_badge.add_css_class('btn-b')
        b_label = Gtk.Label(label='Wyjdź do Steam')
        b_label.add_css_class('legend-label-subtle')
        b_item.append(b_badge)
        b_item.append(b_label)
        legend.append(b_item)

        # View + Menu combo
        combo_item = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        combo_badge = Gtk.Label(label='View + Menu')
        combo_badge.add_css_class('btn-badge')
        combo_badge.add_css_class('btn-combo')
        combo_label = Gtk.Label(label='Powrót')
        combo_label.add_css_class('legend-label-subtle')
        combo_item.append(combo_badge)
        combo_item.append(combo_label)
        legend.append(combo_item)

        content.append(legend)

        self.hint = Gtk.Label(label='')
        self.hint.add_css_class('status-hint')
        self.hint.set_halign(Gtk.Align.START)
        self.hint.set_margin_top(12)
        content.append(self.hint)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.set_halign(Gtk.Align.CENTER)
        root.set_valign(Gtk.Align.CENTER)
        root.append(content)
        self.window.set_child(root)

        css = Gtk.CssProvider()
        css.load_from_data(b'''
window.tv-window {
    background-color: #0f1015;
    color: #f0f2f5;
}
.title {
    font-size: 40px;
    font-weight: 800;
    color: #ffffff;
}
.subtitle {
    font-size: 18px;
    color: #8e93a0;
    margin-top: 4px;
}
.tile {
    background-color: #1a1c24;
    border: 2px solid #2b2e3a;
    border-radius: 20px;
    padding: 24px 22px;
    min-width: 340px;
}
.tile.selected {
    background-color: #242835;
    border: 3px solid #ffffff;
}
.service-badge {
    font-size: 11px;
    font-weight: 800;
    padding: 3px 8px;
    border-radius: 6px;
    color: #ffffff;
}
.badge-youtube { background-color: #e62117; }
.badge-emby { background-color: #2e7d32; }
.badge-netflix { background-color: #e50914; }
.badge-apple { background-color: #6b7afd; }
.badge-canal { background-color: #f3b63f; color: #17181d; }
.badge-xbox { background-color: #3dc26c; }

.tile-title {
    font-size: 28px;
    font-weight: 700;
    color: #ffffff;
    margin-top: 10px;
}
.tile-detail {
    font-size: 16px;
    color: #bfc4d0;
    margin-top: 4px;
}
.tile-source {
    font-size: 13px;
    color: #6b7280;
    margin-top: 6px;
}

.legend-bar {
    background-color: #15171e;
    border: 1px solid #232631;
    border-radius: 16px;
    padding: 12px 24px;
}
.legend-label {
    font-size: 16px;
    color: #f0f2f5;
    font-weight: 600;
}
.legend-label-subtle {
    font-size: 15px;
    color: #8a8f9e;
}
.btn-badge {
    font-size: 14px;
    font-weight: 800;
    padding: 3px 10px;
    border-radius: 8px;
}
.btn-a {
    background-color: #107c10;
    color: #ffffff;
    border-radius: 9999px;
}
.btn-b {
    background-color: #d1242f;
    color: #ffffff;
    border-radius: 9999px;
}
.btn-nav {
    background-color: #2a2e39;
    color: #e2e6f0;
    border: 1px solid #3f4453;
}
.btn-combo {
    background-color: #22252e;
    color: #9398a6;
    border: 1px solid #343845;
    font-size: 12px;
}
.status-hint {
    font-size: 16px;
    color: #9aa0ad;
    min-height: 24px;
}
''')
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.window.present()
        self.controllers = Controllers()
        self.update_selection()
        log(f"uruchomiono dashboard: {', '.join(service['name'] for service in self.services)}")
        GLib.timeout_add(16, self.poll_controllers)
        GLib.timeout_add(250, self.poll_steam_stop)

    def poll_steam_stop(self):
        """Steam's non-Steam wrapper doesn't forward TerminateApp to Python."""
        try:
            size = STEAM_LOG.stat().st_size
            if size < self.steam_log_position:
                self.steam_log_position = 0
            if size > self.steam_log_position:
                with STEAM_LOG.open('r', encoding='utf-8', errors='replace') as stream:
                    stream.seek(self.steam_log_position)
                    added = stream.read()
                    self.steam_log_position = stream.tell()
                if 'Apps.TerminateApp' in added:
                    log('wykryto zatrzymanie aplikacji przez menu Steam')
                    self.quit()
                    return False
        except OSError as error:
            log(f'nie udało się obserwować zatrzymania Steam: {error}')
            return False
        return True

    def on_key(self, _window, keyval, _keycode, _state):
        name = Gdk.keyval_name(keyval)
        if name in ('Return', 'KP_Enter', 'space'):
            self.launch()
            return True
        if name in ('Left', 'Right'):
            self.move_selection(-1 if name == 'Left' else 1)
            return True
        if name == 'Escape':
            self.quit()
            return True
        return False

    def poll_controllers(self):
        keys = self.controllers.pressed()
        if self.child:
            now = time.monotonic()
            browser_names = {service.get('runtime_name') for service in self.services if service.get('kind') == 'browser'}
            if self.child_name in browser_names and 'b' in keys and 'b' not in self.previous:
                if self.child_name == 'Emby':
                    self.forward_browser_key('quit')
                else:
                    self.forward_browser_key('b')
            if {'view', 'menu'} <= keys:
                if not self.return_started:
                    self.return_started = now
                elif now - self.return_started >= 1.2:
                    log(f'View + Menu: powrót z {self.child_name} do dashboardu')
                    if self.child_name in browser_names:
                        self.forward_browser_key('quit')
                    else:
                        try:
                            os.killpg(self.child.pid, signal.SIGTERM)
                        except ProcessLookupError:
                            pass
                    self.return_started = now + 10
            else:
                self.return_started = 0.0
            if self.child_name in browser_names:
                new = keys - self.previous
                for button in ('up', 'down', 'left', 'right', 'lb', 'rb', 'a', 'x'):
                    if button in new:
                        self.forward_browser_key(button, 0)
                        self.browser_repeat = now + 0.50
                        if button in ('up', 'down', 'left', 'right'):
                            self.browser_hold_button = button
                            self.browser_hold_started = now
                        else:
                            self.browser_hold_button = None
                        break
                else:
                    if now >= self.browser_repeat:
                        for button in ('up', 'down', 'left', 'right'):
                            if button in keys:
                                if self.browser_hold_button != button:
                                    self.browser_hold_button = button
                                    self.browser_hold_started = now
                                held_ms = int((now - self.browser_hold_started) * 1000)
                                self.forward_browser_key(button, held_ms)
                                self.browser_repeat = now + (0.11 if held_ms >= 1200 else 0.24)
                                break
            if not any(button in keys for button in ('up', 'down', 'left', 'right')):
                self.browser_hold_button = None
            if self.child.poll() is not None:
                log(f'{self.child_name} zakończone, exit={self.child.returncode}')
                self.child = None
                self.child_name = None
                self.previous = set()
                self.status = f"A uruchamia {self.services[self.selected]['name']}"
                self.hint.set_label('')
                self.update_selection()
                self.window.set_visible(True)
                self.window.fullscreen()
                self.window.present()
            self.previous = keys
            return True
        now = time.monotonic()
        new = keys - self.previous
        if 'a' in new:
            self.launch()
        elif 'left' in new:
            self.move_selection(-1)
        elif 'right' in new:
            self.move_selection(1)
        elif 'b' in new:
            log('B: zamknięto TV mode')
            self.quit()
        self.previous = keys
        return True

    def move_selection(self, change):
        self.selected = (self.selected + change) % len(self.services)
        self.status = f"A uruchamia {self.services[self.selected]['name']}"
        self.hint.set_label('')
        self.update_selection()
        log(f"wybrano {self.services[self.selected]['name']}")

    def forward_browser_key(self, button, held_ms=0):
        """Forward controller navigation as keys only; never as pointer input."""
        label = {
            'up': 'Up', 'down': 'Down', 'left': 'Left', 'right': 'Right',
            'lb': 'F7', 'rb': 'F8', 'a': 'Return', 'b': 'Escape', 'x': 'M',
            'quit': 'ctrl+q',
        }[button]
        try:
            self.chrome_keyboard.tap(self.child_name, button, held_ms)
        except (OSError, RuntimeError, KeyError, TimeoutError) as error:
            log(f'nie dostarczono {label} do {self.child_name} przez Chrome DevTools: {error}')
            return
        log(f'przekazano {label} do {self.child_name} przez Chrome DevTools')

    def update_selection(self):
        for index, tile in enumerate(self.tiles):
            if index == self.selected:
                tile.add_css_class('selected')
            else:
                tile.remove_css_class('selected')
        if hasattr(self, 'action_label') and self.action_label:
            self.action_label.set_label(f"Uruchom {self.services[self.selected]['name']}")

    def launch(self):
        if self.child:
            return
        service = self.services[self.selected]
        name = service['name']
        self.status = f'Uruchamianie {name}…'
        self.hint.set_label(self.status)
        log(f'A: uruchamianie {name}')
        env = os.environ.copy()
        env.pop('LD_PRELOAD', None)
        try:
            if service.get('kind') == 'vacuumtube':
                command = ['/usr/bin/flatpak', 'run', '--nosocket=wayland', '--socket=x11', APP_ID]
                self.child_name = 'VacuumTube'
            else:
                self.child_name = service.get('runtime_name', service['name'].replace(' ', ''))
                profile = Path.home() / '.var' / 'app' / 'com.google.Chrome' / 'config' / f"tv-mode-{service['profile']}-profile"
                profile.mkdir(parents=True, exist_ok=True)
                command = browser_command(service, profile)
            self.child = subprocess.Popen(command, env=env, start_new_session=True)
        except OSError as error:
            self.status = f'Nie udało się uruchomić {name}'
            self.hint.set_label(self.status)
            log(f'błąd uruchomienia {name}: {error}')
            return
        self.focus_deadline = time.monotonic() + 8
        GLib.timeout_add(200, self.focus_child)

    def focus_child(self):
        """Gamescope keeps Big Picture above independently spawned X11 windows.

        Ask the X11 window manager to activate the child only after it has a
        real window.  This is window focus management, not input delivery.
        """
        window_class = 'vacuumtube' if self.child_name == 'VacuumTube' else 'google-chrome'
        result = subprocess.run(
            ['/usr/bin/xdotool', 'search', '--class', window_class],
            env=os.environ.copy(), text=True, capture_output=True, timeout=2,
        )
        windows = result.stdout.split()
        if windows:
            best_window, best_area = None, -1
            for window in windows:
                geometry = subprocess.run(
                    ['/usr/bin/xdotool', 'getwindowgeometry', '--shell', window],
                    env=os.environ.copy(), text=True, capture_output=True, timeout=2,
                )
                values = dict(line.split('=', 1) for line in geometry.stdout.splitlines() if '=' in line)
                area = int(values.get('WIDTH', 0)) * int(values.get('HEIGHT', 0))
                if area > best_area:
                    best_window, best_area = window, area
            subprocess.run(['/usr/bin/xdotool', 'windowactivate', '--sync', best_window],
                           env=os.environ.copy(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
            log(f'okno {self.child_name} aktywowane nad Big Picture Steam')
            self.window.set_visible(False)
            log(f'TV mode pozostaje aktywny jako proces Steam podczas {self.child_name}')
            if self.child_name in browser_names and self.child_name != 'Emby':
                self.script_deadline = time.monotonic() + 8
                GLib.timeout_add(250, self.install_web_script)
            return False
        if time.monotonic() >= self.focus_deadline:
            self.status = f'{self.child_name} uruchomione; nie udało się aktywować okna'
            self.hint.set_label(self.status)
            log(f'{self.child_name} wystartował, ale aktywacja okna nie powiodła się')
            self.window.set_visible(False)
            return False
        return True

    def install_web_script(self):
        if not self.child or self.child.poll() is not None:
            return False
        source = self.chrome_keyboard.netflix_source if self.child_name == 'Netflix' else self.chrome_keyboard.browser_source
        try:
            self.chrome_keyboard.install_script(self.child_name, source)
        except Exception as error:
            if time.monotonic() < self.script_deadline:
                return True
            log(f'nie zainstalowano skryptu fokusu dla {self.child_name}: {type(error).__name__}: {error}')
            return False
        log(f'skrypt fokusu dla {self.child_name} zainstalowany przez Chrome DevTools')
        return False

    def close_request(self, *_args):
        self.quit()
        return False

    def do_shutdown(self):
        self.stop_child_for_shutdown()
        if self.controllers:
            self.controllers.close()
        Gtk.Application.do_shutdown(self)

    def stop_child_for_shutdown(self):
        if not self.child or self.child.poll() is not None:
            return
        log(f'zamykanie potomka {self.child_name} przed wyjściem TV mode')
        if self.child_name in {service.get('runtime_name') for service in self.services if service.get('kind') == 'browser'}:
            try:
                self.chrome_keyboard.tap(self.child_name, 'quit')
            except Exception as error:
                log(f'grzeczne zamknięcie {self.child_name} nie powiodło się: {type(error).__name__}')
        try:
            self.child.wait(timeout=3)
            log(f'potomek {self.child_name} zakończony poprawnie')
            return
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(self.child.pid, signal.SIGTERM)
            self.child.wait(timeout=2)
            log(f'potomek {self.child_name} zakończony SIGTERM')
        except (ProcessLookupError, subprocess.TimeoutExpired):
            log(f'potomek {self.child_name} nie zakończył się po SIGTERM')


if __name__ == '__main__':
    app = TvMode()
    try:
        raise SystemExit(app.run(sys.argv))
    except Exception as error:
        log(f'awaria: {error}')
        raise
