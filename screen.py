import curses
from metadata import Metadata
from operator import add
from textwrap import wrap
from itertools import izip
from abc import ABCMeta, abstractmethod

class ScreenManager(object):
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
        cls.error = None
        cls.areas = []
        cls.areas_stack = {}

    @classmethod
    def _calc(cls, exclude=[]):
        y, x = cls.screen.getmaxyx()
        areas = list(cls.areas)
        for index in exclude:
            areas[index] = None
        coords = []
        l = len([a for a in areas if a is not None])
        try:
            xs = [x // l] * l
            if sum(xs) < x:
                xs[0] += x - sum(xs)
        except ZeroDivisionError:
            xs = []
        x0s = []
        x0 = 0
        for x in xs:
            x0s.append(x0)
            x0 += x
        x_iter = izip(xs, x0s)
        for area in areas:
            if area is None:
                coords.append(None)
            else:
                x, x0 = x_iter.next()
                coords.append((y, x, 0, x0))
        cls.coords = coords

    @classmethod
    def add_area(cls, area):
        cls.areas.append(area)
        cls._calc()
        for index, area in enumerate(cls.areas[:-1]):
            y, x, y0, x0 = cls.get_coords(index)
            area.resize(y, x)
        return len(cls.areas) - 1

    @classmethod
    def replace_area(cls, index, area):
        old_area = cls.areas[index]
        try:
            cls.areas_stack[index].append(old_area)
        except KeyError:
            cls.areas_stack[index] = [old_area]
        cls.areas[index] = area

    @classmethod
    def restore_area(cls, index):
        cls.areas[index] = cls.areas_stack[index].pop()

    @classmethod
    def get_coords(cls, index):
        return cls.coords[index]

    @classmethod
    def draw_all(cls):
        for area in cls.areas:
            if not area.hidden:
                area.draw()

    @classmethod
    def resize(cls):
        exclude = []
        while 1:
            repeat = False
            cls._calc(exclude=exclude)
            for index, (area, coords) in enumerate(izip(cls.areas, cls.coords)):
                if coords is None:
                    continue
                y, x, y0, x0 = coords
                if not area.enough_space(y, x):
                    area.hide()
                    exclude.append(index)
                    repeat = True
                    break
                if area.hidden:
                    area.show()
                area.resize(y, x)
                area.move(y0, x0)
            if not repeat:
                break
        cls.draw_all()

    @classmethod
    def quit(cls):
        curses.nocbreak()
        cls.screen.keypad(0)
        curses.echo()
        curses.curs_set(1)
        curses.endwin()
        if cls.error:
            print 'Error: %s' % cls.error

    @classmethod
    def show_error(cls, exc):
        cls.error = exc.args[0]

class ScreenArea(object):
    __metaclass__ = ABCMeta

    def __init__(self, area_id=None):
        if area_id is not None:
            ScreenManager.replace_area(area_id, self)
            self.area_id = area_id
        else:
            self.area_id = ScreenManager.add_area(self)

    def show(self):
        self.hidden = False

    def move(self, y0, x0):
        if self.window.getbegyx() != (y0, x0):
            self.window.mvwin(y0, x0)

    def hide(self):
        self.hidden = True
        self.window.clear()
        self.window.refresh()

    def reinit(self):
        y, x, y0, x0 = ScreenManager.get_coords(self.area_id)
        if self.enough_space(y, x):
            self.resize(y, x)
            self.move(y0, x0)
            self.draw()
        else:
            self.hide()

    @abstractmethod
    def resize(self, y, x):
        pass

    @abstractmethod
    def enough_space(self, y, x):
        pass

    @abstractmethod
    def draw(self):
        pass

class ScreenError(Exception):
    pass

class TextArea(ScreenArea):
    minx = 20
    lines = []
    es = []

    def __init__(self, title=None, *args, **kwargs):
        super(TextArea, self).__init__(*args, **kwargs)
        y, x, y0, x0 = ScreenManager.get_coords(self.area_id)
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

    def enough_space(self, y, x):
        return x >= self.minx and y >= len(self.lines) + len(self.title)

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
        self.window.resize(y, x)
        self._count_lines()

    def draw(self):
        if not self.hidden:
            self._display()

