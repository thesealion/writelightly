import curses
import datetime
import os
import sys
import conf

from writelightly.edit import edit_date
from writelightly.metadata import Metadata, format_date
from writelightly.screen import ScreenManager, TextArea, ScreenError
from writelightly.scrollable_list import ScrollableList
from writelightly.utils import get_all_months, WLError

import locale
locale.setlocale(locale.LC_ALL, ('en_US', 'UTF-8'))

def show_tags(area_id=None, text_area=None):
    screen = ScreenManager.screen
    screen.addstr(0, 0, 'loading...')
    screen.refresh()

    tags = {}

    for year, month in get_all_months(conf.data_dir):
        m = Metadata.get(year, month)
        for tag, days in m.tags.items():
            for day in days:
                date = datetime.date(year, month, day)
                try:
                    tags[tag].append(date)
                except KeyError:
                    tags[tag] = [date]

    items = sorted(sorted(tags.items(), key=lambda i: i[0]),
                   key=lambda i: len(i[1]), reverse=True)
    tl = ['%s (%d)' % (item[0], len(item[1])) for item in items]
    sl = ScrollableList(tl, area_id=area_id)
    if text_area:
        text_area.set_title('Last entry:')
    else:
        text_area = TextArea()
        text_area.set_title('Last entry:')
    ScreenManager.draw_all()
    def tag_info(index):
        tag, dates = items[index]
        d = dates[-1]
        text_area.show_text(Metadata.get(d.year, d.month).text(d.day))
    tag_info(sl.get_current_index())
    while 1:
        c = sl.window.getch()
        if c == ord('q'):
            break
        if c == curses.KEY_RESIZE:
            ScreenManager.resize()
        if sl.hidden:
            continue
        elif c in (curses.KEY_ENTER, ord('e'), ord('\n')):
            tag, dates = items[sl.get_current_index()]
            show_date_list(tag, dates, sl.area_id, text_area)
            ScreenManager.restore_area(sl.area_id)
            sl.reinit()
            text_area.set_title('Last entry:')
            tag_info(sl.get_current_index())
        else:
            sl.handle_keypress(c)
            tag_info(sl.get_current_index())
    Metadata.write_all()

def show_date_list(tag, dates, area_id=None, text_area=None):
    labels = map(format_date, dates)
    sl = ScrollableList(labels, tag, area_id=area_id)
    sl.draw()
    date = dates[sl.get_current_index()]
    metadata = Metadata.get(date.year, date.month)
    if not text_area:
        text_area = TextArea()
    text_area.set_title()
    text_area.show_text(metadata.text(date.day))
    while 1:
        c = sl.window.getch()
        if curses.keyname(c) == '^O' or c == ord('q'):
            break
        if c == curses.KEY_RESIZE:
            ScreenManager.resize()
        if sl.hidden:
            continue
        if c in (curses.KEY_ENTER, ord('e'), ord('\n')):
            date = dates[sl.get_current_index()]
            edit_date(date)
            sl.draw()
            metadata.load_day(date.day)
            text_area.show_text(metadata.text(date.day))
        elif c in (ord('d'),):
            date = dates[sl.get_current_index()]
            from writelightly.edit import get_edits, show_edits
            edits = get_edits(date)
            if edits:
                show_edits(date, edits, text_area.area_id)
                ScreenManager.restore_area(text_area.area_id)
                text_area.show_text(metadata.text(date.day))
        else:
            sl.handle_keypress(c)
            date = dates[sl.get_current_index()]
            metadata = Metadata.get(date.year, date.month)
            text_area.show_text(metadata.text(date.day))
    Metadata.write_all()

def show_tag(tag):
    dates = []
    for year, month in get_all_months(conf.data_dir):
        m = Metadata.get(year, month)
        if tag in m.tags:
            for day in m.tags[tag]:
                dates.append(datetime.date(year, month, day))
    if not dates:
        raise WLError('No entries for tag %s' % tag)
    else:
        show_date_list(tag, dates)

