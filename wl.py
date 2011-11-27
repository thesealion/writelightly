import curses
import datetime
import os
import sys
import textwrap

from writelightly.calendar import Calendar, lastday
from writelightly.conf import Config
from writelightly.edit import (edit_date, get_edits, edit_file,
        save_tmp_version, clean_tmp, show_edits)
from writelightly.metadata import Metadata
from writelightly.screen import ScreenManager, TextArea
from writelightly.scrollable_list import ScrollableList
from writelightly.tags import show_tags, show_tag
from writelightly.utils import (entry_exists, parse_date, format_time,
        format_size, WLError, WLQuit)

import locale
locale.setlocale(locale.LC_ALL, ('en_US', 'UTF-8'))

def show_calendar():
    """Show an interactive calendar.

    Show the calendar on the left side of the screen and some metadata about
    the selected date on the right. Any entry can be edited in external editor.
    """
    today = datetime.date.today()
    year, month = today.year, today.month
    cal = Calendar(year, month, today.day, entry_exists)
    metadata = Metadata.get(year, month)
    text_area = TextArea()
    ScreenManager.draw_all()
    d = cal.get_current_date()
    text_area.show_text(metadata.text(d.day))
    keys = Config.calendar_keys
    while 1:
        try:
            kn = curses.keyname(cal.window.getch())
        except KeyboardInterrupt:
            break
        except ValueError:
            continue
        if kn in Config.general_keys['quit']:
            raise WLQuit
        if kn in Config.general_keys['quit_mode']:
            break
        if kn == 'KEY_RESIZE':
            ScreenManager.resize()
        if cal.hidden:
            continue
        if kn in keys['left']:
            moved = cal.move_left()
            if not moved:
                cal = cal.get_previous_calendar()
                cal.draw()
                metadata = Metadata.get(cal.year, cal.month)
            text_area.show_text(metadata.text(cal.get_current_day()))
        elif kn in keys['right']:
            moved = cal.move_right()
            if not moved:
                cal = cal.get_next_calendar()
                cal.draw()
                metadata = Metadata.get(cal.year, cal.month)
            text_area.show_text(metadata.text(cal.get_current_day()))
        elif kn in keys['down']:
            cal.move_down()
            text_area.show_text(metadata.text(cal.get_current_day()))
        elif kn in keys['up']:
            cal.move_up()
            text_area.show_text(metadata.text(cal.get_current_day()))
        elif kn in keys['edit']:
            date = cal.get_current_date()
            edit_date(date)
            metadata.load_day(date.day)
            cal.set_active(entry_exists(date))
            text_area.show_text(metadata.text(date.day))
        elif kn in keys['tags']:
            show_tags(cal.area_id, text_area)
            ScreenManager.restore_area(cal.area_id)
            cal.reinit()
            text_area.set_title()
            text_area.show_text(metadata.text(cal.get_current_day()))
        elif kn in keys['edits']:
            date = cal.get_current_date()
            edits = get_edits(date)
            if edits:
                show_edits(date, edits, text_area.area_id)
                ScreenManager.restore_area(text_area.area_id)
                text_area.show_text(metadata.text(date.day))
        elif kn in keys['prev_month']:
            cal = cal.get_previous_calendar(cal.get_current_day())
            cal.draw()
            metadata = Metadata.get(cal.year, cal.month)
            text_area.show_text(metadata.text(cal.get_current_day()))
        elif kn in keys['next_month']:
            cal = cal.get_next_calendar(cal.get_current_day())
            cal.draw()
            metadata = Metadata.get(cal.year, cal.month)
            text_area.show_text(metadata.text(cal.get_current_day()))
    Metadata.write_all()
    clean_tmp()

def edit_single_date(date):
    """Edit a single entry in external editor without initializing screen."""
    date = parse_date(date)
    if not date:
        raise WLError('Unrecognised date format\n')
    edit_date(date)
    metadata = Metadata(date.year, date.month)
    metadata.load_day(date.day)
    metadata.write()

usage = '''Usage:
%(name)s
%(name)s ( <date> | today | yesterday )
%(name)s -t [<tag>]
''' % {'name': sys.argv[0]}

def wrapper(func, with_screen=False):
    if with_screen:
        ScreenManager.init()
    error = None
    try:
        func()
    except WLQuit:
        pass
    except WLError as exc:
        error = exc
    finally:
        if with_screen:
            ScreenManager.quit()
        if error is not None:
            sys.stderr.write('%s\n' % error)

if __name__ == '__main__':
    from getopt import getopt, GetoptError
    from functools import partial

    try:
        options, args = getopt(sys.argv[1:], 'th', ['help'])
    except GetoptError as exc:
        sys.stderr.write('%s\nTry `%s -h` for help\n' % (exc, sys.argv[0]))
        sys.exit(1)
    init_screen = True
    option_names = [o[0] for o in options]
    if '-h' in option_names or '--help' in option_names:
        print usage
        sys.exit()
    if options:
        if args:
            func = partial(show_tag, args[0])
        else:
            func = show_tags
    else:
        if args:
            func = partial(edit_single_date, args[0])
            init_screen = False
        else:
            func = show_calendar
    wrapper(func, init_screen)

