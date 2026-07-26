import base64
import requests
from math import floor, sqrt


def parse_hours(human_time):
    parts = human_time.split('hrs')
    hours = float(parts[0].strip()) if parts[0].strip() else 0
    mins_str = parts[1].replace('mins', '').strip() if len(parts) > 1 else '0'
    minutes = float(mins_str) if mins_str else 0
    return hours + minutes / 60


def safe_fetch_json(url, headers=None, timeout=30):
    return requests.get(url, headers=headers or {}, timeout=timeout).json()


def waka_auth_header(api_key):
    encoded = base64.b64encode(api_key.encode()).decode()
    return {'Authorization': f'Basic {encoded}'}


def parse_boolean(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() == 'true'


def parse_number(value, default):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def hex_to_rgb(hex_str):
    clean = hex_str.replace('#', '').strip()[:6]
    if len(clean) < 6:
        clean = clean.ljust(6, '0')
    try:
        bigint = int(clean, 16)
        return [(bigint >> 16) & 255, (bigint >> 8) & 255, bigint & 255]
    except ValueError:
        return [0, 0, 0]


def rgb_to_hex(r, g, b):
    return ''.join(format(max(0, min(255, x)), '02x') for x in (r, g, b))


def is_dark_color(hex_str):
    r, g, b = hex_to_rgb(hex_str)
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return brightness < 128


def darken_color(hex_str, amount=120):
    r, g, b = hex_to_rgb(hex_str)
    return rgb_to_hex(max(0, r - amount), max(0, g - amount), max(0, b - amount))


def lighten_color(hex_str, amount=120):
    r, g, b = hex_to_rgb(hex_str)
    return rgb_to_hex(min(255, r + amount), min(255, g + amount), min(255, b + amount))


def invert_color(hex_str):
    r, g, b = hex_to_rgb(hex_str)
    return rgb_to_hex(255 - r, 255 - g, 255 - b)


def vary_color(base_hex, variance=30):
    import random
    r, g, b = hex_to_rgb(base_hex)
    rand = lambda: int(random.random() * variance - variance / 2)
    return rgb_to_hex(max(0, min(255, r + rand())), max(0, min(255, g + rand())), max(0, min(255, b + rand())))


def color_distance(c1, c2):
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)


def catmull_rom_to_bezier(points, min_y=0, max_y=float('inf')):
    result = []
    for i in range(len(points) - 1):
        p0 = points[i - 1] if i > 0 else points[i]
        p1 = points[i]
        p2 = points[i + 1]
        p3 = points[i + 2] if i + 2 < len(points) else p2
        cp1x = p1['x'] + (p2['x'] - p0['x']) / 6
        cp1y = p1['y'] + (p2['y'] - p0['y']) / 6
        cp2x = p2['x'] - (p3['x'] - p1['x']) / 6
        cp2y = p2['y'] - (p3['y'] - p1['y']) / 6
        cp1y = max(min_y, min(max_y, cp1y))
        cp2y = max(min_y, min(max_y, cp2y))
        result.append(f'C {cp1x},{cp1y} {cp2x},{cp2y} {p2["x"]},{p2["y"]}')
    path = f'M {points[0]["x"]},{points[0]["y"]} ' + ' '.join(result)
    return path


def format_short_time(seconds):
    if seconds == 0:
        return '00:00'
    h = floor(seconds / 3600)
    m = floor((seconds % 3600) / 60)
    if h > 0:
        return f'{str(h).zfill(2)}:{str(m).zfill(2)}'
    return f'{str(m).zfill(2)}m'


def get_safe_day_name(date_str):
    weekday_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    readable = {'su': 'Sun', 'mo': 'Mon', 'tu': 'Tue', 'we': 'Wed', 'th': 'Thu', 'fr': 'Fri', 'sa': 'Sat'}
    if date_str and date_str.lower() in readable:
        return readable[date_str.lower()]
    from datetime import datetime
    try:
        parsed = datetime.strptime(date_str[:10], '%Y-%m-%d')
        return weekday_names[parsed.weekday()]
    except (ValueError, IndexError):
        return '—'


def get_day_index(day_code):
    mapping = {'su': 0, 'mo': 1, 'tu': 2, 'we': 3, 'th': 4, 'fr': 5, 'sa': 6}
    return mapping.get(day_code.lower(), -1)


def reorder_days(days, start_day_code):
    target_index = get_day_index(start_day_code)
    if target_index < 0:
        return days

    def get_day(d):
        from datetime import datetime
        try:
            return datetime.strptime(d['range']['date'][:10], '%Y-%m-%d').weekday()
        except (ValueError, KeyError):
            return 0

    def offset(day):
        return (get_day(day) - target_index + 7) % 7

    return sorted(days, key=offset)


def generate_y_axis_elements(max_seconds, chart_top, chart_base, chart_height, text_color, chart_width, chart_type, y_axis_label, left_padding):
    ticks = 4
    lines = []
    labels = []
    x_tick_start = left_padding
    x_label = left_padding - 8
    x_axis_end = chart_width + 56
    if chart_type in ('line', 'area'):
        x_tick_start += 15
        x_axis_end -= 15
    for i in range(ticks + 1):
        val = (max_seconds / ticks) * i
        y = chart_base - (val / max_seconds) * chart_height
        label = format_short_time(val)
        lines.append(f'<line x1="{x_tick_start}" y1="{y}" x2="{x_axis_end}" y2="{y}" stroke="#{text_color}" stroke-width="0.5" stroke-dasharray="2,2"/>')
        labels.append(f'<text x="{x_label}" y="{y + 3}" font-size="9" text-anchor="end" fill="#{text_color}">{label}</text>')
    if y_axis_label and chart_type != 'radar':
        label_x = 22
        label_y = chart_top + chart_height / 2
        labels.append(f'<text x="{label_x}" y="{label_y}" font-size="9" text-anchor="middle" transform="rotate(-90, {label_x}, {label_y})" fill="#{text_color}">Time</text>')
    return lines + labels


def truncate_label(name, max_length):
    if len(name) > max_length:
        return name[:max_length - 1] + '…'
    return name


def hex_to_hsl(hex_str):
    hex_str = str(hex_str).replace('#', '')
    bigint = int(hex_str, 16)
    r = ((bigint >> 16) & 255) / 255
    g = ((bigint >> 8) & 255) / 255
    b = (bigint & 255) / 255
    mx = max(r, g, b)
    mn = min(r, g, b)
    h = s = 0
    l = (mx + mn) / 2
    if mx != mn:
        d = mx - mn
        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r:
            h = ((g - b) / d + (6 if g < b else 0))
        elif mx == g:
            h = ((b - r) / d + 2)
        else:
            h = ((r - g) / d + 4)
        h /= 6
    return {'h': h * 360, 's': s * 100, 'l': l * 100}


def hsl_to_hex(h, s, l):
    s /= 100
    l /= 100
    k = lambda n: (n + h / 30) % 12
    a = s * min(l, 1 - l)
    f = lambda n: format(round(255 * (l - a * max(-1, min(k(n) - 3, min(9 - k(n), 1))))), '02x')
    return f(0) + f(8) + f(4)


def generate_color_wheel(base_hex, count):
    base_hsl = hex_to_hsl(base_hex)
    delta = 20
    is_dark = base_hsl['l'] < 50
    start_l = max(base_hsl['l'] - delta, 0) if is_dark else base_hsl['l']
    end_l = base_hsl['l'] if is_dark else max(base_hsl['l'] - delta, 0)
    result = []
    for i in range(count):
        t = i / (count - 1) if count > 1 else 0
        l = round(start_l + (end_l - start_l) * t)
        color = hsl_to_hex(base_hsl['h'], base_hsl['s'], l)
        opacity = 0.1 + (1.0 - 0.1) * t
        result.append({'color': color, 'opacity': f'{opacity:.2f}'})
    return result
