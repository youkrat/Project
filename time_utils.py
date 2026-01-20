class Time:
    def __init__(self, timestamp, timezone_offset):
        local_seconds = timestamp + timezone_offset
        seconds_in_day = local_seconds % 86400
        self.hour = seconds_in_day // 3600
        self.minute = (seconds_in_day % 3600) // 60

    def __str__(self):
        return f"{self._pad(self.hour)}:{self._pad(self.minute)}"

    @staticmethod
    def _pad(v):
        return f"0{v}" if v < 10 else str(v)
