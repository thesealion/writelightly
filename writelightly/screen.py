import curses
from abc import ABCMeta, abstractmethod
from itertools import izip
from textwrap import wrap

from writelightly.conf import Config

class ScreenManager(object):
    """Class that manages areas on screen, their contents and sizes.

    Also it initializes and deinitializes the screen and deals with
    screen resizing.
    """

    @classmethod
    def init(cls):
        """Initialize screen."""
        screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        screen.keypad(1)
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        if Config.general['color']:
            curses.start_color()
        cls.screen = screen
        cls.areas = []
        cls.areas_stack = {}

    @classmethod
    def _calc(cls, exclude=[]):
        """
        Calculate sizes and coordinates for all existing areas.

        exclude: list of area indices to exclude from calculation.

        Right now this method just divides available screen in
        equally-sized columns.
        """
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
        """Add a new area and return its index."""
        cls.areas.append(area)
        cls._calc()
        for index, area in enumerate(cls.areas[:-1]):
            y, x, y0, x0 = cls.get_coords(index)
            area.resize(y, x)
        return len(cls.areas) - 1

    @classmethod
    def replace_area(cls, index, area):
        """Replace an area with a new one.

        And save the old area so it can be restored later.
        """
        old_area = cls.areas[index]
        try:
            cls.areas_stack[index].append(old_area)
        except KeyError:
            cls.areas_stack[index] = [old_area]
        cls.areas[index] = area

    @classmethod
    def get_last_window(cls, index):
        """Get window of the last area with the given index.

        Each area is an instance of ScreenArea and has a "window" attribute.
        When an area is replaced with another one, we use this method to get
        the window object of the previous area because it's unnecessary to 
        create a new window in this case.
        """
        try:
            return cls.areas_stack[index][-1].window
        except LookupError:
            return None

    @classmethod
    def restore_area(cls, index):
        """Restore an area with given index."""
        cls.areas[index] = cls.areas_stack[index].pop()

    @classmethod
    def get_coords(cls, index):
        """Get coordinates (y, x, y0, x0) for an area with given index."""
        return cls.coords[index]

    @classmethod
    def draw_all(cls):
        """Draw all not hidden areas."""
        for area in cls.areas:
            if not area.hidden:
                area.draw()

    @classmethod
    def resize(cls):
        """Handle screen resizing.

        Calculate size for each area, then ask each area if the new size is
        enough for it. If not, hide that area and start from the beginning.
        Finally, draw all areas.
        """
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
        """Deinitialize screen."""
        curses.nocbreak()
        cls.screen.keypad(0)
        curses.echo()
        curses.curs_set(1)
        curses.endwin()

class ScreenArea(object):
    """Abstract class representing an area on the screen. Base for all areas.
    """
    __metaclass__ = ABCMeta

    def __init__(self, area_id=None):
        """Add this area to ScreenManager or replace an existing one.

        This method should be called via super() from subclasses.
        """
        if area_id is not None:
            ScreenManager.replace_area(area_id, self)
            self.area_id = area_id
            self.window = ScreenManager.get_last_window(area_id)
        else:
            self.area_id = ScreenManager.add_area(self)
            self.window = curses.newwin(*ScreenManager.get_coords(self.area_id))

    def show(self):
        """Show this area. Used when the area was hidden earlier."""
        self.hidden = False

    def move(self, y0, x0):
        """Move to the given coordinates."""
        if self.window.getbegyx() != (y0, x0):
            self.window.mvwin(y0, x0)

    def hide(self):
        """Hide this area. Used when there isn't enough space."""
        self.hidden = True
        self.window.clear()
        self.window.refresh()

    def reinit(self):
        """Resync this area with ScreenManager.

        Used when an area was replaced and then restored.
        """
        y, x, y0, x0 = ScreenManager.get_coords(self.area_id)
        if self.enough_space(y, x):
            self.resize(y, x)
            self.move(y0, x0)
            self.draw()
        else:
            self.hide()

    @abstractmethod
    def resize(self, y, x):
        """Resize this area to fit new dimensions."""

    @abstractmethod
    def enough_space(self, y, x):
        """Check if this area can be resized to the given dimensions."""

    @abstractmethod
    def draw(self):
        """Display this area on screen."""

class TextArea(ScreenArea):
    """Simple screen area that just displays some text."""
    minx = 20
    lines = []
    es = []

    def __init__(self, *args, **kwargs):
        # title, text: raw title and text
        # lines: wrapped title and text
        super(TextArea, self).__init__(*args, **kwargs)
        self.hidden = False
        self.title = self.text = None
        self.lines = {'title': [], 'text': []}

    def _set(self, attr, text=None):
        """Set title or text, recalculate lines."""
        setattr(self, attr, text)
        y, x = self.window.getmaxyx()
        lines = self.lines.copy()
        lines[attr] = self._get_lines(text, x) if text else []
        if x >= self.minx and y >= sum(map(len, lines.values())):
            self.lines.update(lines)
            self.show()
        else:
            self.hide()

    def set_title(self, title=None):
        self._set('title', title)

    def set_text(self, text):
        self._set('text', text)

    def show_text(self, text):
        self.set_text(text)
        self.draw()

    @staticmethod
    def _get_lines(text, width):
        """Wrap text preserving existing linebreaks."""
        from operator import add
        return reduce(add, [wrap(line, width) for line in text.split('\n')])

    def enough_space(self, y, x):
        size = (len(self._get_lines(self.text, x)) +
            len(self._get_lines(self.title, x)) if self.title else 0)
        return x >= self.minx and y >= size

    def _display(self):
        """Display lines on screen."""
        self.window.clear()
        for ind, line in enumerate(self.lines['title']):
            self.window.addstr(ind, 0, line, curses.A_BOLD)
        offset = len(self.lines['title'])
        for ind, line in enumerate(self.lines['text']):
            self.window.addstr(ind + offset, 0, line)
        self.window.refresh()

    def resize(self, y, x):
        self.window.resize(y, x)
        self.set_text(self.text)
        self.set_title(self.title)

    def draw(self):
        if not self.hidden:
            self._display()

