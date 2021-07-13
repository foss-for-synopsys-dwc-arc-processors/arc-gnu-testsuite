from pexpect import pxssh, ExceptionPexpect


class SSHConnectionError(Exception):
    pass


class SSHConnectionProcessError(SSHConnectionError):
    def __init__(self, cmd):
        self.cmd = cmd

    def __str__(self):
        return f'Command: \'{self.cmd}\' failed'


class SSHConnection:
    def __init__(self,
                 hostname='127.0.0.1',
                 port=None,
                 username='root',
                 password=None):
        options = {
            "StrictHostKeyChecking": "no",
            "UserKnownHostsFile": "/dev/null"
        }
        try:
            self.ssh = pxssh.pxssh(options=options)
            self.ssh.login(server=hostname,
                           username=username,
                           password=password,
                           login_timeout=120,
                           port=port)
        except ExceptionPexpect as err:
            raise SSHConnectionError(err)

    def run(self, cmd, timeout=-1, check=True):
        try:
            self.ssh.sendline(cmd)
            self.ssh.prompt(timeout=timeout)
            output = self.ssh.before.decode().splitlines()[1:]
            self.ssh.sendline('echo $?')
            self.ssh.prompt(timeout=timeout)
            result = self.ssh.before.decode().strip().splitlines()
            try:
                exitcode = int(result[-1])
            except ValueError:
                exitcode = 1

            if check and exitcode:
                raise SSHConnectionProcessError(cmd)
            return output, exitcode
        except ExceptionPexpect:
            raise SSHConnectionProcessError(cmd)
