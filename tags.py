import curses
import datetime
import os
import conf
from metadata import Metadata, format_date
from scrollable_list import ScrollableList, handle_keypress
from wl import edit_date


data_dir = os.path.expanduser(conf.data_dir)

def main(screen):
    entries = os.listdir(data_dir)

    screen.addstr(0, 0, 'loading...')
    screen.refresh()

    try:
        entries.remove('metadata')
    except ValueError:
        pass

    months = set()
    for entry in entries:
        months.add(tuple(map(int, entry.split('-')[:2])))

    d = sorted(sorted(list(months), key=lambda i: i[1]), key=lambda i: i[0])
    tags = {}

    for year, month in d:
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
    sl = ScrollableList(tl, screen)
    sl.draw()
    nw = curses.newwin(10, 50, 1, 30)
    def tag_info(index):
        tag, dates = items[index]
        d = dates[-1]
        screen.addstr(0, 30, 'Last entry:', curses.A_BOLD)
        screen.refresh()
        Metadata.get(d.year, d.month).show(d.day, nw)
    tag_info(sl.get_current_index())
    while 1:
        c = stdscr.getch()
        if c == ord('q'):
            break
        elif c in (curses.KEY_ENTER, ord('e'), ord('\n')):
            tag, dates = items[sl.get_current_index()]
            show_date_list(tag, dates, screen)
            sl.draw()
            tag_info(sl.get_current_index())
        else:
            handle_keypress(c, sl)
            tag_info(sl.get_current_index())
    Metadata.write_all()

def show_date_list(tag, dates, window):
    labels = map(format_date, dates)
    sl = ScrollableList(labels, window, tag)
    sl.draw()
    nw = curses.newwin(10, 50, 0, 30)
    date = dates[sl.get_current_index()]
    metadata = Metadata.get(date.year, date.month)
    metadata.show(date.day, nw)
    while 1:
        c = stdscr.getch()
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
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(1)
    try:
        curses.curs_set(0)
    except curses.error:
        pass

    try:
        main(stdscr)
    finally:
        stdscr.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()



