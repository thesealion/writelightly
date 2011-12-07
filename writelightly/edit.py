import os
import shutil
import subprocess
import time

from writelightly.conf import Config
from writelightly.utils import WLError, WLQuit

from diff_match_patch import diff_match_patch
DMP = diff_match_patch()

conf = Config.general

class InvalidDataDir(WLError):
    """Raised when a data directory exists as a file."""
    def __init__(self, path):
        message = 'Invalid data directory: %s' % path
        super(InvalidDataDir, self).__init__(message)

def edit_file(path):
    """Call up an external editor specified in config to edit a file."""
    from writelightly.screen import ScreenManager
    ScreenManager.editor_called()
    return subprocess.call('%s %s' % (conf['editor'], path), shell=True)

def edit_date(date):
    """Edit the entry for the given date.

    If the entry exists, back it up to a temporary file, let user edit it,
    then store a reverse diff between versions.
    """
    month_dir = os.path.join(conf['entries_dir'], date.strftime('%Y-%m'))
    diff_dir = os.path.join(conf['diffs_dir'], date.strftime('%Y-%m'))
    for path in (month_dir, diff_dir):
        try:
            os.makedirs(path)
        except OSError:
            if not os.path.isdir(path):
                raise InvalidDataDir(path)

    fn = date.strftime('%d')
    path = os.path.join(month_dir, fn)
    if os.path.exists(path):
        tmp = path + '.tmp'
        shutil.copy(path, tmp)
        new = False
    else:
        new = True

    edit_file(path)

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
    """Get diff between two texts as a string using diff_match_patch"""
    p = [t if isinstance(t, unicode) else t.decode('utf-8') for t in (one, two)]
    diffs = DMP.diff_main(*p)
    DMP.diff_cleanupSemantic(diffs)
    patches = DMP.patch_make(p[0], diffs)
    return DMP.patch_toText(patches)

def get_edits(date):
    """Get a list of diffs for the given date along with their sizes."""
    diff_dir = os.path.join(conf['diffs_dir'], date.strftime('%Y-%m'))
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
    """Get an old version of an entry.

    Given a date, list of edits as returned by get_edits, and an index,
    apply needed diffs, save the result to a file and return its name.
    """
    diff_dir = os.path.join(conf['diffs_dir'], date.strftime('%Y-%m'))
    fn = date.strftime('%d')
    tmp = os.path.join(diff_dir, '%s_%d.tmp' % (fn, edits[index][0]))
    if os.path.exists(tmp):
        return tmp
    month_dir = os.path.join(conf['entries_dir'], date.strftime('%Y-%m'))
    path = os.path.join(month_dir, fn)
    with open(path) as f:
        text = f.read()
    for ts, _ in sorted(edits[index + 1:], reverse=True):
        diff_name = os.path.join(diff_dir, '%s_%d' % (fn, ts))
        with open(diff_name) as f:
            patches = DMP.patch_fromText(f.read())
            applied = DMP.patch_apply(patches, text.decode('utf-8'))
            text = applied[0].encode('utf-8')
    with open(tmp, 'w') as f:
        f.write(text)
    return tmp

def clean_tmp(d=conf['diffs_dir']):
    """Delete all temporary files from a directory."""
    for fn in os.listdir(d):
        path = os.path.join(d, fn)
        if os.path.isdir(path):
            clean_tmp(path)
        elif fn.endswith('.tmp'):
            os.remove(path)

def show_edits(date, edits, area_id):
    """Show all edits of an entry as a scrollable list."""
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
        kn = curses.keyname(sl.window.getch())
        if kn in Config.general_keys['quit']:
            raise WLQuit
        if kn in Config.general_keys['quit_mode']:
            break
        if kn == 'KEY_RESIZE':
            ScreenManager.resize()
        if sl.hidden:
            continue
        elif kn in Config.edits_keys['open']:
            index = sl.get_current_index()
            fn = save_tmp_version(date, edits, index)
            edit_file(fn)
            sl.draw()
        else:
            sl.handle_keypress(kn)
