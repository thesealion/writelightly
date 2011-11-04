# -*- coding: utf-8 -*-

import curses
import datetime
import os
import sys
import textwrap
from calendar import Calendar, lastday
from metadata import Metadata
from utils import entry_exists, parse_date
from screen import ScreenManager, RightWindowManager
import tags
from edit import edit_date

import locale
locale.setlocale(locale.LC_ALL, ('en_US', 'UTF-8'))

def main():
    today = datetime.date.today()
    year, month = today.year, today.month
    cal = Calendar(year, month, 1, entry_exists)
    metadata = Metadata.get(year, month)
    rwm = RightWindowManager()
    ScreenManager.draw_all()
    d = cal.get_current_date()
    rwm.show_text(metadata.text(d.day))
    while 1:
        c = cal.window.getch()
        if c == ord('q'):
            break
        if c == curses.KEY_RESIZE:
            ScreenManager.resize()
        if cal.hidden:
            continue
        if c in (ord('h'), curses.KEY_LEFT):
            moved = cal.move_left()
            if not moved:
                year, month = (year if month != 1 else year - 1,
                              month - 1 if month != 1 else 12)
                cal = Calendar(year, month, lastday(year, month),
                               entry_exists, cal.area_id)
                cal.draw()
                metadata = Metadata.get(year, month)
            d = cal.get_current_date()
            rwm.show_text(metadata.text(d.day))
        elif c in (ord('l'), curses.KEY_RIGHT):
            moved = cal.move_right()
            if not moved:
                year, month = (year if month != 12 else year + 1,
                              month + 1 if month != 12 else 1)
                cal = Calendar(year, month, 1, entry_exists, cal.area_id)
                cal.draw()
                metadata = Metadata.get(year, month)
            d = cal.get_current_date()
            rwm.show_text(metadata.text(d.day))
        elif c in (ord('j'), curses.KEY_DOWN):
            cal.move_down()
            d = cal.get_current_date()
            rwm.show_text(metadata.text(d.day))
        elif c in (ord('k'), curses.KEY_UP):
            cal.move_up()
            d = cal.get_current_date()
            rwm.show_text(metadata.text(d.day))
        elif c in (curses.KEY_ENTER, ord('e'), ord('\n')):
            date = cal.get_current_date()
            edit_date(date)
            metadata.load_day(date.day)
            cal.set_entry_exists_for_current_day(entry_exists(date))
            rwm.show_text(metadata.text(date.day))
        elif c in (ord('t'),):
            tags.main(cal.area_id, rwm)
            ScreenManager.restore_area(cal.area_id)
            cal.reinit()
            rwm.set_title()
            d = cal.get_current_date()
            rwm.show_text(metadata.text(d.day))
    Metadata.write_all()

class InvalidDataDir(Exception):
    pass

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
        ScreenManager.init()
        try:
            main()
        finally:
            ScreenManager.quit()



