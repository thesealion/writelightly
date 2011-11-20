import curses
import random
import unittest

class Screen(object):
    def __init__(self, maxy, maxx):
        self.setmaxyx(maxy, maxx)
        self.pos = (0, 0)

    def clear(self, *args):
        if not args:
            y, x = self.getmaxyx()
            self.lines = []
            for i in range(y):
                self.lines.append(list([' '] * x))
        else:
            y, x, y0, x0 = args
            for i in range(y0, y0 + y):
                try:
                    line = self.lines[i]
                except IndexError:
                    # Following lines are out of range, no need to go over them.
                    # We don't raise an exception here because it's not
                    # an error in curses.
                    break
                line[x0:x0 + x] = [' '] * x

    def keypad(self, val):
        pass

    def getmaxyx(self):
        return self.maxyx

    def addstr(self, y, x, s, a=None):
        if not s:
            return
        line = self.lines[y]
        sl = slice(x, x + len(s))
        if len(line[sl]) != len(s):
            raise CursesError('addstr got a too long string: "%s"' % s)
        if line[sl][0] != ' ' or len(set(line[sl])) != 1:
            if line[sl] != list(s):
                raise CursesError('trying to overwrite "%s" with "%s", y: %d' %
                    (''.join(line[sl]), s, y))
        line[sl] = list(s)

    def refresh(self):
        pass

    def getch(self):
        return commands.get()

    def get_line(self, ind):
        return ''.join(self.lines[ind]).strip()

    def move(self, y, x):
        self.pos = (y, x)

    def getyx(self):
        return self.pos

    def setmaxyx(self, maxy, maxx):
        self.maxyx = (maxy, maxx)
        self.clear()

class Window(Screen):
    def __init__(self, *args):
        if len(args) == 2:
            y0, x0 = args
            sy, sx = get_screen().getmaxyx()
            y, x = sy - y0, sx - x0
        elif len(args) == 4:
            y, x, y0, x0 = args
        else:
            raise CursesError('Bad arguments for newwin: %s' % args)
        self.maxyx = (y, x)
        self.begyx = (y0, x0)
        self.pos = (0, 0)

    def getbegyx(self):
        return self.begyx

    def resize(self, y, x):
        self.maxyx = (y, x)

    def addstr(self, y, x, s, a=None):
        y0, x0 = self.getbegyx()
        get_screen().addstr(y + y0, x + x0, s, a)

    def clear(self):
        y0, x0 = self.getbegyx()
        y, x = self.getmaxyx()
        get_screen().clear(y, x, y0, x0)

class CursesError(Exception):
    pass

screen = None
def get_screen():
    return screen

def initscr():
    global screen
    screen = Screen(100, 100)
    return screen

def newwin(*args):
    return Window(*args)

class CommandsManager(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.commands = []

    def add(self, command):
        if isinstance(command, list):
            self.commands += command
        else:
            self.commands.append(command)

    def get(self):
        try:
            return self.commands.pop(0)
        except IndexError:
            raise CursesError('Run out of commands')

commands = CommandsManager()

def patch_curses():
    if getattr(curses, 'patched', False):
        return
    curses.initscr = initscr
    curses.noecho = lambda: None
    curses.cbreak = lambda: None
    curses.curs_set = lambda val: None
    curses.newwin = newwin
    curses.nocbreak = lambda: None
    curses.echo = lambda: None
    curses.endwin = lambda: None
    curses.keyname = lambda c: c
    curses.patched = True


def get_random_lines(num=None, width=None):
    letters = [chr(c) for c in range(97, 123)] + [' ']
    if not num or not width:
        y, x = get_screen().getmaxyx()
        if not num:
            num = y + 50
        if not width:
            width = x - 1

    def get_line():
        line = ''.join([random.choice(letters)
            for j in range(random.randint(1, width))]).strip()
        return line or get_line()

    return [get_line() for i in range(num)]
