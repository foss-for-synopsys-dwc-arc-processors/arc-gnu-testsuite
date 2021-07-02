from pexpect import pxssh


class SSHConnectionError(Exception):
    pass


class SSHConnectionProcessError(Exception):
    def __init__(self, cmd):
        self.cmd = cmd

    def __str__(self):
        return f'Command {self.cmd} failed'


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
        self.ssh = pxssh.pxssh(options=options)
        try:
            self.ssh.login(server=hostname,
                           username=username,
                           password=password,
                           login_timeout=120,
                           port=port)
        except pxssh.ExceptionPxssh as err:
            raise SSHConnectionError(err)

    def run(self, cmd, check=True):
        try:
            self.ssh.sendline(cmd)
            self.ssh.prompt()
            self.ssh.sendline('echo $?')
            self.ssh.prompt()
            result = self.ssh.before.decode().strip().splitlines()
            exitcode = int(result[-1])
            if check and exitcode:
                raise SSHConnectionProcessError(cmd)
        except pxssh.ExceptionPxssh:
            raise SSHConnectionProcessError(cmd)
