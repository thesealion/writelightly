import curses
import curses.ascii

class TextInput(object):
    """Replacement for curses.textpad that works much better.

    Supports the same interface (do_command and gather), but instead of
    manipulating characters on screen, it keeps them in memory as a string.
    Text input field can have a prefix which looks like a shell prompt and
    can't be modified when editing the value in the field.
    """

    def __init__(self, window, prefix=''):
        """Create a text input on the given window."""
        self.win = window
        window.keypad(1)
        self.prefix = prefix
        self.value = [c for c in prefix]
        self.pos = len(prefix)
        self.maxx = window.getmaxyx()[1]
        self.update()

    def do_command(self, ch):
        """Handle a keyboard command.

        Supports multibyte characters (but it hasn't been really tested).
        """
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
        """Synchronize the current value with the screen."""
        self.win.clear()
        self.win.addstr(0, 0, self.gather())
        self.win.refresh()
        self.win.move(self.win.getyx()[0], self.pos)

    def gather(self):
        """Get the current value."""
        return ''.join(self.value)

    def move_to_new_window(self, window):
        """Draw text input field on another window.

        Used when the old window is no longer visible after a resize.
        """
        self.win = window
        window.keypad(1)
        self.update()

