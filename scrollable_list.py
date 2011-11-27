import curses
import curses.ascii
from textwrap import wrap

from writelightly.conf import Config
from writelightly.screen import ScreenManager, ScreenArea
from writelightly.textinput import TextInput
from writelightly.utils import get_char, WLError

class ScrollableListError(WLError):
    pass

class ScrollableList(ScreenArea):
    """List of text items displayed on screen with ability to scroll them."""

    minx = 10
    miny = 3
    hidden = False

    def __init__(self, lines, heading=None, *args, **kwargs):
        """Initialize from a list of lines and an optional heading."""
        super(ScrollableList, self).__init__(*args, **kwargs)
        self.window.keypad(1)
        y, x = self.window.getmaxyx()
        self._calc_lines(lines)
        self.heading = heading
        self.offset = len(heading.split('\n')) if heading else 0
        self.ysize = y - self.offset
        self.top = 0                                   # index of the top
                                                       # screen line

        self.bottom = len(self.lines[:self.ysize]) - 1 # index of the bottom
                                                       # screen line

        self.itop = 0                              # index of the top item
        self.ibottom = self.lines[self.bottom][0]  # index of the bottom item
        self.current = self.itop                   # index of the current item
        self.term = None
        self.search_mode = False

    def _calc_lines(self, lines=None, width=None):
        """Wrap raw lines to fit area width.

        Sets attributes:
        - lines: screen lines. An original line can be broken into several
          screen lines.
        - items: items that correspond to original lines. Each of them is a
          list of screen line indices.
        - original: original lines for items that consist of more than one
          screen line, stored by item index.
        """
        if lines is None:
            if not self.lines:
                raise ScrollableListError('no lines to recalc')
            def get_original(index):
                item = self.items[index]
                if len(item) == 1:
                    return self.lines[item[0]][1]
                return self.original[index]
            lines = map(get_original, range(len(self.items)))
        if width is None:
            width = self.window.getmaxyx()[1] - 1
        self.lines, self.items = [], []
        self.original = {}
        i = j = 0
        for line in lines:
            if not line.strip():
                raise ScrollableListError('Empty list items are not allowed')
            cl = []
            for l in wrap(line, width):
                self.lines.append((j, l))
                cl.append(i)
                i += 1
            self.items.append(cl)
            if len(cl) > 1:
                self.original[j] = line
            j += 1
        self.last = len(self.lines) - 1

    def draw(self):
        self.window.clear()
        if self.heading:
            for index, line in enumerate(self.heading.split('\n')):
                self.window.addstr(index, 0, line, curses.A_BOLD)
        for index, (item_id, line) in enumerate(self.lines[self.top:self.bottom+1]):
            self.window.addstr(index + self.offset, 0, line)
        self._change()

    def _change(self, highlight=True):
        """Highlight or dehighlight the current selected item."""
        attr = curses.A_REVERSE if highlight else 0
        for line_id in self.items[self.current]:
            if self.top <= line_id <= self.bottom:
                self.window.addstr(line_id - self.top + self.offset, 0,
                                   self.lines[line_id][1], attr)
        self.window.refresh()

    def _scroll(self, lines):
        """Scroll the list given number of screen lines down.

        If "lines" is negative, scroll up.
        Low-level function, will break if "lines" is too big.
        """
        self.top += lines
        self.bottom += lines
        self.itop = self.lines[self.top][0]
        self.ibottom = self.lines[self.bottom][0]
        if not self.itop <= self.current <= self.ibottom:
            self.current = self.itop if lines > 0 else self.ibottom
        self.draw()

    def _goto(self, index):
        """Make the item with the given index selected, scroll if needed."""
        self._change(False)
        self.current = index
        lines = self.items[index]
        first_line_index, last_line_index = lines[0], lines[-1]
        if first_line_index < self.top:
            self._scroll(first_line_index - self.top)
        elif last_line_index > self.bottom:
            self._scroll(last_line_index - self.bottom)
        else:
            self._change()

    def move_down(self):
        """Move selection to the next item."""
        if self.current < self.ibottom:
            self._change(False)
            self.current += 1
            last_line_id = self.items[self.current][-1]
            if last_line_id > self.bottom:
                self._scroll(last_line_id - self.bottom)
            else:
                self._change()
        elif self.bottom < self.last:
            self.current += 1
            last_line_id = self.items[self.current][-1]
            self._scroll(last_line_id - self.bottom)

    def move_up(self):
        """Move selection to the previous item."""
        if self.current > self.itop:
            self._change(False)
            self.current -= 1
            first_line_id = self.items[self.current][0]
            if first_line_id < self.top:
                self._scroll(first_line_id - self.top)
            else:
                self._change()
        elif self.top > 0:
            self.current -= 1
            first_line_id = self.items[self.current][0]
            self._scroll(first_line_id - self.top)

    def scroll_down(self, lines=1):
        """Scroll one line down."""
        if self.bottom < self.last:
            dif = self.last - self.bottom
            if lines > dif:
                lines = dif
            self._scroll(lines)

    def scroll_up(self, lines=1):
        """Scroll one line up."""
        if self.top > 0:
            if lines > self.top:
                lines = self.top
            self._scroll(-lines)

    def scroll_screen_down(self):
        """Scroll one screen down."""
        self.scroll_down(self.ysize)

    def scroll_halfscreen_down(self):
        """Scroll half a screen down."""
        self.scroll_down(self.ysize // 2)

    def scroll_screen_up(self):
        """Scroll one screen up."""
        self.scroll_up(self.ysize)

    def scroll_halfscreen_up(self):
        """Scroll half a screen up."""
        self.scroll_up(self.ysize // 2)

    def move_to_top(self):
        """Scroll to top and make the first item selected."""
        self._goto(0)

    def move_to_bottom(self):
        """Scroll to bottom and make the last item selected."""
        self._goto(len(self.items) - 1)

    def get_current_index(self):
        """Return the index of the current selected item."""
        return self.current

    def enough_space(self, y, x):
        return y >= self.miny and x >= self.minx

    def resize(self, y=None, x=None):
        if not y:
            y = ScreenManager.get_coords(self.area_id)[0]
        if not x:
            x = ScreenManager.get_coords(self.area_id)[1]
        if self.search_mode:
            y -= 1
        self.window.resize(y, x)
        self._calc_lines()
        new_ysize = self.window.getmaxyx()[0] - self.offset
        dif = new_ysize - self.ysize
        self.ysize = new_ysize

        bottom_lines = self.last - self.bottom
        down = dif if bottom_lines >= dif else bottom_lines
        if down < dif:
            top_lines = self.top
            up = dif - down if top_lines >= dif - down else top_lines
            self.top -= up

        self.bottom = self.top + self.ysize - 1
        if self.bottom > self.last:
            self.bottom = self.last
        self.ibottom = self.lines[self.bottom][0]
        if self.current > self.ibottom:
            self.current = self.ibottom

    def get_items(self, start, stop, reverse=False):
        """
        Get an iterator cycling through original lines from "start" to "stop".
        """
        step = 1 if not reverse else -1
        last = len(self.items) - 1
        if stop < 0:
            stop = last
        elif stop > last:
            stop = 0
        if start < 0:
            start = last
        elif start > last:
            start = 0
        while 1:
            try:
                if start in self.original:
                    line = self.original[start]
                else:
                    line = self.lines[self.items[start][0]][1]
            except IndexError:
                pass
            else:
                yield start, line
            if start == stop:
                break
            start += step
            if not reverse and start > last:
                start = 0
            elif reverse and start < 0:
                start = last

    def handle_keypress(self, kn):
        """React to a keyboard command, if applicable.

        Given the output of curses.keyname, find it in config for list keys
        and perform the appropriate action.
        """
        keys = Config.list_keys
        if kn in keys['down']:
            self.move_down()
        elif kn in keys['up']:
            self.move_up()
        elif kn in keys['scroll_down']:
            self.scroll_down()
        elif kn in keys['scroll_up']:
            self.scroll_up()
        elif kn in keys['top']:
            self.move_to_top()
        elif kn in keys['bottom']:
            self.move_to_bottom()
        elif kn in keys['page_down']:
            self.scroll_screen_down()
        elif kn in keys['page_up']:
            self.scroll_screen_up()
        elif kn in keys['halfpage_down']:
            self.scroll_halfscreen_down()
        elif kn in keys['halfpage_up']:
            self.scroll_halfscreen_up()
        elif kn in keys['find_next'] + keys['find_prev']:
            if not self.term:
                return
            a, b = self.current + 1, self.current - 1
            if kn in keys['find_next']:
                params = (a, b)
            else:
                params = (b, a, True)
            for index, line in self.get_items(*params):
                if self.term in line.lower():
                    self._goto(index)
                    break
        elif kn in keys['search']:
            self.handle_search()

    def handle_search(self):
        """Let user search through items of the list."""
        self.search_mode = True
        self.resize()

        initial = self.current

        maxx = 50
        tw = curses.newwin(1, maxx, self.window.getbegyx()[0] +
            self.window.getmaxyx()[0], 0)
        t = TextInput(tw, '/')
        try:
            curses.curs_set(1)
        except curses.error:
            pass
        while 1:
            try:
                ch = get_char(tw)
            except KeyboardInterrupt:
                self._goto(initial)
                break
            try:
                kn = curses.keyname(ch)
            except TypeError:
                kn = ''
            if kn == '^J':
                self.term = t.gather()[1:].lower()
                break
            elif kn == 'KEY_RESIZE':
                self.resize()
                tw = curses.newwin(1, maxx, self.window.getbegyx()[0] +
                    self.window.getmaxyx()[0], 0)
                t.move_to_new_window(tw)
                continue
            t.do_command(ch)
            pat = t.gather()
            if not pat:
                self._goto(initial)
                break
            pat = pat[1:].lower()
            if not pat:
                self._goto(initial)
            found = False
            for index, line in self.get_items(initial, initial - 1):
                if pat in line.lower():
                    found = True
                    self._goto(index)
                    break
            if not found:
                self._goto(initial)
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        self.search_mode = False
        self.resize()
        self.draw()


