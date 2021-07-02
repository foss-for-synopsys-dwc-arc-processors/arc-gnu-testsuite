import os
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_free_port(udp=False):
    sock = socket.socket(socket.AF_INET,
                         socket.SOCK_STREAM if not udp else socket.SOCK_DGRAM)
    sock.bind(('', 0))
    address = sock.getsockname()
    sock.close()
    return address[1]


def mkdir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def find_file(name, path, follow_symlinks=True):
    for root, _, files in os.walk(path, followlinks=follow_symlinks):
        if name in files:
            return os.path.join(root, name)
    return None


def timestamp(timestamp_format='%Y%m%d%H%M%S'):
    return datetime.now().strftime(timestamp_format)


def run_command(args,
                cwd=None, env=None, timeout=None, shell=False, verbose=True):
    if env is not None:
        env = dict(os.environ, **env)

    return subprocess.run(
        args,
        stdout=sys.stdout if verbose else subprocess.DEVNULL,
        stderr=sys.stderr,
        cwd=cwd,
        env=env,
        timeout=timeout,
        shell=shell,
        check=True)
