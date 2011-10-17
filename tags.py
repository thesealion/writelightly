import curses
import datetime
import os
import conf
from metadata import Metadata
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
        m = Metadata(year, month)
        m.write()
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
    while 1:
        c = stdscr.getch()
        if c == ord('q'):
            break
        elif c in (curses.KEY_ENTER, ord('e'), ord('\n')):
            tag, dates = items[sl.get_current_index()]
            show_date_list(tag, dates, screen)
            sl.draw()
        else:
            handle_keypress(c, sl)

def show_date_list(tag, dates, window):
    labels = ['%s %d, %d' % (date.strftime('%B'),
                             date.day, date.year) for date in dates]
    sl = ScrollableList(labels, window, tag)
    sl.draw()
    while 1:
        c = stdscr.getch()
        if curses.keyname(c) == '^O' or c == ord('q'):
            break
        elif c in (curses.KEY_ENTER, ord('e'), ord('\n')):
            edit_date(dates[sl.get_current_index()])
            sl.draw()
        else:
            handle_keypress(c, sl)

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



