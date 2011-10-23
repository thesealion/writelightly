import curses
import datetime
import os
import sys
import conf
from metadata import Metadata, format_date
from scrollable_list import ScrollableList, handle_keypress
from wl import edit_date
from utils import init_screen, deinit_screen, get_all_months

data_dir = os.path.expanduser(conf.data_dir)

def main(screen):
    screen.addstr(0, 0, 'loading...')
    screen.refresh()

    tags = {}

    for year, month in get_all_months(data_dir):
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
    sw = curses.newwin(0, 30, 0, 0)
    sw.keypad(1)
    sl = ScrollableList(tl, sw)
    sl.draw()
    nw = curses.newwin(10, 50, 1, 30)
    tw = curses.newwin(1, 50, 0, 30)
    def tag_info(index):
        tag, dates = items[index]
        d = dates[-1]
        tw.addstr(0, 0, 'Last entry:', curses.A_BOLD)
        tw.refresh()
        Metadata.get(d.year, d.month).show(d.day, nw)
    tag_info(sl.get_current_index())
    while 1:
        c = sw.getch()
        if c == ord('q'):
            break
        elif c in (curses.KEY_ENTER, ord('e'), ord('\n')):
            tag, dates = items[sl.get_current_index()]
            tw.clear()
            tw.refresh()
            show_date_list(tag, dates, sw, nw)
            sl.draw()
            tag_info(sl.get_current_index())
        else:
            handle_keypress(c, sl)
            tag_info(sl.get_current_index())
    Metadata.write_all()

def show_date_list(tag, dates, window, nw):
    labels = map(format_date, dates)
    sl = ScrollableList(labels, window, tag)
    sl.draw()
    date = dates[sl.get_current_index()]
    metadata = Metadata.get(date.year, date.month)
    metadata.show(date.day, nw)
    while 1:
        c = window.getch()
        if curses.keyname(c) == '^O' or c == ord('q'):
            break
        elif c in (curses.KEY_ENTER, ord('e'), ord('\n')):
            date = dates[sl.get_current_index()]
            edit_date(date)
            sl.draw()
            metadata.load_day(date.day)
            metadata.show(date.day, nw)
        else:
            handle_keypress(c, sl)
            date = dates[sl.get_current_index()]
            metadata = Metadata.get(date.year, date.month)
            metadata.show(date.day, nw)

if __name__ == '__main__':
    args = sys.argv[1:]
    if args:
        tag = args[0]
        dates = []
        for year, month in get_all_months(data_dir):
            m = Metadata.get(year, month)
            if tag in m.tags:
                for day in m.tags[tag]:
                    dates.append(datetime.date(year, month, day))
        if not dates:
            print 'No entries for tag %s' % tag
        else:
            screen = init_screen()
            try:
                show_date_list(tag, dates, screen)
            finally:
                deinit_screen(screen)
    else:
        screen = init_screen()
        try:
            main(screen)
        finally:
            deinit_screen(screen)



