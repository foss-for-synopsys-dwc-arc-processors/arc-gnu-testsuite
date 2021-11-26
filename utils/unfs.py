import logging
import os
import subprocess
import tempfile

from utils import get_free_port


class Unfs:
    def __init__(self, unfs_path, mount_dir):
        self.unfs = None
        self.unfs_path = unfs_path
        self.mount_dir = mount_dir
        self.exports = self._create_exports()

    def _create_exports(self):
        options = [
            self.mount_dir,
            '(rw,no_root_squash,no_all_squash,insecure)\n'
        ]

        with tempfile.NamedTemporaryFile(delete=False, mode="w") as exports:
            exports.write(' '.join(options))

        return exports.name

    def stop(self):
        if self.unfs is not None:
            self.unfs.terminate()

        os.unlink(self.exports)

    def serve(self):
        nfsport, mountport = get_free_port(udp=True), get_free_port(udp=True)
        args = [
            self.unfs_path,
            '-d',
            '-p',
            '-e', self.exports,
            '-n', str(nfsport),
            '-m', str(mountport)
        ]

        logging.info('starting unfs3  with: %s', ' '.join(args))
        self.unfs = subprocess.Popen(args,
                                     stdout=subprocess.DEVNULL,
                                     start_new_session=True)

        return nfsport, mountport
