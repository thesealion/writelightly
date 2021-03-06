import datetime
import os
import re

class WLError(Exception):
    """Base class for all Writelightly exceptions."""

class WLQuit(WLError):
    """Raised when user sends a quit command."""

def lastday(*args):
    """Return the last day of the given month.

    Takes datetime.date or year and month, returns an integer.
    >>> lastday(2011, 11)
    30
    >>> lastday(datetime.date(2011, 2, 1))
    28
    """
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
    """Check if an entry for the given date exists."""
    from metadata import Metadata
    data = Metadata.get(date.year, date.month).get_data_for_day(date.day)
    return data is not None

def format_size(size):
    """Format a size of a file in bytes to be human-readable."""
    size = int(size)
    if size > 1024:
        kib = size // 1024 + (size % 1024) / 1024.0
        return ('%.2f' % kib).rstrip('0').rstrip('.') + ' KiB'
    return '%d B' % size

def format_date(date):
    return '%s %d, %d' % (date.strftime('%B'), date.day, date.year)

def get_all_months(data_dir):
    """
    Return a sorted list of (year, month) tuples for months that have entries.
    """
    entries_dir = os.path.join(data_dir, 'entries')
    entries = os.listdir(entries_dir)

    months = set()
    for entry in entries:
        months.add(tuple(map(int, entry.split('-'))))

    return sorted(sorted(list(months), key=lambda i: i[1]), key=lambda i: i[0])

def parse_date(date):
    """Try to recognize a date using several formats."""
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

def get_char(win):
    """Use win.getch() to get a character even if it's multibyte.

    A magic function that I found somewhere on the Internet. But it works
    well, at least for Russian characters in a UTF-8-based shell.
    Needs testing.
    """
    def get_check_next_byte():
        c = win.getch()
        if 128 <= c <= 191:
            return c
        else:
            raise UnicodeError

    bytes = []
    c = win.getch()
    if c <= 127:
        return c
    elif 194 <= c <= 223:
        bytes.append(c)
        bytes.append(get_check_next_byte())
    elif 224 <= c <= 239:
        bytes.append(c)
        bytes.append(get_check_next_byte())
        bytes.append(get_check_next_byte())
    elif 240 <= c <= 244:
        bytes.append(c)
        bytes.append(get_check_next_byte())
        bytes.append(get_check_next_byte())
        bytes.append(get_check_next_byte())
    else:
        return c
    buf = ''.join([chr(b) for b in bytes])
    return buf

def format_time(ts, full=False):
    """Format a timestamp relatively to the current time."""
    if not ts:
        return 'unknown'
    dt = datetime.datetime.fromtimestamp(ts)
    today = datetime.date.today()
    fmt = ' '.join(filter(None, [
        '%Y' if dt.year != today.year or full else '',
        '%b %d' if (dt.month, dt.day) != (today.month, today.day)
            or full else '',
        '%H:%M'
    ]))
    return dt.strftime(fmt)

