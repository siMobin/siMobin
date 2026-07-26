import math
import random

from cards.utils import hex_to_hsl, hsl_to_hex, waka_auth_header, safe_fetch_json


def shift_lightness(hex_str, amount):
    hsl = hex_to_hsl(hex_str)
    return hsl_to_hex(hsl['h'], hsl['s'], min(100, max(0, hsl['l'] + amount)))


def generate_palette(count):
    palette = []
    for i in range(count):
        hue = (i * 360) / count
        saturation = 75
        lightness = 55
        palette.append(hsl_to_hex(hue, saturation, lightness))
    for i in range(len(palette) - 1, 0, -1):
        j = int(random.random() * (i + 1))
        palette[i], palette[j] = palette[j], palette[i]
    return palette


def get_ai_agent_card(
    api_key,
    username,
    text_color='5f574f',
    title_color='ffff',
    bg_color='f8f6f3',
    font_family='Calibri',
    chart_color='9c8f80',
):
    text_color = text_color.replace('#', '')
    title_color = title_color.replace('#', '')
    bg_color = bg_color.replace('#', '')
    chart_color = chart_color.replace('#', '')
    api_key = api_key or ''
    if not api_key:
        raise ValueError('Missing WAKATIME_API_KEY')

    headers = waka_auth_header(api_key)
    url = f'https://wakatime.com/api/v1/users/{username}/stats/all_time'
    json = safe_fetch_json(url, headers=headers)
    data = json.get('data')

    if data:
        line_changes = data.get('ai_model_line_changes') or {}
        costs = data.get('ai_model_costs') or {}

        breakdown = data.get('ai_model_breakdown') or []
        if not line_changes and breakdown:
            for item in breakdown:
                name = item.get('name')
                line_changes[name] = item.get('lines', 0)
                costs[name] = costs.get(name, 0) + item.get('cost', 0)
    else:
        line_changes = {}
        costs = {}

    return build_ai_agent_svg(
        data={'ai_agent_line_changes': line_changes, 'ai_agent_costs': costs},
        text_color=text_color, title_color=title_color, bg_color=bg_color,
        font_family=font_family, chart_color=chart_color,
    )


def build_ai_agent_svg(data, text_color='5f574f', title_color='ffff', bg_color='f8f6f3', font_family='Calibri', chart_color='9c8f80'):
    text_color = text_color.replace('#', '')
    title_color = title_color.replace('#', '')
    bg_color = bg_color.replace('#', '')
    chart_color = chart_color.replace('#', '')

    line_changes = data.get('ai_agent_line_changes', {}) or {}
    costs = data.get('ai_agent_costs', {}) or {}

    agents = []
    for name, lines in line_changes.items():
        agents.append({'name': name, 'lines': lines, 'cost': costs.get(name, 0)})
    agents.sort(key=lambda a: -a['lines'])

    total_lines = sum(a['lines'] for a in agents)
    if total_lines == 0:
        return {'content': '<svg width="400" height="200" xmlns="http://www.w3.org/2000/svg"><text x="200" y="100" text-anchor="middle" fill="#999">No AI agent data</text></svg>', 'width': 400, 'height': 200}

    def fmt(n):
        abs_n = abs(n)
        if abs_n >= 1e9:
            return f'{n / 1e9:.1f}'.rstrip('0').rstrip('.') + 'B'
        if abs_n >= 1e6:
            return f'{n / 1e6:.1f}'.rstrip('0').rstrip('.') + 'M'
        if abs_n >= 1e3:
            return f'{n / 1e3:.1f}'.rstrip('0').rstrip('.') + 'K'
        return f'{n:,}'

    def fmt_cost(n):
        return f'${n:.2f}'

    chart_hsl = hex_to_hsl(chart_color)
    is_dark_chart = chart_hsl['l'] < 50

    palette = generate_palette(len(agents))

    donut_bg = shift_lightness(chart_color, 40) if is_dark_chart else shift_lightness(chart_color, -40)

    cx, cy, r = 200, 105, 55
    circ = 2 * math.pi * r

    cumulative = 0
    slices = []
    for i, agent in enumerate(agents):
        length = circ * (agent['lines'] / total_lines)
        slices.append({
            **agent,
            'color': palette[i],
            'dasharray': f'{length} {circ - length}',
            'dashoffset': -cumulative,
        })
        cumulative += length

    slices_svg = ''
    for s in slices:
        slices_svg += f'''
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#{s["color"]}" stroke-width="26"
      stroke-dasharray="{s["dasharray"]}"
      stroke-dashoffset="{s["dashoffset"]}"
      transform="rotate(-90 {cx} {cy})"
      stroke-linecap="butt" />'''

    donut = f'''
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#{donut_bg}" stroke-width="26" />
    {slices_svg}
    <text x="{cx}" y="{cy - 4}" text-anchor="middle" fill="#{text_color}" font-size="24" font-weight="bold" font-family="{font_family}">
      {fmt(total_lines)}
    </text>
    <text x="{cx}" y="{cy + 12}" text-anchor="middle" fill="#{text_color}" font-size="14" font-family="{font_family}">
      lines of code
    </text>'''

    legend_y = 190
    col_w = 200
    rows = []
    for i, agent in enumerate(agents):
        col = 0 if i < math.ceil(len(agents) / 2) else 1
        row = i if col == 0 else i - math.ceil(len(agents) / 2)
        x = col * col_w + 20
        y = legend_y + row * 24
        pct = f'{(agent["lines"] / total_lines * 100):.1f}'
        rows.append(f'''
      <rect x="{x}" y="{y - 10}" width="10" height="10" fill="#{palette[i % len(palette)]}" rx="2" />
      <text x="{x + 16}" y="{y}" fill="#{text_color}" font-size="12" font-family="{font_family}">
        <tspan font-weight="bold">{agent["name"]}</tspan> {fmt(agent["lines"])} lines ({pct}%) · {fmt_cost(agent["cost"])}
      </text>''')

    num_cols = 2
    rows_per_col = math.ceil(len(agents) / num_cols)
    height = legend_y + rows_per_col * 24 + 20

    content = f'''<svg width="400" height="{height}" viewBox="0 0 400 {height}" xmlns="http://www.w3.org/2000/svg">
  <text x="200" y="28" text-anchor="middle" fill="#{title_color}" font-size="16" font-weight="bold" font-family="{font_family}">AI Agents</text>
  {donut}
  {" ".join(rows)}
</svg>'''

    return {
        'content': content,
        'width': 400,
        'height': height,
    }
