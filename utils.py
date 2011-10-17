import curses

def init_screen():
    screen = curses.initscr()
    curses.noecho()
    curses.cbreak()
    screen.keypad(1)
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    return screen

def deinit_screen(screen):
    screen.keypad(0)
    curses.nocbreak()
    curses.echo()
    curses.endwin()
