import random
import unittest
from writelightly.scrollable_list import ScrollableList
from writelightly.screen import ScreenManager

from writelightly.tests.base import patch_curses, get_screen
patch_curses()

class TestScrollableList(unittest.TestCase):
    def setUp(self):
        ScreenManager.init()

    def tearDown(self):
        ScreenManager.quit()

    def _get_lines(self):
        letters = [chr(c) for c in range(97, 123)]
        y, x = get_screen().getmaxyx()
        lines = []
        for i in range(y + 50):
            line = ''
            length = random.randint(1, x - 1)
            for j in range(length):
                line += random.choice(letters)
            lines.append(line)
        return lines

    def test_moving(self):
        lines = self._get_lines()
        sl = ScrollableList(lines)
        ScreenManager.draw_all()

        screen = get_screen()
        y, x = screen.getmaxyx()
        ind = sl.get_current_index
        screen_line = lambda ind: ''.join(screen.lines[ind]).strip()

        self.assertEquals(ind(), 0)
        for i in range(y):
            self.assertEquals(screen_line(i), lines[i])
        sl.move_up()
        self.assertEquals(ind(), 0)

        sl.move_to_bottom()
        self.assertEquals(ind(), len(lines) - 1)
        sl.move_down()
        self.assertEquals(ind(), len(lines) - 1)
        self.assertEquals(screen_line(0), lines[-y])
        sl.move_to_top()
        self.assertEquals(ind(), 0)
        self.assertEquals(screen_line(-1), lines[y - 1])

        for i in range(len(lines)):
            sl.move_down()
        self.assertEquals(ind(), len(lines) - 1)
        self.assertEquals(screen_line(0), lines[-y])
        self.assertEquals(screen_line(-1), lines[-1])

    def test_scrolling(self):
        lines = self._get_lines()
        sl = ScrollableList(lines)
        ScreenManager.draw_all()
        screen = get_screen()
        y, x = screen.getmaxyx()

        ind = sl.get_current_index
        screen_line = lambda ind: ''.join(screen.lines[ind]).strip()

        for i in range(len(lines) - y):
            sl.scroll_down()
            self.assertEquals(ind(), i + 1)
            self.assertEquals(screen_line(0), lines[i + 1])
        self.assertEquals(screen_line(-1), lines[-1])

if __name__ == '__main__':
    unittest.main()

