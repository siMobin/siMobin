import math
import random
from datetime import datetime

from cards.utils import waka_auth_header, safe_fetch_json


def get_personal_info_card(
    api_key,
    username,
    text_color='5f574f',
    bg_color='f8f6f3',
    title_color='2d2a26',
    font_family='Calibri',
    border_color=None,
    chart_color=None,
):
    text_color = text_color.replace('#', '')
    bg_color = bg_color.replace('#', '')
    title_color = title_color.replace('#', '')
    border_color = border_color.replace('#', '') if border_color else text_color
    chart_color = chart_color.replace('#', '') if chart_color else text_color
    api_key = api_key or ''
    if not api_key:
        raise ValueError('Missing WAKATIME_API_KEY')

    headers = waka_auth_header(api_key)
    url = f'https://wakatime.com/api/v1/users/{username}/stats/all_time'
    json = safe_fetch_json(url, headers=headers)
    data = json.get('data')

    return build_personal_info_svg(data=data, text_color=text_color, bg_color=bg_color, title_color=title_color, font_family=font_family, border_color=border_color, chart_color=chart_color)


def build_personal_info_svg(data, text_color='5f574f', bg_color='f8f6f3', title_color='2d2a26', font_family='Calibri', border_color=None, chart_color=None):
    text_color = text_color.replace('#', '')
    bg_color = bg_color.replace('#', '')
    title_color = title_color.replace('#', '')
    border_color = border_color.replace('#', '') if border_color else text_color
    chart_color = chart_color.replace('#', '') if chart_color else text_color

    def parse_total_time(str_val):
        if not str_val or str_val == 'N/A':
            return None
        parts = str_val.split(' ')
        hours = '0'
        mins = '0'
        for i in range(0, len(parts) - 1, 2):
            val = parts[i]
            unit = (parts[i + 1] or '').lower()
            if unit.startswith('hr'):
                hours = val
            elif unit.startswith('min'):
                mins = val
        return {'hours': hours, 'mins': mins}

    def format_duration(total_seconds):
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        if hours > 0:
            hour_label = 'hour' if hours == 1 else 'hours'
            minute_label = 'minute' if minutes == 1 else 'minutes'
            return f'{hours} {hour_label} {minutes} {minute_label}'
        minute_label = 'minute' if minutes == 1 else 'minutes'
        return f'{minutes} {minute_label}'

    total_time = data.get('human_readable_total', 'N/A')
    daily_avg = data.get('human_readable_daily_average', 'N/A')
    best_day = data.get('best_day') or None

    now = datetime.now()
    day_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    def ordinal(d):
        if 3 < d < 21:
            return 'th'
        return {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')

    def fmt_date(date_str):
        d = datetime.strptime(date_str[:10], '%Y-%m-%d')
        return f'{day_names[d.weekday()]} {month_names[d.month - 1]} {d.day}{ordinal(d.day)}, {d.year}'

    current_day_str = fmt_date(now.strftime('%Y-%m-%d'))
    most_active_str = fmt_date(best_day['date']) if best_day else 'N/A'
    most_active_time = best_day.get('text', '') if best_day else ''

    parsed = parse_total_time(total_time)
    categories = data.get('categories', [])
    has_categories = len(categories) > 0

    cx, cy, r = 135, 140, 72
    right_x = 240
    card_width = 480

    def polar_to_cartesian(cx, cy, r, angle_deg):
        rad = (angle_deg - 90) * math.pi / 180
        return {'x': cx + r * math.cos(rad), 'y': cy + r * math.sin(rad)}

    def describe_donut(cx, cy, outer_r, inner_r, start_angle, end_angle):
        outer_s = polar_to_cartesian(cx, cy, outer_r, start_angle)
        outer_e = polar_to_cartesian(cx, cy, outer_r, end_angle)
        inner_s = polar_to_cartesian(cx, cy, inner_r, start_angle)
        inner_e = polar_to_cartesian(cx, cy, inner_r, end_angle)
        large = 1 if (end_angle - start_angle) > 180 else 0
        return f'M {outer_s["x"]} {outer_s["y"]} A {outer_r} {outer_r} 0 {large} 1 {outer_e["x"]} {outer_e["y"]} L {inner_e["x"]} {inner_e["y"]} A {inner_r} {inner_r} 0 {large} 0 {inner_s["x"]} {inner_s["y"]} Z'

    hue_offset = random.random() * 360
    cat_colors = []
    for i in range(len(categories)):
        h = (i * 137.508 + hue_offset) % 360
        cat_colors.append(f'hsl({h}, 60%, 55%)')

    hole_r = 42
    donut_content = ''
    current_angle = 0
    if has_categories:
        for i, cat in enumerate(categories):
            slice_angle = (cat['percent'] / 100) * 360
            end_angle = current_angle + slice_angle
            if slice_angle > 0:
                donut_content += f'<path d="{describe_donut(cx, cy, r, hole_r, current_angle, end_angle)}" fill="{cat_colors[i]}" />\n'
            current_angle = end_angle
        remaining = 360 - current_angle
        if remaining > 0.01:
            donut_content += f'<path d="{describe_donut(cx, cy, r, hole_r, current_angle, 360)}" fill="#e0e0e0" />\n'

    right_content = ''
    y_pos = 50

    right_content += f'<text x="{right_x}" y="{y_pos}" fill="#{text_color}" font-size="12" font-family="{font_family}"><tspan font-weight="bold">Daily Avg:</tspan> {daily_avg}</text>\n'
    y_pos += 19

    right_content += f'<text x="{right_x}" y="{y_pos}" fill="#{text_color}" font-size="12" font-family="{font_family}"><tspan font-weight="bold">Peak:</tspan> {most_active_time}</text>\n'
    y_pos += 19

    if has_categories:
        y_pos += 8
        right_content += f'<text x="{right_x}" y="{y_pos}" fill="#{title_color}" font-size="12" font-weight="bold" font-family="{font_family}">Categories</text>\n'
        y_pos += 17

        for i, cat in enumerate(categories):
            dot_x = right_x
            dot_y = y_pos - 7
            right_content += f'<rect x="{dot_x}" y="{dot_y}" width="8" height="8" rx="2" fill="{cat_colors[i]}" />\n'
            right_content += f'<text x="{right_x + 13}" y="{y_pos}" fill="#{text_color}" font-size="12" font-family="{font_family}">{cat["name"]}</text>\n'
            right_content += f'<text x="{right_x + 190}" y="{y_pos}" fill="#{text_color}" font-size="10" font-family="{font_family}" text-anchor="end">{format_duration(cat["total_seconds"])}</text>\n'
            y_pos += 19

    card_height = max(y_pos + 20, cy + r + 30)

    accent = title_color or border_color

    if has_categories:
        if parsed:
            main_content = f'''{donut_content}
    <text x="{cx}" y="{cy - 2}" text-anchor="middle" fill="#{text_color}" font-size="24" font-weight="bold" font-family="{font_family}">{parsed["hours"]}<tspan font-size="14" font-weight="normal"> hr</tspan></text>
    <text x="{cx}" y="{cy + 14}" text-anchor="middle" fill="#{text_color}" font-size="14" font-weight="bold" font-family="{font_family}">{parsed["mins"]}<tspan font-size="10" font-weight="normal"> min</tspan></text>
{right_content}'''
        else:
            main_content = f'''{donut_content}
    <text x="{cx}" y="{cy + 4}" text-anchor="middle" fill="#{text_color}" font-size="13" font-family="{font_family}">N/A</text>
{right_content}'''
    elif parsed:
        main_content = f'''
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#{accent}" stroke-width="4" />
    <text x="{cx}" y="{cy - 5}" text-anchor="middle" fill="#{text_color}" font-size="28" font-weight="bold" font-family="{font_family}">{parsed["hours"]}<tspan font-size="12" font-weight="normal"> hr</tspan></text>
    <text x="{cx}" y="{cy + 24}" text-anchor="middle" fill="#{text_color}" font-size="14" font-weight="bold" font-family="{font_family}">{parsed["mins"]}<tspan font-size="8" font-weight="normal"> min</tspan></text>
    {right_content}'''
    else:
        main_content = f'''
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#{accent}" stroke-width="2" />
    <text x="{cx}" y="{cy + 6}" text-anchor="middle" fill="#{text_color}" font-size="16" font-family="{font_family}">N/A</text>
    {right_content}'''

    content = f'''<svg width="{card_width}" height="{card_height}" viewBox="0 0 {card_width} {card_height}" xmlns="http://www.w3.org/2000/svg">
  <text x="{card_width / 2}" y="30" text-anchor="middle" fill="#{title_color}" font-size="15" font-weight="bold" font-family="{font_family}">Coding History</text>
{main_content}
</svg>'''

    return {
        'content': content,
        'width': card_width,
        'height': card_height,
    }
