import requests
from cards.coding_activity_card import get_coding_activity_card
from cards.utils import waka_auth_header


def get_day_index(day_code):
    mapping = {'su': 0, 'mo': 1, 'tu': 2, 'we': 3, 'th': 4, 'fr': 5, 'sa': 6}
    return mapping.get(day_code.lower(), -1)


def reorder_days(days, start_day_code):
    target_index = get_day_index(start_day_code)
    if target_index < 0:
        return days

    def get_day(d):
        return get_day_index(d['range']['date'])

    def offset(day):
        return (get_day(day) - target_index + 7) % 7

    return sorted(days, key=offset)


def get_weekday_average_card(
    api_key=None,
    username='',
    text_color='',
    chart_color='',
    chart_type='bar',
    bg_color='',
    chart_curved_line=False,
    start_day=None,
    heading_type=None,
    mixed_colors=False,
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

    api_url = f'https://wakatime.com/api/v1/users/{username}/insights/weekdays?range=last_year'

    resp = requests.get(api_url, headers=waka_auth_header(api_key_val))
    json_data = resp.json()

    weekday_avg = json_data.get('data', {}).get('weekdays')

    if not weekday_avg:
        raise ValueError('No weekday average insight data available.')

    weekday_to_code = {
        'sunday': 'su',
        'monday': 'mo',
        'tuesday': 'tu',
        'wednesday': 'we',
        'thursday': 'th',
        'friday': 'fr',
        'saturday': 'sa'
    }

    days = []
    for d in weekday_avg:
        code = weekday_to_code.get(d['name'].lower(), d['name'])
        days.append({
            'range': {'date': code},
            'grand_total': {
                'total_seconds': d['average'],
                'text': d['human_readable_average']
            }
        })

    if start_day and start_day != '-7':
        days = reorder_days(days, start_day)

    total_seconds = sum(d['grand_total']['total_seconds'] for d in days)
    max_seconds = max(d['grand_total']['total_seconds'] for d in days)

    heading_text = 'Average Weekly Coding Time'
    if heading_type == 'friendly':
        max_day = max(days, key=lambda d: d['grand_total']['total_seconds'])
        readable = {
            'su': 'Sunday', 'mo': 'Monday', 'tu': 'Tuesday', 'we': 'Wednesday',
            'th': 'Thursday', 'fr': 'Friday', 'sa': 'Saturday'
        }
        day_name = readable.get(max_day['range']['date'], max_day['range']['date'])
        heading_text = f"I'm most productive on {day_name}s"

    return get_coding_activity_card(
        api_key=api_key,
        username=username,
        text_color=text_color,
        chart_color=chart_color,
        chart_type=chart_type,
        bg_color=bg_color,
        chart_curved_line=chart_curved_line,
        start_day=start_day,
        heading_type='custom',
        custom_heading=heading_text,
        mixed_colors=mixed_colors,
        hide_legend=hide_legend,
        hide_total=hide_total,
        hide_time=hide_time,
        hide_percentage=hide_percentage,
        hide_title=hide_title,
        y_axis=y_axis,
        y_axis_label=y_axis_label,
        custom_days=days,
    )
