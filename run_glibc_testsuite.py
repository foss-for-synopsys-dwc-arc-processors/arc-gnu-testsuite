#!/usr/bin/env python3

import argparse
import logging
import multiprocessing
import os
import sys

from testsuite.glibctestsuite import GlibcTestSuite, GlibcTestSuiteError


def dir_path(path):
    if path and os.path.isdir(path):
        return path
    raise argparse.ArgumentTypeError(
        f'directory path doesn\'t exist: \'{path}\'')


def file_path(path):
    if path or os.path.isfile(path):
        return path
    raise argparse.ArgumentTypeError(f'file path doesn\'t exist: \'{path}\'')


def parse_arguments():
    parser = argparse.ArgumentParser()
    logging.basicConfig(stream=sys.stderr, format='%(levelname)s: %(message)s',
                        level=logging.INFO)

    group = parser.add_argument_group('general options')
    group.add_argument('--toolchain-prefix',
                       type=str,
                       required=True,
                       help=f'toolchain prefix')

    group.add_argument('--toolchain-path',
                       type=dir_path,
                       required=True,
                       help=f'path to toolchain')

    group.add_argument('--glibc-dir',
                       type=dir_path,
                       required=True,
                       help='path to glibc directory')

    group.add_argument('--linux-headers-dir',
                       type=dir_path,
                       required=True,
                       help='path to linux headers')

    group.add_argument('--linux-headers-version',
                       type=str,
                       default=os.environ.get('LINUX_HEADERS_VERSION'),
                       help='linux headers version')

    group.add_argument('--kernel',
                       type=file_path,
                       default=os.environ.get('KERNEL_PATH', None),
                       help=f'path to kernel')

    group = parser.add_argument_group('QEMU options')
    group.add_argument('--cpu',
                       type=str,
                       help=f'processor to emulate')

    group.add_argument('--qemu-path',
                       type=file_path,
                       help='path to QEMU emulator')

    group.add_argument('--qemu-extra-opts',
                       type=str,
                       help='additional QEMU options')

    group = parser.add_argument_group('nSIM options')
    group.add_argument('--nsim-path',
                       type=file_path,
                       help='path to nSIM emulator')

    group.add_argument('--nsim-propsfile',
                       type=file_path,
                       help='nSIM properties file.')

    group.add_argument('--nsim-ifname',
                       type=file_path,
                       help='nSIM network interface name')

    group = parser.add_argument_group('build options')
    cpu_count = multiprocessing.cpu_count()
    group.add_argument('--build-jobs',
                       type=int,
                       default=cpu_count,
                       help=f'number of jobs to build tests({cpu_count})')

    build_flags = '-O2'
    group.add_argument('--cflags',
                       type=str,
                       default=os.environ.get('CFLAGS', build_flags),
                       help=f'CFLAGS options({build_flags})')

    group.add_argument('--cxxflags',
                       type=str,
                       default=os.environ.get('CXXFLAGS', build_flags),
                       help=f'CXXFLAGS options({build_flags})')

    group = parser.add_argument_group('SSH options')
    ssh_hostname = '127.0.0.1'
    group.add_argument('--ssh-host',
                       type=str,
                       default=ssh_hostname,
                       help=f'target ssh hostname({ssh_hostname})')

    group.add_argument('--ssh-port',
                       type=int,
                       help='target ssh port')

    group = parser.add_argument_group('NFS options')
    group.add_argument('--unfs',
                       type=file_path,
                       help='Path to unfs3')

    group.add_argument('--nfs-server-ip',
                       type=str,
                       help=f'NFS server IP address')

    group = parser.add_argument_group('test options')
    timeout = 600
    group.add_argument('--timeoutfactor',
                       type=int,
                       default=timeout,
                       help=f'TIMEOUTAFACTOR on the remote machine({timeout})')
    group.add_argument('--test-jobs',
                       type=int,
                       default=1,
                       help='number of jobs to run tests(1)')

    group.add_argument('--subdir',
                       type=str,
                       help='testing only a subset of tests(optional)')

    group.add_argument('--allow-time-setting',
                       help='set GLIBC_TEST_ALLOW_TIME_SETTING env variable',
                       action='store_true')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--build-only',
                       help='run build only',
                       action='store_true')

    group.add_argument('--check-only',
                       help='run tests only',
                       action='store_true')

    group.add_argument('--xcheck-only',
                       help='run xtests only',
                       action='store_true')
    parser.add_argument('--verbose',
                        help='enable verbose output',
                        action='store_true')

    return parser.parse_args()


def main():
    args = parse_arguments()

    build_only = args.build_only
    check_only = args.check_only
    xcheck_only = args.xcheck_only
    toolchain_path = args.toolchain_path
    cflags = args.cflags
    cxxflags = args.cxxflags

    env = {}
    if toolchain_path is not None:
        env['PATH'] = os.path.join(toolchain_path, 'bin') + \
                      os.pathsep + \
                      os.environ['PATH']

    if cflags is not None:
        env['CFLAGS'] = cflags
    if cxxflags is not None:
        env['CXXFLAGS'] = cxxflags

    if not build_only and not check_only and not xcheck_only:
        build_only = check_only = xcheck_only = True

    try:
        testsuite = GlibcTestSuite(args.toolchain_prefix,
                                   args.allow_time_setting,
                                   args.timeoutfactor,
                                   args.glibc_dir,
                                   args.kernel,
                                   args.unfs,
                                   args.cpu,
                                   args.qemu_path,
                                   args.qemu_extra_opts,
                                   args.nsim_path,
                                   args.nsim_propsfile,
                                   args.nsim_ifname,
                                   args.build_jobs,
                                   args.test_jobs,
                                   args.linux_headers_dir,
                                   args.linux_headers_version,
                                   args.toolchain_path,
                                   args.ssh_host,
                                   args.ssh_port,
                                   args.nfs_server_ip,
                                   args.subdir,
                                   args.verbose,
                                   check_only,
                                   xcheck_only,
                                   env)

        if build_only:
            testsuite.configure()
            testsuite.build()
            testsuite.install()

        if check_only or xcheck_only:
            testsuite.run()

    except GlibcTestSuiteError as err:
        logging.error(err)
        sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())
