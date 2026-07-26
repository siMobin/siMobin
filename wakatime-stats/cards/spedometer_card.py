import math
import re
import requests
from cards.utils import waka_auth_header, hex_to_hsl, hsl_to_hex, generate_color_wheel


def hex_to_rgba(hex_str, opacity):
    hex_str = hex_str.replace('#', '')
    if len(hex_str) == 3:
        hex_str = ''.join(c + c for c in hex_str)
    bigint = int(hex_str, 16)
    r = (bigint >> 16) & 255
    g = (bigint >> 8) & 255
    b = bigint & 255
    return f'rgba({r},{g},{b},{opacity})'


def darken_hex_color(hex_str, factor=0.95):
    hsl = hex_to_hsl(hex_str)
    darkened_l = hsl['l'] * factor
    return hsl_to_hex(hsl['h'], hsl['s'], darkened_l)


def seconds_to_hms(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    return {'h': h, 'm': m}


def format_hm(hm):
    return f"{hm['h']} hrs {hm['m']} mins"


def polar_to_cartesian(cx, cy, r, angle_deg):
    rad = math.radians(angle_deg - 90)
    return {
        'x': cx + r * math.cos(rad),
        'y': cy + r * math.sin(rad),
    }


def describe_arc(cx, cy, r, start_angle, end_angle):
    start = polar_to_cartesian(cx, cy, r, start_angle)
    end = polar_to_cartesian(cx, cy, r, end_angle)
    large_arc_flag = 1 if abs(end_angle - start_angle) > 180 else 0
    return f'M {start["x"]} {start["y"]} A {r} {r} 0 {large_arc_flag} 1 {end["x"]} {end["y"]}'


def get_arrow_svg(diff, color='#000', size=14):
    up = (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" '
        f'stroke-width="3" stroke-linecap="round" stroke-linejoin="round">'
        f'<line x1="12" y1="19" x2="12" y2="5"></line>'
        f'<polyline points="5 12 12 5 19 12"></polyline>'
        f'</svg>'
    )
    down = (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" '
        f'stroke-width="3" stroke-linecap="round" stroke-linejoin="round">'
        f'<line x1="12" y1="5" x2="12" y2="19"></line>'
        f'<polyline points="19 12 12 19 5 12"></polyline>'
        f'</svg>'
    )
    return up if diff >= 0 else down


def _parse_custom_emojis(input_str):
    if not input_str:
        return [''] * 5
    emojis = []
    for char in input_str:
        cp = ord(char)
        if (
            cp > 0xFFFF
            or 0x2600 <= cp <= 0x27BF
            or 0x2B50 <= cp <= 0x2B55
        ):
            emojis.append(char)
    return [emojis[i] if i < len(emojis) else '' for i in range(5)]


def get_spedometer_card(
    api_key=None,
    username=None,
    text_color='ccc',
    font_family='Arial',
    difficulty='easy',
    label_type='standard',
    chart_color='4ade80',
    custom_emojis=None,
    show_high_score=None,
):
    chart_color = chart_color.replace('#', '')
    text_color = text_color.replace('#', '')
    if not api_key:
        raise Exception('Missing WAKATIME_API_KEY')

    headers = waka_auth_header(api_key)

    today_res = requests.get(
        f'https://wakatime.com/api/v1/users/{username}/durations?date=today',
        headers=headers,
    )
    yearly_res = requests.get(
        f'https://wakatime.com/api/v1/users/{username}/stats/last_year',
        headers=headers,
    )

    today_data = today_res.json()
    yearly_stats = yearly_res.json()

    today_seconds = sum(
        s.get('duration', 0) for s in (today_data.get('data') or [])
    ) or 0
    avg_seconds = (yearly_stats.get('data') or {}).get('daily_average', 1) or 1
    most_active_day = (yearly_stats.get('data') or {}).get('best_day', {}) or {}
    most_active_day_text = most_active_day.get('text', 'N/A')

    reference_seconds = avg_seconds
    best_day = (yearly_stats.get('data') or {}).get('best_day', {}) or {}
    best_day_seconds = best_day.get('total_seconds', 0) or 0

    try:
        if difficulty == 'self':
            best_day_seconds = (yearly_stats.get('data') or {}).get('best_day', {}) or {}
            best_day_seconds = best_day_seconds.get('total_seconds', 0) or avg_seconds
            reference_seconds = best_day_seconds * 0.8
        else:
            if difficulty == 'easy':
                target_rank = 10000
            elif difficulty == 'medium':
                target_rank = 1000
            elif difficulty == 'hard':
                target_rank = 1
            else:
                target_rank = 10000
            page = math.ceil(target_rank / 100)
            leaders_res = requests.get(
                f'https://wakatime.com/api/v1/leaders?page={page}',
                headers=headers,
            )
            leaders_data = leaders_res.json()
            target_entry = None
            for entry in (leaders_data.get('data') or []):
                if int(entry.get('rank', 0)) == target_rank:
                    target_entry = entry
                    break
            reference_seconds = (
                (target_entry.get('running_total') or {}).get('daily_average', avg_seconds)
                if target_entry else avg_seconds
            )
    except Exception as e:
        print(f'[Spedometer] Failed to fetch reference data -> fallback to avgSeconds. {e}')

    scale_max_seconds = reference_seconds / 0.8
    percent = min((today_seconds / scale_max_seconds) * 100, 200) if scale_max_seconds > 0 else 0
    percent_change = round(((today_seconds - avg_seconds) / avg_seconds) * 100) if avg_seconds > 0 else 0
    today_hm = seconds_to_hms(today_seconds)
    avg_hm = seconds_to_hms(avg_seconds)

    width = 300
    height = 260
    cx = width / 2
    cy = 160
    r = 80

    custom_emoji_array = _parse_custom_emojis(custom_emojis)

    standard_labels = ['Poor', 'Fair', 'Good', 'Great', 'Excellent']
    game_labels = ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond']

    label_sets = {
        'game': game_labels,
        'standard': standard_labels,
        'emoji': ['🌱', '🌿', '🌾', '🌳', '🌲'],
        'emojiStandard': ['🌱 Poor', '🌿 Fair', '🌾 Good', '🌳 Great', '🌲 Excellent'],
        'emojiGame': ['🌱 Bronze', '🌿 Silver', '🌾 Gold', '🌳 Platinum', '🌲 Diamond'],
        'customEmoji': custom_emoji_array,
        'customStandard': [f'{e} {s}' if e else s for e, s in zip(custom_emoji_array, standard_labels)],
        'customGame': [f'{e} {g}' if e else g for e, g in zip(custom_emoji_array, game_labels)],
        'customEmojiStandard': [
            (f'{e} {s}' if e else s) if idx < len(custom_emoji_array) and custom_emoji_array[idx] else s
            for idx, (e, s) in enumerate(zip(custom_emoji_array, standard_labels))
        ],
        'customEmojiGame': [
            (f'{e} {g}' if e else g) if idx < len(custom_emoji_array) and custom_emoji_array[idx] else g
            for idx, (e, g) in enumerate(zip(custom_emoji_array, game_labels))
        ],
    }

    chosen_labels = label_sets.get(label_type, standard_labels)
    chart_colors = generate_color_wheel(chart_color, 5)

    segments = []
    for i in range(5):
        segments.append({
            'start': i * 36,
            'end': (i + 1) * 36,
            'color': chart_colors[i]['color'],
            'opacity': chart_colors[i]['opacity'],
            'label': chosen_labels[i] if i < len(chosen_labels) else '',
        })

    arc_paths = []
    for i, s in enumerate(segments):
        arc_paths.append(
            f'<path d="{describe_arc(cx, cy, r, s["start"], s["end"])}" '
            f'stroke="{hex_to_rgba(s["color"], s["opacity"])}" '
            f'stroke-width="45" fill="none" />\n'
            f'<path id="arcLabel-{i}" d="{describe_arc(cx, cy, r + 30, s["start"], s["end"])}" fill="none" />\n'
            f'<text font-size="10" fill="#{text_color}" font-family="{font_family}">\n'
            f'  <textPath href="#arcLabel-{i}" startOffset="50%" text-anchor="middle">{s["label"]}</textPath>\n'
            f'</text>'
        )

    arc_group = (
        f'<g transform="rotate(-90, {cx}, {cy})">\n'
        + '\n'.join(arc_paths)
        + '\n</g>'
    )

    angle_deg = (min(percent, 100) / 100) * 180
    display_angle = angle_deg - 90
    tip = polar_to_cartesian(cx, cy, r - 4, display_angle)
    left = polar_to_cartesian(cx, cy, 4, display_angle + 90)
    right = polar_to_cartesian(cx, cy, 4, display_angle - 90)
    needle_color = darken_hex_color(chart_color, 0.75)

    needle = (
        f'<polygon points="{left["x"]},{left["y"]} {tip["x"]},{tip["y"]} {right["x"]},{right["y"]}" '
        f'fill="{needle_color}" />\n'
        f'<circle cx="{cx}" cy="{cy}" r="4" fill="{needle_color}"/>'
    )

    high_score_marker = ''
    if show_high_score and best_day_seconds > 0:
        high_score_percent = (best_day_seconds / scale_max_seconds) * 100 if scale_max_seconds > 0 else 0
        if high_score_percent <= 100:
            high_score_angle = (high_score_percent / 100) * 180 - 90
            base_segment_index = min(int(high_score_percent / 20), 4)
            base_color = chart_colors[base_segment_index]['color'] if base_segment_index < len(chart_colors) else '#888'
            base_hsl = hex_to_hsl(base_color)
            adjusted_l = min(base_hsl['l'] + 15, 95)
            lighter_hex = hsl_to_hex(base_hsl['h'], base_hsl['s'], adjusted_l)
            inner = polar_to_cartesian(cx, cy, r - 22.5, high_score_angle)
            outer = polar_to_cartesian(cx, cy, r + 22.5, high_score_angle)
            label_radius = r - 35
            label_pos = polar_to_cartesian(cx, cy, label_radius, high_score_angle)
            high_score_marker = (
                f'<line x1="{inner["x"]}" y1="{inner["y"]}" x2="{outer["x"]}" y2="{outer["y"]}" '
                f'stroke="{lighter_hex}" stroke-width="2" />\n'
                f'<text x="{label_pos["x"]}" y="{label_pos["y"]}" font-size="12" font-weight="bold" '
                f'fill="{lighter_hex}" font-family="{font_family}" text-anchor="middle">⚑</text>'
            )

    return {
        'content': (
            f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'xmlns="http://www.w3.org/2000/svg">\n'
            f'  <text x="50%" y="22" text-anchor="middle" font-size="14" '
            f'fill="#{text_color}" font-family="{font_family}">\n'
            f'    <tspan font-weight="bold">{format_hm(today_hm)}</tspan>\n'
            f'    <tspan font-weight="normal"> Today</tspan>\n'
            f'  </text>\n'
            f'  {arc_group}\n'
            f'  {needle}\n'
            f'  {high_score_marker}\n'
            f'  <g transform="translate({width / 2 - 40}, {cy + 42})">\n'
            f'    {get_arrow_svg(percent_change, f"#{text_color}", 14)}\n'
            f'    <text x="20" y="12" font-size="13" fill="#{text_color}" '
            f'font-family="{font_family}">\n'
            f'      {abs(percent_change)}% {"increase" if percent_change >= 0 else "decrease"}\n'
            f'    </text>\n'
            f'  </g>\n'
            f'  <text x="50%" y="{cy + 70}" text-anchor="middle" font-size="13" '
            f'fill="#{text_color}" font-family="{font_family}">\n'
            f'    <tspan font-weight="bold">{format_hm(avg_hm)}</tspan>\n'
            f'    <tspan font-weight="normal"> Daily Average</tspan>\n'
            f'  </text>\n'
            f'  <text x="50%" y="{cy + 90}" text-anchor="middle" font-size="13" '
            f'fill="#{text_color}" font-family="{font_family}">\n'
            f'    <tspan font-weight="bold">{most_active_day_text}</tspan>\n'
            f'    <tspan font-weight="normal"> Most Active Day</tspan>\n'
            f'  </text>\n'
            f'</svg>'
        ),
        'width': width,
        'height': height,
    }
