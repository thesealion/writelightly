import itertools
import random
import unittest
from writelightly.scrollable_list import ScrollableList
from writelightly.screen import ScreenManager

from writelightly.tests.base import patch_curses, get_screen, commands
patch_curses()

class TestScrollableList(unittest.TestCase):
    def setUp(self):
        ScreenManager.init()

    def tearDown(self):
        ScreenManager.quit()

    def _get_lines(self, num=None, width=None):
        def get_line():
            line = ''
            length = random.randint(1, width)
            for j in range(length):
                line += random.choice(letters)
            return line

        letters = [chr(c) for c in range(97, 123)] + [' ']
        y, x = get_screen().getmaxyx()
        if not num:
            num = y + 50
        if not width:
            width = x - 1
        lines = []
        for i in range(num):
            line = get_line()
            while not line.strip():
                line = get_line()
            lines.append(line.strip())
        return lines

    def test_moving(self):
        lines = self._get_lines()
        sl = ScrollableList(lines)
        ScreenManager.draw_all()

        screen = get_screen()
        y, x = screen.getmaxyx()
        ind = sl.get_current_index

        self.assertEquals(ind(), 0)
        for i in range(y):
            self.assertEquals(screen.get_line(i), lines[i])
        sl.move_up()
        self.assertEquals(ind(), 0)

        sl.move_to_bottom()
        self.assertEquals(ind(), len(lines) - 1)
        sl.move_down()
        self.assertEquals(ind(), len(lines) - 1)
        self.assertEquals(screen.get_line(0), lines[-y])
        sl.move_to_top()
        self.assertEquals(ind(), 0)
        self.assertEquals(screen.get_line(-1), lines[y - 1])

        for i in range(len(lines)):
            sl.move_down()
        self.assertEquals(ind(), len(lines) - 1)
        self.assertEquals(screen.get_line(0), lines[-y])
        self.assertEquals(screen.get_line(-1), lines[-1])

    def test_scrolling(self):
        lines = self._get_lines()
        sl = ScrollableList(lines)
        ScreenManager.draw_all()
        screen = get_screen()
        y, x = screen.getmaxyx()

        ind = sl.get_current_index

        for i in range(len(lines) - y):
            sl.scroll_down()
            self.assertEquals(ind(), i + 1)
            self.assertEquals(screen.get_line(0), lines[i + 1])
        self.assertEquals(screen.get_line(-1), lines[-1])
        up = min(len(lines) - y, y)
        sl.scroll_screen_up()
        self.assertEquals(screen.get_line(-1), lines[-up-1])

    def test_search(self):
        screen = get_screen()
        y, x = screen.getmaxyx()
        lines = self._get_lines(300)
        lines1 = self._get_lines(3)
        prefix = lines[random.randint(y, 299)][:3]
        for i in range(3):
            lines.insert(random.randint(y, 299 + i), prefix + lines1[i][3:])
        indices = [ind for ind, line in enumerate(lines)
                if line.startswith(prefix)]
        sl = ScrollableList(lines)
        ScreenManager.draw_all()
        commands.add([ord(c) for c in prefix])
        commands.add(ord('\n'))
        sl.handle_search()
        next_index = itertools.cycle(indices).next
        for i in range(10):
            index = next_index()
            self.assertEquals(sl.get_current_index(), index)
            self.assertTrue(lines[index] in map(screen.get_line, range(y)))
            sl.handle_keypress(ord('n'))
        sl.move_to_bottom()
        if not screen.get_line(-1).startswith(prefix):
            sl.handle_keypress(ord('N'))
        previous_index = itertools.cycle(reversed(indices)).next
        for i in range(10):
            index = previous_index()
            self.assertEquals(sl.get_current_index(), index)
            self.assertTrue(lines[index] in map(screen.get_line, range(y)))
            sl.handle_keypress(ord('N'))

if __name__ == '__main__':
    unittest.main()

