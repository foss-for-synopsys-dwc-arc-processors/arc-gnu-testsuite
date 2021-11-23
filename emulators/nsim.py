from emulators.emulator import Emulator, EmulatorError
from shutil import which
from typing import Optional, List


class NsimEmulator(Emulator):
    def __init__(self,
                 nsim_path: str,
                 kernel: str,
                 props: Optional[List[str]] = None,
                 propsfile: Optional[str] = None,
                 log_path: Optional[str] = None):

        if nsim_path is None:
            nsim_path = which('nsimdrv')
            if nsim_path is None:
                raise EmulatorError('nSIM emulator was not found')

        args = []

        if props:
            for prop in props:
                args += ['-prop', prop]

        if propsfile:
            args += ['-propsfile', propsfile]

        if kernel:
            args += [kernel]

        super().__init__(command=nsim_path, args=args, log_path=log_path)

    @classmethod
    def name(cls) -> str:
        return 'nsim'
