import curses

class ScrollableList(object):
    def __init__(self, lines, window):
        self.lines = lines
        self.last = len(self.lines) - 1
        self.window = window
        self.ysize = self.window.getmaxyx()[0]
        self.top = 0
        self.bottom = len(self.lines[:self.ysize]) - 1
        self.current = self.top

    def draw(self):
        self.window.clear()
        for index, item in enumerate(self.lines[self.top:self.bottom+1]):
            self.window.addstr(index, 0, item)
        self.window.addstr(self.current-self.top, 0, self.lines[self.current],
                           curses.A_REVERSE)
        self.window.refresh()

    def _change(self, highlight=True):
        attr = curses.A_REVERSE if highlight else 0
        self.window.addstr(self.current - self.top, 0,
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



