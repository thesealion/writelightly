import datetime
import curses

def lastday(date):
    next_first = datetime.date(date.year if date.month != 12 else date.year + 1,
                               date.month + 1 if date.month != 12 else 1, 1)
    return (next_first - datetime.timedelta(days=1)).day

class Calendar(object):
    def __init__(self, year, month):
        self.year, self.month = year, month
        self.data = []
        self.selected = ()
        self.window = None

    def draw(self, window, x0, y0, entry_exists=lambda date: False):
        self.window = window
        first = datetime.date(self.year, self.month, 1)
        x, y = x0, y0 + 1
        week = [None] * first.weekday()
        x += 3 * first.weekday()
        last = lastday(first)
        day = first.day
        data = []
        while day <= last:
            date = datetime.date(self.year, self.month, day)
            week.append((x, y, entry_exists(date), day))
            if len(week) == 7:
                data.append(week)
                week = []
                y += 1
                x = x0
            else:
                x += 3
            day += 1
        if week:
            data.append(week + [None] * (7 - len(week)))
        self.data = data
        window.addstr(y0, x0, 'Mo Tu We Th Fr Sa Su')
        for w_ind, week in enumerate(data):
            for d_ind, day in enumerate(week):
                if day is None:
                    continue
                x, y, ee, d = day
                attr = curses.A_BOLD if ee else 0
                window.addstr(y, x, '%2d' % d, attr)
                if d == datetime.date.today().day:
                    self.selected = (d_ind, w_ind)
        self._change(True) #initial highlighting of today's date

    def _change(self, highlight):
        """Highlight or dehighlight the current selected date."""
        d_ind, w_ind = self.selected
        x, y, ee, d = self.data[w_ind][d_ind]
        attr = curses.A_BOLD if ee else 0
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

    def move_left(self):
        d_ind, w_ind = self.selected
        if d_ind == 0:
            if w_ind != 0 and self.data[w_ind-1][6] is not None:
                w_ind -= 1
                d_ind = 6
        else:
            if self.data[w_ind][d_ind-1] is not None:
                d_ind -= 1
        self._move(d_ind, w_ind)

    def move_right(self):
        d_ind, w_ind = self.selected
        if d_ind == 6:
            if w_ind != len(self.data) - 1 and self.data[w_ind+1][0] is not None:
                w_ind += 1
                d_ind = 0
        else:
            if self.data[w_ind][d_ind+1] is not None:
                d_ind += 1
        self._move(d_ind, w_ind)

    def move_up(self):
        d_ind, w_ind = self.selected
        if w_ind != 0 and self.data[w_ind-1][d_ind] is not None:
            w_ind -= 1
        else:
            w_ind = len(self.data) - 1
            if self.data[w_ind][d_ind] is None:
                w_ind -= 1
        self._move(d_ind, w_ind)

    def move_down(self):
        d_ind, w_ind = self.selected
        if w_ind != len(self.data) - 1 and self.data[w_ind+1][d_ind] is not None:
            w_ind += 1
        else:
            w_ind = 0 if self.data[0][d_ind] is not None else 1
        self._move(d_ind, w_ind)

    def get_current_date(self):
        d_ind, w_ind = self.selected
        x, y, ee, d = self.data[w_ind][d_ind]
        return datetime.date(self.year, self.month, d)

    def set_entry_exists_for_current_day(self, ee):
        d_ind, w_ind = self.selected
        x, y, _, d = self.data[w_ind][d_ind]
        self.data[w_ind][d_ind] = (x, y, ee, d)
        self._change(True)

