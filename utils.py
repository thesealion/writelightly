import curses
import datetime
import os
import re

def init_screen():
    screen = curses.initscr()
    curses.noecho()
    curses.cbreak()
    screen.keypad(1)
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    return screen

def deinit_screen(screen):
    screen.keypad(0)
    curses.nocbreak()
    curses.echo()
    curses.endwin()

def lastday(*args):
    if not args:
        raise TypeError('I need some arguments')
    if len(args) == 1 and type(args[0]) is datetime.date:
        year, month = args[0].year, args[0].month
    elif len(args) == 2 and type(args[0]) is int and type(args[1]) is int:
        year, month = args
    else:
        raise TypeError('Give me either datetime.date or year and month')
    next_first = datetime.date(year if month != 12 else year + 1,
                               month + 1 if month != 12 else 1, 1)
    return (next_first - datetime.timedelta(days=1)).day

def entry_exists(date):
    from metadata import Metadata
    data = Metadata.get(date.year, date.month).get_data_for_day(date.day)
    return data is not None

def format_size(size):
    if size > 1024:
        kib = size // 1024 + (size % 1024) / 1024.0
        return ('%.2f' % kib).rstrip('0').rstrip('.') + ' KiB'
    return '%d B' % size

def format_date(date):
    return '%s %d, %d' % (date.strftime('%B'), date.day, date.year)

def get_all_months(data_dir):
    entries = os.listdir(data_dir)
    try:
        entries.remove('metadata')
    except ValueError:
        pass

    months = set()
    for entry in entries:
        months.add(tuple(map(int, entry.split('-')[:2])))

    return sorted(sorted(list(months), key=lambda i: i[1]), key=lambda i: i[0])

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
