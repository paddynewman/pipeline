import datetime


def _parse_cron_field(value, lo, hi):
    result = set()
    for part in value.split(","):
        part = part.strip()
        if "/" in part:
            range_part, step_str = part.rsplit("/", 1)
            try:
                step = int(step_str)
                if step < 1:
                    raise ValueError("step must be >= 1")
            except ValueError as exc:
                raise ValueError(f'Invalid step in "{part}": {exc}')
            if range_part == "*":
                start, end = lo, hi
            elif "-" in range_part:
                a, b = range_part.split("-", 1)
                start, end = int(a), int(b)
            else:
                start = end = int(range_part)
            result.update(range(start, end + 1, step))
        elif part == "*":
            result.update(range(lo, hi + 1))
        elif "-" in part:
            a, b = part.split("-", 1)
            result.update(range(int(a), int(b) + 1))
        else:
            result.add(int(part))
    for v in result:
        if v < lo or v > hi:
            raise ValueError(f"Value {v} out of range [{lo}, {hi}]")
    return result


def validate_cron(schedule):
    fields = schedule.strip().split()
    if len(fields) != 5:
        return "Schedule must have exactly 5 fields: minute hour day month weekday"
    ranges = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 6)]
    names = ["minute", "hour", "day", "month", "weekday"]
    for field, (lo, hi), name in zip(fields, ranges, names):
        try:
            _parse_cron_field(field, lo, hi)
        except ValueError as exc:
            return f'Invalid {name} field "{field}": {exc}'
    return None


def next_cron_run(schedule, now=None):
    if validate_cron(schedule):
        return None
    current = now or datetime.datetime.now()
    candidate = current.replace(second=0, microsecond=0) + datetime.timedelta(minutes=1)
    limit = candidate + datetime.timedelta(days=366)
    while candidate <= limit:
        if cron_matches(schedule, candidate):
            return candidate
        candidate += datetime.timedelta(minutes=1)
    return None


def cron_matches(schedule, dt):
    fields = schedule.strip().split()
    if len(fields) != 5:
        return False
    ranges = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 6)]
    # cron weekday: 0=Sunday … 6=Saturday; Python weekday(): 0=Monday … 6=Sunday
    weekday = (dt.weekday() + 1) % 7
    values = [dt.minute, dt.hour, dt.day, dt.month, weekday]
    for field, (lo, hi), value in zip(fields, ranges, values):
        try:
            if value not in _parse_cron_field(field, lo, hi):
                return False
        except ValueError:
            return False
    return True
