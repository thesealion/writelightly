import curses
import datetime
import os
import sys

from writelightly.conf import Config
from writelightly.edit import edit_date, get_edits, show_edits
from writelightly.metadata import Metadata, format_date
from writelightly.screen import ScreenManager, TextArea
from writelightly.scrollable_list import ScrollableList
from writelightly.utils import get_all_months, WLError

conf = Config.general

import locale
locale.setlocale(locale.LC_ALL, ('en_US', 'UTF-8'))

def show_tags(area_id=None, text_area=None):
    """Show all tags sorted by entries number as a scrollable list."""
    screen = ScreenManager.screen
    screen.addstr(0, 0, 'loading...')
    screen.refresh()

    tags = {}

    for year, month in get_all_months(conf['data_dir']):
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
        try:
            kn = curses.keyname(sl.window.getch())
        except KeyboardInterrupt:
            break
        except ValueError:
            continue
        if kn == 'q':
            break
        if kn == 'KEY_RESIZE':
            ScreenManager.resize()
        if sl.hidden:
            continue
        elif kn in Config.tags_keys['details']:
            tag, dates = items[sl.get_current_index()]
            show_date_list(tag, dates, sl.area_id, text_area)
            ScreenManager.restore_area(sl.area_id)
            sl.reinit()
            text_area.set_title('Last entry:')
            tag_info(sl.get_current_index())
        else:
            sl.handle_keypress(kn)
            tag_info(sl.get_current_index())
    Metadata.write_all()

def show_date_list(tag, dates, area_id=None, text_area=None):
    """Show the list of entries for a tag."""
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
        try:
            kn = curses.keyname(sl.window.getch())
        except KeyboardInterrupt:
            break
        if kn in ('^O', 'q'):
            break
        if kn == 'KEY_RESIZE':
            ScreenManager.resize()
        if sl.hidden:
            continue
        if kn in Config.tag_details_keys['edit']:
            date = dates[sl.get_current_index()]
            edit_date(date)
            sl.draw()
            metadata.load_day(date.day)
            text_area.show_text(metadata.text(date.day))
        elif kn in Config.tag_details_keys['edits']:
            date = dates[sl.get_current_index()]
            edits = get_edits(date)
            if edits:
                show_edits(date, edits, text_area.area_id)
                ScreenManager.restore_area(text_area.area_id)
                text_area.show_text(metadata.text(date.day))
        else:
            sl.handle_keypress(kn)
            date = dates[sl.get_current_index()]
            metadata = Metadata.get(date.year, date.month)
            text_area.show_text(metadata.text(date.day))
    Metadata.write_all()

def show_tag(tag):
    """Find all entries for a tag and call show_date_list."""
    dates = []
    for year, month in get_all_months(conf['data_dir']):
        m = Metadata.get(year, month)
        if tag in m.tags:
            for day in m.tags[tag]:
                dates.append(datetime.date(year, month, day))
    if not dates:
        raise WLError('No entries for tag %s' % tag)
    else:
        show_date_list(tag, dates)

