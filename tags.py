import curses
import datetime
import os
import sys
import conf
from metadata import Metadata, format_date
from scrollable_list import ScrollableList
from edit import edit_date
from utils import get_all_months
from screen import ScreenManager, TextArea, ScreenError

import locale
locale.setlocale(locale.LC_ALL, ('en_US', 'UTF-8'))

def main(area_id=None, text_area=None):
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
            if not sl.hidden:
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

def show_date_list(tag, dates, area_id, text_area):
    labels = map(format_date, dates)
    sl = ScrollableList(labels, tag, area_id=area_id)
    sl.draw()
    date = dates[sl.get_current_index()]
    metadata = Metadata.get(date.year, date.month)
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
        else:
            sl.handle_keypress(c)
            date = dates[sl.get_current_index()]
            text_area.show_text(Metadata.get(date.year, date.month).text(date.day))

if __name__ == '__main__':
    args = sys.argv[1:]
    if args:
        tag = args[0]
        dates = []
        for year, month in get_all_months(conf.data_dir):
            m = Metadata.get(year, month)
            if tag in m.tags:
                for day in m.tags[tag]:
                    dates.append(datetime.date(year, month, day))
        if not dates:
            print 'No entries for tag %s' % tag
        else:
            ScreenManager.init()
            try:
                show_date_list(tag, dates)
            finally:
                ScreenManager.quit()
    else:
        ScreenManager.init()
        try:
            main()
        except ScreenError, exc:
            ScreenManager.show_error(exc)
        finally:
            ScreenManager.quit()



