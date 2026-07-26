from datetime import datetime
import math
import requests
from cards.utils import (
    waka_auth_header,
    parse_boolean,
    format_short_time,
    get_safe_day_name,
    reorder_days,
    generate_y_axis_elements,
    is_dark_color,
    lighten_color,
    darken_color,
    vary_color,
    catmull_rom_to_bezier,
)


def _circle_pack(items, center_x, center_y):
    if not items:
        return items
    sorted_items = sorted(items, key=lambda x: -x['value'])
    max_val = sorted_items[0]['value'] if sorted_items else 1
    placed = []
    for item in sorted_items:
        val_ratio = item['value'] / max_val if max_val > 0 else 0
        r = max(10, val_ratio * 50)
        item['r'] = r
        if not placed:
            item['x'] = center_x
            item['y'] = center_y
            placed.append(item)
        else:
            best_x = center_x
            best_y = center_y
            best_dist = float('inf')
            for anchor in placed:
                for angle_deg in range(0, 360, 3):
                    rad = math.radians(angle_deg)
                    tx = anchor['x'] + (anchor['r'] + r + 1) * math.cos(rad)
                    ty = anchor['y'] + (anchor['r'] + r + 1) * math.sin(rad)
                    collision = False
                    for p in placed:
                        if math.hypot(tx - p['x'], ty - p['y']) < p['r'] + r - 0.5:
                            collision = True
                            break
                    if not collision:
                        d = math.hypot(tx - center_x, ty - center_y)
                        if d < best_dist:
                            best_dist = d
                            best_x, best_y = tx, ty
            item['x'] = best_x
            item['y'] = best_y
            placed.append(item)
    return placed


def get_coding_activity_card(
    api_key=None,
    username=None,
    text_color='ccc',
    chart_color='4ade80',
    chart_type='bar',
    bg_color='1a1a2e',
    chart_curved_line=None,
    start_day=None,
    heading_type='standard',
    custom_heading=None,
    mixed_colors=None,
    hide_legend=None,
    hide_total=None,
    hide_time=None,
    hide_percentage=None,
    hide_title=None,
    y_axis=None,
    y_axis_label=None,
    custom_days=None,
):
    chart_color = chart_color.replace('#', '')
    text_color = text_color.replace('#', '')
    if not api_key:
        raise Exception('Missing WAKATIME_API_KEY')

    res = requests.get(
        f'https://wakatime.com/api/v1/users/{username}/summaries?range=last_7_days',
        headers=waka_auth_header(api_key),
    )
    json_data = res.json()
    days = custom_days or json_data.get('data')
    if not days or len(days) == 0:
        raise Exception('No 7-day summary data available.')

    if start_day and start_day != '-7':
        days = reorder_days(days, start_day)

    total_seconds = sum(d['grand_total']['total_seconds'] for d in days)
    max_seconds = max(d['grand_total']['total_seconds'] for d in days)

    if heading_type == 'custom':
        heading_text = custom_heading
    elif heading_type == 'friendly':
        most_productive = max(days, key=lambda d: d['grand_total']['total_seconds'])
        day_name = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][
            datetime.strptime(most_productive['range']['date'][:10], '%Y-%m-%d').weekday()
        ]
        heading_text = f'This week, my most productive day was {day_name}'
    else:
        heading_text = 'This Week\'s Coding Time'

    has_y_axis = parse_boolean(y_axis) and chart_type in ('bar', 'line', 'area')
    has_y_axis_label = parse_boolean(y_axis_label) and chart_type in ('bar', 'line', 'area')
    left_padding = 70 if (has_y_axis or has_y_axis_label) else 0
    left_padding_no_y = 30 if (not has_y_axis and not has_y_axis_label) else 0
    top_padding = 22.5
    bar_width = 30
    spacing = 15
    title_height = 0 if parse_boolean(hide_title) else 14
    chart_top = top_padding + title_height + 10
    chart_height = 60
    chart_bottom = 60
    chart_base = chart_top + chart_height
    radar_padding = 110
    bubble_padding = 35
    height = chart_base + chart_bottom
    if chart_type == 'radar':
        height += radar_padding
    if chart_type == 'bubble':
        height -= bubble_padding
    chart_width = len(days) * (bar_width + spacing)

    def get_mixed_color(index):
        use_lighten = is_dark_color(bg_color)
        adjust_color = lighten_color if use_lighten else darken_color
        if parse_boolean(mixed_colors) and index > 0:
            return adjust_color(chart_color, 20 + index * 10)
        return chart_color

    chart_svg_blocks = []

    if chart_type == 'bar':
        bar_blocks = []
        for i, d in enumerate(days):
            seconds = d['grand_total']['total_seconds']
            pct = f'{(seconds / total_seconds) * 100:.1f}' if total_seconds > 0 else '0.0'
            bar_h = (seconds / max_seconds) * chart_height if max_seconds > 0 else 0
            if bar_h == 0 and seconds == 0:
                bar_h = 1.5
            x = i * (bar_width + spacing) + left_padding + left_padding_no_y
            y = chart_base - bar_h
            blocks = []
            fill = get_mixed_color(i)
            blocks.append(f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_h}" fill="#{fill}" rx="3" ry="3" />')
            short_time = format_short_time(seconds)
            if not parse_boolean(hide_time):
                blocks.append(f'<text x="{x + bar_width / 2}" y="{y - 4}" font-size="9" text-anchor="middle" fill="#{text_color}">{short_time}</text>')
            day_name = get_safe_day_name(d['range']['date'])
            blocks.append(f'<text x="{x + bar_width / 2}" y="{chart_base + 12}" font-weight="bold" font-size="10" text-anchor="middle" fill="#{text_color}">{day_name}</text>')
            if not parse_boolean(hide_percentage):
                blocks.append(f'<text x="{x + bar_width / 2}" y="{chart_base + 24}" font-size="9" text-anchor="middle" fill="#{text_color}">{pct}%</text>')
            bar_blocks.append('\n'.join(blocks))
        y_axis_elements = []
        if has_y_axis:
            y_axis_elements = generate_y_axis_elements(
                max_seconds, chart_top, chart_base, chart_height,
                text_color, chart_width, chart_type, y_axis_label, left_padding,
            )
        chart_svg_blocks = y_axis_elements + bar_blocks

    elif chart_type == 'line':
        curved = (
            chart_curved_line.lower() == 'true' if isinstance(chart_curved_line, str)
            else bool(chart_curved_line)
        )
        points = []
        for i, d in enumerate(days):
            seconds = d['grand_total']['total_seconds']
            pct = f'{(seconds / total_seconds) * 100:.1f}' if total_seconds > 0 else '0.0'
            x = i * (bar_width + spacing) + left_padding + left_padding_no_y + bar_width / 2
            y_val = (seconds / max_seconds) * chart_height if max_seconds > 0 else 0
            y = chart_base - y_val
            points.append({'x': x, 'y': y, 'seconds': seconds, 'date': d['range']['date'], 'pct': pct})
        if curved and len(points) > 1:
            path_d = catmull_rom_to_bezier(points, min_y=chart_base - chart_height, max_y=chart_base)
        else:
            segments = []
            for j, p in enumerate(points):
                segments.append(f'{"M" if j == 0 else "L"} {p["x"]} {p["y"]}')
            path_d = ' '.join(segments)
        circles = [
            f'<circle cx="{p["x"]}" cy="{p["y"]}" r="2.5" fill="#{get_mixed_color(i)}" />'
            for i, p in enumerate(points)
        ]
        y_axis_elements = []
        if has_y_axis:
            y_axis_elements = generate_y_axis_elements(
                max_seconds, chart_top, chart_base, chart_height,
                text_color, chart_width, chart_type, y_axis_label, left_padding,
            )
        labels = []
        for i, p in enumerate(points):
            short_time = format_short_time(p['seconds'])
            day_name = get_safe_day_name(days[i]['range']['date'])
            time_label = (
                f'<text x="{p["x"]}" y="{p["y"] - 6}" font-size="9" text-anchor="middle" '
                f'fill="#{text_color}" fill-opacity="0.8">{short_time}</text>'
            ) if not parse_boolean(hide_time) else ''
            day_label = (
                f'<text x="{p["x"]}" y="{chart_base + 12}" font-weight="bold" font-size="10" '
                f'text-anchor="middle" fill="#{text_color}" fill-opacity="0.7">{day_name}</text>'
            )
            pct_label = (
                f'<text x="{p["x"]}" y="{chart_base + 24}" font-size="9" text-anchor="middle" '
                f'fill="#{text_color}" fill-opacity="0.6">{p["pct"]}%</text>'
            ) if not parse_boolean(hide_percentage) else ''
            label_text = '\n'.join(filter(None, [time_label, day_label, pct_label]))
            labels.append(label_text)
        chart_svg_blocks = y_axis_elements + [
            f'<path d="{path_d}" fill="none" stroke="#{chart_color}" stroke-width="2" />',
        ] + circles + labels

    elif chart_type == 'area':
        curved = (
            chart_curved_line.lower() == 'true' if isinstance(chart_curved_line, str)
            else bool(chart_curved_line)
        )
        points = []
        for i, d in enumerate(days):
            seconds = d['grand_total']['total_seconds']
            pct = f'{(seconds / total_seconds) * 100:.1f}' if total_seconds > 0 else '0.0'
            x = i * (bar_width + spacing) + left_padding + left_padding_no_y + bar_width / 2
            y_val = (seconds / max_seconds) * chart_height if max_seconds > 0 else 0
            y = chart_base - y_val
            points.append({'x': x, 'y': y, 'seconds': seconds, 'date': d['range']['date'], 'pct': pct})
        if curved and len(points) > 1:
            line_path = catmull_rom_to_bezier(points, min_y=chart_base - chart_height, max_y=chart_base)
        else:
            segments = []
            for j, p in enumerate(points):
                segments.append(f'{"M" if j == 0 else "L"} {p["x"]} {p["y"]}')
            line_path = ' '.join(segments)
        area_path = f'{line_path} L {points[-1]["x"]} {chart_base} L {points[0]["x"]} {chart_base} Z'
        circles = [
            f'<circle cx="{p["x"]}" cy="{p["y"]}" r="2.5" fill="#{get_mixed_color(i)}" />'
            for i, p in enumerate(points)
        ]
        y_axis_elements = []
        if has_y_axis:
            y_axis_elements = generate_y_axis_elements(
                max_seconds, chart_top, chart_base, chart_height,
                text_color, chart_width, chart_type, y_axis_label, left_padding,
            )
        labels = []
        for i, p in enumerate(points):
            short_time = format_short_time(p['seconds'])
            day_name = get_safe_day_name(days[i]['range']['date'])
            time_label = (
                f'<text x="{p["x"]}" y="{p["y"] - 6}" font-size="9" text-anchor="middle" '
                f'fill="#{text_color}" fill-opacity="0.8">{short_time}</text>'
            ) if not parse_boolean(hide_time) else ''
            day_label = (
                f'<text x="{p["x"]}" y="{chart_base + 12}" font-weight="bold" font-size="10" '
                f'text-anchor="middle" fill="#{text_color}" fill-opacity="0.7">{day_name}</text>'
            )
            pct_label = (
                f'<text x="{p["x"]}" y="{chart_base + 24}" font-size="9" text-anchor="middle" '
                f'fill="#{text_color}" fill-opacity="0.6">{p["pct"]}%</text>'
            ) if not parse_boolean(hide_percentage) else ''
            label_text = '\n'.join(filter(None, [time_label, day_label, pct_label]))
            labels.append(label_text)
        chart_svg_blocks = y_axis_elements + [
            f'<path d="{area_path}" fill="#{chart_color}" fill-opacity="0.2" />',
            f'<path d="{line_path}" fill="none" stroke="#{chart_color}" stroke-width="2" />',
        ] + circles + labels

    elif chart_type == 'radar':
        cx = (chart_width + 48) / 2
        cy = chart_top + chart_height / 2 + radar_padding / 1.7
        radius = min(chart_height, chart_width) / 0.7
        angle_step = (2 * math.pi) / len(days)
        use_lighten = is_dark_color(bg_color)
        adjust_color = darken_color if use_lighten else lighten_color
        adjusted_color = adjust_color(text_color, 120)

        points = []
        for i, d in enumerate(days):
            angle = i * angle_step - math.pi / 2
            seconds = d['grand_total']['total_seconds']
            pct = f'{(seconds / total_seconds) * 100:.1f}' if total_seconds > 0 else '0.0'
            r = (seconds / max_seconds) * radius if max_seconds > 0 else 0
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append({'x': x, 'y': y, 'angle': angle, 'seconds': seconds, 'date': d['range']['date'], 'pct': pct})

        grid = []
        levels = 4
        for lvl in range(1, levels + 1):
            r = (lvl / levels) * radius
            path_parts = []
            for i in range(len(days)):
                angle = i * angle_step - math.pi / 2
                x = cx + r * math.cos(angle)
                y = cy + r * math.sin(angle)
                path_parts.append(f'{"M" if i == 0 else "L"} {x} {y}')
            grid.append(f'<path d="{" ".join(path_parts)} Z" fill="none" stroke="#{adjusted_color}" stroke-dasharray="2,2" stroke-width="0.5"/>')

        axis_lines = []
        for i in range(len(days)):
            angle = i * angle_step - math.pi / 2
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            axis_lines.append(f'<line x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="#{adjusted_color}" stroke-width="0.5"/>')

        labels = []
        for i, d in enumerate(days):
            angle = i * angle_step - math.pi / 2
            label_dist = radius + 12
            x = cx + label_dist * math.cos(angle)
            y = cy + label_dist * math.sin(angle)
            day_name = get_safe_day_name(d['range']['date'])
            labels.append(
                f'<text x="{x}" y="{y}" font-size="10" text-anchor="middle" '
                f'alignment-baseline="middle" fill="#{text_color}">{day_name}</text>'
            )

        radar_y_axis = []
        if parse_boolean(y_axis):
            angle = math.pi / 14
            label_angle_deg = 77
            for i in range(5):
                val = (max_seconds / 4) * i
                r = (val / max_seconds) * radius if max_seconds > 0 else 0
                x = cx + r * math.cos(angle)
                y = cy + r * math.sin(angle)
                radar_y_axis.append(f'<circle cx="{x}" cy="{y}" r="0.8" fill="#{text_color}"/>')
                if parse_boolean(y_axis_label) or i == 0 or i == 4:
                    if i == 0:
                        continue
                    label_text = format_short_time(val)
                    label_y = y - (18 + r * 0.05)
                    label_x = x - 2
                    radar_y_axis.append(
                        f'<text x="{label_x}" y="{label_y}" font-size="8" text-anchor="start" '
                        f'transform="rotate({label_angle_deg}, {label_x}, {label_y})" '
                        f'fill="#{text_color}">{label_text}</text>'
                    )

        legend_y_offset = 60
        legend_line_height = 24
        legend_cols = 2
        legend_col_width = 180
        center_offset_x = ((chart_width + 100) - legend_cols * legend_col_width) / 2

        all_pill_texts = [
            f'{format_short_time(d["grand_total"]["total_seconds"])} '
            f'({(d["grand_total"]["total_seconds"] / total_seconds) * 100:.1f}%)'
            for d in days
        ]
        max_pill_text = max(all_pill_texts, key=len)
        uniform_pill_width = len(max_pill_text) * 5 + 8

        legend_items = []
        if not parse_boolean(hide_legend):
            for i, d in enumerate(days):
                short_time = format_short_time(d['grand_total']['total_seconds'])
                pct_val = (d['grand_total']['total_seconds'] / total_seconds) * 100 if total_seconds > 0 else 0
                pct_text = f'{pct_val:.1f}%'
                day_name = get_safe_day_name(d['range']['date'])
                x = center_offset_x + (i % legend_cols) * legend_col_width
                y = chart_base + radar_padding + legend_y_offset + (i // legend_cols) * legend_line_height
                pill_text = f'{short_time} ({pct_text})'
                pill_x = x + len(day_name) * 12 + 12
                ratio = d['grand_total']['total_seconds'] / max_seconds if max_seconds > 0 else 0
                opacity = min(0.1 + 0.6 * ratio, 1.0)
                legend_items.append(
                    f'<text x="{x}" y="{y}" font-size="10" font-weight="bold" fill="#{text_color}">{day_name}:</text>\n'
                    f'<rect x="{pill_x}" y="{y - 10}" width="{uniform_pill_width}" height="14" '
                    f'fill="#{chart_color}" fill-opacity="{opacity:.2f}" />\n'
                    f'<text x="{pill_x + uniform_pill_width / 2}" y="{y + 1}" font-size="9" '
                    f'text-anchor="middle" fill="#{text_color}">{pill_text}</text>'
                )

        legend_height = math.ceil(len(days) / legend_cols) * legend_line_height + legend_y_offset
        if not parse_boolean(hide_legend):
            height = chart_base + radar_padding + legend_height + 20

        chart_svg_blocks = (
            grid + axis_lines + [
                f'<polygon points="{" ".join(f"{p["x"]},{p["y"]}" for p in points)}" '
                f'fill="#{chart_color}" fill-opacity="0.2" stroke="#{chart_color}" stroke-width="2"/>'
            ] + labels + radar_y_axis + legend_items
        )

    elif chart_type == 'bubble':
        items = [
            {'value': d['grand_total']['total_seconds'], 'index': i}
            for i, d in enumerate(days)
        ]
        chart_size = max(chart_width, 240)
        packed = _circle_pack(items, chart_size / 2, chart_size * 0.75 / 2)
        bubble_y_offset = 25
        for node in packed:
            node['y'] += bubble_y_offset
        max_y = max(n['y'] + n['r'] for n in packed) if packed else 0
        actual_bubble_height = max_y
        max_bubble_chart_height = chart_base - chart_top + 220
        scale_y = 1
        if actual_bubble_height > max_bubble_chart_height:
            scale_y = max_bubble_chart_height / actual_bubble_height
            for node in packed:
                node['y'] = chart_top + (node['y'] - chart_top) * scale_y
                node['r'] *= scale_y
        height = max_y + 20
        min_x = min(n['x'] - n['r'] for n in packed) if packed else 0
        max_x = max(n['x'] + n['r'] for n in packed) if packed else 0
        bubble_width = max_x - min_x
        svg_center = (chart_width + 48) / 2
        bubble_center = min_x + bubble_width / 2
        x_offset = svg_center - bubble_center

        elements = []
        legend_items = []
        legend_cols = 2
        legend_col_width = 190
        legend_circle_offset = 12
        legend_text_offset = 24
        legend_y_offset = 40
        legend_line_height = 20
        center_offset_x = ((chart_width + 100) - legend_cols * legend_col_width) / 2

        for i, node in enumerate(packed):
            day_index = node['index']
            d = days[day_index]
            seconds = d['grand_total']['total_seconds']
            pct_val = (seconds / total_seconds) * 100 if total_seconds > 0 else 0
            short_time = format_short_time(seconds)
            day_name = get_safe_day_name(d['range']['date'])
            color = vary_color(chart_color)
            elements.append(
                f'<circle cx="{node["x"]}" cy="{node["y"]}" r="{node["r"]}" '
                f'fill="#{color}" fill-opacity="0.85" />'
            )
            if not parse_boolean(hide_legend):
                lx = center_offset_x + (i % legend_cols) * legend_col_width
                ly = max_y + 30 + (i // legend_cols) * legend_line_height
                legend_items.append(
                    f'<circle cx="{lx + legend_circle_offset}" cy="{ly}" r="6" fill="#{color}" />\n'
                    f'<text x="{lx + legend_text_offset}" y="{ly + 3}" font-size="10" '
                    f'font-weight="bold" fill="#{text_color}">{day_name}:</text>\n'
                    f'<text x="{lx + legend_text_offset + 50}" y="{ly + 3}" font-size="10" '
                    f'fill="#{text_color}">{short_time} ({pct_val:.1f}%)</text>'
                )

        bubble_group = f'<g transform="translate({x_offset}, 0)">\n' + '\n'.join(elements) + '\n</g>'
        if not parse_boolean(hide_legend):
            legend_h = math.ceil(len(days) / legend_cols) * legend_line_height + legend_y_offset
            height += legend_h
        chart_svg_blocks = [bubble_group] + legend_items

    elif chart_type == 'donut':
        center_x = (chart_width + 48) / 2
        center_y = chart_top + chart_height + 30
        outer_radius = 80
        inner_radius = 40
        outer_label_radius = outer_radius + 16
        inner_label_radius1 = (outer_radius + inner_radius) / 2 - 8
        inner_label_radius2 = (outer_radius + inner_radius) / 2 + 4
        start_angle = 0.0
        elements = []
        defs = []

        for i, d in enumerate(days):
            seconds = d['grand_total']['total_seconds']
            if seconds == 0:
                continue
            pct = seconds / total_seconds if total_seconds > 0 else 0
            angle = pct * 2 * math.pi
            end_angle = start_angle + angle
            large_arc_flag = 1 if angle > math.pi else 0
            color = get_mixed_color(i)

            x1 = center_x + outer_radius * math.cos(start_angle)
            y1 = center_y + outer_radius * math.sin(start_angle)
            x2 = center_x + outer_radius * math.cos(end_angle)
            y2 = center_y + outer_radius * math.sin(end_angle)
            x3 = center_x + inner_radius * math.cos(end_angle)
            y3 = center_y + inner_radius * math.sin(end_angle)
            x4 = center_x + inner_radius * math.cos(start_angle)
            y4 = center_y + inner_radius * math.sin(start_angle)

            elements.append(
                f'<path d="M {x1} {y1} A {outer_radius} {outer_radius} 0 {large_arc_flag} 1 {x2} {y2} '
                f'L {x3} {y3} A {inner_radius} {inner_radius} 0 {large_arc_flag} 0 {x4} {y4} Z" '
                f'fill="#{color}" />'
            )

            day_name = get_safe_day_name(d['range']['date'])
            short_time = format_short_time(seconds)
            pct_text = f'{pct * 100:.1f}%'
            percentage = pct * 100

            if percentage >= 1:
                dx1 = center_x + outer_label_radius * math.cos(start_angle)
                dy1 = center_y + outer_label_radius * math.sin(start_angle)
                dx2 = center_x + outer_label_radius * math.cos(end_angle)
                dy2 = center_y + outer_label_radius * math.sin(end_angle)
                day_path_id = f'dayPath{i}'
                defs.append(
                    f'<path id="{day_path_id}" fill="none" d="M {dx1} {dy1} '
                    f'A {outer_label_radius} {outer_label_radius} 0 {large_arc_flag} 1 {dx2} {dy2}" />'
                )
                anchor = 'start' if percentage < 5 else 'middle'
                offset = '5%' if percentage < 5 else '50%'
                elements.append(
                    f'<text font-size="9" fill="#{text_color}">'
                    f'<textPath href="#{day_path_id}" startOffset="{offset}" '
                    f'text-anchor="{anchor}">{day_name}</textPath></text>'
                )

            min_label_angle = math.pi / 10
            if not parse_boolean(hide_time) and angle >= min_label_angle:
                t1x = center_x + inner_label_radius1 * math.cos(start_angle)
                t1y = center_y + inner_label_radius1 * math.sin(start_angle)
                t2x = center_x + inner_label_radius1 * math.cos(end_angle)
                t2y = center_y + inner_label_radius1 * math.sin(end_angle)
                time_path_id = f'timePath{i}'
                defs.append(
                    f'<path id="{time_path_id}" fill="none" d="M {t1x} {t1y} '
                    f'A {inner_label_radius1} {inner_label_radius1} 0 {large_arc_flag} 1 {t2x} {t2y}" />'
                )
                elements.append(
                    f'<text font-size="8" fill="#{text_color}">'
                    f'<textPath href="#{time_path_id}" startOffset="50%" '
                    f'text-anchor="middle">{short_time}</textPath></text>'
                )

            if not parse_boolean(hide_percentage) and angle >= min_label_angle:
                p1x = center_x + inner_label_radius2 * math.cos(start_angle)
                p1y = center_y + inner_label_radius2 * math.sin(start_angle)
                p2x = center_x + inner_label_radius2 * math.cos(end_angle)
                p2y = center_y + inner_label_radius2 * math.sin(end_angle)
                pct_path_id = f'pctPath{i}'
                defs.append(
                    f'<path id="{pct_path_id}" fill="none" d="M {p1x} {p1y} '
                    f'A {inner_label_radius2} {inner_label_radius2} 0 {large_arc_flag} 1 {p2x} {p2y}" />'
                )
                elements.append(
                    f'<text font-size="8" fill="#{text_color}">'
                    f'<textPath href="#{pct_path_id}" startOffset="50%" '
                    f'text-anchor="middle">{pct_text}</textPath></text>'
                )

            start_angle = end_angle

        height += 110
        if defs:
            elements.insert(0, f'<defs>{"".join(defs)}</defs>')
        chart_svg_blocks = elements

    elif chart_type == 'spiral':
        center_x = (chart_width + 34) / 2
        center_y = chart_top + chart_height + 60
        total_spiral_points = 360
        total_turns = 3
        angle_increment = (2 * math.pi * total_turns) / total_spiral_points
        scale_x = 1.3
        scale_y = 0.5
        base_radius = 30
        pin_height = 85

        spiral_path_points = []
        for i in range(total_spiral_points):
            angle = i * angle_increment
            radius = base_radius + 24 * angle / (2 * math.pi)
            x = center_x + radius * math.cos(angle) * scale_x
            y = center_y + radius * math.sin(angle) * scale_y
            spiral_path_points.append({'x': x, 'y': y})

        elements = []
        for i in range(len(spiral_path_points) - 1):
            p1 = spiral_path_points[i]
            p2 = spiral_path_points[i + 1]
            t = i / (len(spiral_path_points) - 1)
            dx = p2['x'] - p1['x']
            dy = p2['y'] - p1['y']
            angle = math.atan2(dy, dx)
            orientation = abs(math.sin(angle))
            stroke_w = 2 + 3 * t + 7.5 * orientation
            overshoot = 0.5
            dist = math.hypot(dx, dy)
            ux = dx / dist if dist > 0 else 0
            uy = dy / dist if dist > 0 else 0
            x1 = p1['x'] - ux * overshoot
            y1 = p1['y'] - uy * overshoot
            x2 = p2['x'] + ux * overshoot
            y2 = p2['y'] + uy * overshoot
            elements.append(
                f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'stroke="#{chart_color}" stroke-width="{stroke_w:.2f}" '
                f'stroke-linecap="round" stroke-opacity="1" />'
            )

        step_interval = round(total_spiral_points / (len(days) + 1))
        labels = []
        for i, d in enumerate(days):
            spiral_idx = i * step_interval
            if spiral_idx >= len(spiral_path_points):
                continue
            point = spiral_path_points[spiral_idx]
            x = point['x']
            y = point['y']
            if i == 2:
                x -= 19
                y += 1
            label_y = y - pin_height
            seconds = d['grand_total']['total_seconds']
            ratio = seconds / max_seconds if max_seconds > 0 else 0
            dot_radius = 1.8 + (5.2 - 1.8) * ratio
            use_lighten = is_dark_color(bg_color)
            adj_color = lighten_color if use_lighten else darken_color
            adjusted_color = adj_color(chart_color, 60)
            short_time = format_short_time(seconds)
            pct_str = f'{ratio * 100:.1f}%'
            day_name = get_safe_day_name(d['range']['date'])
            elements.append(
                f'<circle cx="{x}" cy="{y}" r="{dot_radius:.2f}" fill="#{adjusted_color}" />'
            )
            elements.append(
                f'<line x1="{x}" y1="{y}" x2="{x}" y2="{label_y}" '
                f'stroke="#{adjusted_color}" stroke-width="1.2" />'
            )
            label_parts = []
            if not parse_boolean(hide_time):
                label_parts.append(short_time)
            if not parse_boolean(hide_percentage):
                label_parts.append(pct_str)
            label_str = ' • '.join(label_parts)
            if label_parts:
                labels.append(
                    f'<text x="{x}" y="{label_y - 8}" font-size="9.5" text-anchor="middle" '
                    f'fill="#{text_color}">{day_name}</text>\n'
                    f'<text transform="rotate(-90, {x + 12}, {label_y + 12})" '
                    f'x="{x + 10}" y="{label_y + 10}" '
                    f'font-size="8.5" text-anchor="end" fill="#{text_color}">{label_str}</text>'
                )
            else:
                labels.append(
                    f'<text x="{x}" y="{label_y - 8}" font-size="9.5" text-anchor="middle" '
                    f'fill="#{text_color}">{day_name}</text>'
                )

        now_point = spiral_path_points[-1]
        now_x = now_point['x']
        now_y = now_point['y']
        now_label_y = now_y - pin_height
        now_ratio = total_seconds / (max_seconds * len(days)) if max_seconds > 0 and len(days) > 0 else 0
        now_radius = 1.8 + (5.2 - 1.8) * now_ratio
        use_lighten = is_dark_color(bg_color)
        adj_color = lighten_color if use_lighten else darken_color
        adjusted_color = adj_color(chart_color, 60)
        elements.append(
            f'<circle cx="{now_x}" cy="{now_y}" r="{now_radius:.2f}" fill="#{adjusted_color}" />'
        )
        elements.append(
            f'<line x1="{now_x}" y1="{now_y}" x2="{now_x}" y2="{now_label_y}" '
            f'stroke="#{adjusted_color}" stroke-width="1.2" />'
        )
        labels.append(
            f'<text x="{now_x}" y="{now_label_y - 8}" font-size="9.5" text-anchor="middle" '
            f'fill="#{text_color}">Now</text>'
        )

        spiral_bottom = spiral_path_points[-1]['y'] + 100
        height = max(height, spiral_bottom)
        chart_svg_blocks = [
            f'<g>{"\n".join(elements)}</g>',
            f'<g>{"\n".join(labels)}</g>',
        ]

    total_secs2 = sum(d['grand_total']['total_seconds'] for d in days)

    def format_full_time(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        hour_part = f'{h} hr{"s" if h != 1 else ""}' if h > 0 else ''
        minute_part = f'{m} min{"s" if m != 1 else ""}' if m > 0 else ''
        return ' '.join(filter(None, [hour_part, minute_part]))

    total_time_text = format_full_time(total_secs2)

    is_friendly = (
        heading_type == 'friendly'
        or (heading_type == 'custom' and custom_heading and len(custom_heading) > 26)
    )
    heading_font_size = 12 if is_friendly else 14

    x_center = (
        chart_width / 2 + 20
        if chart_type == 'radar'
        else left_padding / 2 + chart_width / 2 + 20
    )

    title = (
        f'<text x="{x_center}" y="{top_padding}" font-size="{heading_font_size}" '
        f'text-anchor="middle" fill="#{text_color}" font-weight="bold">{heading_text}</text>'
    ) if not parse_boolean(hide_title) else ''

    centered_total = (
        f'<text x="{x_center}" y="{height - 10}" font-size="12" text-anchor="middle" '
        f'fill="#{text_color}"><tspan font-weight="bold">Total:</tspan> {total_time_text}</text>'
    ) if not parse_boolean(hide_total) else ''

    return {
        'content': '\n'.join(filter(None, [title, '\n'.join(chart_svg_blocks), centered_total])),
        'height': height,
        'width': (
            max(chart_width, 300) + 48
            if chart_type == 'radar'
            else max(chart_width, 300) + 48 + left_padding
        ),
    }
