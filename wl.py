# -*- coding: utf-8 -*-

import curses
import datetime
import locale
import os
import re
import subprocess
import sys
import tempfile
from calendar import Calendar

locale.setlocale(locale.LC_ALL, ('en_US', 'UTF-8'))

data_dir = '~/.wl'
editor = 'gvim -f'


def entry_exists(date):
    path = os.path.join(os.path.expanduser(data_dir), str(date))
    return os.path.exists(path)

def main(stdscr):
    today = datetime.date.today()
    cal = Calendar(today.year, today.month)
    cal.draw(stdscr, 1, 1, entry_exists)
    while 1:
        c = stdscr.getch()
        if c == ord('q'):
            break
        if c in (ord('h'), curses.KEY_LEFT):
            cal.move_left()
        elif c in (ord('l'), curses.KEY_RIGHT):
            cal.move_right()
        elif c in (ord('j'), curses.KEY_DOWN):
            cal.move_down()
        elif c in (ord('k'), curses.KEY_UP):
            cal.move_up()
        elif c in (curses.KEY_ENTER, ord('e'), ord('\n')):
            date = cal.get_current_date()
            edit_date(date)
            cal.set_entry_exists_for_current_day(entry_exists(date))

def parse_date(date):
    if date == 'today':
        return datetime.date.today()
    if date == 'yesterday':
        return datetime.date.today() - datetime.timedelta(days=1)
    for p in ['(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})',
              '(?P<month>\d{2})/(?P<day>\d{2})/(?P<year>\d{4})',
              '(?P<day>\d{2}).(?P<month>\d{2}).(?P<year>\d{4})']:
        m = re.match(p, date)
        if m:
            d = m.groupdict()
            return datetime.date(int(d['year']), int(d['month']), int(d['day']))
    return None

def edit_date(date):
    filename = str(date)
    dir_path = os.path.expanduser(data_dir)
    if os.path.isfile(dir_path):
        print '%s is not a directory' % dir_path
        sys.exit()
    try:
        os.mkdir(dir_path)
    except OSError:
        pass

    path = os.path.join(dir_path, filename)
    if os.path.exists(path):
        with open(path) as f:
            content = f.read()
    else:
        content = ''

    _, tmpfn = tempfile.mkstemp(text=True)
    with open(tmpfn, 'w') as f:
        f.write(content)
    exit_code = subprocess.call('%s %s' % (editor, tmpfn), shell=True)

    with open(tmpfn) as f:
        new_content = f.read()

    with open(path, 'w') as f:
        f.write(new_content)

    os.remove(tmpfn)

if __name__ == '__main__':
    args = sys.argv[1:]
    if args:
        date = parse_date(args[0])
        if not date:
            print 'Usage: %s [<date>]' % sys.argv[0]
            sys.exit()
        edit_date(date)
    else:
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(1)
        curses.curs_set(0)

        try:
            main(stdscr)
        finally:
            stdscr.keypad(0)
            curses.nocbreak()
            curses.echo()
            curses.endwin()



