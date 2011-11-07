import os
import tempfile
import shutil
import subprocess
import time
import conf

from diff_match_patch import diff_match_patch
DMP = diff_match_patch()

class InvalidDataDir(Exception):
    pass

def edit_date(date):
    month_dir = os.path.join(conf.entries_dir, date.strftime('%Y-%m'))
    try:
        os.makedirs(month_dir)
    except OSError:
        if not os.path.exists(month_dir) or not os.path.isdir(month_dir):
            raise InvalidDataDir

    fn = date.strftime('%d')
    path = os.path.join(month_dir, fn)
    if os.path.exists(path):
        tmp = path + '.tmp'
        shutil.copy(path, tmp)
        new = False
    else:
        new = True

    exit_code = subprocess.call('%s %s' % (conf.editor, path), shell=True)

    diff_dir = os.path.join(conf.diffs_dir, date.strftime('%Y-%m'))
    try:
        os.makedirs(diff_dir)
    except OSError:
        if not os.path.exists(diff_dir) or not os.path.isdir(diff_dir):
            raise InvalidDataDir

    diff_name = os.path.join(diff_dir, '%s_%d' % (fn, time.time()))
    if new:
        open(diff_name, 'w').close()
    else:
        with open(path) as f:
            new_content = f.read()
        with open(tmp) as f:
            old_content = f.read()
        diff = get_diff(new_content, old_content)
        if diff:
            with open(diff_name, 'w') as f:
                f.write(diff)
        os.remove(tmp)

def get_diff(one, two):
    diffs = DMP.diff_main(one, two)
    DMP.diff_cleanupSemantic(diffs)
    patches = DMP.patch_make(one, diffs)
    return DMP.patch_toText(patches)

def get_edits(date):
    diff_dir = os.path.join(conf.diffs_dir, date.strftime('%Y-%m'))
    try:
        ld = os.listdir(diff_dir)
    except OSError:
        raise InvalidDataDir
    day = date.strftime('%d')
    timestamps = [int(fn.split('_')[1]) for fn in ld if fn.startswith(day)]
    return sorted(timestamps)

