#!/usr/bin/env python

import os
import shutil
import re
import errno
import sys
import yaml


fs_empty_fn = 'empty_fs.vfat'
fs_fn = 'fs.vfat'
fs_firmware_start = 0x99000
final_firmware_fn = 'rgb-controller-esp8266.bin'


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
                exec(sline)
                py_modules = [x + '.py' for x in py_modules]
            elif sline.startswith('packages'):
                exec(sline)
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

    print "Done local setup for device", cfg['name']


def run(cfg):
    setup(cfg)
    cmd = 'micropython {}'.format(os.path.join(cfg['_path'], cfg['main']))
    print '\n$ {}\n'.format(cmd)
    shell_run(cmd)


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
    # boot + main
    shutil.copy2(os.path.join('platform', '_boot.py'), mod_dir)
    shutil.copy2(os.path.join(cfg['_path'], cfg['main']), os.path.join(mod_dir, 'main.py'))
    # compile micropython for esp8266
    shell_run('docker run --rm '
              '-v`pwd`/deps/micropython:/micropython '
              '-v`pwd`/{}/modules:/micropython/ports/esp8266/modules '
              '-v`pwd`/{}/esp8266:/micropython/ports/esp8266/build '
              'arsenicus/esp-open-sdk '
              '/bin/bash -c ". ~/.bashrc && cd /micropython/ports/esp8266 && make"'.format(build_dir, build_dir))


def help():
    fn = sys.argv[0]
    print '\nUtility to build / run / setup IOT platform device.\n'
    print 'Usage: {} <command> <device path>\n'.format(fn)
    print 'Where command is:'
    print '\tbuild    - build image(s).'
    print '\trun      - run device in emulation mode locally.'
    print '\tsetup    - setup micropython environment to run device locally.\n'
    print 'E.g.'
    print '$ {} build devices/neopixel_controller\n'.format(fn)


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
        print 'Unknown command "{}"'.format(cmd)
        quit(1)
    commands[cmd](cfg)
