from textwrap import wrap
import unittest
from writelightly.screen import ScreenManager, TextArea

from writelightly.tests.base import patch_curses, get_screen, get_random_lines
patch_curses()

class TestTextArea(unittest.TestCase):
    def setUp(self):
        ScreenManager.init()

    def tearDown(self):
        ScreenManager.quit()

    def test_text(self):
        screen = get_screen()
        screen.setmaxyx(10, 20)
        ta = TextArea()
        ta.minx = 10

        lines = []
        # we need some lines longer than 10
        while not 0 < len([l for l in lines if len(l) > 10]) < 5:
            lines = get_random_lines(5, 15)

        def check():
            for index, line in enumerate(lines):
                self.assertEqual(screen.get_line(index), line)
        ta.show_text('\n'.join(lines))
        check()

        screen.setmaxyx(10, 10)
        ScreenManager.resize()
        nl = []
        for line in lines:
            nl += wrap(line, 10)
        lines = nl
        check()

        assert len(lines) < 10
        screen.setmaxyx(len(lines), 10)
        ScreenManager.resize()
        check()

        screen.setmaxyx(len(lines) - 1, 10)
        ScreenManager.resize()
        old, lines = lines, [''] * (len(lines) - 1)
        check()

        lines = old
        screen.setmaxyx(len(lines), 10)
        ScreenManager.resize()
        check()

        screen.setmaxyx(10, 9)
        ScreenManager.resize()
        lines = [''] * len(lines)
        check()

    def test_title(self):
        screen = get_screen()
        y = 10
        screen.setmaxyx(y, 20)
        ta = TextArea()
        ta.minx = 10

        lines = [chr(i) for i in range(97, 96 + y)]
        ta.show_text('\n'.join(lines))
        self.assertEqual(screen.get_line(0), lines[0])
        title = ''
        while len(title) < 10:
            title += get_random_lines(1, 20)[0].replace(' ', '')
        title = title[:10]
        ta.set_title(title)
        ta.draw()
        self.assertEqual(screen.get_line(0), title)

        title *= 3
        ta.set_title(title)
        ta.draw()
        self.assertEqual(screen.get_line(0), '')

        screen.setmaxyx(y, 30)
        ScreenManager.resize()
        self.assertEqual(screen.get_line(0), title)


if __name__ == '__main__':
    unittest.main()
