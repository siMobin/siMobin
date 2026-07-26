import math
import requests

from cards.utils import (
    format_short_time,
    hex_to_rgb,
    rgb_to_hex,
    is_dark_color,
    darken_color,
    lighten_color,
    vary_color,
    generate_y_axis_elements,
    truncate_label,
    waka_auth_header,
    safe_fetch_json,
    parse_boolean,
    parse_number,
)


def split_label_two_lines(name, line_length=8):
    first = name[:line_length]
    second = name[line_length:line_length * 2] if len(name) > line_length else ''
    return first, second


def simple_pack(data, width, height, padding=2):
    total = sum(d['value'] for d in data)
    cx, cy = width / 2, height / 2
    angle = 0
    leaves = []
    for i, d in enumerate(sorted(data, key=lambda x: -x['value'])):
        r = math.sqrt(d['value'] / total) * min(width, height) / 2
        if i == 0:
            x, y = cx, cy
        else:
            angle += 0.5 + 1 / (i + 1)
            dist = (i * min(width, height)) / (len(data) * 2)
            x = cx + dist * math.cos(angle)
            y = cy + dist * math.sin(angle)
        leaves.append({'x': x, 'y': y, 'r': max(r, 5), 'data': d})
    return leaves


def get_alltime_projects_card(
    api_key,
    username,
    text_color='5f574f',
    font_family='Calibri',
    chart_color='9c8f80',
    chart_type='bar',
    bg_color='f8f6f3',
    chart_curved_line=False,
    heading_type='normal',
    mixed_colors=False,
    num_projs=5,
    hide_legend=False,
    hide_total=False,
    hide_time=False,
    hide_percentage=False,
    hide_title=False,
    y_axis=False,
    y_axis_label=False,
):
    chart_color = chart_color.replace('#', '')
    text_color = text_color.replace('#', '')
    api_key = api_key or ''
    if not api_key:
        raise ValueError('Missing WAKATIME_API_KEY')

    headers = waka_auth_header(api_key)
    url = f'https://wakatime.com/api/v1/users/{username}/stats/all_time'
    json = safe_fetch_json(url, headers=headers)
    data = json.get('data')
    if not data or not data.get('projects'):
        raise ValueError('No all-time project data available.')

    num_projs = parse_number(num_projs, 5)
    top_projects = sorted(data['projects'], key=lambda x: -x['total_seconds'])[:num_projs]

    total_seconds = sum(p['total_seconds'] for p in top_projects)
    max_seconds = max(p['total_seconds'] for p in top_projects) if top_projects else 0

    if heading_type == 'friendly':
        top_proj = top_projects[0]['name'] if top_projects else 'Unknown'
        heading_text = f'I mostly code for {top_proj}'
    else:
        heading_text = 'My Top Projects'

    has_y_axis = parse_boolean(y_axis, False) and chart_type in ('bar', 'line', 'area')
    has_y_axis_label = parse_boolean(y_axis_label, False) and chart_type in ('bar', 'line', 'area')
    left_padding = 70 if (has_y_axis or has_y_axis_label) else 0
    left_padding_no_y = 30 if (not has_y_axis and not has_y_axis_label) else 0
    top_padding = 22.5
    bar_width = 30
    spacing = 15
    title_height = 0 if parse_boolean(hide_title, False) else 14
    chart_top = top_padding + title_height + 10
    chart_height = 60
    chart_bottom = 60
    chart_base = chart_top + chart_height
    radar_padding = 110
    bubble_padding = 35
    height = chart_base + chart_bottom
    chart_width = len(top_projects) * (bar_width + spacing)

    if chart_type == 'bar':
        height += 10
    if chart_type == 'bar_vertical':
        chart_width += 110
    if chart_type == 'bubble':
        height -= bubble_padding
        chart_width += 70
    if chart_type == 'radar':
        height += radar_padding
        chart_width += 40

    def get_mixed_color(index):
        use_lighten = is_dark_color(bg_color)
        adjust_color = lighten_color if use_lighten else darken_color
        if mixed_colors and index > 0:
            return adjust_color(chart_color, 20 + index * 10)
        return chart_color

    chart_svg_blocks = []

    if chart_type == 'bar':
        bar_blocks = []
        for i, proj in enumerate(top_projects):
            seconds = proj['total_seconds']
            pct = f'{(seconds / total_seconds * 100):.1f}' if total_seconds else '0.0'
            bar_h = (seconds / max_seconds) * chart_height if max_seconds else 0
            if bar_h == 0 and seconds == 0:
                bar_h = 1.5
            x = i * (bar_width + spacing) + left_padding + left_padding_no_y
            y = chart_base - bar_h
            fill = get_mixed_color(i)
            short_time = format_short_time(seconds)
            blocks = []
            blocks.append(f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_h}" fill="#{fill}" rx="3" ry="3" />')
            if not parse_boolean(hide_time, False):
                blocks.append(f'<text x="{x + bar_width / 2}" y="{y - 4}" font-size="9" text-anchor="middle" fill="#{text_color}">{short_time}</text>')
            line1, line2 = split_label_two_lines(proj['name'], 6)
            blocks.append(f'<text font-family="{font_family}" x="{x + bar_width / 2}" y="{chart_base + 10}" font-weight="bold" font-size="9" text-anchor="middle" fill="#{text_color}">{line1}</text>')
            if line2:
                blocks.append(f'<text font-family="{font_family}" x="{x + bar_width / 2}" y="{chart_base + 20}" font-weight="bold" font-size="9" text-anchor="middle" fill="#{text_color}">{line2}</text>')
            if not parse_boolean(hide_percentage, False):
                blocks.append(f'<text font-family="{font_family}" x="{x + bar_width / 2}" y="{chart_base + 34}" font-size="9" text-anchor="middle" fill="#{text_color}">{pct}%</text>')
            bar_blocks.append('\n'.join(blocks))
        y_axis_elements = []
        if has_y_axis:
            y_axis_elements = generate_y_axis_elements(max_seconds, chart_top, chart_base, chart_height, text_color, chart_width, chart_type, y_axis_label, left_padding)
        chart_svg_blocks = y_axis_elements + bar_blocks

    elif chart_type == 'bar_vertical':
        row_height = 24
        bar_max_width = chart_width - left_padding - 160
        bar_blocks = []
        for i, proj in enumerate(top_projects):
            seconds = proj['total_seconds']
            pct = f'{(seconds / total_seconds * 100):.1f}' if total_seconds else '0.0'
            bar_w = (seconds / max_seconds) * bar_max_width if max_seconds else 0
            y = chart_top + i * row_height
            fill = get_mixed_color(i)
            short_time = format_short_time(seconds)
            blocks = []
            blocks.append(f'<text font-family="{font_family}" x="{130 + left_padding - 8}" y="{y + 9}" font-size="10" text-anchor="end" fill="#{text_color}">{truncate_label(proj["name"], 20)}</text>')
            blocks.append(f'<rect x="{130 + left_padding}" y="{y}" width="{bar_w}" height="12" fill="#{fill}" rx="2" ry="2" />')
            hide_t = parse_boolean(hide_time, False)
            hide_p = parse_boolean(hide_percentage, False)
            if not hide_t and hide_p:
                blocks.append(f'<text font-family="{font_family}" x="{130 + left_padding + bar_w + 6}" y="{y + 9}" font-size="9" fill="#{text_color}">{short_time}</text>')
            if not hide_t and not hide_p:
                blocks.append(f'<text font-family="{font_family}" x="{130 + left_padding + bar_w + 6}" y="{y + 9}" font-size="9" fill="#{text_color}">{short_time}    |    {pct}%</text>')
            if hide_t and not hide_p:
                blocks.append(f'<text font-family="{font_family}" x="{130 + left_padding + bar_w + 6}" y="{y + 9}" font-size="9" fill="#{text_color}">{pct}%</text>')
            bar_blocks.append('\n'.join(blocks))
        height = len(top_projects) * row_height + chart_top + 30
        chart_svg_blocks = bar_blocks

    elif chart_type == 'radar':
        cx = (chart_width + 48) / 2
        cy = chart_top + chart_height / 2 + radar_padding / 1.4
        radius = min(chart_height, chart_width) / 0.7
        angle_step = 2 * math.pi / len(top_projects)
        use_lighten = is_dark_color(bg_color)
        adjust_color = darken_color if use_lighten else lighten_color
        adjusted_color = adjust_color(text_color, 120)

        points = []
        for i, proj in enumerate(top_projects):
            angle = i * angle_step - math.pi / 2
            seconds = proj['total_seconds']
            pct = f'{(seconds / total_seconds * 100):.1f}' if total_seconds else '0.0'
            r = (seconds / max_seconds) * radius if max_seconds else 0
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append({'x': x, 'y': y, 'angle': angle, 'seconds': seconds, 'label': truncate_label(proj['name'], 20), 'pct': pct})

        grid = []
        levels = 4
        for lvl in range(1, levels + 1):
            r = (lvl / levels) * radius
            path = []
            for j in range(len(top_projects)):
                a = j * angle_step - math.pi / 2
                x = cx + r * math.cos(a)
                y = cy + r * math.sin(a)
                path.append(f'{"M" if j == 0 else "L"} {x} {y}')
            grid.append(f'<path d="{" ".join(path)} Z" fill="none" stroke="#{adjusted_color}" stroke-dasharray="2,2" stroke-width="0.5"/>')

        axis_lines = []
        for j in range(len(top_projects)):
            a = j * angle_step - math.pi / 2
            x = cx + radius * math.cos(a)
            y = cy + radius * math.sin(a)
            axis_lines.append(f'<line x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="#{adjusted_color}" stroke-width="0.5"/>')

        labels = []
        for i, proj in enumerate(top_projects):
            a = i * angle_step - math.pi / 2
            label_dist = radius + 20
            x = cx + label_dist * math.cos(a)
            y = cy + label_dist * math.sin(a)
            labels.append(f'<text font-family="{font_family}" x="{x}" y="{y}" font-size="10" text-anchor="middle" alignment-baseline="middle" fill="#{text_color}">{truncate_label(proj["name"], 6)}</text>')

        radar_y_axis = []
        if parse_boolean(y_axis, False):
            angle = math.pi / 14
            label_angle_deg = 77
            for i in range(5):
                val = (max_seconds / 4) * i
                r = (val / max_seconds) * radius if max_seconds else 0
                x = cx + r * math.cos(angle)
                y = cy + r * math.sin(angle)
                radar_y_axis.append(f'<circle cx="{x}" cy="{y}" r="0.8" fill="#{text_color}"/>')
                if y_axis_label or i == 0 or i == 4:
                    if i == 0:
                        continue
                    label = format_short_time(val)
                    label_y_offset = 18 + r * 0.05
                    label_y = y - label_y_offset
                    label_x = x - 2
                    radar_y_axis.append(f'<text font-family="{font_family}" x="{label_x}" y="{label_y}" font-size="8" text-anchor="start" transform="rotate({label_angle_deg}, {label_x}, {label_y})" fill="#{text_color}">{label}</text>')

        legend_y_offset = 80
        legend_line_height = 24
        legend_cols = 2
        legend_col_width = 220
        center_offset_x = ((chart_width + 70) - legend_cols * legend_col_width) / 2

        all_pill_texts = []
        for proj in top_projects:
            t = format_short_time(proj['total_seconds'])
            p = f'{((proj["total_seconds"] / total_seconds) * 100):.1f}%' if total_seconds else '0.0%'
            all_pill_texts.append(f'{t} ({p})')
        max_pill_text = max(all_pill_texts, key=len) if all_pill_texts else ''
        uniform_pill_width = len(max_pill_text) * 5 + 8

        legend_items = []
        if not parse_boolean(hide_legend, False):
            for i, proj in enumerate(top_projects):
                short_time = format_short_time(proj['total_seconds'])
                pct_val = f'{((proj["total_seconds"] / total_seconds) * 100):.1f}%' if total_seconds else '0.0%'
                label = truncate_label(proj['name'], 20)
                x = center_offset_x + (i % legend_cols) * legend_col_width
                y = chart_base + radar_padding + legend_y_offset + (i // legend_cols) * legend_line_height
                pill_text = f'{short_time} ({pct_val})'
                pill_x = x + 125
                ratio = proj['total_seconds'] / max_seconds if max_seconds else 0
                opacity = f'{(0.1 + 0.6 * ratio):.2f}'
                legend_items.append(f'<text font-family="{font_family}" x="{x}" y="{y}" font-size="10" font-weight="bold" fill="#{text_color}">{label}:</text>')
                legend_items.append(f'<rect x="{pill_x}" y="{y - 10}" width="{uniform_pill_width}" height="14" fill="#{chart_color}" fill-opacity="{opacity}" />')
                legend_items.append(f'<text font-family="{font_family}" x="{pill_x + uniform_pill_width / 2}" y="{y + 1}" font-size="9" text-anchor="middle" fill="#{text_color}">{pill_text}</text>')

        legend_height = math.ceil(len(top_projects) / legend_cols) * legend_line_height + legend_y_offset
        if not parse_boolean(hide_legend, False):
            height = chart_base + radar_padding + legend_height + 20

        chart_svg_blocks = grid + axis_lines + [
            f'<polygon points="{" ".join(f"{p["x"]},{p["y"]}" for p in points)}" fill="#{chart_color}" fill-opacity="0.2" stroke="#{chart_color}" stroke-width="2"/>'
        ] + labels + radar_y_axis + legend_items

    elif chart_type == 'bubble':
        bubble_data = [{'value': p['total_seconds'], 'index': i} for i, p in enumerate(top_projects)]
        chart_size = max(chart_width, 240)
        leaves = simple_pack(bubble_data, chart_size, chart_size * 0.75)

        bubble_y_offset = 25
        for leaf in leaves:
            leaf['y'] += bubble_y_offset

        max_y = max(n['y'] + n['r'] for n in leaves) if leaves else 0
        actual_bubble_height = max_y
        max_bubble_chart_height = chart_base - chart_top + 220

        if actual_bubble_height > max_bubble_chart_height and leaves:
            scale_y = max_bubble_chart_height / actual_bubble_height
            for leaf in leaves:
                leaf['y'] = chart_top + (leaf['y'] - chart_top) * scale_y
                leaf['r'] *= scale_y

        height = max_y + 20

        min_x = min(n['x'] - n['r'] for n in leaves) if leaves else 0
        max_x = max(n['x'] + n['r'] for n in leaves) if leaves else 0
        bubble_width = max_x - min_x
        svg_center = (chart_width + 48) / 2
        bubble_center = min_x + bubble_width / 2
        x_offset = svg_center - bubble_center

        elements = []
        legend_items = []
        legend_cols = 2
        legend_col_width = 230
        legend_circle_offset = 12
        legend_text_offset = 24
        legend_y_offset_bubble = 40
        legend_line_height = 20
        center_offset_x_bubble = ((chart_width + 50) - legend_cols * legend_col_width) / 2

        for i, leaf in enumerate(leaves):
            proj_index = leaf['data']['index']
            proj = top_projects[proj_index]
            seconds = proj['total_seconds']
            pct = f'{(seconds / total_seconds * 100):.1f}' if total_seconds else '0.0'
            short_time = format_short_time(seconds)
            label = truncate_label(proj['name'], 20)
            color = vary_color(chart_color)
            elements.append(f'<circle cx="{leaf["x"]}" cy="{leaf["y"]}" r="{leaf["r"]}" fill="#{color}" fill-opacity="0.85" />')
            if not parse_boolean(hide_legend, False):
                x = center_offset_x_bubble + (i % legend_cols) * legend_col_width
                y = max_y + 30 + (i // legend_cols) * legend_line_height
                legend_items.append(f'<circle cx="{x + legend_circle_offset}" cy="{y}" r="6" fill="#{color}" />')
                legend_items.append(f'<text font-family="{font_family}" x="{x + legend_text_offset}" y="{y + 3}" font-size="10" font-weight="bold" fill="#{text_color}">{label}:</text>')
                legend_items.append(f'<text font-family="{font_family}" x="{x + legend_text_offset + 135}" y="{y + 3}" font-size="10" fill="#{text_color}">{short_time} ({pct}%)</text>')

        bubble_group = f'<g transform="translate({x_offset}, 0)">\n' + '\n'.join(elements) + '\n</g>'

        if not parse_boolean(hide_legend, False):
            legend_h = math.ceil(len(top_projects) / legend_cols) * legend_line_height + legend_y_offset_bubble
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
        min_label_angle = math.pi / 10
        label_padding = 0.08
        start_angle = 0

        elements = []
        defs_list = []
        hide_t = parse_boolean(hide_time, False)
        hide_p = parse_boolean(hide_percentage, False)

        for i, proj in enumerate(top_projects):
            seconds = proj['total_seconds']
            if seconds == 0:
                continue
            pct = seconds / total_seconds if total_seconds else 0
            pct_value = f'{pct * 100:.1f}'
            hide_outer_label = float(pct_value) < 5
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

            elements.append(f'<path d="M {x1} {y1} A {outer_radius} {outer_radius} 0 {large_arc_flag} 1 {x2} {y2} L {x3} {y3} A {inner_radius} {inner_radius} 0 {large_arc_flag} 0 {x4} {y4} Z" fill="#{color}" />')

            label = truncate_label(proj['name'], 20)
            short_time = format_short_time(seconds)
            pct_text = pct_value + '%'

            if not hide_outer_label:
                label_start = start_angle + label_padding
                label_end = end_angle - label_padding
                dx1 = center_x + outer_label_radius * math.cos(label_start)
                dy1 = center_y + outer_label_radius * math.sin(label_start)
                dx2 = center_x + outer_label_radius * math.cos(label_end)
                dy2 = center_y + outer_label_radius * math.sin(label_end)
                day_path_id = f'dayPath{i}'
                defs_list.append(f'<path id="{day_path_id}" fill="none" d="M {dx1} {dy1} A {outer_label_radius} {outer_label_radius} 0 {large_arc_flag} 1 {dx2} {dy2}" />')
                label_char_width = 5.5
                estimated_label_width = len(label) * label_char_width
                arc_length_estimate = outer_label_radius * (label_end - label_start)
                anchor = 'start' if estimated_label_width > arc_length_estimate else 'middle'
                start_offset = '2%' if anchor == 'start' else '50%'
                elements.append(f'<text font-family="{font_family}" font-size="9" fill="#{text_color}"><textPath font-family="{font_family}" href="#{day_path_id}" startOffset="{start_offset}" text-anchor="{anchor}">{label}</textPath></text>')

            if not hide_t and angle >= min_label_angle:
                t1x = center_x + inner_label_radius1 * math.cos(start_angle)
                t1y = center_y + inner_label_radius1 * math.sin(start_angle)
                t2x = center_x + inner_label_radius1 * math.cos(end_angle)
                t2y = center_y + inner_label_radius1 * math.sin(end_angle)
                time_path_id = f'timePath{i}'
                defs_list.append(f'<path id="{time_path_id}" fill="none" d="M {t1x} {t1y} A {inner_label_radius1} {inner_label_radius1} 0 {large_arc_flag} 1 {t2x} {t2y}" />')
                elements.append(f'<text font-family="{font_family}" font-size="8" fill="#{text_color}"><textPath font-family="{font_family}" href="#{time_path_id}" startOffset="50%" text-anchor="middle">{short_time}</textPath></text>')

            if not hide_p and angle >= min_label_angle:
                p1x = center_x + inner_label_radius2 * math.cos(start_angle)
                p1y = center_y + inner_label_radius2 * math.sin(start_angle)
                p2x = center_x + inner_label_radius2 * math.cos(end_angle)
                p2y = center_y + inner_label_radius2 * math.sin(end_angle)
                pct_path_id = f'pctPath{i}'
                defs_list.append(f'<path id="{pct_path_id}" fill="none" d="M {p1x} {p1y} A {inner_label_radius2} {inner_label_radius2} 0 {large_arc_flag} 1 {p2x} {p2y}" />')
                elements.append(f'<text font-family="{font_family}" font-size="8" fill="#{text_color}"><textPath font-family="{font_family}" href="#{pct_path_id}" startOffset="50%" text-anchor="middle">{pct_text}</textPath></text>')

            start_angle = end_angle

        height += 110

        if defs_list:
            elements.insert(0, f'<defs>{" ".join(defs_list)}</defs>')
        chart_svg_blocks = elements

    total_time_text = data.get('human_readable_total', '')

    is_friendly = heading_type == 'friendly'
    heading_font_size = 12 if is_friendly else 14

    x_center = chart_width / 2 + 20 if chart_type == 'radar' else left_padding / 2 + chart_width / 2 + 20

    title = ''
    if not parse_boolean(hide_title, False):
        title = f'<text font-family="{font_family}" x="{x_center}" y="{top_padding}" font-size="{heading_font_size}" text-anchor="middle" fill="#{text_color}" font-weight="bold">{heading_text}</text>'

    centered_total = ''
    if not parse_boolean(hide_total, False):
        centered_total = f'<text font-family="{font_family}" x="{x_center}" y="{height - 10}" font-size="12" text-anchor="middle" fill="#{text_color}"><tspan font-weight="bold">Total:</tspan> {total_time_text}</text>'

    content = '\n'.join([title] + chart_svg_blocks + [centered_total])

    if chart_type == 'radar':
        w = max(chart_width, 300) + 48
    else:
        w = max(chart_width, 300) + 48 + left_padding

    return {
        'content': content,
        'height': height,
        'width': w,
    }
