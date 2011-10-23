import curses
import curses.ascii
from curses.textpad import Textbox

class TextInput(Textbox, object):
    def __init__(self, window, prefix=''):
        self.prefix = prefix
        self.value = [c for c in prefix]
        self.pos = len(prefix)
        super(TextInput, self).__init__(window)
        for c in prefix:
            self._do_command(ord(c))

    def _do_command(self, ch):
        super(TextInput, self).do_command(ch)

    def do_command(self, ch):
        dc = True
        if curses.ascii.isprint(ch):
            if self.pos < self.maxx:
                self.value.append(chr(ch))
                self.pos += 1
        elif ch in (curses.ascii.SOH, curses.KEY_HOME):                           # ^a
            dc = False
            for _ in range(self.pos - len(self.prefix)):
                self._do_command(curses.KEY_LEFT)
            self.pos = len(self.prefix)
        elif ch in (curses.ascii.STX, curses.KEY_LEFT):
            if self.pos > len(self.prefix):
                self.pos -= 1
            else:
                dc = False
        elif ch in (curses.ascii.BS, curses.KEY_BACKSPACE):
            l = len(self.prefix)
            if self.pos > l:
                self.pos -= 1
                self.value.pop(self.pos)
            elif self.pos == l and len(self.value) == l:
                self.pos  = 0
                self.value = []
            else:
                dc = False
        elif ch in (curses.ascii.EOT, curses.KEY_DC):                           # ^d
            try:
                self.value.pop(self.pos)
            except IndexError:
                pass
            dc = False
            self._do_command(curses.ascii.EOT)
        elif ch in (curses.ascii.ENQ, curses.KEY_END):                           # ^e
            dc = False
            for _ in range(len(self.value) - self.pos):
                self._do_command(curses.KEY_RIGHT)
            self.pos = len(self.value)
        elif ch in (curses.ascii.ACK, curses.KEY_RIGHT):       # ^f
            if self.pos < self.maxx and self.pos < len(self.value):
                self.pos += 1
            else:
                dc = False
                pass
        else:
            dc = False
        if dc:
            self._do_command(ch)
        else:
            self.win.move(*self.win.getyx())

    def gather(self):
        return ''.join(self.value)

