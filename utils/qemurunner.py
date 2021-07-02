import pexpect
from pexpect import ExceptionPexpect


class QemuProcessError(Exception):
    pass


class QemuCalledProcessError(QemuProcessError):
    def __init__(self, exitcode, cmd):
        self.exitcode = exitcode
        self.cmd = cmd

    def __str__(self):
        return f'Command {self.cmd} returned non-zero exit code {self.exitcode}'


class QemuRunner:
    def __init__(self, qemu_path=None, prompt='# ', log_path=None):
        self.qemu = None
        self.qemu_path = qemu_path
        self.log_path = log_path
        self.prompt = prompt

    def boot(self, kernel=None, kernel_cmdline=None, options=None):

        qemu_cmd = [self.qemu_path, '-nographic', '-display', 'none']

        if options:
            qemu_cmd += options

        if kernel_cmdline is None:
            kernel_cmdline = []

        if kernel:
            qemu_cmd += ['-kernel', kernel]

        if kernel_cmdline:
            qemu_cmd += ['-append', ' '.join(kernel_cmdline)]

        print('qemu starting with: {}'.format(' '.join(qemu_cmd)))
        self.qemu = pexpect.spawn(qemu_cmd[0], qemu_cmd[1:],
                                  timeout=5,
                                  encoding='utf-8',
                                  env={'QEMU_AUDIO_DRV': 'none'})

        if self.log_path:
            self.qemu.logfile = open(self.log_path, "w")
            print(f'qemu log will be saved: {self.log_path}')

    def login(self,
              user='root',
              password=None,
              timeout=600,
              login_prompt=r'\w+ login:'):
        try:
            self.qemu.expect([login_prompt, pexpect.TIMEOUT], timeout=timeout)
        except ExceptionPexpect:
            raise QemuProcessError('System does not boot')

        self.qemu.sendline(user)
        if password:
            self.qemu.expect('Password:')
            self.qemu.sendline(password)
        try:
            self.qemu.expect([self.prompt, pexpect.TIMEOUT])
        except ExceptionPexpect:
            raise QemuProcessError('Cannot login')
        self.run('dmesg -n 1')

    def run(self, cmd, timeout=-1, check=False):
        exitcode, output = 0, ''
        try:
            self.qemu.sendline(cmd)
            self.qemu.expect(self.prompt, timeout=timeout)
            output = self.qemu.before.replace('\r\r', '\r').splitlines()[1:]

            self.qemu.sendline('echo $?')
            self.qemu.expect(self.prompt)
        except ExceptionPexpect:
            QemuCalledProcessError(exitcode, cmd)

        exitcode = self.qemu.before.splitlines()[2]
        exitcode = int(exitcode)
        if check and exitcode:
            raise QemuCalledProcessError(exitcode, cmd)
        return output, exitcode

    def stop(self):
        if self.qemu is None:
            return
        self.qemu.terminate(force=True)
