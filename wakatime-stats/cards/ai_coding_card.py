from cards.utils import waka_auth_header, safe_fetch_json


def get_ai_coding_card(
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
    chart_color = chart_color.replace('#', '')
    bg_color = bg_color.replace('#', '')
    api_key = api_key or ''
    if not api_key:
        raise ValueError('Missing WAKATIME_API_KEY')

    headers = waka_auth_header(api_key)
    url = f'https://wakatime.com/api/v1/users/{username}/stats/all_time'
    json = safe_fetch_json(url, headers=headers)
    data = json.get('data')

    return build_ai_coding_svg(data=data, text_color=text_color, title_color=title_color, bg_color=bg_color, font_family=font_family, chart_color=chart_color)


def build_ai_coding_svg(data, text_color='5f574f', title_color='ffff', bg_color='f8f6f3', font_family='Calibri', chart_color='9c8f80'):
    text_color = text_color.replace('#', '')
    title_color = title_color.replace('#', '')
    chart_color = chart_color.replace('#', '')
    bg_color = bg_color.replace('#', '')

    ai_add = data.get('ai_additions', 0) or 0
    ai_del = data.get('ai_deletions', 0) or 0
    human_add = data.get('human_additions', 0) or 0
    human_del = data.get('human_deletions', 0) or 0

    ai_total = ai_add + ai_del
    human_total = human_add + human_del
    grand_total = ai_total + human_total
    ai_pct = (ai_total / grand_total * 100) if grand_total > 0 else 0

    input_tokens = data.get('ai_input_tokens', 0) or 0
    output_tokens = data.get('ai_output_tokens', 0) or 0
    total_cost = data.get('ai_model_total_cost', 0) or 0
    ai_sessions = data.get('ai_sessions', 0) or 0
    prompt_events = data.get('ai_prompt_events_total', 0) or 0

    def fmt(n):
        if n >= 1e9:
            return f'{n / 1e9:.1f}B'
        if n >= 1e6:
            return f'{n / 1e6:.1f}M'
        if n >= 1e3:
            return f'{n / 1e3:.1f}K'
        return str(int(n))

    def fmt_cost(n):
        return f'${n:.2f}'

    cx, cy, r = 200, 105, 55
    circ = 2 * 3.141592653589793 * r
    ai_dash = circ * (max(ai_pct, 2) / 100)

    donut = f'''
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#{chart_color}" stroke-width="26" opacity="0.2" />
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#{chart_color}" stroke-width="26"
      stroke-dasharray="{ai_dash} {circ}"
      stroke-dashoffset="{circ * 0.25}"
      transform="rotate(-90 {cx} {cy})"
      stroke-linecap="butt" />
    <text x="{cx}" y="{cy - 2}" text-anchor="middle" fill="#{text_color}" font-size="24" font-weight="bold" font-family="{font_family}">
      {ai_pct:.1f}%
    </text>
    <text x="{cx}" y="{cy + 14}" text-anchor="middle" fill="#{text_color}" font-size="14" font-family="{font_family}">
      AI-driven
    </text>'''

    lh = 24
    c1x, c2x = 25, 210
    rows1 = [
        {'label': 'AI Lines', 'value': f'+{fmt(ai_add)} / -{fmt(ai_del)}'},
        {'label': 'Human Lines', 'value': f'+{fmt(human_add)} / -{fmt(human_del)}'},
        {'label': 'Tokens In', 'value': fmt(input_tokens)},
        {'label': 'Tokens Out', 'value': fmt(output_tokens)},
    ]
    rows2 = [
        {'label': 'Cost', 'value': fmt_cost(total_cost)},
        {'label': 'Human Review', 'value': f'{fmt(ai_sessions)} sessions'},
        {'label': 'Human Follow-up', 'value': f'{fmt(prompt_events)} edits'},
    ]

    max_rows = max(len(rows1), len(rows2))
    start_y = 200
    lines = []

    for i in range(max_rows):
        y = start_y + i * lh
        if i < len(rows1):
            lines.append(f'<text x="{c1x}" y="{y}" fill="#{text_color}" font-size="13" font-family="{font_family}"><tspan font-weight="bold">{rows1[i]["label"]}:</tspan> {rows1[i]["value"]}</text>')
        if i < len(rows2):
            lines.append(f'<text x="{c2x}" y="{y}" fill="#{text_color}" font-size="13" font-family="{font_family}"><tspan font-weight="bold">{rows2[i]["label"]}:</tspan> {rows2[i]["value"]}</text>')

    height = start_y + max_rows * lh + 15

    content = f'''<svg width="400" height="{height}" viewBox="0 0 400 {height}" xmlns="http://www.w3.org/2000/svg">
  <text x="200" y="28" text-anchor="middle" fill="#{title_color}" font-size="16" font-weight="bold" font-family="{font_family}">AI Coding ({ai_pct:.1f}% AI-driven)</text>
  {donut}
  {chr(10).join(lines)}
</svg>'''

    return {
        'content': content,
        'width': 400,
        'height': height,
    }
