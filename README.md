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

### Running Glibc Testsuite for `archs` on the remote target

```sh
./run_glibc_testsuite.py --toolchain-path <toolchain path> \
                         --toolchain-prefix=arc-linux-gnu \
                         --glibc-dir <glibc dir> \
                         --linux-headers-dir <linux headers dir> \
                         --unfs <unfsd path> \
                         --ssh-host <target ip address>
```

### Running Glibc Testsuite for `archs` on the QEMU emulator

```sh
./run_glibc_testsuite.py --toolchain-path <toolchain path> \
                         --toolchain-prefix=arc-linux-gnu \
                         --glibc-dir <glibc dir> \
                         --linux-headers-dir <linux headers dir> \
                         --unfs <unfsd path> \
                         --kernel <path to kernel> \
                         --cpu archs \
                         --qemu-path <path to qemu>
```

### Running Glibc Testsuite for `archs` on the nSIM emulator

```sh
./run_glibc_testsuite.py --toolchain-path <toolchain path> \
                         --toolchain-prefix=arc-linux-gnu \
                         --glibc-dir <glibc dir> \
                         --linux-headers-dir <linux headers dir> \
                         --unfs <unfsd path> \
                         --kernel <path to kernel> \
                         --ssh-host <target ip address> \
                         --nsim-props support/nsim/nsim_hs.props \
                         --nsim-ifname=<tap interace>
```

## Usage

```sh
usage: run_glibc_testsuite.py [-h] --toolchain-prefix TOOLCHAIN_PREFIX --toolchain-path TOOLCHAIN_PATH --glibc-dir GLIBC_DIR --linux-headers-dir LINUX_HEADERS_DIR [--linux-headers-version LINUX_HEADERS_VERSION] [--kernel KERNEL] [--cpu CPU] [--qemu-path QEMU_PATH] [--nsim-path NSIM_PATH] [--nsim-propsfile NSIM_PROPSFILE] [--nsim-ifname NSIM_IFNAME] [--build-jobs BUILD_JOBS]
                              [--cflags CFLAGS] [--cxxflags CXXFLAGS] [--ssh-host SSH_HOST] [--ssh-port SSH_PORT] [--unfs UNFS] [--nfs-server-ip NFS_SERVER_IP] [--timeoutfactor TIMEOUTFACTOR] [--test-jobs TEST_JOBS] [--subdir SUBDIR] [--allow-time-setting] [--build-only | --check-only | --xcheck-only] [--verbose]

optional arguments:
  -h, --help            show this help message and exit
  --build-only          run build only
  --check-only          run tests only
  --xcheck-only         run xtests only
  --verbose             enable verbose output

general options:
  --toolchain-prefix TOOLCHAIN_PREFIX
                        toolchain prefix
  --toolchain-path TOOLCHAIN_PATH
                        path to toolchain
  --glibc-dir GLIBC_DIR
                        path to glibc directory
  --linux-headers-dir LINUX_HEADERS_DIR
                        path to linux headers
  --linux-headers-version LINUX_HEADERS_VERSION
                        linux headers version
  --kernel KERNEL       path to kernel

QEMU options:
  --cpu CPU             processor to emulate
  --qemu-path QEMU_PATH
                        path to QEMU emulator

nSIM options:
  --nsim-path NSIM_PATH
                        path to nSIM emulator
  --nsim-propsfile NSIM_PROPSFILE
                        nSIM properties file.
  --nsim-ifname NSIM_IFNAME
                        nSIM network interface name

build options:
  --build-jobs BUILD_JOBS
                        number of jobs to build tests(8)
  --cflags CFLAGS       CFLAGS options(-O2)
  --cxxflags CXXFLAGS   CXXFLAGS options(-O2)

SSH options:
  --ssh-host SSH_HOST   target ssh hostname(127.0.0.1)
  --ssh-port SSH_PORT   target ssh port

NFS options:
  --unfs UNFS           Path to unfs3
  --nfs-server-ip NFS_SERVER_IP
                        NFS server IP address

test options:
  --timeoutfactor TIMEOUTFACTOR
                        TIMEOUTAFACTOR on the remote machine(600)
  --test-jobs TEST_JOBS
                        number of jobs to run tests(1)
  --subdir SUBDIR       testing only a subset of tests(optional)
  --allow-time-setting  set GLIBC_TEST_ALLOW_TIME_SETTING env variable
```
