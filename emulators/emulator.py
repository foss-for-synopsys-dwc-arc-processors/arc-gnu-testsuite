import abc
import pexpect
from abc import ABC
from pexpect import ExceptionPexpect


class EmulatorError(Exception):
    pass


class EmulatorCalledProcessError(EmulatorError):
    def __init__(self, exitcode: int, cmd: str):
        self.exitcode = exitcode
        self.cmd = cmd

    def __str__(self):
        return f'Command {self.cmd} returned non-zero exit code {self.exitcode}'


class Emulator(ABC):
    def __init__(self, command, args, env=None, prompt='# ', log_path=None):
        self.command = command
        self.args = args
        self.env = env
        self.prompt = prompt
        self.logfile = None

        print(f"{self.name()} starting with: {command} {' '.join(args)}")
        if log_path:
            self.logfile = open(log_path, "w")
            print(f'{self.name()} log will be saved: {log_path}')

        try:
            self.emulator = pexpect.spawn(self.command, self.args,
                                          timeout=5,
                                          encoding='utf-8',
                                          env=self.env)
            self.emulator.logfile = self.logfile

        except ExceptionPexpect as err:
            raise EmulatorError(err)

    @classmethod
    @abc.abstractmethod
    def name(cls) -> str:
        pass

    def login(self,
              user='root',
              password=None,
              timeout=600,
              login_prompt=r'\w+ login:'):
        try:
            self.emulator.expect([login_prompt, pexpect.TIMEOUT],
                                 timeout=timeout)
        except ExceptionPexpect:
            raise EmulatorError('System does not boot')

        self.emulator.sendline(user)
        if password:
            self.emulator.expect('Password:')
            self.emulator.sendline(password)
        try:
            self.emulator.expect([self.prompt, pexpect.TIMEOUT])
        except ExceptionPexpect:
            raise EmulatorError('Cannot login')
        self.run('dmesg -n 1')

    def run(self, cmd, timeout=-1, check=False):
        exitcode, output = 0, ''
        try:
            self.emulator.sendline(cmd)
            self.emulator.expect(self.prompt, timeout=timeout)
            output = self.emulator.before.replace(
                '\r\r', '\r').splitlines()[1:]

            self.emulator.sendline('echo $?')
            self.emulator.expect(self.prompt)
        except ExceptionPexpect:
            EmulatorError(exitcode, cmd)

        result = self.emulator.before.splitlines()
        try:
            exitcode = int(result[-1])
        except ValueError:
            exitcode = 1

        if check and exitcode:
            raise EmulatorError(exitcode, cmd)
        return output, exitcode

    def stop(self):
        if self.emulator is None:
            return
        self.emulator.terminate(force=True)
