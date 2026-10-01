#!/usr/bin/env python3
"""SwiftBar plugin: shows current solar altitude (degrees) in the menu bar."""
import datetime
import math
import sys

sys.stdout.reconfigure(encoding="utf-8")

# MacOS is really bad with location access requests, sometimes it works and
# others not. This degrades script updates and reliability. Although we can
#  request coordinates by city name from online APIs, that also has its own
# complications while we want to keep things simple so we're just hard-coding
# country for reference, city for display, and coordinates for calculation.
COUNTRY_NAME = "Germany"
LOCATION_NAME = "Berlin"
LATITUDE = 52.5200
LONGITUDE = 13.4050


def solar_altitude_deg(lat, lon, when_utc):
    day_of_year = when_utc.timetuple().tm_yday
    hour = when_utc.hour + when_utc.minute / 60 + when_utc.second / 3600

    gamma = 2 * math.pi / 365 * (day_of_year - 1 + (hour - 12) / 24)

    eqtime = 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2 * gamma)
        - 0.040849 * math.sin(2 * gamma)
    )
    decl = (
        0.006918
        - 0.399912 * math.cos(gamma)
        + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2 * gamma)
        + 0.000907 * math.sin(2 * gamma)
        - 0.002697 * math.cos(3 * gamma)
        + 0.00148 * math.sin(3 * gamma)
    )

    time_offset = eqtime + 4 * lon
    true_solar_time = hour * 60 + time_offset
    hour_angle = math.radians(true_solar_time / 4 - 180)

    lat_rad = math.radians(lat)
    cos_zenith = (
        math.sin(lat_rad) * math.sin(decl)
        + math.cos(lat_rad) * math.cos(decl) * math.cos(hour_angle)
    )
    cos_zenith = max(-1.0, min(1.0, cos_zenith))
    zenith = math.degrees(math.acos(cos_zenith))
    return 90 - zenith


def find_falling_crossing_local(lat, lon, target_deg=6.0):
    """Local time today when the sun's altitude falls through target_deg."""
    now_local = datetime.datetime.now().astimezone()
    midnight_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)

    prev_diff = None
    prev_t = None
    for minute in range(0, 24 * 60 + 1):
        t_local = midnight_local + datetime.timedelta(minutes=minute)
        t_utc = t_local.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        diff = solar_altitude_deg(lat, lon, t_utc) - target_deg

        if prev_diff is not None and prev_diff >= 0 > diff:
            frac = prev_diff / (prev_diff - diff)
            return prev_t + (t_local - prev_t) * frac

        prev_diff = diff
        prev_t = t_local

    return None


def main():
    now_local = datetime.datetime.now().astimezone()
    altitude = solar_altitude_deg(LATITUDE, LONGITUDE, datetime.datetime.utcnow())
    crossing = find_falling_crossing_local(LATITUDE, LONGITUDE)
    if crossing is None:
        crossing_str = "n/a today"
    else:
        verb = "already reached" if crossing <= now_local else "reaches"
        crossing_str = f"{verb} 6° at {crossing.strftime('%H:%M')}"

    print(f"☀ {altitude:.0f}°")
    print("---")
    print(f"Sun at {altitude:.0f}° at {now_local.strftime('%H:%M')} in {LOCATION_NAME}")
    print(f"{crossing_str} | color=gray")
    print("Refresh | refresh=true")


if __name__ == "__main__":
    main()
