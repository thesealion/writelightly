import curses
import random
import unittest

from writelightly.screen import ScreenManager
from writelightly.textinput import TextInput

from writelightly.tests.base import patch_curses, get_screen
patch_curses()

class TestTextInput(unittest.TestCase):
    def setUp(self):
        ScreenManager.init()

    def tearDown(self):
        ScreenManager.quit()

    def test_input(self):
        win = curses.newwin(0, 0)
        t = TextInput(win, '/')
        screen = get_screen()

        line = ''
        def check():
            self.assertEquals(screen.get_line(0), t.gather())
            self.assertEquals(t.gather(), '/' + line)

        check()

        letters = [chr(c) for c in range(97, 123)]
        for i in range(15):
            l = random.choice(letters)
            line += l
            t.do_command(ord(l))
            check()

        t.do_command(curses.KEY_BACKSPACE)
        line = line[:-1]
        check()

        for i in range(len(line) + 5):
            t.do_command(curses.KEY_LEFT)
            check()
        l = random.choice(letters)
        t.do_command(ord(l))
        line = l + line
        check()

        t.do_command(curses.KEY_DC)
        line = line[0] + line[2:]
        check()

        t.do_command(curses.KEY_END)
        l = random.choice(letters)
        t.do_command(ord(l))
        line += l
        check()

        t.do_command(curses.KEY_HOME)
        l = random.choice(letters)
        t.do_command(ord(l))
        line = l + line
        check()

        for i in range(len(line) + 5):
            t.do_command(curses.KEY_RIGHT)
            check()
        l = random.choice(letters)
        t.do_command(ord(l))
        line += l
        check()

        for i in range(len(line)):
            t.do_command(curses.KEY_BACKSPACE)
            line = line[:-1]
            check()
        self.assertEquals(line, '')
        t.do_command(curses.KEY_BACKSPACE)
        self.assertEquals(screen.get_line(0), t.gather())
        self.assertEquals(t.gather(), '')

    def test_moving(self):
        win = curses.newwin(0, 0)
        t = TextInput(win, '>>>')
        screen = get_screen()

        line = '1 2 3 4 5 6 7 all good children go to heaven'
        for l in line:
            t.do_command(ord(l))
        self.assertEquals(screen.get_line(0), t.gather())
        self.assertEquals(t.gather(), '>>>' + line)

        t.move_to_new_window(curses.newwin(5, 0))
        self.assertEquals(screen.get_line(5), t.gather())
        self.assertEquals(t.gather(), '>>>' + line)

        t.move_to_new_window(curses.newwin(10, 10))
        self.assertEquals(screen.get_line(10), t.gather())
        self.assertEquals(t.gather(), '>>>' + line)

if __name__ == '__main__':
    unittest.main()


