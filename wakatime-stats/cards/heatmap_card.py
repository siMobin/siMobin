from datetime import datetime, timedelta
import requests
from cards.utils import waka_auth_header


def get_heatmap_card(
    api_key=None,
    github_token=None,
    default_source=None,
    username=None,
    font_family='Arial',
    heatmap_color='4ade80',
    start_day='mo',
    text_color='ccc',
    hide_title=None,
    heading_type='standard',
):
    heatmap_color = heatmap_color.replace('#', '')
    text_color = text_color.replace('#', '')
    has_github = bool(github_token)
    source_pref = (default_source or ('combo' if has_github else 'waka')).lower()
    if not has_github:
        source_pref = 'waka'
    wants_combo = source_pref == 'combo' or (source_pref == 'github' and has_github and api_key)
    today = datetime.utcnow()
    by_date = {}
    github_by_date = {}
    waka_by_date = {}

    if has_github:
        try:
            from_dt = today - timedelta(days=365)
            query = '''
                query heatmap($login:String!, $from:DateTime!, $to:DateTime!) {
                  user(login:$login) {
                    contributionsCollection(from:$from, to:$to) {
                      contributionCalendar {
                        weeks {
                          contributionDays {
                            date
                            contributionCount
                          }
                        }
                      }
                    }
                  }
                }
            '''
            res = requests.post(
                'https://api.github.com/graphql',
                json={
                    'query': query,
                    'variables': {
                        'login': username,
                        'from': from_dt.isoformat(),
                        'to': today.isoformat(),
                    },
                },
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {github_token}',
                },
            )
            json_data = res.json()
            if json_data.get('errors'):
                raise Exception('; '.join(e['message'] for e in json_data['errors']))
            weeks = (
                json_data.get('data', {})
                .get('user', {})
                .get('contributionsCollection', {})
                .get('contributionCalendar', {})
                .get('weeks') or []
            )
            for week in weeks:
                for day in (week.get('contributionDays') or []):
                    if day.get('date'):
                        github_by_date[day['date']] = day.get('contributionCount', 0) or 0
        except Exception as e:
            print(f'GitHub heatmap fetch failed: {e}')

    if not has_github or wants_combo or source_pref == 'waka' or len(github_by_date) == 0:
        if not api_key and (source_pref != 'github' or wants_combo or len(github_by_date) == 0):
            raise Exception('Missing WAKATIME_API_KEY')
        resp = requests.get(
            'https://wakatime.com/api/v1/users/current/insights/days/last_year',
            headers=waka_auth_header(api_key),
        )
        json_data = resp.json()
        if not resp.ok or not (json_data.get('data') or {}).get('days'):
            raise Exception(f"WakaTime API error: {json_data.get('error', 'Invalid response')}")
        days = json_data['data']['days']
        for day in days:
            if day.get('date') and isinstance(day.get('total'), (int, float)):
                waka_by_date[day['date']] = day['total']

    if wants_combo and len(github_by_date) > 0 and len(waka_by_date) > 0:
        all_dates = set(github_by_date.keys()) | set(waka_by_date.keys())
        for d in all_dates:
            by_date[d] = max(github_by_date.get(d, 0) or 0, waka_by_date.get(d, 0) or 0)
    elif source_pref == 'github' and len(github_by_date) > 0:
        by_date.update(github_by_date)
    else:
        by_date.update(waka_by_date if len(waka_by_date) > 0 else github_by_date)

    totals_by_month = [0] * 12
    for date_str, total in by_date.items():
        month = datetime.strptime(date_str[:10], '%Y-%m-%d').month - 1
        totals_by_month[month] += total
    max_month_index = totals_by_month.index(max(totals_by_month))
    month_name = datetime(2000, max_month_index + 1, 1).strftime('%B')

    if heading_type == 'friendly':
        heading_text = f'This year, my most productive month was {month_name}'
    elif wants_combo:
        heading_text = 'COMBINED ACTIVITY LAST YEAR'
    elif has_github:
        heading_text = 'GITHUB ACTIVITY LAST YEAR'
    else:
        heading_text = 'ACTIVITY LAST YEAR'

    start_from_sunday = start_day == 'su'
    cell_size = 10
    cell_gap = 2
    top_padding = 50
    left_padding = 40

    days_arr = []
    for i in range(364, -1, -1):
        d = today - timedelta(days=i)
        days_arr.append(d)

    grid_rects = ''
    month_labels = {}
    max_val = max(by_date.values()) if by_date else 1

    for i, d in enumerate(days_arr):
        key = d.strftime('%Y-%m-%d')
        day_of_week = d.weekday()
        if start_from_sunday:
            weekday = (day_of_week + 1) % 7
        else:
            weekday = day_of_week
        week = i // 7
        x = week * (cell_size + cell_gap)
        y = weekday * (cell_size + cell_gap)
        secs = by_date.get(key, 0) or 0
        opacity = min((secs / max_val) * 0.9 + 0.1, 1.0) if max_val > 0 else 0.1
        grid_rects += (
            f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
            f'rx="2" ry="2" fill="#{heatmap_color}" fill-opacity="{opacity:.2f}" '
            f'stroke="#{text_color}" stroke-width="0.5" />\n'
        )
        month = d.month
        if month not in month_labels or d.day == 1:
            month_labels[month] = x

    month_label_els = '\n'.join(
        f'<text x="{x}" y="-6" font-size="10" fill="#{text_color}" '
        f'font-family="{font_family}">{datetime(2000, int(m), 1).strftime("%b")}</text>'
        for m, x in month_labels.items()
    )

    if start_from_sunday:
        day_labels = ['Sun', 'Tue', 'Thu']
        day_indexes = [0, 2, 4]
    else:
        day_labels = ['Mon', 'Wed', 'Fri']
        day_indexes = [0, 2, 4]

    day_label_els = '\n'.join(
        f'<text x="-6" y="{i * (cell_size + cell_gap) + cell_size / 2}" font-size="10" '
        f'text-anchor="end" alignment-baseline="middle" fill="#{text_color}" '
        f'font-family="{font_family}">{day_labels[idx // 2]}</text>'
        for idx, i in enumerate(day_indexes)
    )

    grid_height = 7 * (cell_size + cell_gap)
    grid_width = 53 * (cell_size + cell_gap)
    width = grid_width + left_padding + 20
    height = top_padding + grid_height + 40

    if hide_title:
        title = ''
    else:
        title = (
            f'<text x="{left_padding}" y="18" font-size="14" fill="#{text_color}" '
            f'font-family="{font_family}" font-weight="bold">{heading_text}</text>'
        )

    legend_swatches = '\n'.join(
        f'<rect x="{grid_width - 145 + 30 + i * 12}" y="{grid_height + 6}" '
        f'width="10" height="10" rx="2" ry="2" fill="#{heatmap_color}" fill-opacity="{o}"/>'
        for i, o in enumerate([0.1, 0.3, 0.5, 0.7, 0.9, 1.0])
    )

    return {
        'width': width,
        'height': height,
        'content': f'''
      {title}
      <g transform="translate({left_padding}, {top_padding})">
        {month_label_els}
        {day_label_els}
        {grid_rects}
        <text x="{grid_width - 145}" y="{grid_height + 14}" font-size="10" fill="#{text_color}" font-family="{font_family}">Less</text>
        {legend_swatches}
        <text x="{grid_width - 38}" y="{grid_height + 14}" font-size="10" fill="#{text_color}" font-family="{font_family}">More</text>
      </g>
    ''',
    }
