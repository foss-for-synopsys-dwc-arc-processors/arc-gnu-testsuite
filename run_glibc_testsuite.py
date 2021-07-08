#!/usr/bin/env python3

import argparse
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

    parser.add_argument('--cpu',
                        type=str,
                        help=f'processor to emulate')

    parser.add_argument('--toolchain-prefix',
                        type=str,
                        required=True,
                        help=f'toolchain prefix')

    parser.add_argument('--toolchain-path',
                        type=dir_path,
                        required=True,
                        help=f'path to toolchain')

    parser.add_argument('--glibc-dir',
                        type=dir_path,
                        required=True,
                        help='path to glibc directory')

    parser.add_argument('--kernel',
                        type=file_path,
                        default=os.environ.get('KERNEL_PATH', None),
                        help=f'path to kernel')

    parser.add_argument('--linux-headers-dir',
                        type=dir_path,
                        required=True,
                        help='path to linux headers')

    parser.add_argument('--linux-headers-version',
                        type=str,
                        default=os.environ.get('LINUX_HEADERS_VERSION'),
                        help='linux headers version')

    parser.add_argument('--qemu-path',
                        type=file_path,
                        help='path to QEMU emulator')

    parser.add_argument('--unfs',
                        type=file_path,
                        help='Path to unfs3(optional)')

    ssh_hostname = '127.0.0.1'
    parser.add_argument('--ssh-host',
                        type=str,
                        default=ssh_hostname,
                        help=f'target ssh hostname({ssh_hostname})')

    parser.add_argument('--ssh-port',
                        type=int,
                        help=f'target ssh port(22)')

    parser.add_argument('--server-ip',
                        type=str,
                        help=f'NFS server IP address')
    timeout = 600
    parser.add_argument('--timeoutfactor',
                        type=int,
                        default=timeout,
                        help=f'TIMEOUTAFACTOR on the remote machine({timeout})')

    cpu_count = multiprocessing.cpu_count()
    parser.add_argument('--build-jobs',
                        type=int,
                        default=cpu_count,
                        help=f'number of jobs to build tests({cpu_count})')

    parser.add_argument('--test-jobs',
                        type=int,
                        default=1,
                        help='number of jobs to run tests(1)')

    parser.add_argument('--subdir',
                        type=str,
                        help='testing only a subset of tests(optional)')

    parser.add_argument('--verbose',
                        help='enable verbose output',
                        action='store_true')

    build_flags = '-O2'
    parser.add_argument('--cflags',
                        type=str,
                        default=os.environ.get('CFLAGS', build_flags),
                        help=f'CFLAGS options({build_flags})')

    parser.add_argument('--cxxflags',
                        type=str,
                        default=os.environ.get('CXXFLAGS', build_flags),
                        help=f'CXXFLAGS options({build_flags})')

    parser.add_argument('--allow-time-setting',
                        help='set GLIBC_TEST_ALLOW_TIME_SETTING env variable',
                        action='store_true')

    parser.add_argument('--build',
                        help='run build',
                        action='store_true')

    parser.add_argument('--check',
                        help='run tests',
                        action='store_true')

    parser.add_argument('--xcheck',
                        help='run xtests',
                        action='store_true')

    return parser.parse_args()


def main():
    args = parse_arguments()

    run_build = args.build
    run_check = args.check
    run_xcheck = args.xcheck
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

    if not run_build and not run_check and not run_xcheck:
        run_build = run_check = run_xcheck = True

    try:
        testsuite = GlibcTestSuite(args.cpu,
                                   args.toolchain_prefix,
                                   args.allow_time_setting,
                                   args.timeoutfactor,
                                   args.glibc_dir,
                                   args.qemu_path,
                                   args.kernel,
                                   args.unfs,
                                   args.build_jobs,
                                   args.test_jobs,
                                   args.linux_headers_dir,
                                   args.linux_headers_version,
                                   args.toolchain_path,
                                   args.ssh_host,
                                   args.ssh_port,
                                   args.server_ip,
                                   args.subdir,
                                   args.verbose,
                                   run_check,
                                   run_xcheck,
                                   env)

        if run_build:
            testsuite.configure()
            testsuite.build()
            testsuite.install()

        if run_check or run_xcheck:
            testsuite.run()

    except GlibcTestSuiteError as err:
        print(f'ERROR: {err}')
    sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())
