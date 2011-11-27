import curses
import datetime

from writelightly.screen import ScreenManager, ScreenArea
from writelightly.utils import lastday

class Calendar(ScreenArea):
    """Class representing a calendar for one month.

    It displays it on screen in a format similar to the Unix "cal" command
    but with the ability to interactively select a date.
    Some dates can be "active" (displayed empasized).
    """
    minx = 20
    miny = 10
    hidden = False

    def __init__(self, year, month, init_day=None,
                 is_active=lambda date: False, *args, **kwargs):
        """Initialize calendar by year and month.

        init_day: day of the month that is initially selected
        is_active: function that takes a datetime.date instance and
                   returns True if that date is "active"
        """
        super(Calendar, self).__init__(*args, **kwargs)
        self.window = curses.newwin(*ScreenManager.get_coords(self.area_id))
        self.window.keypad(1)
        self.year, self.month = year, month
        self.selected = ()
        last = lastday(year, month)
        if not init_day:
            init_day = datetime.date.today().day
        if init_day > last:
            init_day = last
        self.init_day = init_day
        self.is_active = is_active

        first = datetime.date(self.year, self.month, 1)
        x, y = 0, 1
        week = [None] * first.weekday()
        x += 3 * first.weekday()
        last = lastday(first)
        day = first.day
        data = []
        while day <= last:
            date = datetime.date(self.year, self.month, day)
            week.append((x, y, is_active(date), day))
            if len(week) == 7:
                data.append(week)
                week = []
                y += 1
                x = 0
            else:
                x += 3
            day += 1
        if week:
            data.append(week + [None] * (7 - len(week)))
        self.data = data
        self.miny = len(self.data) + 1

    def draw(self):
        """Display calendar on screen."""
        self.window.clear()
        self.window.addstr(0, 0, 'Mo Tu We Th Fr Sa Su')
        init_day = self.get_current_day() or self.init_day
        for w_ind, week in enumerate(self.data):
            for d_ind, day in enumerate(week):
                if day is None:
                    continue
                x, y, active, d = day
                attr = curses.A_BOLD if active else 0
                self.window.addstr(y, x, '%2d' % d, attr)
                if d == init_day:
                    self.selected = (d_ind, w_ind)
        self._change(True)

    def _change(self, highlight):
        """Highlight or dehighlight the current selected date."""
        d_ind, w_ind = self.selected
        x, y, active, d = self.data[w_ind][d_ind]
        attr = curses.A_BOLD if active else 0
        if highlight:
            attr += curses.A_REVERSE
        self.window.addstr(y, x, '%2d' % d, attr)
        self.window.refresh()

    def _move(self, d_ind, w_ind):
        """Move selection to the given coordinates."""
        if (d_ind, w_ind) != self.selected:
            self._change(False)
            self.selected = (d_ind, w_ind)
            self._change(True)
            return True
        return False

    def move_left(self):
        """Move selection one step to the left.

        Do nothing and return False if the move is impossible
        (the current day is the first day of the month).
        """
        d_ind, w_ind = self.selected
        if d_ind == 0:
            if w_ind != 0 and self.data[w_ind-1][6] is not None:
                w_ind -= 1
                d_ind = 6
        else:
            if self.data[w_ind][d_ind-1] is not None:
                d_ind -= 1
        return self._move(d_ind, w_ind)

    def move_right(self):
        """Move selection one step to the right.

        Do nothing and return False if the move is impossible
        (the current day is the last day of the month).
        """
        d_ind, w_ind = self.selected
        if d_ind == 6:
            if w_ind != len(self.data) - 1 and self.data[w_ind+1][0] is not None:
                w_ind += 1
                d_ind = 0
        else:
            if self.data[w_ind][d_ind+1] is not None:
                d_ind += 1
        return self._move(d_ind, w_ind)

    def move_up(self):
        """Move selection one step up.

        Go to the bottom row if we're on the top one.
        """
        d_ind, w_ind = self.selected
        if w_ind != 0 and self.data[w_ind-1][d_ind] is not None:
            w_ind -= 1
        else:
            w_ind = len(self.data) - 1
            if self.data[w_ind][d_ind] is None:
                w_ind -= 1
        return self._move(d_ind, w_ind)

    def move_down(self):
        """Move selection one step down.

        Go to the top row if we're on the bottom one.
        """
        d_ind, w_ind = self.selected
        if w_ind != len(self.data) - 1 and self.data[w_ind+1][d_ind] is not None:
            w_ind += 1
        else:
            w_ind = 0 if self.data[0][d_ind] is not None else 1
        return self._move(d_ind, w_ind)

    def get_current_day(self):
        """Return the current selected day of month as an integer."""
        if not self.selected:
            return None
        d_ind, w_ind = self.selected
        x, y, active, d = self.data[w_ind][d_ind]
        return d

    def get_current_date(self):
        """Return the current selected date as a datetime.date instance."""
        day = self.get_current_day()
        return datetime.date(self.year, self.month, day) if day else None

    def set_active(self, is_active):
        """Change "active" attribute of the current date."""
        d_ind, w_ind = self.selected
        x, y, _, d = self.data[w_ind][d_ind]
        self.data[w_ind][d_ind] = (x, y, is_active, d)
        self._change(True)

    def enough_space(self, y, x):
        return y >= self.miny and x >= self.minx

    def resize(self, y, x):
        self.window.resize(y, x)

    def move(self, y0, x0):
        if self.window.getbegyx() != (y0, x0):
            self.window.mvwin(y0, x0)

    def get_next_calendar(self, day=None):
        """Return a Calendar instance representing the next month."""
        year, month = (self.year if self.month != 12 else self.year + 1,
                       self.month + 1 if self.month != 12 else 1)
        return Calendar(year, month, day or 1, self.is_active, self.area_id)

    def get_previous_calendar(self, day=None):
        """Return a Calendar instance representing the previous month."""
        year, month = (self.year if self.month != 1 else self.year - 1,
                       self.month - 1 if self.month != 1 else 12)
        return Calendar(year, month, day or lastday(year, month),
                        self.is_active, self.area_id)

