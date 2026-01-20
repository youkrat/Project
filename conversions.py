def convert_temp(kelvin: float) -> tuple:
    """
    Convert temperature from Kelvin to (Celsius, Fahrenheit).
    """
    c = kelvin - 273.15
    f = c * 9 / 5 + 32
    return round(c, 1), round(f, 1)
