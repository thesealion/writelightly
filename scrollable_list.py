import curses
from textinput import TextInput
import curses.ascii

class ScrollableList(object):
    def __init__(self, lines, window, heading=None):
        self.lines = lines
        self.last = len(self.lines) - 1
        self.window = window
        self.heading = heading
        self.offset = len(heading.split('\n')) if heading else 0
        self.ysize = self.window.getmaxyx()[0] - self.offset
        self.top = 0
        self.bottom = len(self.lines[:self.ysize]) - 1
        self.current = self.top
        self.term = None

    def draw(self):
        self.window.clear()
        if self.heading:
            for index, line in enumerate(self.heading.split('\n')):
                self.window.addstr(index, 0, line, curses.A_BOLD)
        for index, item in enumerate(self.lines[self.top:self.bottom+1]):
            self.window.addstr(index + self.offset, 0, item)
        self._change()

    def _change(self, highlight=True):
        attr = curses.A_REVERSE if highlight else 0
        self.window.addstr(self.current - self.top + self.offset, 0,
                           self.lines[self.current], attr)
        self.window.refresh()

    def move_down(self):
        if self.current < self.bottom:
            self._change(False)
            self.current += 1
            self._change()
        elif self.bottom < self.last:
            self.top += 1
            self.bottom += 1
            self.current += 1
            self.draw()

    def move_up(self):
        if self.current > self.top:
            self._change(False)
            self.current -= 1
            self._change()
        elif self.top > 0:
            self.top -= 1
            self.bottom -= 1
            self.current -= 1
            self.draw()

    def scroll_down(self, lines=1):
        if self.bottom < self.last:
            dif = self.last - self.bottom
            if lines > dif:
                lines = dif
            self.top += lines
            self.bottom += lines
            if self.current < self.top:
                self.current = self.top
            self.draw()

    def scroll_up(self, lines=1):
        if self.top > 0:
            if lines > self.top:
                lines = self.top
            self.top -= lines
            self.bottom -= lines
            if self.current > self.bottom:
                self.current = self.bottom
            self.draw()

    def scroll_screen_down(self):
        self.scroll_down(self.ysize)

    def scroll_halfscreen_down(self):
        self.scroll_down(self.ysize // 2)

    def scroll_screen_up(self):
        self.scroll_up(self.ysize)

    def scroll_halfscreen_up(self):
        self.scroll_up(self.ysize // 2)

    def move_to_top(self):
        self.top = 0
        self.bottom = len(self.lines[:self.ysize]) - 1
        self.current = 0
        self.draw()

    def move_to_bottom(self):
        self.bottom = self.last
        self.top = self.bottom - self.ysize + 1
        if self.top < 0:
            self.top = 0
        self.current = self.bottom
        self.draw()

    def get_current_index(self):
        return self.current

    def resize(self):
        new_ysize = self.window.getmaxyx()[0] - self.offset
        dif = new_ysize - self.ysize
        self.ysize = new_ysize
        if dif > 0: #window increased
            bottom_lines = self.last - self.bottom
            down = dif if bottom_lines >= dif else bottom_lines
            self.bottom += down
            if down < dif:
                top_lines = self.top
                up = dif - down if top_lines >= dif - down else top_lines
                self.top -= up
        elif dif < 0: #window decreased
            if self.ysize <= len(self.lines):
                self.bottom = self.top + len(self.lines[self.top:][:self.ysize]) - 1
                if self.current > self.bottom:
                    self.current = self.bottom
        else: #nothing changed
            return
        self.draw()

    def goto(self, index):
        if self.top <= index <= self.bottom:
            self._change(False)
            self.current = index
            self._change()
        elif index < self.top:
            dif = self.top - index
            self.top -= dif
            self.current = self.top
            self.bottom -= dif
            self.draw()
        elif index > self.bottom:
            dif = index - self.bottom
            self.top += dif
            self.bottom += dif
            self.current = self.bottom
            self.draw()

    def get_lines(self, start, stop, reverse=False):
        step = 1 if not reverse else -1
        if stop < 0:
            stop = self.last
        elif stop > self.last:
            stop = 0
        while 1:
            try:
                yield start, self.lines[start]
            except IndexError:
                pass
            if start == stop:
                break
            start += step
            if not reverse and start > self.last:
                start = 0
            elif reverse and start < 0:
                start = self.last

def handle_keypress(char, sl):
    try:
        kn = curses.keyname(char)
    except ValueError:
        kn = ''
    if char in (ord('j'), curses.KEY_DOWN):
        sl.move_down()
    elif char in (ord('k'), curses.KEY_UP):
        sl.move_up()
    elif kn == '^E':
        sl.scroll_down()
    elif kn == '^Y':
        sl.scroll_up()
    elif char in (ord('g'), curses.KEY_HOME):
        sl.move_to_top()
    elif char in (ord('G'), curses.KEY_END):
        sl.move_to_bottom()
    elif kn in ('^F', 'KEY_NPAGE'):
        sl.scroll_screen_down()
    elif kn in ('^B', 'KEY_PPAGE'):
        sl.scroll_screen_up()
    elif kn == '^D':
        sl.scroll_halfscreen_down()
    elif kn == '^U':
        sl.scroll_halfscreen_up()
    elif char == curses.KEY_RESIZE:
        sl.resize()
    elif char in (ord('n'), ord('N')):
        if not sl.term:
            return
        a, b = sl.current + 1, sl.current - 1
        if char == ord('n'):
            params = (a, b)
        else:
            params = (b, a, True)
        for index, line in sl.get_lines(*params):
            if line.startswith(sl.term):
                sl.goto(index)
                break
    elif char == ord('/'):
        handle_search(sl)

def handle_search(sl):
    y, x = sl.window.getmaxyx()
    sl.window.resize(y - 1, x)
    sl.resize()

    initial = sl.current

    def quit():
        curses.curs_set(0)
        sl.window.resize(y, x)
        sl.resize()

    maxx = 50
    tw = curses.newwin(1, maxx, sl.window.getbegyx()[0] + y - 1, 0)
    t = TextInput(tw, '/')
    curses.curs_set(1)
    while 1:
        try:
            ch = tw.getch()
        except KeyboardInterrupt:
            sl.goto(initial)
            quit()
            break
        if ch in (curses.KEY_ENTER, curses.ascii.NL):
            curses.curs_set(0)
            quit()
            sl.term = t.gather()[1:]
            break
        t.do_command(ch)
        pat = t.gather()
        if not pat:
            sl.goto(initial)
            quit()
            break
        pat = pat[1:]
        if not pat:
            sl.goto(initial)
        found = False
        for index, line in sl.get_lines(initial, initial - 1):
            if line.startswith(pat):
                found = True
                sl.goto(index)
                break
        if not found:
            sl.goto(initial)


