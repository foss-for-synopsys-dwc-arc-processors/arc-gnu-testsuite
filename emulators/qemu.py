from emulators.emulator import Emulator
from typing import List, Optional


class QemuEmulator(Emulator):
    def __init__(self,
                 qemu_path: str,
                 options: List[str],
                 kernel: str,
                 kernel_cmdline: Optional[List[str]] = None,
                 prompt: str = '# ',
                 log_path: Optional[str] = None):
        self.qemu_path = qemu_path
        self.log_path = log_path
        self.prompt = prompt

        command = qemu_path
        args = ['-nographic', '-display', 'none']
        env = {'QEMU_AUDIO_DRV': 'none'}

        if options:
            args += options

        if kernel:
            args += ['-kernel', kernel]

        if kernel_cmdline:
            args += ['-append', ' '.join(kernel_cmdline)]

        super().__init__(command, args, env, prompt, log_path)

    @classmethod
    def name(cls) -> str:
        return 'qemu'
