import curses
from textinput import TextInput
import curses.ascii
import textwrap
from utils import get_char
from screen import ScreenManager, ScreenError, ScreenArea

class ScrollableListError(Exception):
    pass

class ScrollableList(ScreenArea):
    minx = 10
    miny = 3
    hidden = False

    def __init__(self, lines, heading=None, *args, **kwargs):
        super(ScrollableList, self).__init__(*args, **kwargs)
        self.window = curses.newwin(*ScreenManager.get_coords(self.area_id))
        self.window.keypad(1)
        y, x = self.window.getmaxyx()
        self._calc_lines(lines)
        self.last = len(self.lines) - 1
        self.heading = heading
        self.offset = len(heading.split('\n')) if heading else 0
        self.ysize = y - self.offset
        self.top = 0
        self.bottom = len(self.lines[:self.ysize]) - 1
        self.itop = 0
        self.ibottom = self.lines[self.bottom][0]
        self.current = self.itop
        self.term = None
        self.search_mode = False

    def _calc_lines(self, lines=None, width=None):
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
            cl = []
            for l in textwrap.wrap(line, width):
                self.lines.append((j, l))
                cl.append(i)
                i += 1
            self.items.append(cl)
            if len(cl) > 1:
                self.original[j] = line
            j += 1

    def draw(self):
        self.window.clear()
        if self.heading:
            for index, line in enumerate(self.heading.split('\n')):
                self.window.addstr(index, 0, line, curses.A_BOLD)
        for index, (item_id, line) in enumerate(self.lines[self.top:self.bottom+1]):
            self.window.addstr(index + self.offset, 0, line)
        self._change()

    def _change(self, highlight=True):
        attr = curses.A_REVERSE if highlight else 0
        for line_id in self.items[self.current]:
            if self.top <= line_id <= self.bottom:
                self.window.addstr(line_id - self.top + self.offset, 0,
                                   self.lines[line_id][1], attr)
        self.window.refresh()

    def _scroll(self, lines):
        self.top += lines
        self.bottom += lines
        self.itop = self.lines[self.top][0]
        self.ibottom = self.lines[self.bottom][0]
        if not self.itop <= self.current <= self.ibottom:
            self.current = self.itop if lines > 0 else self.ibottom
        self.draw()

    def _goto(self, index):
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
        if self.bottom < self.last:
            dif = self.last - self.bottom
            if lines > dif:
                lines = dif
            self._scroll(lines)

    def scroll_up(self, lines=1):
        if self.top > 0:
            if lines > self.top:
                lines = self.top
            self._scroll(-lines)

    def scroll_screen_down(self):
        self.scroll_down(self.ysize)

    def scroll_halfscreen_down(self):
        self.scroll_down(self.ysize // 2)

    def scroll_screen_up(self):
        self.scroll_up(self.ysize)

    def scroll_halfscreen_up(self):
        self.scroll_up(self.ysize // 2)

    def move_to_top(self):
        self._goto(0)

    def move_to_bottom(self):
        self._goto(len(self.items) - 1)

    def get_current_index(self):
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

    def handle_keypress(self, char):
        try:
            kn = curses.keyname(char)
        except ValueError:
            kn = ''
        if char in (ord('j'), curses.KEY_DOWN):
            self.move_down()
        elif char in (ord('k'), curses.KEY_UP):
            self.move_up()
        elif kn == '^E':
            self.scroll_down()
        elif kn == '^Y':
            self.scroll_up()
        elif char in (ord('g'), curses.KEY_HOME):
            self.move_to_top()
        elif char in (ord('G'), curses.KEY_END):
            self.move_to_bottom()
        elif kn in ('^F', 'KEY_NPAGE'):
            self.scroll_screen_down()
        elif kn in ('^B', 'KEY_PPAGE'):
            self.scroll_screen_up()
        elif kn == '^D':
            self.scroll_halfscreen_down()
        elif kn == '^U':
            self.scroll_halfscreen_up()
        elif char in (ord('n'), ord('N')):
            if not self.term:
                return
            a, b = self.current + 1, self.current - 1
            if char == ord('n'):
                params = (a, b)
            else:
                params = (b, a, True)
            for index, line in self.get_items(*params):
                if line.lower().startswith(self.term):
                    self._goto(index)
                    break
        elif char == ord('/'):
            self.handle_search()

    def handle_search(self):
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
            if ch in (curses.KEY_ENTER, ord('\n')):
                try:
                    curses.curs_set(0)
                except curses.error:
                    pass
                self.term = t.gather()[1:].lower()
                break
            elif ch == curses.KEY_RESIZE:
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
                if line.lower().startswith(pat):
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


