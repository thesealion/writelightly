import curses

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

    def draw(self):
        self.window.clear()
        if self.heading:
            for index, line in enumerate(self.heading.split('\n')):
                self.window.addstr(index, 0, line, curses.A_BOLD)
        for index, item in enumerate(self.lines[self.top:self.bottom+1]):
            self.window.addstr(index + self.offset, 0, item)
        self._change()
        self.window.refresh()

    def _change(self, highlight=True):
        attr = curses.A_REVERSE if highlight else 0
        self.window.addstr(self.current - self.top + self.offset, 0,
                           self.lines[self.current], attr)

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
            self.bottom -= abs(dif)
            if self.current > self.bottom:
                self.current = self.bottom
        else: #nothing changed
            return
        self.draw()

def handle_keypress(char, sl):
    if char in (ord('j'), curses.KEY_DOWN):
        sl.move_down()
    elif char in (ord('k'), curses.KEY_UP):
        sl.move_up()
    elif curses.keyname(char) == '^E':
        sl.scroll_down()
    elif curses.keyname(char) == '^Y':
        sl.scroll_up()
    elif char in (ord('g'), curses.KEY_HOME):
        sl.move_to_top()
    elif char in (ord('G'), curses.KEY_END):
        sl.move_to_bottom()
    elif curses.keyname(char) in ('^F', 'KEY_NPAGE'):
        sl.scroll_screen_down()
    elif curses.keyname(char) in ('^B', 'KEY_PPAGE'):
        sl.scroll_screen_up()
    elif curses.keyname(char) == '^D':
        sl.scroll_halfscreen_down()
    elif curses.keyname(char) == '^U':
        sl.scroll_halfscreen_up()
    elif char == curses.KEY_RESIZE:
        sl.resize()

