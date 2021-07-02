# ARC GNU Testsuite

## Prerequisites

For running Glibc Testsuite, you will need:

- QEMU (qemu-system-arc)
- Linux Kernel (vmlinux)
- User-Space NFSv3 Server (unfs3)
- Glibc Sources
- Linux Headers

### Installing python3 dependencies

```sh
pip3 install -r requirements.txt
```

### Building UNFS3 from sources

For building [unfs3](https://github.com/unfs3/unfs3) you will need `make` `gcc` `flex` `bison` `nfs-client` to compile UNFS3

```sh
./bootstrap   # (only when building from git)
./configure
make
make install
```

### Installing Linux Headers

Download Linux kernel sources from [kernel.org](https://www.kernel.org)

```sh
curl -JLO https://cdn.kernel.org/pub/linux/kernel/v5.x/linux-5.4.124.tar.xz
```

Run the following command to install Linux headers for `arhs`:

```sh
tar xJf linux-5.4.124.tar.xz
CC=arc-linux-gnu- ARCH=arc make INSTALL_HDR_PATH=../linux-headers/usr headers_install -C linux-5.4.124
```

### Download Glibc sources

```sh
git clone https://github.com/foss-for-synopsys-dwc-arc-processors/glibc.git
```

## Running Glibc Testsuite

It may be useful to pass `CFLAGS` and `CXXFLAGS` environment variables to configure glibc.
The default values of `CFLAGS` and `CXXFLAGS` are ‘-O2’. For example:

```sh
export CFLAGS="-mcpu=hs38 -O2"
export CXXFLAGS="-mcpu=hs38 -O2"
```

> **Note**
>
> You could also set `CFLAGS` and `CXXFLAGS` with `--cflags` and `--cxxflags` script options

Run the following command to execute Glibc testing for `arhs` target:

```sh
./run_glibc_testsuite.py --qemu <qemu path> --toolchain-path <toolchain path> --toolchain-prefix=arc-linux-gnu --kernel <vmlinux path> --glibc-dir <glibc dir> --linux-headers-dir <linux headers dir> --unfs <unfsd path>
```

## Usage

```sh
usage: run_glibc_testsuite.py [-h] [--cpu CPU] [--toolchain-prefix TOOLCHAIN_PREFIX] [--qemu-path QEMU_PATH] [--ssh-host SSH_HOST] [--ssh-port SSH_PORT] --kernel KERNEL [--toolchain-path TOOLCHAIN_PATH] [--linux-headers-dir LINUX_HEADERS_DIR] [--linux-headers-version LINUX_HEADERS_VERSION] [--timeoutfactor TIMEOUTFACTOR] [--build-jobs BUILD_JOBS]
                              [--test-jobs TEST_JOBS] --glibc-dir GLIBC_DIR [--subdir SUBDIR] [--cflags CFLAGS] [--cxxflags CXXFLAGS] [--unfs UNFS] [--allow-time-setting] [--build] [--check] [--xcheck]

optional arguments:
  -h, --help            show this help message and exit
  --cpu CPU             processor to emulate(hs6x)
  --toolchain-prefix TOOLCHAIN_PREFIX
                        toolchain prefix(arc64-linux-gnu)
  --qemu-path QEMU_PATH
                        path to QEMU emulator
  --ssh-host SSH_HOST   target ssh hostname(127.0.0.1)
  --ssh-port SSH_PORT   target ssh port(22)
  --kernel KERNEL       path to kernel(vmlinux)
  --toolchain-path TOOLCHAIN_PATH
                        path to toolchain
  --linux-headers-dir LINUX_HEADERS_DIR
                        path to linux headers
  --linux-headers-version LINUX_HEADERS_VERSION
                        linux headers version
  --timeoutfactor TIMEOUTFACTOR
                        TIMEOUTAFACTOR on the remote machine(600)
  --build-jobs BUILD_JOBS
                        number of jobs to build tests(8)
  --test-jobs TEST_JOBS
                        number of jobs to run tests(1)
  --glibc-dir GLIBC_DIR
                        path to glibc directory
  --subdir SUBDIR       testing only a subset of tests(optional)
  --cflags CFLAGS       CFLAGS options(-O2)
  --cxxflags CXXFLAGS   CXXFLAGS options(-O2)
  --unfs UNFS           Path to unfs3(optional)
  --allow-time-setting  set GLIBC_TEST_ALLOW_TIME_SETTING env variable
  --build               run build
  --check               run tests
  --xcheck              run xtests
```
