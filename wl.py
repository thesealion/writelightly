# -*- coding: utf-8 -*-

import curses
import datetime
import locale
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from calendar import Calendar, lastday

locale.setlocale(locale.LC_ALL, ('en_US', 'UTF-8'))

data_dir = '~/.wl'
editor = 'gvim -f'

data_dir = os.path.expanduser(data_dir)


def entry_exists(date):
    path = os.path.join(data_dir, str(date))
    return os.path.exists(path)

def get_metadata(date):
    path = os.path.join(data_dir, str(date))
    lines, words = 0, 0
    try:
        with open(path) as f:
            for line in f:
                if not line.strip():
                    continue
                lines += 1
                words += len(line.split())
    except IOError:
        return None
    return (lines, words, os.path.getsize(path))


def get_metadata_for_month(year, month):
    data = {}
    for day in range(1, lastday(year, month) + 1):
        data[day] = get_metadata(datetime.date(year, month, day))
    return data

def show_metadata(date, metadata, window):
    window.clear()
    window.addstr(1, 1, '%s %d, %d' % (date.strftime('%B'), date.day, date.year))
    try:
        m = '%d lines, %d words, %d bytes' % (metadata[date.day])
    except TypeError:
        m = 'No entry for selected date'
    window.addstr(2, 1, m)
    window.addstr(6, 1, '\n'.join(textwrap.wrap('Use arrow keys to navigate through dates, press Enter to '
                    'edit or create entry for selected date.', 48)))
    window.refresh()

def main(stdscr):
    today = datetime.date.today()
    year, month = today.year, today.month
    cal = Calendar(year, month)
    cal.draw(stdscr, 1, 1, entry_exists)
    metadata = get_metadata_for_month(year, month)
    nw = curses.newwin(10, 50, 0, 30)
    show_metadata(cal.get_current_date(), metadata, nw)
    while 1:
        c = stdscr.getch()
        if c == ord('q'):
            break
        if c in (ord('h'), curses.KEY_LEFT):
            moved = cal.move_left()
            if not moved:
                year, month = (year if month != 1 else year - 1,
                              month - 1 if month != 1 else 12)
                cal = Calendar(year, month)
                stdscr.clear()
                cal.draw(stdscr, 1, 1, entry_exists, lastday(year, month))
                metadata = get_metadata_for_month(year, month)
            show_metadata(cal.get_current_date(), metadata, nw)
        elif c in (ord('l'), curses.KEY_RIGHT):
            moved = cal.move_right()
            if not moved:
                year, month = (year if month != 12 else year + 1,
                              month + 1 if month != 12 else 1)
                cal = Calendar(year, month)
                stdscr.clear()
                cal.draw(stdscr, 1, 1, entry_exists, 1)
                metadata = get_metadata_for_month(year, month)
            show_metadata(cal.get_current_date(), metadata, nw)
        elif c in (ord('j'), curses.KEY_DOWN):
            cal.move_down()
            show_metadata(cal.get_current_date(), metadata, nw)
        elif c in (ord('k'), curses.KEY_UP):
            cal.move_up()
            show_metadata(cal.get_current_date(), metadata, nw)
        elif c in (curses.KEY_ENTER, ord('e'), ord('\n')):
            date = cal.get_current_date()
            edit_date(date)
            cal.set_entry_exists_for_current_day(entry_exists(date))
            metadata[date.day] = get_metadata(date)
            show_metadata(date, metadata, nw)

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
    if os.path.isfile(data_dir):
        print '%s is not a directory' % data_dir
        sys.exit()
    try:
        os.mkdir(data_dir)
    except OSError:
        pass

    path = os.path.join(data_dir, filename)
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

    if new_content:
        with open(path, 'w') as f:
            f.write(new_content)
    else:
        if os.path.exists(path):
            os.remove(path)

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



