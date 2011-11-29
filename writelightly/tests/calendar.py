import unittest
import math
import datetime
from writelightly.utils import lastday
from writelightly.calendar import Calendar

from writelightly.screen import ScreenManager

from writelightly.tests.base import patch_curses, get_screen
patch_curses()

class TestCalendar(unittest.TestCase):
    def setUp(self):
        ScreenManager.init()

    def tearDown(self):
        ScreenManager.quit()

    def test_current_month_cal(self):
        today = datetime.date.today()
        cal = Calendar(today.year, today.month, today.day)
        ScreenManager.draw_all()

        # check the first line
        screen = get_screen()
        lines = screen.lines
        days = 'Mo Tu We Th Fr Sa Su'
        self.assertEquals(lines[0], list(days + ' ' *
            (screen.getmaxyx()[1] - len(days))))

        # check the location of the first day
        first = datetime.date(today.year, today.month, 1)
        x = first.weekday() * 3
        self.assertEquals(lines[1][x:x + 2], list(' 1'))

        # check the location of the last day
        last = lastday(today)
        x = datetime.date(today.year, today.month, last).weekday() * 3
        weeks = int(math.ceil((last - (7 - first.weekday())) / 7.0)) + 1
        self.assertEquals(lines[weeks][x:x + 2], list(str(last)))

    def test_moving(self):
        today = datetime.date.today()
        day = 1
        last = lastday(today)
        cal = Calendar(today.year, today.month, day)
        ScreenManager.draw_all()

        # moving from the first day to the last
        while day < last:
            cal.move_right()
            day += 1
            self.assertEquals(cal.get_current_day(), day)

        # moving from the last day to the 7th
        while day > 7:
            cal.move_left()
            day -= 1
            self.assertEquals(cal.get_current_day(), day)

        # moving up and down
        cal.move_down()
        self.assertEquals(cal.get_current_day(), 14)
        cal.move_up()
        self.assertEquals(cal.get_current_day(), 7)

if __name__ == '__main__':
    unittest.main()

