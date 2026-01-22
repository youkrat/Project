"""
statistics.py
Basic statistical functions
"""

'''
Mean

Represents the average environmental condition over time.

Moving Average

Smooths high-frequency sensor noise while preserving trend.

Median

Reduces the influence of extreme sensor spikes.

Min / Max / Range

Captures environmental bounds and variability.

Variance

Quantifies dispersion of sensor readings around the mean.

Standard Deviation

Measures stability and reliability of the sensor.
'''
# -----------------------------
# 1. Mean
# -----------------------------
def mean(values):
    """
    Compute arithmetic mean.
    """
    if not values:
        return None
    total = 0
    count = 0
    for v in values:
        total += v
        count += 1
    return total / count


# -----------------------------
# 2. Moving Average
# -----------------------------
def moving_average(values, window):
    """
    Compute simple moving average over last `window` values.
    """
    if not values or window <= 0:
        return None

    if len(values) < window:
        window = len(values)

    total = 0
    for v in values[-window:]:
        total += v

    return total / window


# -----------------------------
# 3. Median
# -----------------------------
def median(values):
    """
    Compute median (robust to outliers).
    """
    if not values:
        return None

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2

    if n % 2 == 1:
        return sorted_vals[mid]
    else:
        return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2


# -----------------------------
# 4. Min / Max / Range
# -----------------------------
def min_max_range(values):
    """
    Return (min, max, range).
    """
    if not values:
        return None, None, None

    min_val = values[0]
    max_val = values[0]

    for v in values[1:]:
        if v < min_val:
            min_val = v
        if v > max_val:
            max_val = v

    return min_val, max_val, max_val - min_val


# -----------------------------
# 5. Variance
# -----------------------------
def variance(values):
    """
    Population variance.
    """
    if not values:
        return None

    mu = mean(values)
    total = 0

    for v in values:
        diff = v - mu
        total += diff * diff

    return total / len(values)


# -----------------------------
# 6. Standard Deviation
# -----------------------------
def std_dev(values):
    """
    Population standard deviation.
    """
    var = variance(values)
    if var is None:
        return None
    return var ** 0.5

# -----------------------------
# 7. Pearson Correlation
# -----------------------------
def correlation(xs, ys):
    """
    Compute Pearson correlation coefficient between two datasets.
    Returns value in [-1, 1].
    """
    if not xs or not ys:
        return None

    n = min(len(xs), len(ys))
    if n < 2:
        return None

    xs = xs[-n:]
    ys = ys[-n:]

    mx = mean(xs)
    my = mean(ys)

    num = 0
    dx = 0
    dy = 0

    for x, y in zip(xs, ys):
        a = x - mx
        b = y - my
        num += a * b
        dx += a * a
        dy += b * b

    if dx == 0 or dy == 0:
        return None

    return num / (dx * dy) ** 0.5

