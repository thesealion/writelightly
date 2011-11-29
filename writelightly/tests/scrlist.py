import itertools
import random
import unittest
from writelightly.scrollable_list import ScrollableList
from writelightly.screen import ScreenManager

from writelightly.tests.base import (patch_curses, get_screen, commands,
    get_random_lines)
patch_curses()

class TestScrollableList(unittest.TestCase):
    def setUp(self):
        ScreenManager.init()

    def tearDown(self):
        ScreenManager.quit()

    def _move_down_and_up(self, sl):
        sl.move_to_top()
        ind = sl.get_current_index
        self.assertEquals(ind(), 0)
        for i in range(1, len(sl.items)):
            sl.move_down()
            self.assertEquals(ind(), i)
        self.assertEquals(ind(), len(sl.items) - 1)
        while i > 0:
            i -= 1
            sl.move_up()
            self.assertEquals(ind(), i)
        self.assertEquals(ind(), 0)

    def _scroll_down_and_up(self, sl):
        sl.move_to_top()
        ind = sl.get_current_index
        screen = get_screen()
        self.assertEquals(ind(), 0)

        i = 0
        item_id = sl.lines[i][0]
        while screen.get_line(-1) != sl.lines[-1][1]:
            sl.scroll_down()
            i += 1
            item_id = sl.lines[i][0]
            self.assertEquals(ind(), item_id)
        sl.move_to_bottom()
        i = sl.last
        item_id = sl.lines[i][0]
        while screen.get_line(0) != sl.lines[0][1]:
            sl.scroll_up()
            i -= 1
            item_id = sl.lines[i][0]
            self.assertEquals(ind(), item_id)

    def test_moving(self):
        lines = get_random_lines()
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
        self._move_down_and_up(sl)

    def test_scrolling(self):
        lines = get_random_lines()
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
        lines = get_random_lines(300)
        lines1 = get_random_lines(3)
        prefix = lines[random.randint(y, 299)][:3]
        for i in range(3):
            lines.insert(random.randint(y, 299 + i), prefix + lines1[i][3:])
        indices = [ind for ind, line in enumerate(lines)
                if prefix in line]
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
            sl.handle_keypress('n')
        sl.move_to_bottom()
        if prefix not in screen.get_line(-1):
            sl.handle_keypress('N')
        previous_index = itertools.cycle(reversed(indices)).next
        for i in range(10):
            index = previous_index()
            self.assertEquals(sl.get_current_index(), index)
            self.assertTrue(lines[index] in map(screen.get_line, range(y)))
            sl.handle_keypress('N')

    def test_resize(self):
        lines = get_random_lines()
        sl = ScrollableList(lines)
        ScreenManager.draw_all()

        screen = get_screen()
        y, x = maxyx = screen.getmaxyx()
        j = 0
        def resize():
            screen.setmaxyx(y, x)
            ScreenManager.resize()
            if not sl.hidden:
                self._move_down_and_up(sl)
                self._scroll_down_and_up(sl)
                if j % 2 == 0:
                    sl.move_to_bottom()
        while y > 1:
            y -= random.randint(1, 20)
            if y < 1:
                y = 1
            j += 1
            resize()
        while y < maxyx[0]:
            y += random.randint(1, 20)
            if y > maxyx[0]:
                y = maxyx[0]
            j -= 1
            resize()
        while x > 1:
            x -= random.randint(1, 20)
            if x < 1:
                x = 1
            j += 1
            resize()
        while x > maxyx[1]:
            x += random.randint(1, 20)
            if x > maxyx[1]:
                x = maxyx[1]
            j += 1
            resize()

if __name__ == '__main__':
    unittest.main()

