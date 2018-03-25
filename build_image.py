#!/usr/bin/env python3

import os
import shutil
import re
import errno


build_dir = './build'
fs_empty_fn = 'empty_fs.vfat'
fs_fn = 'fs.vfat'
fs_firmware_start = 0x99000
final_firmware_fn = 'rgb-controller-esp8266.bin'


# mkdir -p
def mkdir_p(path):
    print('[MKDIR]', path)
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def run(cmd):
    print('[RUN]', cmd)
    ret = os.system(cmd)
    if ret != 0:
        raise SystemExit('Failed to execute shell command.')


def vfat_add_files(fn, src, dst_path='/'):
    """Adds files to VFAT filesystem"""
    fn = os.path.join(build_dir, fn)
    run('MTOOLS_SKIP_CHECK=1 mcopy -s -i %s %s ::%s' % (fn, src, dst_path))


def create_web_archive(infile, outfile, path='ui'):
    """Creates all-in-one html gzipped page by embedding assets like css/js/etc"""
    if outfile.endswith('.gz'):
        outfile = outfile[:-3]
    with open(os.path.join(path, infile), 'rb') as fin:
        with open(os.path.join(build_dir, outfile), 'wb') as fout:
            for line in fin:
                m = re.search(b'<link.+href="(.+)">', line)
                if m:
                    head = b'<style>\n'
                    bottom = b'\n</style>\n'
                else:
                    m = re.search(b'<script.*src="(.+)">', line)
                    if m:
                        head = b'<script>\n'
                        bottom = b'\n</script>\n'
                if m:
                    src = m.group(1).decode()
                    print("Embedding '{}' into {}".format(src, outfile))
                    with open(os.path.join(path, src), 'rb') as f:
                        fout.write(head)
                        fout.write(f.read())
                        fout.write(bottom)
                else:
                    fout.write(line)
    run('gzip -f --best --no-name %s' % os.path.join(build_dir, outfile))


if __name__ == '__main__':
    # Build image:
    # 1. Cleanup build folder
    # 2. Prepare python modules thats are going to be "frozen"
    # 3. Create FAT filesystem
    # 4. Compile micropython firmware
    # 5. Append it to the (almost) end of firmware
    # shutil.rmtree(build_dir, ignore_errors=True)
    mkdir_p(os.path.join(build_dir, 'modules'))
    # Copy deps
    run('cp -rf deps/micropython-lib/uasyncio/uasyncio/ {}/modules/uasyncio'.format(build_dir))
    run('cp -f deps/micropython-lib/uasyncio.core/uasyncio/core.py {}/modules/uasyncio/'.format(build_dir))
    run('cp -rf deps/tinyweb/tinyweb/ {}/modules/tinyweb'.format(build_dir))
    run('cp -rf deps/micropython-esp-utils/utils/ {}/modules/utils'.format(build_dir))
    run('cp -rf controller/ {}/modules'.format(build_dir))
    # Create one page web archives
    create_web_archive('setup.html', 'setup_all.html.gz')
    create_web_archive('dashboard.html', 'dashboard_all.html.gz')
    # Create filesystem
    shutil.copyfile(fs_empty_fn, os.path.join(build_dir, fs_fn))
    vfat_add_files(fs_fn, os.path.join(build_dir, 'setup_all.html.gz'))
    vfat_add_files(fs_fn, os.path.join(build_dir, 'dashboard_all.html.gz'))
    # Compile micropython
    run('docker run --rm '
        '-v`pwd`/deps/micropython:/micropython '
        '-v`pwd`/{}/modules:/micropython/ports/esp8266/modules '
        '-v`pwd`/{}/firmware:/micropython/ports/esp8266/build '
        'arsenicus/esp-open-sdk '
        '/bin/bash -c ". ~/.bashrc && cd /micropython/ports/esp8266 && make"'.format(build_dir, build_dir))
    # Add filesystem to the firmware
    with open(os.path.join(build_dir, 'firmware', 'firmware-combined.bin'), 'rb') as f:
        firmware = f.read()
        firmware_len = len(firmware)
    with open(os.path.join(build_dir, fs_fn), 'rb') as f:
        fs = f.read()
    # Fill empty space with 0xff between firmare and filesystem
    padding = b'\xff' * (fs_firmware_start - firmware_len)
    # # Write final firmware
    print('Base image', firmware_len)
    print('Padding   ', len(padding))
    print('Filesystem', len(fs))
    print('Total size', firmware_len + len(padding) + len(fs))
    final_fn = os.path.join(build_dir, final_firmware_fn)
    with open(final_fn, 'wb') as f:
        f.write(firmware)
        f.write(padding)
        f.write(fs)
    print('\nRGB Controller Firmware {} is ready.'.format(final_fn))
