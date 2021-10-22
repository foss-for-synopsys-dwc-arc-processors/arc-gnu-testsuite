import os
import socket
import subprocess
import tempfile
from emulators.emulator import EmulatorError
from emulators.nsim import NsimEmulator
from emulators.qemu import QemuEmulator
from shutil import copyfile

import utils
from utils import run_command, mkdir, get_free_port
from utils.ssh import SSHConnection, SSHConnectionError
from utils.unfs import Unfs


class GlibcTestSuiteError(Exception):
    pass


class GlibcTestSuite:
    def __init__(self,
                 toolchain_prefix,
                 allow_time_setting,
                 timeoutfactor,
                 glibc_dir,
                 kernel_path,
                 unfs_path=None,
                 cpu=None,
                 qemu_path=None,
                 qemu_extra_opts=None,
                 nsim_path=None,
                 nsim_propsfile=None,
                 nsim_ifname=None,
                 build_jobs=1,
                 test_jobs=1,
                 linux_headers_dir=None,
                 linux_headers_version=None,
                 toolchain_path=None,
                 ssh_host=None,
                 ssh_port=None,
                 nfs_server_ip=None,
                 subdir=None,
                 verbose=False,
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
        self.emulator = None
        self.qemu_path = qemu_path
        self.qemu_extra_opts = qemu_extra_opts
        self.nsim_path = nsim_path
        self.nsim_propsfile = nsim_propsfile
        self.nsim_ifname = nsim_ifname
        self.unfs = None
        self.unfs_path = None
        self.build_jobs = build_jobs
        self.test_jobs = test_jobs
        self.linux_headers_dir = os.path.realpath(linux_headers_dir)
        self.linux_headers_version = linux_headers_version
        self.toolchain_path = toolchain_path
        self.ssh_host = ssh_host
        self.ssh_port = 22 if ssh_port is None else ssh_port
        self.nfs_server_ip = nfs_server_ip
        self.subdir = subdir
        self.verbose = verbose
        self.env = env

        if qemu_path and (nsim_propsfile or nsim_ifname):
            raise GlibcTestSuiteError(
                'Only one emulator can be executed at the same time')

        if qemu_path:
            self.qemu_path = os.path.realpath(qemu_path)
            if kernel_path is None:
                raise GlibcTestSuiteError('Please, specify kernel path')
            if cpu is None:
                raise GlibcTestSuiteError('Please, specify cpu to emulate')
            if ssh_port is None:
                self.ssh_port = get_free_port()
            if nfs_server_ip is None:
                self.nfs_server_ip = '10.0.2.2'

        if nsim_propsfile:
            self.nsim_propsfile = os.path.realpath(nsim_propsfile)

        if kernel_path:
            self.kernel_path = os.path.realpath(kernel_path)

        if unfs_path:
            self.unfs_path = os.path.realpath(unfs_path)

        if self.nfs_server_ip is None:
            self.nfs_server_ip = self._host_ip_address()

        self.make_options = []
        if run_check:
            self.make_options.append('check')
        if run_xcheck:
            self.make_options.append('xcheck')

    def _install_library(self, library_name):
        if self.toolchain_path is None:
            return

        library_path = utils.find_file(library_name, self.toolchain_path)
        if library_path:
            copyfile(library_path,
                     os.path.join(self.install_dir, 'lib', library_name),
                     follow_symlinks=True)

    def _host_ip_address(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect((self.ssh_host, self.ssh_port))
            address = sock.getsockname()[0]
            sock.close()
            return address
        except socket.error as err:
            raise GlibcTestSuiteError(f'Failed to get server IP: {err}')

    def _run_nfs_server(self):
        self.unfs = Unfs(self.unfs_path, self.glibc_dir)
        return self.unfs.serve()

    def _setup_nsim_network(self):
        netmask = utils.get_netmask(self.nsim_ifname)
        self.emulator.run(f'ip a add {self.ssh_host}/{netmask} dev eth0')
        self.emulator.run('ip l set up dev eth0')

    def _run_qemu(self):
        qemu_options = [
            '-cpu', self.cpu,
            '-netdev', f'user,id=net0,hostfwd=tcp::{self.ssh_port}-:22',
            '-device', 'virtio-net-device,netdev=net0',
            '--global', 'cpu.freq_hz=50000000'
        ]

        if self.qemu_extra_opts:
            qemu_options += self.qemu_extra_opts.split (' ')

        qemu_log = os.path.join(self.build_dir, f'qemu-{utils.timestamp()}.log')

        try:
            self.emulator = QemuEmulator(qemu_path=self.qemu_path,
                                         options=qemu_options,
                                         kernel=self.kernel_path,
                                         log_path=qemu_log)
            self.emulator.login()
        except EmulatorError as err:
            raise GlibcTestSuiteError(err)

    def _run_nsim(self):
        nsim_options = [
            f'nsim_mem-dev=virt-net,start=0xf0108000,end=0xf010a000,irq=35,tap={self.nsim_ifname}'
        ]

        nsim_log = os.path.join(self.build_dir, f'nsim-{utils.timestamp()}.log')

        try:
            self.emulator = NsimEmulator(nsim_path=self.nsim_path,
                                         kernel=self.kernel_path,
                                         props=nsim_options,
                                         propsfile=self.nsim_propsfile,
                                         log_path=nsim_log)
            self.emulator.login()
            if self.nsim_ifname:
                self._setup_nsim_network()
        except EmulatorError as err:
            raise GlibcTestSuiteError(err)

    def _mount_nfs(self, mount_dir, nfsport, mountport):
        try:
            timeout = 30
            ssh = SSHConnection(hostname=self.ssh_host, port=self.ssh_port)
            ssh.run(f'mkdir -p {mount_dir}', timeout=timeout)
            mount_args = [
                f'mount', '-o',
                f'noac,nolock,nfsvers=3,port={nfsport},mountport={mountport}',
                f'{self.nfs_server_ip}:{mount_dir}', mount_dir
            ]
            ssh.run(' '.join(mount_args), timeout=timeout)
        except SSHConnectionError as err:
            raise GlibcTestSuiteError(f'Failed to mount NFS mount: {err}')

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
            f'root@{self.ssh_host}'
        ]

        if self.allow_time_setting:
            command += ['--allow-time-setting']

        return command

    def _run_make(self, args):
        make_command = 'make {}'.format(' '.join(args))
        return run_command(args=make_command,
                           cwd=self.build_dir,
                           env=self.env,
                           shell=True,
                           verbose=self.verbose)

    def _run_tests(self, test_wrapper_cmd):
        for option in self.make_options:
            make_args = [
                '-i',
                'test-wrapper=\'{}\''.format(' '.join(test_wrapper_cmd)),
                f'PARALLELMFLAGS=-j{self.test_jobs}',
                option
            ]

            if self.subdir:
                make_args.append(f'subdirs={self.subdir}')

            self._run_make(make_args)

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
        try:
            run_command(args=args,
                        cwd=self.build_dir,
                        env=self.env,
                        verbose=self.verbose)
        except subprocess.CalledProcessError as err:
            raise GlibcTestSuiteError(err)

    def build(self):
        try:
            self._run_make([f'PARALLELMFLAGS=-j{self.build_jobs}'])
        except subprocess.CalledProcessError as err:
            raise GlibcTestSuiteError(err)

    def install(self):
        try:
            self._run_make(['install'])

            for library in ['libgcc_s.so.1', 'libstdc++.so.6']:
                self._install_library(library)
        except subprocess.CalledProcessError as err:
            raise GlibcTestSuiteError(err)

    def run(self):
        ssh_cmd = ''
        try:
            nfsport = mountport = 0
            if self.unfs_path:
                nfsport, mountport = self._run_nfs_server()

            if self.qemu_path:
                self._run_qemu()

            if self.nsim_propsfile:
                self._run_nsim()

            self._mount_nfs(self.glibc_dir, nfsport, mountport)
            ssh_cmd = self._create_ssh_wrapper()
            test_wrapper_cmd = self._test_wrapper_command(ssh_cmd)
            self._run_tests(test_wrapper_cmd)
        finally:
            if self.unfs:
                self.unfs.stop()

            if ssh_cmd:
                os.unlink(ssh_cmd)
