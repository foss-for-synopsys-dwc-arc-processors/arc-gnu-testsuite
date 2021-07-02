import os
import tempfile
from shutil import copyfile

import utils
from utils import run_command, mkdir, get_free_port
from utils.qemurunner import QemuRunner, QemuProcessError
from utils.ssh import SSHConnection, SSHConnectionError
from utils.unfs import Unfs


class GlibcTestSuite:
    def __init__(self,
                 cpu,
                 toolchain_prefix,
                 allow_time_setting,
                 timeoutfactor,
                 glibc_dir,
                 qemu_path,
                 kernel_path,
                 unfs_path,
                 build_jobs,
                 test_jobs,
                 linux_headers_dir=None,
                 linux_headers_version=None,
                 toolchain_path=None,
                 ssh_host=None,
                 ssh_port=None,
                 subdir=None,
                 run_check=True,
                 run_xcheck=True,
                 env=None
                 ):

        self.cpu = cpu
        self.toolchain_prefix = toolchain_prefix
        self.allow_time_setting = allow_time_setting
        self.timeoutfactor = timeoutfactor
        self.glibc_dir = os.path.realpath(glibc_dir)
        self.build_dir = os.path.join(self.glibc_dir, 'build')
        self.install_dir = os.path.join(self.build_dir, 'install')
        self.qemu = None
        self.qemu_path = None
        self.kernel_path = os.path.realpath(kernel_path)
        self.unfs = None
        self.unfs_path = None
        self.build_jobs = build_jobs
        self.test_jobs = test_jobs
        self.linux_headers_dir = os.path.realpath(linux_headers_dir)
        self.linux_headers_version = linux_headers_version
        self.toolchain_path = toolchain_path
        self.ssh_host = ssh_host
        self.ssh_port = get_free_port() if ssh_port is None else ssh_port
        self.subdir = subdir
        self.env = env

        if unfs_path is not None:
            self.unfs_path = os.path.realpath(unfs_path)

        if qemu_path is not None:
            self.qemu_path = os.path.realpath(qemu_path)

        self.make_options = []
        if run_check:
            self.make_options.append('check')
        if run_xcheck:
            self.make_options.append('xcheck')

    def _copy_libgcc_s(self):
        if self.toolchain_path is None:
            return

        libgcc_s_name = 'libgcc_s.so.1'
        libgcc_s_path = utils.find_file(libgcc_s_name, self.toolchain_path)
        if libgcc_s_path:
            copyfile(libgcc_s_path,
                     os.path.join(self.install_dir, 'lib', libgcc_s_name),
                     follow_symlinks=True)

    def _run_nfs_server(self):
        address = '127.0.0.1' if self.ssh_host == '127.0.0.1' else '0.0.0.0'
        self.unfs = Unfs(self.unfs_path, self.glibc_dir, address)
        return self.unfs.serve()

    def _run_qemu(self):
        qemu_option = [
            '-cpu', self.cpu,
            '-netdev', f'user,id=net0,hostfwd=tcp::{self.ssh_port}-:22',
            '-device', 'virtio-net-device,netdev=net0',
            '--global', 'cpu.freq_hz=50000000'
        ]

        qemu_log = os.path.join('/tmp', f'qemu-{utils.timestamp()}.log')

        try:
            self.qemu = QemuRunner(self.qemu_path, log_path=qemu_log)
            self.qemu.boot(kernel=self.kernel_path, options=qemu_option)
            self.qemu.login()
        except QemuProcessError as err:
            raise SystemError(f'Failed to boot QEMU: {err}\n'
                              f'Please, see the log file: '
                              f'{self.qemu.log_path}')

    def _mount_nfs(self, mount_dir, nfsport, mountport):
        try:
            ssh = SSHConnection(hostname=self.ssh_host, port=self.ssh_port)
            ssh.run(f'mkdir -p {mount_dir}')
            mount_args = [
                f'mount', '-o',
                f'noac,nolock,nfsvers=3,port={nfsport},mountport={mountport}',
                f'10.0.2.2:{mount_dir}', mount_dir
            ]
            ssh.run(' '.join(mount_args))
        except SSHConnectionError as err:
            raise SystemError(f'Failed to mount NFS mount: {err}')

    def _create_ssh_wrapper(self):
        command = [
            'exec',
            'ssh',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-o', 'StrictHostKeyChecking=no',
            '-p', str(self.ssh_port),
            '\"$@\"',
            '\n'
        ]

        with tempfile.NamedTemporaryFile(delete=False, mode="w") as ssh_cmd:
            ssh_cmd.write('#!/bin/sh\n\n')
            ssh_cmd.write(' '.join(command))

        os.chmod(ssh_cmd.name, 0o775)

        return ssh_cmd.name

    def _test_wrapper_command(self, ssh_cmd):
        command = [
            os.path.join(self.glibc_dir, 'scripts', 'cross-test-ssh.sh'),
            '--ssh', ssh_cmd,
            '--timeoutfactor', str(self.timeoutfactor),
            'root@localhost'
        ]

        if self.allow_time_setting:
            command += ['--allow-time-setting']

        return command

    def _run_tests(self, test_wrapper_cmd):
        for option in self.make_options:
            make_args = [
                'make',
                '-i',
                'test-wrapper=\'{}\''.format(' '.join(test_wrapper_cmd)),
                f'PARALLELMFLAGS=-j{self.test_jobs}',
                option
            ]

            if self.subdir:
                make_args.append(f'subdirs={self.subdir}')

            run_command(' '.join(make_args), cwd=self.build_dir, shell=True,
                        env=self.env)

    def configure(self):
        args = [
            f'{self.glibc_dir}/configure',
            f'--target={self.toolchain_prefix}',
            f'--host={self.toolchain_prefix}',
            '--build=x86_64',
            '--enable-shared',
            '--disable-profile',
            '--disable-werror',
            '--without-gd',
            f'--prefix={self.install_dir}'
        ]

        if self.linux_headers_dir:
            args.append(f'--with-headers={self.linux_headers_dir}/usr/include')
        if self.linux_headers_version:
            args.append(f'--enable-kernel={self.linux_headers_version}')

        mkdir(self.build_dir)
        run_command(args=args, cwd=self.build_dir, env=self.env, verbose=False)

    def build(self):
        make_args = [
            'make',
            f'PARALLELMFLAGS=-j{self.build_jobs}'
        ]

        run_command(make_args, cwd=self.build_dir, env=self.env, verbose=False)

    def install(self):
        make_args = [
            'make',
            'install'
        ]
        run_command(make_args, cwd=self.build_dir, env=self.env, verbose=False)
        self._copy_libgcc_s()

    def run(self):
        ssh_cmd = ''
        try:
            nfsport = mountport = 0
            if self.unfs_path:
                nfsport, mountport = self._run_nfs_server()

            if self.qemu_path:
                self._run_qemu()

            self._mount_nfs(self.glibc_dir, nfsport, mountport)
            ssh_cmd = self._create_ssh_wrapper()
            test_wrapper_cmd = self._test_wrapper_command(ssh_cmd)
            self._run_tests(test_wrapper_cmd)
        finally:
            if self.unfs:
                self.unfs.stop()

            if ssh_cmd:
                os.unlink(ssh_cmd)
