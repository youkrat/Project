from config import (
    DAY_THRESHOLD,
    NIGHT_THRESHOLD,
    TREND_EPSILON
)

_last_state = "Unknown"

def time_of_day_from_trend(lux_history):
    if len(lux_history) < 10:
        return "Unknown"

    mid = len(lux_history) // 2
    first = sum(lux_history[:mid]) / mid
    second = sum(lux_history[mid:]) / (len(lux_history) - mid)
    delta = second - first

    if second > DAY_THRESHOLD and delta > TREND_EPSILON:
        return "Day"
    if second < NIGHT_THRESHOLD and delta < -TREND_EPSILON:
        return "Night"
    if delta < -TREND_EPSILON:
        return "Approaching Night"
    if delta > TREND_EPSILON:
        return "Approaching Day"

    return "Stable"


def stable_time_state(new_state):
    global _last_state
    if new_state in ("Day", "Night"):
        _last_state = new_state
    return _last_state
