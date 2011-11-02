import curses
from metadata import Metadata
from operator import add
from textwrap import wrap

class ScreenManager(object):
    error = None

    @classmethod
    def init(cls):
        screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        screen.keypad(1)
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        cls.screen = screen
        cls._calc()

    @classmethod
    def _calc(cls):
        y, x = cls.screen.getmaxyx()
        x1 = x // 2
        x2 = x - x1
        x01, x02 = 0, x1
        y1 = y2 = y
        y01 = y02 = 0
        cls.coords = ((y1, x1, y01, x01), (y2, x2, y02, x02))

    @classmethod
    def get_left_area(cls):
        return cls.coords[0]

    @classmethod
    def get_right_area(cls):
        return cls.coords[1]

    @classmethod
    def add_left(cls, area_manager):
        cls.left = area_manager

    @classmethod
    def add_right(cls, area_manager):
        cls.right = area_manager

    @classmethod
    def resize(cls):
        cls._calc()
        for label in ('left', 'right'):
            if hasattr(cls, label):
                area = getattr(cls, label)
                getter = getattr(cls, 'get_%s_area' % label)
                y, x, y0, x0 = getter()
                area.resize(y, x)
                area.move(y0, x0)
                area.draw()

    @classmethod
    def quit(cls):
        cls.screen.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
        if cls.error:
            print 'Error: %s' % cls.error

    @classmethod
    def show_error(cls, exc):
        cls.error = exc.args[0]

class ScreenError(Exception):
    pass

class RightWindowManager(object):
    minx = 20

    def __init__(self, title=None):
        y, x, y0, x0 = ScreenManager.get_right_area()
        self.window = curses.newwin(y, x, y0, x0)
        self.content = None
        self.hidden = False
        self.set_title(title)

    def set_title(self, title=None):
        y, x = self.window.getmaxyx()
        self.title = wrap(title, x) if title else []

    def show_text(self, text):
        self.content = text
        self._count_lines()
        self.draw()

    def _count_lines(self):
        y, x = self.window.getmaxyx()
        wrapped = [wrap(line, x) for line in self.content.split('\n')]
        self.lines = reduce(add, wrapped)

    def _hide(self):
        self.hidden = True
        self.window.clear()
        self.window.refresh()
        ScreenManager.resize()

    def _enough_space(self):
        y, x = self.window.getmaxyx()
        if x < self.minx or y < len(self.lines):
            return False
        return True

    def _display(self):
        self.window.clear()
        if self.title:
            for ind, line in enumerate(self.title):
                self.window.addstr(ind, 0, line, curses.A_BOLD)
        offset = len(self.title)
        for ind, line in enumerate(self.lines):
            self.window.addstr(ind + offset, 0, line)
        self.window.refresh()

    def resize(self, y, x):
        if y < 2:
            self._hide()
            return
        self.window.resize(y, x)
        self._count_lines()
    
    def draw(self):
        if self._enough_space():
            if self.hidden:
                self.hidden = False
            self._display()
        else:
            if not self.hidden:
                self._hide()

    def move(self, y0, x0):
        self.window.mvwin(y0, x0)

