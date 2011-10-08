# -*- coding: utf-8 -*-

import curses
import locale
import datetime
locale.setlocale(locale.LC_ALL, ('en_US', 'UTF-8'))

def lastday(date):
    next_first = datetime.date(date.year if date.month != 12 else date.year + 1,
                               date.month + 1 if date.month != 12 else 1, 1)
    return (next_first - datetime.timedelta(days=1)).day

def main(stdscr):
    today = datetime.date.today()
    first = datetime.date(today.year, today.month, 1)
    month = []
    x, y = 0, 1
    week = [None] * first.weekday()
    x += 3 * first.weekday()
    last = lastday(first)
    day = first.day
    while day <= last:
        week.append((x, y, day))
        if len(week) == 7:
            month.append(week)
            week = []
            y += 1
            x = 0
        else:
            x += 3
        day += 1
    if week:
        month.append(week + [None] * (7 - len(week)))
    stdscr.addstr(0, 0, 'Mo Tu We Th Fr Sa Su')
    for w_ind, week in enumerate(month):
        for d_ind, day in enumerate(week):
            if day is None:
                continue
            x, y, d = day
            stdscr.addstr(y, x, '%2d' % d)
            if d == today.day:
                selected = (d_ind, w_ind)
    def change(selected, highlight):
        d_ind, w_ind = selected
        x, y, d = month[w_ind][d_ind]
        args = [y, x, '%2d' % d]
        if highlight:
            args.append(curses.A_REVERSE)
        stdscr.addstr(*args)
        stdscr.refresh()
    change(selected, True)
    while 1:
        c = stdscr.getch()
        d_ind, w_ind = selected
        if c == ord('q'):
            break
        if c in (ord('h'), curses.KEY_LEFT):
            if d_ind == 0:
                if w_ind != 0 and month[w_ind-1][6] is not None:
                    w_ind -= 1
                    d_ind = 6
            else:
                if month[w_ind][d_ind-1] is not None:
                    d_ind -= 1
        elif c in (ord('l'), curses.KEY_RIGHT):
            if d_ind == 6:
                if w_ind != len(month) - 1 and month[w_ind+1][0] is not None:
                    w_ind += 1
                    d_ind = 0
            else:
                if month[w_ind][d_ind+1] is not None:
                    d_ind += 1
        elif c in (ord('j'), curses.KEY_DOWN):
            if w_ind != len(month) - 1 and month[w_ind+1][d_ind] is not None:
                w_ind += 1
            else:
                w_ind = 0 if month[0][d_ind] is not None else 1
        elif c in (ord('k'), curses.KEY_UP):
            if w_ind != 0 and month[w_ind-1][d_ind] is not None:
                w_ind -= 1
            else:
                w_ind = len(month) - 1
                if month[w_ind][d_ind] is None:
                    w_ind -= 1
        if (d_ind, w_ind) != selected:
            change(selected, False)
            selected = (d_ind, w_ind)
            change(selected, True)

if __name__ == '__main__':
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(1)
    curses.curs_set(0)

    try:
        main(stdscr)
    finally:
        stdscr.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
