#!/usr/bin/env python3

import os
import glob
import shutil
import re
import errno
import sys
import yaml


fs_empty_fn = 'platform/empty_fs.vfat'
fs_fn = 'fs.vfat'
data_flash_start = 0xa0000
sec_size = 4096

# mkdir -p
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def shell_run(cmd):
    ret = os.system(cmd)
    if ret != 0:
        raise SystemExit('Failed to execute shell command.')


def load_config(path):
    with open(os.path.join(path, 'config.yaml')) as f:
        cfg = yaml.load(f)
        cfg['_path'] = path
        return cfg


def get_mlib_files(name):
    fn = os.path.join('deps', 'micropython-lib', name)
    packages = []
    py_modules = []
    with open(os.path.join(fn, 'setup.py')) as f:
        for line in f:
            sline = line.strip()[:-1]
            if sline.startswith('py_modules'):
                namespace = {}
                exec(sline, namespace)
                py_modules = [x + '.py' for x in namespace['py_modules']]
            elif sline.startswith('packages'):
                namespace = {}
                exec(sline, namespace)
                packages = namespace['packages']
    return packages, py_modules


def setup(cfg):
    cdir = os.getcwd()
    mdir = os.path.join(os.path.expanduser("~"), '.micropython/lib')
    # Cleanup micropython lib dir
    shutil.rmtree(mdir, ignore_errors=True)
    mkdir_p(mdir)

    # Make symlinks to all frozen things
    for it in cfg.get('frozen', []):
        parts = os.path.split(it)
        mkdir_p(os.path.join(mdir, parts[0]))
        if os.path.isdir(it):
            os.symlink(os.path.join(cdir, it), os.path.join(mdir, it))
        else:
            mkdir_p(os.path.join(mdir, parts[0]))
            os.symlink(os.path.join(cdir, it), os.path.join(mdir, it))

    # .. for external packages
    for it in cfg.get('packages', []):
        parts = os.path.split(it)
        os.symlink(os.path.join(cdir, it), os.path.join(mdir, parts[-1]))

    # micropython library deps
    for it in cfg.get('micropython-lib', []) + ['unittest']:
        pkg_dir = os.path.join(cdir, 'deps', 'micropython-lib', it)
        pkg, pymods = get_mlib_files(it)
        for p in pkg:
            mkdir_p(os.path.join(mdir, p))
            full = os.path.join(pkg_dir, p)
            for f in os.listdir(full):
                os.symlink(os.path.join(full, f), os.path.join(mdir, p, f))
        for py in pymods:
            os.symlink(os.path.join(pkg_dir, py), os.path.join(mdir, py))
    # Add mocks into micropython
    for f in os.listdir(os.path.join(cdir, 'mock')):
        os.symlink(os.path.join(cdir, 'mock', f), os.path.join(mdir, f))

    print("Done local setup for device", cfg['name'])


def run(cfg):
    setup(cfg)
    cmd = 'micropython {}'.format(os.path.join(cfg['_path'], cfg['main']))
    print('\n$ {}\n'.format(cmd))
    shell_run(cmd)


def process_ui_vuetify(mount_point, fat_fn, fscfg):
    print('Compiling Vue UI application...')
    uipath = fscfg['ui-vuetify']
    shell_run('cd {} && npm run build'.format(uipath))
    # Copy dist folder into build_root
    build_dst = os.path.join(os.path.dirname(fat_fn))
    dest_dir = build_dst + mount_point
    shutil.rmtree(dest_dir, ignore_errors=True)
    shell_run('cp -rf {}/ {}'.format(os.path.join(uipath, 'dist'), dest_dir))
    # Embed css/js right into html - this will save load time
    # Reading original file from ui dir
    with open(os.path.join(uipath, 'public', 'index.html'), 'r') as fin:
        lines = fin.readlines()
    # Write changes into _build dir
    indexfile = os.path.join(dest_dir, 'index.html')
    with open(indexfile, 'w') as fout:
        for line in lines:
            # remove refs to css / js
            m = re.search('<link.+[css|js]\/app', line)
            if m:
                continue
            fout.write(line)
            if '<title>' in line:
                fcss = glob.glob(os.path.join(uipath, 'dist/css/*.css'))[0]
                print("\tInjecting CSS", fcss)
                with open(fcss, 'r') as css:
                    fout.write('<style>\n')
                    fout.write(css.read())
                    fout.write('</style>\n')
            if '</body>' in line:
                fjs = glob.glob(os.path.join(uipath, 'dist/js/*.js'))[0]
                print('\tInjecting JS', fjs)
                with open(fjs, 'r') as js:
                    fout.write('<script>\n')
                    fout.write(js.read())
                    fout.write('</script>\n')
    # Remove unwanted files from vue build folder
    for f in glob.glob(os.path.join(dest_dir, '**/*.*'), recursive=True):
        name, ext = os.path.splitext(f)
        # delete unwanted files
        if ext in ['.css', '.map', '.js']:
            os.remove(f)
            continue
        # pre gzip files - to save flash and improve web app performance
        if fscfg.get('gzip', True):
            shell_run('gzip -f --best --no-name {}'.format(f))
    shell_run('MTOOLS_SKIP_CHECK=1 mcopy -s -i {} {}/* ::/'.format(fat_fn, dest_dir))
    print()


def build(cfg):
    build_dir = cfg.get('build_dir', '_build')
    # Copy everything which needs to be frozen
    mod_dir = os.path.join(build_dir, 'modules')
    shutil.rmtree(mod_dir, ignore_errors=True)
    shutil.rmtree(os.path.join(build_dir, 'esp8266', 'frozen_mpy'), ignore_errors=True)
    mkdir_p(mod_dir)
    for it in cfg.get('frozen', []):
        if os.path.isdir(it):
            shutil.copytree(it, os.path.join(mod_dir, it))
        else:
            mkdir_p(os.path.join(mod_dir, os.path.split(it)[0]))
            shutil.copy2(it, os.path.join(mod_dir, it))
    for it in cfg.get('packages', []):
        shutil.copytree(it, os.path.join(mod_dir, os.path.split(it)[1]))
    for it in cfg.get('micropython-lib', []):
        pkg_dir = os.path.join('deps', 'micropython-lib', it)
        pkg, pymods = get_mlib_files(it)
        for p in pkg:
            shell_run('cp -rf {}/ {}'.format(os.path.join(pkg_dir, p), os.path.join(mod_dir, p)))
        for py in pymods:
            shutil.copy2(os.path.join(pkg_dir, py), mod_dir)
    # boot + device files
    shutil.copy2(os.path.join('platform', '_boot.py'), mod_dir)
    for f in os.listdir(cfg['_path']):
        if not f.endswith('.py'):
            continue
        if f == cfg['main']:
            # rename main device file into main.py
            dst = 'main.py'
        else:
            dst = f
        shutil.copy2(os.path.join(cfg['_path'], f), os.path.join(mod_dir, dst))
    # compile micropython for esp8266
    shell_run('docker run --rm '
              '-v`pwd`/deps/micropython:/micropython '
              '-v`pwd`/{}/modules:/micropython/ports/esp8266/modules '
              '-v`pwd`/{}/esp8266:/micropython/ports/esp8266/build '
              'arsenicus/esp-open-sdk '
              '/bin/bash -c ". ~/.bashrc && cd /micropython/ports/esp8266 && make"'.format(build_dir, build_dir))
    # Prepare final image
    base_firmware_fn = os.path.join(build_dir, 'esp8266', 'firmware-combined.bin')
    if os.stat(base_firmware_fn).st_size > data_flash_start:
        print("\nERROR:Image too big, unable append file system.")
        quit(1)
    with open(base_firmware_fn, 'rb') as f:
        firmware = f.read()
        firmware_len = len(firmware)
    # Add padding between firmare and metadata
    padding = b'\xff' * (data_flash_start - firmware_len)
    # Image metadata, located at 0xa0000 sector.
    meta = bytearray([0xff] * sec_size)
    # Write final firmware
    final_fn = os.path.join(build_dir, cfg['name'] + '.bin')
    fs_total_len = 0
    with open(final_fn, 'wb') as fout:
        fout.write(firmware)
        fout.write(padding)
        fout.write(meta)
        # Add filesystems
        meta_off = 0  # offset in metadata
        fs_sect = data_flash_start // sec_size + 1
        print()
        for mount_point, fscfg in cfg.get('filesystems', {}).items():
            print('Creating filesystem {}'.format(mount_point))
            if len(mount_point) > 16:
                print("Mount point '{}' too long".format(mount_point))
                quit(1)
            if mount_point[0] != '/':
                print("Invalid mount point", mount_point)
            # Create FAT
            fat_fn = os.path.join(build_dir, mount_point[1:] + '.vfat')
            shutil.copy2(fs_empty_fn, fat_fn)
            # If this is special types like "ui-vuetify" this requires some
            # proprocessing
            if 'ui-vuetify' in fscfg:
                process_ui_vuetify(mount_point, fat_fn, fscfg)
            if 'files' in fscfg:
                for f in fscfg['files']:
                    print('\t', f)
                    shell_run('MTOOLS_SKIP_CHECK=1 mcopy -s -i {} {} ::/{}'.format(fat_fn, f, f))
            print('\n{} summary:'.format(mount_point))
            # Fill meta with final FS information
            fs_len = os.stat(fat_fn).st_size
            # Final len includes: reserve space + padding
            fs_final_len = fs_len + fscfg.get('reserved', sec_size)
            fs_padding = sec_size - (fs_final_len % sec_size)
            if fs_padding == sec_size:
                fs_padding = 0
            fs_final_len += fs_padding
            # Write FS padding
            if fs_padding:
                with open(fat_fn, 'ab') as fs:
                    fs.write(b'\xff' * (fs_final_len - fs_len))
            print('\tvFat size ', fs_len)
            print('\tReserved  ', fscfg.get('reserved', sec_size))
            print('\tPadding   ', fs_padding)
            print('\tStart Sec ', fs_sect)
            print('\tTotal Len ', fs_final_len)
            print()
            fs_total_len += fs_final_len
            # Update meta info
            meta[meta_off:meta_off + 16] = mount_point.ljust(16).encode()
            meta_off += 16
            meta[meta_off:meta_off + 4] = fs_sect.to_bytes(4, 'big')
            meta_off += 4
            meta[meta_off:meta_off + 4] = fs_final_len.to_bytes(4, 'big')
            meta_off += 4
            meta[meta_off] = fscfg.get('readonly', False)
            # 3 bytes reserved
            meta_off += 4
            fs_sect += fs_final_len // sec_size
            # Write prepared filesystem into image
            with open(fat_fn, 'rb') as fin:
                fout.write(fin.read())
        # Re-write meta data
        fout.seek(firmware_len + len(padding))
        fout.write(meta)
        # print(meta)

    print('Summary:')
    print('\tBase image ', firmware_len)
    print('\tPadding    ', len(padding))
    print('\tMeta       ', len(meta))
    print('\tFilesystems', fs_total_len)
    print('\tTotal size ', firmware_len + len(padding) + fs_total_len + len(meta))
    print('\nFirmware for {} ready: ./{}\n'.format(cfg['name'], final_fn))


def help():
    fn = sys.argv[0]
    print('\nUtility to build / run / setup IOT platform device.\n')
    print('Usage: {} <command> <device path>\n'.format(fn))
    print('Where command is:')
    print('\tbuild    - build image(s).')
    print('\trun      - run device in emulation mode locally.')
    print('\tsetup    - setup micropython environment to run device locally.\n')
    print('E.g.')
    print('$ {} build devices/neopixel_controller\n'.format(fn))


commands = {'run': run,
            'setup': setup,
            'build': build}

if __name__ == '__main__':
    if len(sys.argv) < 3:
        help()
        quit(1)
    # Load device config, then run command
    cfg = load_config(sys.argv[2])

    cmd = sys.argv[1]
    if cmd not in commands:
        print('Unknown command "{}"'.format(cmd))
        quit(1)
    commands[cmd](cfg)
