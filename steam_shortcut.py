#!/usr/bin/env python3
"""Install the TV mode launcher as a non-Steam shortcut."""
import struct
import zlib
import os
from pathlib import Path

NAME = 'TV mode'
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
    files = list(HOME.glob('.steam/steam/userdata/*/config/shortcuts.vdf'))
    if len(files) != 1:
        raise SystemExit(f'expected one Steam shortcuts file, found {len(files)}')
    path = files[0]
    root, _ = read_object(path.read_bytes())
    entries = root.setdefault('shortcuts', {})
    for key, entry in list(entries.items()):
        if entry.get('AppName') == NAME:
            del entries[key]
    executable = f'"{EXE}"'
    appid = zlib.crc32((executable + NAME).encode()) | 0x80000000
    entries[str(max((int(key) for key in entries), default=-1) + 1)] = {
        'appid': appid, 'AppName': NAME, 'Exe': executable,
        'StartDir': f'"{EXE.parent}"', 'icon': '', 'ShortcutPath': '',
        'LaunchOptions': '', 'IsHidden': 0, 'AllowDesktopConfig': 1,
        'AllowOverlay': 1, 'OpenVR': 0, 'Devkit': 0, 'DevkitGameID': '',
        'LastPlayTime': 0, 'tags': {'0': 'test'},
    }
    path.write_bytes(write_object(root))
    print(f'installed {NAME}: {appid}')


if __name__ == '__main__':
    main()
