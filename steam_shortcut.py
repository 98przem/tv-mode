#!/usr/bin/env python3
"""Install or remove the TV mode non-Steam shortcut."""
import argparse
import struct
import zlib
import os
from pathlib import Path

NAME = 'TV mode'
LEGACY_NAMES = {'TV mode (test)'}
EXE = Path(__file__).resolve().parent / 'launch'
HOME = Path(os.environ.get('HOME', str(Path.home())))


def read_object(data, pos=0):
    result = {}
    while pos < len(data):
        kind = data[pos]
        pos += 1
        if kind == 8:
            return result, pos
        end = data.index(0, pos)
        key = data[pos:end].decode()
        pos = end + 1
        if kind == 0:
            value, pos = read_object(data, pos)
        elif kind == 1:
            end = data.index(0, pos)
            value = data[pos:end].decode()
            pos = end + 1
        elif kind == 2:
            value = struct.unpack_from('<I', data, pos)[0]
            pos += 4
        else:
            raise ValueError(f'unsupported VDF type: {kind}')
        result[key] = value
    raise ValueError('unterminated VDF object')


def write_object(value):
    result = bytearray()
    for key, item in value.items():
        if isinstance(item, dict):
            result.extend(b'\0' + key.encode() + b'\0' + write_object(item))
        elif isinstance(item, int):
            result.extend(b'\2' + key.encode() + b'\0' + struct.pack('<I', item & 0xffffffff))
        else:
            result.extend(b'\1' + key.encode() + b'\0' + str(item).encode() + b'\0')
    result.append(8)
    return bytes(result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--remove', action='store_true', help='remove the TV mode shortcut')
    args = parser.parse_args()
    files = list(HOME.glob('.steam/steam/userdata/*/config/shortcuts.vdf'))
    if len(files) != 1:
        raise SystemExit(f'expected one Steam shortcuts file, found {len(files)}')
    path = files[0]
    root, _ = read_object(path.read_bytes())
    entries = root.setdefault('shortcuts', {})
    matches = [
        (key, entry) for key, entry in entries.items()
        if entry.get('AppName') == NAME or entry.get('AppName') in LEGACY_NAMES
    ]
    if args.remove:
        for key, _entry in matches:
            del entries[key]
        path.write_bytes(write_object(root))
        print(f'removed {NAME}')
        return
    executable = f'"{EXE}"'
    if matches:
        key, entry = next(
            ((key, entry) for key, entry in matches if entry.get('AppName') == NAME),
            matches[0],
        )
        for duplicate_key, _entry in matches:
            if duplicate_key != key:
                del entries[duplicate_key]
        entry.update({
            'AppName': NAME, 'Exe': executable, 'StartDir': f'"{EXE.parent}"',
            'LaunchOptions': '', 'IsHidden': 0, 'AllowDesktopConfig': 1,
            'AllowOverlay': 1, 'tags': {},
        })
        appid = entry['appid']
    else:
        appid = zlib.crc32((executable + NAME).encode()) | 0x80000000
        key = str(max((int(key) for key in entries), default=-1) + 1)
        entries[key] = {
            'appid': appid, 'AppName': NAME, 'Exe': executable,
            'StartDir': f'"{EXE.parent}"', 'icon': '', 'ShortcutPath': '',
            'LaunchOptions': '', 'IsHidden': 0, 'AllowDesktopConfig': 1,
            'AllowOverlay': 1, 'OpenVR': 0, 'Devkit': 0, 'DevkitGameID': '',
            'LastPlayTime': 0, 'tags': {},
        }
    path.write_bytes(write_object(root))
    print(f'installed {NAME}: {appid}')


if __name__ == '__main__':
    main()
