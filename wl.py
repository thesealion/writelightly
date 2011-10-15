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
from metadata import Metadata
import conf

locale.setlocale(locale.LC_ALL, ('en_US', 'UTF-8'))

data_dir = os.path.expanduser(conf.data_dir)


def entry_exists(date):
    path = os.path.join(data_dir, str(date))
    return os.path.exists(path)


def show_metadata(date, metadata, window):
    window.clear()
    window.addstr(1, 1, '%s %d, %d' % (date.strftime('%B'), date.day, date.year))
    try:
        m = '%(lines)d lines, %(words)d words, %(size)s' % (metadata)
        tags = ', '.join(metadata['tags'])
    except TypeError:
        m = 'No entry for selected date'
        tags = None
    window.addstr(2, 1, m)
    if tags:
        window.addstr(3, 1, 'Tags: %s' % tags)
    window.addstr(6, 1, '\n'.join(textwrap.wrap('Use arrow keys to navigate through dates, press Enter to '
                    'edit or create entry for selected date.', 48)))
    window.refresh()

def main(stdscr):
    today = datetime.date.today()
    year, month = today.year, today.month
    cal = Calendar(year, month)
    cal.draw(stdscr, 1, 1, entry_exists)
    metadata = Metadata(year, month)
    nw = curses.newwin(10, 50, 0, 30)
    d = cal.get_current_date()
    show_metadata(d, metadata.get_data_for_day(d.day), nw)
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
                metadata.write()
                metadata = Metadata(year, month)
            d = cal.get_current_date()
            show_metadata(d, metadata.get_data_for_day(d.day), nw)
        elif c in (ord('l'), curses.KEY_RIGHT):
            moved = cal.move_right()
            if not moved:
                year, month = (year if month != 12 else year + 1,
                              month + 1 if month != 12 else 1)
                cal = Calendar(year, month)
                stdscr.clear()
                cal.draw(stdscr, 1, 1, entry_exists, 1)
                metadata.write()
                metadata = Metadata(year, month)
            d = cal.get_current_date()
            show_metadata(d, metadata.get_data_for_day(d.day), nw)
        elif c in (ord('j'), curses.KEY_DOWN):
            cal.move_down()
            d = cal.get_current_date()
            show_metadata(d, metadata.get_data_for_day(d.day), nw)
        elif c in (ord('k'), curses.KEY_UP):
            cal.move_up()
            d = cal.get_current_date()
            show_metadata(d, metadata.get_data_for_day(d.day), nw)
        elif c in (curses.KEY_ENTER, ord('e'), ord('\n')):
            date = cal.get_current_date()
            edit_date(date)
            cal.set_entry_exists_for_current_day(entry_exists(date))
            metadata.load_day(date.day)
            show_metadata(date, metadata.get_data_for_day(date.day), nw)
    metadata.write()

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
        new = False
    else:
        content = '\n'
        new = True

    _, tmpfn = tempfile.mkstemp(text=True)

    action = 'new entry' if new else 'editing entry'
    header = '#%s %d, %d: %s\n' % (date.strftime('%B'), date.day, date.year,
                                   action)
    with open(tmpfn, 'w') as f:
        f.write(header)
        f.write(content)
    exit_code = subprocess.call('%s %s' % (conf.editor, tmpfn), shell=True)

    with open(tmpfn) as f:
        new_content = f.read()
    if new_content.startswith(header):
        new_content = new_content.replace(header, '', 1)

    if new_content.strip():
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
        metadata = Metadata(date.year, date.month)
        metadata.load_day(date.day)
        metadata.write()
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



