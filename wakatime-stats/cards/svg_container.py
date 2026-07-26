import os
import json
import re
from pathlib import Path


def hex_to_svg_fill(hex_str):
    if len(hex_str) == 8:
        alpha = int(hex_str[6:8], 16)
        if alpha == 0:
            return {'fill': 'none'}
        return {'fill': f'#{hex_str[:6]}', 'fill-opacity': f'{alpha / 255:.2f}'}
    return {'fill': f'#{hex_str}'}


def hex_to_svg_stroke(hex_str):
    if len(hex_str) == 8:
        alpha = int(hex_str[6:8], 16)
        if alpha == 0:
            return {'stroke': 'none'}
        return {'stroke': f'#{hex_str[:6]}', 'stroke-opacity': f'{alpha / 255:.2f}'}
    return {'stroke': f'#{hex_str}'} if hex_str else {'stroke': 'none'}


def load_logo(logo_color, static_dir):
    logo_path = os.path.join(static_dir, 'wakatime.svg')
    if not os.path.exists(logo_path):
        return ''
    with open(logo_path, 'r', encoding='utf-8') as f:
        raw = f.read()
    inner = re.sub(r'<\?xml[^>]*>', '', raw)
    inner = re.sub(r'<!DOCTYPE[^>]*>', '', inner)
    inner = re.sub(r'<svg[^>]*>', '', inner)
    inner = inner.replace('</svg>', '')
    return f'<g transform="translate(20,12.5) scale(0.075)" style="color:#{logo_color}">{inner}</g>'


def load_theme(theme_name, static_dir):
    themes_path = os.path.join(static_dir, 'color_themes.json')
    if not os.path.exists(themes_path):
        return {}
    with open(themes_path, 'r', encoding='utf-8') as f:
        themes = json.load(f)
    selected = next((t for t in themes if t['theme_name'] == theme_name.lower()), None)
    if selected:
        return {
            'bg_color': selected['bg_color'],
            'text_color': selected['text_color'],
            'border_color': selected['border_color'],
            'title_color': selected['title_color'],
            'chart_color': selected['chart_color'],
            'rank_color': selected['rank_color'],
            'logo_color': selected['logo_color'],
            'heatmap_color': selected['heatmap_color']
        }
    return {}


def svg_container(bg_color='ffffff', border_color='333333', border_width=1, border_radius=4,
                  font_family='Calibri', show_header=True, show_logo=True, logo_color='000000',
                  title_color='333333', title_prefix='', components=None, scale=False,
                  title_scale_value=None, component_scale_values=None, static_dir='static'):
    if components is None:
        components = []
    if component_scale_values is None:
        component_scale_values = {}

    spacing = 20
    base_title_height = 40
    svg_tag_regex = re.compile(r'^<svg[^>]*>|<\/svg>$')
    header_visible = show_header
    logo_visible = header_visible and show_logo

    logoSvg = ''
    if logo_visible:
        logoSvg = load_logo(logo_color, static_dir)

    component_widths = [c.get('width', 0) for c in components]
    svg_effective_width = max(component_widths + [350])

    title_text = f"{title_prefix or ''} Stats".strip()

    logo_scale = 0.075
    group_x = 20
    group_y = 20
    logo_width = 400
    logo_height = 400
    scaled_logo_height = logo_height * logo_scale
    text_font_size = 16
    text_y = logo_height * logo_scale / 2

    effective_title_scale = title_scale_value * (svg_effective_width / 350) if isinstance(title_scale_value, (int, float)) else 1

    logo_inner = ''
    if logo_visible and logoSvg:
        logo_inner = re.sub(r'^<g[^>]*>|<\/g>$', '', logoSvg)

    scaled_title_block = ''
    if header_visible:
        logo_part = ''
        if logo_visible and logo_inner:
            logo_part = f'<g transform="scale({logo_scale})" style="color:#{logo_color}">{logo_inner}</g>'
        scaled_title_block = f'''
    <g transform="translate({group_x}, {group_y}) scale({effective_title_scale})">
      {logo_part}
      <text x="{logo_width * logo_scale}" y="{text_y}" fill="#{title_color}" font-size="{text_font_size}" font-family="{font_family}">
        {title_text}
      </text>
    </g>'''

    title_height = base_title_height * title_scale_value if isinstance(title_scale_value, (int, float)) else 0
    if not header_visible:
        title_height = 0

    scaled_components = []
    for idx, c in enumerate(components):
        original_width = c.get('width', 0) or 0
        has_custom = idx in component_scale_values
        user_scale = component_scale_values.get(idx, 1)
        if has_custom:
            final_scale = user_scale
        elif scale and original_width > 0:
            final_scale = svg_effective_width / original_width
        else:
            final_scale = 1
        scaled_components.append({
            **c,
            'originalWidth': original_width,
            'finalScale': final_scale,
            'scaledWidth': original_width * final_scale
        })

    title_padding_bottom = 10
    current_y = title_height + (spacing + title_padding_bottom if header_visible else title_padding_bottom)

    wrapped_components = []
    for c in scaled_components:
        content = c['content']
        cleaned = re.sub(svg_tag_regex, '', content).strip()
        height = c.get('height', 0)
        original_width = c['originalWidth']
        final_scale = c['finalScale']
        comp_type = c.get('type', '')
        scaled_width = original_width * final_scale
        offset_x = 0 if comp_type == 'basic' else (svg_effective_width - scaled_width) / 2
        block = f'<g transform="translate({offset_x}, {current_y}) scale({final_scale})">\n      {cleaned}\n    </g>'
        current_y += height * final_scale + spacing
        wrapped_components.append(block)

    bg_fill = hex_to_svg_fill(bg_color)
    border_stroke = hex_to_svg_stroke(border_color if border_width > 0 else '')

    total_height = current_y

    rect_attrs = ' '.join(f'{k}="{v}"' for k, v in {**bg_fill, **border_stroke}.items())
    border_stroke_width = f' stroke-width="{border_width}"' if border_stroke.get('stroke', 'none') != 'none' else ''

    svg = f'''<svg width="{svg_effective_width}" height="{total_height}" xmlns="http://www.w3.org/2000/svg" style="font-family:{font_family},sans-serif;">
  <rect
    x="{border_width / 2}"
    y="{border_width / 2}"
    width="{svg_effective_width - border_width}"
    height="{total_height - border_width}"
    {rect_attrs}
    {border_stroke_width}
    rx="{border_radius}"
    ry="{border_radius}"
  />
  {scaled_title_block}
  {chr(10).join(wrapped_components)}
</svg>'''
    return svg
