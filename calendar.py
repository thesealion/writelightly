import datetime
import curses

def lastday(*args):
    if not args:
        raise TypeError('I need some arguments')
    if len(args) == 1 and type(args[0]) is datetime.date:
        year, month = args[0].year, args[0].month
    elif len(args) == 2 and type(args[0]) is int and type(args[1]) is int:
        year, month = args
    else:
        raise TypeError('Give me either datetime.date or year and month')
    next_first = datetime.date(year if month != 12 else year + 1,
                               month + 1 if month != 12 else 1, 1)
    return (next_first - datetime.timedelta(days=1)).day

class Calendar(object):
    def __init__(self, year, month, window, init_day=None,
                 is_bold=lambda date: False):
        self.year, self.month = year, month
        self.data = []
        self.selected = ()
        self.window = window
        if not init_day:
            init_day = datetime.date.today().day
        self.init_day = init_day
        self.is_bold = is_bold

    def draw(self):
        first = datetime.date(self.year, self.month, 1)
        x, y = 0, 1
        week = [None] * first.weekday()
        x += 3 * first.weekday()
        last = lastday(first)
        day = first.day
        data = []
        while day <= last:
            date = datetime.date(self.year, self.month, day)
            week.append((x, y, self.is_bold(date), day))
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
        self.window.clear()
        self.window.addstr(0, 0, 'Mo Tu We Th Fr Sa Su')
        init_day = self.get_current_day() or self.init_day
        for w_ind, week in enumerate(data):
            for d_ind, day in enumerate(week):
                if day is None:
                    continue
                x, y, bold, d = day
                attr = curses.A_BOLD if bold else 0
                self.window.addstr(y, x, '%2d' % d, attr)
                if d == init_day:
                    self.selected = (d_ind, w_ind)
        self._change(True)

    def _change(self, highlight):
        """Highlight or dehighlight the current selected date."""
        d_ind, w_ind = self.selected
        x, y, bold, d = self.data[w_ind][d_ind]
        attr = curses.A_BOLD if bold else 0
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
        d_ind, w_ind = self.selected
        if w_ind != 0 and self.data[w_ind-1][d_ind] is not None:
            w_ind -= 1
        else:
            w_ind = len(self.data) - 1
            if self.data[w_ind][d_ind] is None:
                w_ind -= 1
        return self._move(d_ind, w_ind)

    def move_down(self):
        d_ind, w_ind = self.selected
        if w_ind != len(self.data) - 1 and self.data[w_ind+1][d_ind] is not None:
            w_ind += 1
        else:
            w_ind = 0 if self.data[0][d_ind] is not None else 1
        return self._move(d_ind, w_ind)

    def get_current_day(self):
        if not self.selected:
            return None
        d_ind, w_ind = self.selected
        x, y, bold, d = self.data[w_ind][d_ind]
        return d

    def get_current_date(self):
        day = self.get_current_day()
        return datetime.date(self.year, self.month, day) if day else None

    def set_entry_exists_for_current_day(self, ee):
        d_ind, w_ind = self.selected
        x, y, _, d = self.data[w_ind][d_ind]
        self.data[w_ind][d_ind] = (x, y, ee, d)
        self._change(True)

