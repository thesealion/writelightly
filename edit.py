import os
import shutil
import subprocess
import tempfile
import time

from writelightly import conf
from writelightly.utils import WLError

from diff_match_patch import diff_match_patch
DMP = diff_match_patch()

class InvalidDataDir(WLError):
    pass

def edit_file(path):
    return subprocess.call('%s %s' % (conf.editor, path), shell=True)

def edit_date(date):
    month_dir = os.path.join(conf.entries_dir, date.strftime('%Y-%m'))
    try:
        os.makedirs(month_dir)
    except OSError:
        if not os.path.isdir(month_dir):
            raise InvalidDataDir(month_dir)

    fn = date.strftime('%d')
    path = os.path.join(month_dir, fn)
    if os.path.exists(path):
        tmp = path + '.tmp'
        shutil.copy(path, tmp)
        new = False
    else:
        new = True

    exit_code = edit_file(path)

    diff_dir = os.path.join(conf.diffs_dir, date.strftime('%Y-%m'))
    try:
        os.makedirs(diff_dir)
    except OSError:
        if not os.path.isdir(diff_dir):
            raise InvalidDataDir(diff_dir)

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
        raise InvalidDataDir(diff_dir)
    day = date.strftime('%d')
    timestamps = [int(fn.split('_')[1]) for fn in ld if fn.startswith(day)
        and not fn.endswith('.tmp')]
    sizes = [os.path.getsize(os.path.join(diff_dir, '%s_%d' % (day, ts)))
        for ts in timestamps]
    return sorted(zip(timestamps, sizes))

def save_tmp_version(date, edits, index):
    diff_dir = os.path.join(conf.diffs_dir, date.strftime('%Y-%m'))
    fn = date.strftime('%d')
    tmp = os.path.join(diff_dir, '%s_%d.tmp' % (fn, edits[index][0]))
    if os.path.exists(tmp):
        return tmp
    month_dir = os.path.join(conf.entries_dir, date.strftime('%Y-%m'))
    path = os.path.join(month_dir, fn)
    with open(path) as f:
        text = f.read()
    for ts, _ in sorted(edits[index + 1:], reverse=True):
        diff_name = os.path.join(diff_dir, '%s_%d' % (fn, ts))
        with open(diff_name) as f:
            patches = DMP.patch_fromText(f.read())
            text = DMP.patch_apply(patches, text)[0]
    with open(tmp, 'w') as f:
        f.write(text)
    return tmp

def clean_tmp(d=conf.diffs_dir):
    for fn in os.listdir(d):
        path = os.path.join(d, fn)
        if os.path.isdir(path):
            clean_tmp(path)
        elif fn.endswith('.tmp'):
            os.remove(path)

def show_edits(date, edits, area_id):
    from writelightly.screen import ScreenManager
    from writelightly.utils import format_time, format_size
    from writelightly.scrollable_list import ScrollableList
    import curses
    formatted = ['%s, created' % format_time(edits[0][0], full=True)]
    formatted += ['%s, %s' % (format_time(ts, full=True),
        format_size(size)) for ts, size in edits[1:]]
    sl = ScrollableList(formatted, area_id=area_id)
    sl.draw()
    while 1:
        c = sl.window.getch()
        if c == ord('q'):
            break
        if c == curses.KEY_RESIZE:
            ScreenManager.resize()
        if sl.hidden:
            continue
        elif c in (curses.KEY_ENTER, ord('e'), ord('\n')):
            index = sl.get_current_index()
            fn = save_tmp_version(date, edits, index)
            edit_file(fn)
        else:
            sl.handle_keypress(c)
