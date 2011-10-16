import curses
import datetime
import os
import conf
from metadata import Metadata
from scrollable_list import ScrollableList


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
            try:
                tags[tag] += len(days)
            except KeyError:
                tags[tag] = len(days)

    items = sorted(sorted(tags.items(), key=lambda i: i[0]),
                   key=lambda i: i[1], reverse=True)
    tl = ['%s (%d)' % item for item in items]
    sl = ScrollableList(tl, screen)
    sl.draw()
    while 1:
        c = stdscr.getch()
        if c == ord('q'):
            break
        if c in (ord('j'), curses.KEY_DOWN):
            sl.move_down()
        elif c in (ord('k'), curses.KEY_UP):
            sl.move_up()
        elif curses.keyname(c) == '^E':
            sl.scroll_down()
        elif curses.keyname(c) == '^Y':
            sl.scroll_up()
        elif c in (ord('g'), curses.KEY_HOME):
            sl.move_to_top()
        elif c in (ord('G'), curses.KEY_END):
            sl.move_to_bottom()

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



