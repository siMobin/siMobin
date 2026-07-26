import math
import requests
from cards.utils import (
    waka_auth_header, format_short_time, get_safe_day_name, is_dark_color,
    darken_color, lighten_color, hex_to_rgb, rgb_to_hex, color_distance,
    catmull_rom_to_bezier, generate_y_axis_elements, truncate_label,
    vary_color, reorder_days
)


def lighten_opacity(ratio):
    ratio_min = 0.08
    ratio_max = 0.25
    clamped = max(0, min(1, ratio))
    return round(ratio_max - (clamped * (ratio_max - ratio_min)), 2)


def adjust_text_color_for_background(base_text_color, fill_color, opacity):
    hex_str = fill_color.lstrip('#')
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    brightness = ((r * 299 + g * 587 + b * 114) / 100) * opacity
    is_dark = brightness < 128
    text_rgb = hex_to_rgb(base_text_color.lstrip('#'))
    factor = 0.25 if is_dark else 0.01
    adjusted = [
        max(0, min(255, round(c * factor)))
        for c in text_rgb
    ]
    return f'#{rgb_to_hex(*adjusted)}'


def get_language_breakdown_card(
    api_key=None,
    username='',
    text_color='',
    chart_color='',
    chart_type='bar',
    bg_color='',
    chart_curved_line=False,
    start_day=None,
    heading_type=None,
    hide_legend=False,
    hide_total=False,
    hide_time=False,
    hide_percentage=False,
    hide_title=False,
    y_axis=False,
    y_axis_label=False,
):
    chart_color = chart_color.lstrip('#')
    text_color = text_color.lstrip('#')
    api_key_val = api_key or ''
    if not api_key_val:
        raise ValueError('Missing WAKATIME_API_KEY')

    resp = requests.get(
        f'https://wakatime.com/api/v1/users/{username}/summaries?range=last_7_days',
        headers=waka_auth_header(api_key_val)
    )
    json_data = resp.json()
    days = json_data.get('data') or []
    if not days:
        raise ValueError('No 7-day summary data available.')

    if start_day and start_day != '-7':
        days = reorder_days(days, start_day)

    language_data_by_day = []
    for d in days:
        date = d['range']['date']
        languages = d.get('languages') or []
        lang_map = {}
        for l in languages:
            lang_map[l['name']] = lang_map.get(l['name'], 0) + l['total_seconds']
        language_data_by_day.append({
            'date': date,
            'languages': lang_map
        })

    all_languages = list(set(
        name for day_data in language_data_by_day
        for name in day_data['languages']
    ))

    language_series = {}
    for name in all_languages:
        language_series[name] = [
            day_data['languages'].get(name, 0)
            for day_data in language_data_by_day
        ]

    daily_totals = [
        sum(day_data['languages'].values())
        for day_data in language_data_by_day
    ]

    total_seconds = sum(daily_totals)
    max_seconds = max(daily_totals) if daily_totals else 0

    if heading_type == 'friendly':
        lang_totals = {}
        for d in days:
            for l in d.get('languages') or []:
                lang_totals[l['name']] = lang_totals.get(l['name'], 0) + l['total_seconds']
        sorted_langs = sorted(lang_totals.items(), key=lambda x: -x[1])
        top_language = sorted_langs[0][0] if sorted_langs else 'various languages'
        heading_text = f'This week, I mostly wrote in {top_language}'
    else:
        heading_text = "This Week's Coding Time by Language"

    has_y_axis = y_axis and chart_type in ('bar', 'line', 'area')
    has_y_axis_label = y_axis_label and chart_type in ('bar', 'line', 'area')
    left_padding = 70 if (has_y_axis or has_y_axis_label) else 0
    left_padding_no_y = 30 if (not has_y_axis and not has_y_axis_label) else 0
    top_padding = 22.5
    bar_width = 30
    spacing = 15
    title_height = 0 if hide_title else 14
    chart_top = top_padding + title_height + 10
    chart_height = 60
    chart_bottom = 60
    chart_base = chart_top + chart_height
    radar_padding = 110
    height = chart_base + chart_bottom
    if chart_type == 'radar':
        height += radar_padding
    chart_width = len(days) * (bar_width + spacing)

    language_colors = {}
    for name in all_languages:
        new_color = None
        attempts = 0
        existing = list(language_colors.values())
        while True:
            new_color = vary_color(chart_color, 90)
            attempts += 1
            if not any(color_distance(c, new_color) < 60 for c in existing) or attempts >= 10:
                break
        language_colors[name] = new_color.lstrip('#')

    if chart_type == 'bar':
        all_blocks = []
        for i, d in enumerate(days):
            x = i * (bar_width + spacing) + left_padding + left_padding_no_y
            y = chart_base
            day_blocks = []
            for lang in all_languages:
                seconds = language_series[lang][i]
                if not seconds:
                    continue
                height_ratio = seconds / max_seconds if max_seconds > 0 else 0
                segment_height = height_ratio * chart_height
                y -= segment_height
                day_blocks.append(f'''
            <rect x="{x}" y="{y}" width="{bar_width}" height="{segment_height}" fill="#{language_colors[lang]}" rx="2" ry="2">
              <title>{truncate_label(lang, 10)}: {format_short_time(seconds)}</title>
            </rect>
          ''')
            total_seconds_for_day = daily_totals[i]
            short_time = format_short_time(total_seconds_for_day)
            pct = f'{(total_seconds_for_day / total_seconds * 100):.1f}' if total_seconds > 0 else '0.0'
            if not hide_time:
                day_blocks.insert(0, f'<text x="{x + bar_width / 2}" y="{y - 4}" font-size="9" text-anchor="middle" fill="#{text_color}">{short_time}</text>')
            day_name = get_safe_day_name(d['range']['date'])
            day_blocks.append(f'<text x="{x + bar_width / 2}" y="{chart_base + 12}" font-weight="bold" font-size="10" text-anchor="middle" fill="#{text_color}">{day_name}</text>')
            if not hide_percentage:
                day_blocks.append(f'<text x="{x + bar_width / 2}" y="{chart_base + 24}" font-size="9" text-anchor="middle" fill="#{text_color}">{pct}%</text>')
            all_blocks.extend(day_blocks)

        y_axis_elements = generate_y_axis_elements(max_seconds, chart_top, chart_base, chart_height, text_color, chart_width, chart_type, y_axis_label, left_padding) if y_axis and chart_type in ('bar', 'line', 'area') else []

        legend_y_offset = 48
        legend_line_height = 20
        legend_cols = 3
        max_label_length = max(len(l) for l in all_languages) if all_languages else 0
        avg_char_width = 6.5
        label_width = max_label_length * avg_char_width
        legend_col_width = 12 + 10 + label_width + 10
        svg_width = max(chart_width, 300) + 125 + left_padding
        total_legend_width = legend_cols * legend_col_width
        center_offset_x = (svg_width - total_legend_width) / 2

        legend_items = []
        if not hide_legend:
            for idx, lang in enumerate(all_languages):
                lx = center_offset_x + (idx % legend_cols) * legend_col_width
                ly = chart_base + legend_y_offset + (idx // legend_cols) * legend_line_height
                legend_items.append(f'''
            <circle cx="{lx}" cy="{ly - 4}" r="5" fill="#{language_colors[lang]}" />
            <text x="{lx + 12}" y="{ly}" font-size="10" fill="#{text_color}">{truncate_label(lang, 10)}</text>
          ''')

        legend_height_total = 0 if hide_legend else math.ceil(len(all_languages) / legend_cols) * legend_line_height + legend_y_offset
        height = max(height, chart_base + legend_y_offset + legend_height_total - 30)

        chart_blocks = y_axis_elements + all_blocks + legend_items

    elif chart_type == 'line':
        curved = chart_curved_line if isinstance(chart_curved_line, bool) else str(chart_curved_line).lower() == 'true'
        elements = []
        label_elements = []

        for lang in all_languages:
            points = []
            for i, seconds in enumerate(language_series[lang]):
                x = i * (bar_width + spacing) + left_padding + left_padding_no_y + bar_width / 2
                y_val = (seconds / max_seconds) * chart_height if max_seconds > 0 else 0
                y = chart_base - y_val
                points.append({'x': x, 'y': y, 'seconds': seconds, 'dayIndex': i})

            if all(p['seconds'] == 0 for p in points):
                continue

            path_d = ''
            if curved and len(points) > 1:
                path_d = catmull_rom_to_bezier(points, chart_base - chart_height, chart_base)
            else:
                path_d = ' '.join(f'{"M" if i == 0 else "L"} {p["x"]} {p["y"]}' for i, p in enumerate(points))

            color = language_colors[lang]
            elements.append(f'<path d="{path_d}" fill="none" stroke="#{color}" stroke-width="2" />')
            for p in points:
                elements.append(f'<circle cx="{p["x"]}" cy="{p["y"]}" r="2" fill="#{color}"><title>{truncate_label(lang, 10)}: {format_short_time(p["seconds"])}</title></circle>')

            if not hide_time or not hide_percentage:
                for p in points:
                    short_time = format_short_time(p['seconds'])
                    pct = f'{(p["seconds"] / total_seconds * 100):.1f}' if total_seconds > 0 else '0.0'
                    time_label = f'<text x="{p["x"]}" y="{p["y"] - 6}" font-size="8.5" text-anchor="middle" fill="#{text_color}" fill-opacity="0.9">{short_time}</text>' if not hide_time else ''
                    pct_label = f'<text x="{p["x"]}" y="{p["y"] - 16}" font-size="8" text-anchor="middle" fill="#{text_color}" fill-opacity="0.6">{pct}%</text>' if not hide_percentage else ''
                    label_elements.append(f'{time_label}{pct_label}')

        y_axis_elements = generate_y_axis_elements(max_seconds, chart_top, chart_base, chart_height, text_color, chart_width, chart_type, y_axis_label, left_padding) if y_axis and chart_type in ('bar', 'line', 'area') else []

        day_labels = []
        for i, d in enumerate(days):
            x = i * (bar_width + spacing) + left_padding + bar_width / 2
            day_name = get_safe_day_name(d['range']['date'])
            day_labels.append(f'<text x="{x}" y="{chart_base + 12}" font-weight="bold" font-size="10" text-anchor="middle" fill="#{text_color}" fill-opacity="0.7">{day_name}</text>')

        output_blocks = y_axis_elements + elements + label_elements + day_labels

        if not hide_legend:
            legend_y_offset = 36
            legend_line_height = 20
            legend_cols = 3
            max_label_length = max(len(l) for l in all_languages) if all_languages else 0
            avg_char_width = 6.5
            label_width = max_label_length * avg_char_width
            legend_col_width = 12 + 10 + label_width + 10
            svg_width = max(chart_width, 300) + 125 + left_padding
            total_legend_width = legend_cols * legend_col_width
            center_offset_x = (svg_width - total_legend_width) / 2

            legend_items = []
            for idx, lang in enumerate(all_languages):
                lx = center_offset_x + (idx % legend_cols) * legend_col_width
                ly = chart_base + legend_y_offset + (idx // legend_cols) * legend_line_height
                legend_items.append(f'''
            <circle cx="{lx}" cy="{ly - 4}" r="5" fill="#{language_colors[lang]}" />
            <text x="{lx + 12}" y="{ly}" font-size="10" fill="#{text_color}">{truncate_label(lang, 10)}</text>
          ''')

            legend_height_total = math.ceil(len(all_languages) / legend_cols) * legend_line_height + legend_y_offset
            height = max(height, chart_base + legend_y_offset + legend_height_total - 20)
            chart_blocks = output_blocks + legend_items
        else:
            chart_blocks = output_blocks

    elif chart_type == 'area':
        curved = chart_curved_line if isinstance(chart_curved_line, bool) else str(chart_curved_line).lower() == 'true'
        x_positions = [i * (bar_width + spacing) + left_padding + left_padding_no_y + bar_width / 2 for i in range(len(days))]
        area_elements = []
        label_elements = []

        for lang in all_languages:
            color = language_colors[lang]
            points = []
            for i in range(len(days)):
                seconds = language_series[lang][i]
                h = (seconds / max_seconds) * chart_height if max_seconds > 0 else 0
                if seconds > 0 and h < 1.5:
                    h = 1.5
                x = x_positions[i]
                y = chart_base - h
                points.append({'x': x, 'y': y, 'seconds': seconds})

            top_line = ''
            if curved and len(points) > 1:
                top_line = catmull_rom_to_bezier(points, chart_base - chart_height, chart_base)
            else:
                top_line = ' '.join(f'{"M" if i == 0 else "L"} {p["x"]} {p["y"]}' for i, p in enumerate(points))

            bottom_points = [{'x': p['x'], 'y': chart_base} for p in points][::-1]
            area_path = f'''
        {top_line}
        {' '.join(f'L {p["x"]} {p["y"]}' for p in bottom_points)}
        Z
      '''

            area_elements.append(f'<path d="{area_path.strip()}" fill="#{color}" fill-opacity="0.25" />')
            area_elements.append(f'<path d="{top_line.strip()}" fill="none" stroke="#{color}" stroke-width="1.5" />')

            if not hide_time or not hide_percentage:
                for p in points:
                    short_time = format_short_time(p['seconds'])
                    pct = f'{(p["seconds"] / total_seconds * 100):.1f}' if total_seconds > 0 else '0.0'
                    time_label = f'<text x="{p["x"]}" y="{p["y"] - 6}" font-size="8.5" text-anchor="middle" fill="#{text_color}" fill-opacity="0.85">{short_time}</text>' if not hide_time else ''
                    pct_label = f'<text x="{p["x"]}" y="{p["y"] - 15}" font-size="8" text-anchor="middle" fill="#{text_color}" fill-opacity="0.6">{pct}%</text>' if not hide_percentage else ''
                    label_elements.append(f'''
            <circle cx="{p["x"]}" cy="{p["y"]}" r="2.2" fill="#{color}">
              <title>{truncate_label(lang, 10)}: {short_time}</title>
            </circle>
            {time_label}{pct_label}
          ''')

        y_axis_elements = generate_y_axis_elements(max_seconds, chart_top, chart_base, chart_height, text_color, chart_width, chart_type, y_axis_label, left_padding) if y_axis and chart_type in ('bar', 'line', 'area') else []

        day_labels = []
        for i, d in enumerate(days):
            x = x_positions[i]
            day_name = get_safe_day_name(d['range']['date'])
            day_labels.append(f'<text x="{x}" y="{chart_base + 12}" font-weight="bold" font-size="10" text-anchor="middle" fill="#{text_color}" fill-opacity="0.7">{day_name}</text>')

        output_blocks = y_axis_elements + area_elements + label_elements + day_labels

        if not hide_legend:
            legend_y_offset = 36
            legend_line_height = 20
            legend_cols = 3
            max_label_length = max(len(l) for l in all_languages) if all_languages else 0
            avg_char_width = 6.5
            label_width = max_label_length * avg_char_width
            legend_col_width = 12 + 10 + label_width + 10
            svg_width = max(chart_width, 300) + 125 + left_padding
            total_legend_width = legend_cols * legend_col_width
            center_offset_x = (svg_width - total_legend_width) / 2

            legend_items = []
            for idx, lang in enumerate(all_languages):
                lx = center_offset_x + (idx % legend_cols) * legend_col_width
                ly = chart_base + legend_y_offset + (idx // legend_cols) * legend_line_height
                legend_items.append(f'''
            <circle cx="{lx}" cy="{ly - 4}" r="5" fill="#{language_colors[lang]}" />
            <text x="{lx + 12}" y="{ly}" font-size="10" fill="#{text_color}">{truncate_label(lang, 10)}</text>
          ''')

            legend_height_total = math.ceil(len(all_languages) / legend_cols) * legend_line_height + legend_y_offset
            height = max(height, chart_base + legend_y_offset + legend_height_total - 20)
            chart_blocks = output_blocks + legend_items
        else:
            chart_blocks = output_blocks

    elif chart_type == 'radar':
        svg_width_radar = max(chart_width, 300) + 48
        cx = svg_width_radar / 2
        cy = chart_top + chart_height / 2 + radar_padding / 1.7
        radius = min(chart_height, chart_width) / 0.7
        angle_step = 2 * math.pi / len(days)
        use_lighten = is_dark_color(bg_color)
        adjust = lighten_color if use_lighten else darken_color
        adjusted_color = adjust(text_color, 120)

        grid = []
        levels = 4
        for lvl in range(1, levels + 1):
            r = (lvl / levels) * radius
            path = []
            for i in range(len(days)):
                a = i * angle_step - math.pi / 2
                x = cx + r * math.cos(a)
                y = cy + r * math.sin(a)
                path.append(f'{"M" if i == 0 else "L"} {x} {y}')
            grid.append(f'<path d="{" ".join(path)} Z" fill="none" stroke="#{adjusted_color}" stroke-dasharray="2,2" stroke-width="0.5"/>')

        axis_lines = []
        for i in range(len(days)):
            a = i * angle_step - math.pi / 2
            x = cx + radius * math.cos(a)
            y = cy + radius * math.sin(a)
            axis_lines.append(f'<line x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="#{adjusted_color}" stroke-width="0.5"/>')

        language_polygons = []
        for lang in all_languages:
            points = []
            for i, seconds in enumerate(language_series[lang]):
                a = i * angle_step - math.pi / 2
                r = (seconds / max_seconds) * radius if max_seconds > 0 else 0
                x = cx + r * math.cos(a)
                y = cy + r * math.sin(a)
                points.append({'x': x, 'y': y, 'seconds': seconds})

            polygon_points = ' '.join(f'{p["x"]},{p["y"]}' for p in points)
            color = language_colors[lang]
            language_polygons.append(f'''
          <polygon points="{polygon_points}" fill="#{color}" fill-opacity="0.2" stroke="#{color}" stroke-width="2" />
          {"".join(f'<circle cx="{p["x"]}" cy="{p["y"]}" r="2.2" fill="#{color}"><title>{truncate_label(lang, 10)}: {format_short_time(p["seconds"])}</title></circle>' for p in points)}
        ''')

        labels = []
        for i, d in enumerate(days):
            a = i * angle_step - math.pi / 2
            label_dist = radius + 12
            x = cx + label_dist * math.cos(a)
            y = cy + label_dist * math.sin(a)
            day_name = get_safe_day_name(d['range']['date'])
            labels.append(f'<text x="{x}" y="{y}" font-size="10" text-anchor="middle" alignment-baseline="middle" fill="#{text_color}">{day_name}</text>')

        radar_y_axis = []
        if y_axis:
            y_angle = math.pi / 14
            label_angle_deg = 77
            for i in range(5):
                val = (max_seconds / 4) * i
                r = (val / max_seconds) * radius if max_seconds > 0 else 0
                x = cx + r * math.cos(y_angle)
                y = cy + r * math.sin(y_angle)
                radar_y_axis.append(f'<circle cx="{x}" cy="{y}" r="0.8" fill="#{text_color}"/>')
                if y_axis_label or i == 0 or i == 4:
                    if i == 0:
                        continue
                    label = format_short_time(val)
                    label_y_offset = 18 + r * 0.05
                    label_y = y - label_y_offset
                    label_x = x - 2
                    radar_y_axis.append(f'<text x="{label_x}" y="{label_y}" font-size="8" text-anchor="start" transform="rotate({label_angle_deg}, {label_x}, {label_y})" fill="#{text_color}">{label}</text>')

        legend_y_offset_radar = 47.5
        legend_line_height_radar = 20
        legend_cols_radar = 2
        max_label_length_radar = max(len(l) for l in all_languages) if all_languages else 0
        avg_char_width_radar = 6.5
        label_width_radar = max_label_length_radar * avg_char_width_radar
        legend_col_width_radar = 12 + 10 + label_width_radar + 10
        svg_width_radar2 = max(chart_width, 300) + -20
        total_legend_width_radar = legend_cols_radar * legend_col_width_radar
        center_offset_x_radar = (svg_width_radar2 - total_legend_width_radar) / 2

        lang_totals = {}
        for lang in all_languages:
            lang_totals[lang] = sum(language_series[lang])

        pill_box_width = 60
        name_box_width = 60

        legend_items_radar = []
        if not hide_legend:
            for idx, lang in enumerate(all_languages):
                lx = center_offset_x_radar + (idx % legend_cols_radar) * (name_box_width + pill_box_width + 20)
                ly = chart_base + radar_padding + legend_y_offset_radar + (idx // legend_cols_radar) * legend_line_height_radar

                value_seconds = lang_totals[lang]
                raw_color = language_colors.get(lang, chart_color)
                ratio_val = value_seconds / max_seconds if max_seconds > 0 else 0
                fill = raw_color
                ratio_opacity = 0.1 * (max_seconds / (value_seconds * 800)) if value_seconds > 0 else 0
                fill_opacity = lighten_opacity(ratio_opacity)
                adj_text_color = adjust_text_color_for_background(text_color, fill, fill_opacity)

                pill_text = f'{format_short_time(value_seconds)} ({(value_seconds / total_seconds * 100):.1f}%)' if total_seconds > 0 else f'{format_short_time(value_seconds)} (0.0%)'

                legend_items_radar.append(f'''
            <text x="{lx}" y="{ly}" font-size="10" font-weight="bold" fill="#{text_color}">{truncate_label(lang, 10)}</text>
            <rect x="{lx + name_box_width}" y="{ly - 10}" width="{pill_box_width}" height="14" rx="4" ry="4" fill="#{fill}" fill-opacity="{fill_opacity}" />
            <text x="{lx + name_box_width + pill_box_width / 2}" y="{ly + 1}" font-size="9" text-anchor="middle" fill="#{adjusted_color}">{pill_text}</text>
          ''')

        legend_height_radar = math.ceil(len(all_languages) / legend_cols_radar) * legend_line_height_radar + legend_y_offset_radar
        if not hide_legend:
            height = chart_base + radar_padding + legend_height_radar + 15

        chart_blocks = grid + axis_lines + language_polygons + labels + radar_y_axis + legend_items_radar

    else:
        chart_blocks = []

    total_time_text = json_data.get('cumulative_total', {}).get('text', '')

    is_friendly = heading_type == 'friendly'
    heading_font_size = 12 if is_friendly else 14

    x_center = chart_width / 2 + 20 if chart_type == 'radar' else left_padding / 2 + chart_width / 2 + 20

    title = ''
    if not hide_title:
        title = f'<text x="{x_center}" y="{top_padding}" font-size="{heading_font_size}" text-anchor="middle" fill="#{text_color}" font-weight="bold">{heading_text}</text>'

    centered_total = ''
    if not hide_total:
        centered_total = f'<text x="{x_center}" y="{height - 10}" font-size="12" text-anchor="middle" fill="#{text_color}"><tspan font-weight="bold">Total:</tspan> {total_time_text}</text>'

    return {
        'content': f'''
    {title}
    {" ".join(chart_blocks)}
    {centered_total}
  ''',
        'height': height,
        'width': max(chart_width, 300) + 48 + left_padding if chart_type != 'radar' else max(chart_width, 300) + 48
    }
