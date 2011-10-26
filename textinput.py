import curses
import curses.ascii

class TextInput(object):
    def __init__(self, window, prefix=''):
        self.win = window
        window.keypad(1)
        self.prefix = prefix
        self.value = [c for c in prefix]
        self.pos = len(prefix)
        self.maxx = window.getmaxyx()[1]
        self.update()

    def do_command(self, ch):
        if type(ch) is str and len(ch) > 1:
            if self.pos < self.maxx:
                self.value.insert(self.pos, ch)
                self.pos += 1
        else:
            if curses.ascii.isprint(ch):
                if self.pos < self.maxx:
                    self.value.insert(self.pos, chr(ch))
                    self.pos += 1
            elif ch in (curses.ascii.SOH, curses.KEY_HOME):
                self.pos = len(self.prefix)
            elif ch in (curses.ascii.STX, curses.KEY_LEFT):
                if self.pos > len(self.prefix):
                    self.pos -= 1
            elif ch in (curses.ascii.BS, curses.KEY_BACKSPACE):
                l = len(self.prefix)
                if self.pos > l:
                    self.pos -= 1
                    self.value.pop(self.pos)
                elif self.pos == l and len(self.value) == l:
                    self.pos  = 0
                    self.value = []
            elif ch in (curses.ascii.EOT, curses.KEY_DC):
                try:
                    self.value.pop(self.pos)
                except IndexError:
                    pass
            elif ch in (curses.ascii.ENQ, curses.KEY_END):
                self.pos = len(self.value)
            elif ch in (curses.ascii.ACK, curses.KEY_RIGHT):
                if self.pos < self.maxx and self.pos < len(self.value):
                    self.pos += 1
        self.update()

    def update(self):
        self.win.clear()
        self.win.addstr(0, 0, self.gather())
        self.win.refresh()
        self.win.move(self.win.getyx()[0], self.pos)

    def gather(self):
        return ''.join(self.value)

    def move_to_new_window(self, window):
        self.win = window
        window.keypad(1)
        self.update()

