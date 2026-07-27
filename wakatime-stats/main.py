import os
import sys
from pathlib import Path
from inspect import signature
import argparse

from dotenv import load_dotenv

from cards.basic_stats_card import get_basic_stats_card
from cards.heatmap_card import get_heatmap_card
from cards.coding_activity_card import get_coding_activity_card
from cards.spedometer_card import get_spedometer_card
from cards.star_rank_card import get_star_rank_card
from cards.weekday_average_card import get_weekday_average_card
from cards.project_breakdown_card import get_project_breakdown_card
from cards.language_breakdown_card import get_language_breakdown_card
from cards.alltime_languages_card import get_alltime_languages_card
from cards.alltime_projects_card import get_alltime_projects_card
from cards.ai_coding_card import get_ai_coding_card
from cards.personal_info_card import get_personal_info_card
from cards.ai_agent_card import get_ai_agent_card
from cards.svg_container import svg_container, load_theme

load_dotenv()

BASE_DIR = Path(__file__).parent
STATIC_DIR = str(BASE_DIR / 'static')
OUTPUT_DIR = BASE_DIR / 'output'

WAKATIME_USERNAME = os.getenv('WAKATIME_USERNAME', '')
WAKATIME_API_KEY = os.getenv('WAKATIME_API_KEY', '')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')

DEFAULT_STYLES = {
    'bg_color': 'f8f6f3',
    'title_color': '2d2a26',
    'text_color': '5f574f',
    'logo_color': '7a7266',
    'border_color': 'dcd7ce',
    'border_width': 2,
    'border_radius': 10,
    'font_family': 'Calibri',
    'show_header': False,
    'show_logo': True,
    'title_prefix': '',
}

# Per-card extra options
CARD_EXTRA = {
    'basic': {
        'hide_daily_average': False,
        'hide_total_time': False,
        'hide_languages': False,
        'hide_projects': False,
        'hide_operating_systems': False,
        'hide_most_active_day': False,
    },
    'heatmap': {
        'heatmap_color': '9c8f80',
        'start_day': 'mo',
        'heading_type': 'friendly',
        'hide_title': False,
    },
    'weekly': {
        'chart_type': 'bar',
        'chart_color': '9c8f80',
        'chart_curved_line': True,
        'start_day': '-7',
        'heading_type': 'friendly',
        'custom_heading': '',
        'mixed_colors': False,
        'hide_legend': False,
        'hide_total': False,
        'hide_time': False,
        'hide_percentage': False,
        'hide_title': False,
        'y_axis': False,
        'y_axis_label': False,
        'custom_days': '',
    },
    'weekly_projs': {
        'chart_type': 'bar',
        'chart_color': '9c8f80',
        'chart_curved_line': True,
        'start_day': '-7',
        'heading_type': 'friendly',
        'hide_legend': False,
        'hide_total': False,
        'hide_time': True,
        'hide_percentage': True,
        'hide_title': False,
        'y_axis': False,
        'y_axis_label': False,
    },
    'weekly_langs': {
        'chart_type': 'bar',
        'chart_color': '9c8f80',
        'chart_curved_line': True,
        'start_day': '-7',
        'heading_type': 'friendly',
        'hide_legend': False,
        'hide_total': False,
        'hide_time': True,
        'hide_percentage': True,
        'hide_title': False,
        'y_axis': False,
        'y_axis_label': False,
    },
    'weekly_avg': {
        'chart_type': 'bar',
        'chart_color': '9c8f80',
        'chart_curved_line': True,
        'start_day': 'mo',
        'heading_type': 'friendly',
        'mixed_colors': False,
        'hide_legend': False,
        'hide_total': False,
        'hide_time': False,
        'hide_percentage': False,
        'hide_title': False,
        'y_axis': False,
        'y_axis_label': False,
    },
    'all_langs': {
        'chart_type': 'bar_vertical',
        'chart_color': '9c8f80',
        'chart_curved_line': True,
        'heading_type': 'friendly',
        'mixed_colors': False,
        'num_langs': '10',
        'hide_legend': False,
        'hide_total': False,
        'hide_time': False,
        'hide_percentage': False,
        'hide_title': False,
        'y_axis': False,
        'y_axis_label': False,
    },
    'all_projs': {
        'chart_type': 'bar_vertical',
        'chart_color': '9c8f80',
        'chart_curved_line': True,
        'heading_type': 'friendly',
        'mixed_colors': False,
        'num_projs': '10',
        'hide_legend': False,
        'hide_total': False,
        'hide_time': False,
        'hide_percentage': False,
        'hide_title': False,
        'y_axis': False,
        'y_axis_label': False,
    },
    'ai_coding': {
        'chart_color': '9c8f80',
    },
    'personal_info': {},
    'ai_agent': {
        'chart_color': '9c8f80',
    },
    'spedometer': {
        'difficulty': 'medium',
        'label_type': 'standard',
        'chart_color': '9c8f80',
        'custom_emojis': '',
        'show_high_score': True,
    },
    'rank': {
        'rank_color': '9c8f80',
        'hide_title': False,
        'show_icons': True,
    },
}


def filter_kwargs(func, kwargs):
    sig = signature(func)
    valid = set(sig.parameters.keys())
    return {k: v for k, v in kwargs.items() if k in valid}


def generate_card(name, card_type, card_func, extra_opts=None):
    print(f'  Generating {name} ({card_type})...')
    opts = {
        'api_key': WAKATIME_API_KEY,
        'github_token': GITHUB_TOKEN,
        'default_source': 'combo' if GITHUB_TOKEN else 'waka',
        'username': WAKATIME_USERNAME,
        **DEFAULT_STYLES,
        **(CARD_EXTRA.get(card_type, {})),
        **(extra_opts or {}),
    }
    try:
        filtered = filter_kwargs(card_func, opts)
        result = card_func(**filtered)
        svg = svg_container(
            **filter_kwargs(svg_container, {**DEFAULT_STYLES, 'static_dir': STATIC_DIR}),
            components=[{**result, 'type': card_type}],
        )
        output_path = OUTPUT_DIR / f'{name}.svg'
        output_path.write_text(svg, encoding='utf-8')
        print(f'    -> Saved {output_path}')
    except Exception as e:
        print(f'    -> ERROR: {e}')


def apply_theme(theme_name):
    theme = load_theme(theme_name, STATIC_DIR)
    if not theme:
        print(f'  Theme "{theme_name}" not found, using defaults')
        return
    print(f'  Applied theme: {theme_name}')
    DEFAULT_STYLES.update({k: v for k, v in theme.items() if k in DEFAULT_STYLES})
    for card_opts in CARD_EXTRA.values():
        for theme_key, card_key in [('chart_color', 'chart_color'), ('rank_color', 'rank_color'), ('heatmap_color', 'heatmap_color')]:
            if theme_key in theme and card_key in card_opts:
                card_opts[card_key] = theme[theme_key]


def main():
    parser = argparse.ArgumentParser(description='Generate WakaTime stats SVGs')
    parser.add_argument('--theme', '-t', default=None, help='Theme name from color_themes.json')
    args = parser.parse_args()

    if not WAKATIME_API_KEY:
        print('ERROR: WAKATIME_API_KEY not set in .env')
        sys.exit(1)
    if not WAKATIME_USERNAME:
        print('ERROR: WAKATIME_USERNAME not set in .env')
        sys.exit(1)

    if args.theme:
        apply_theme(args.theme)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cards = [
        ('basic', 'basic', get_basic_stats_card, None),
        ('heatmap', 'heatmap', get_heatmap_card, None),
        ('weekly', 'weekly', get_coding_activity_card, None),
        ('weekly_projs', 'weekly_projs', get_project_breakdown_card, None),
        ('weekly_langs', 'weekly_langs', get_language_breakdown_card, None),
        ('weekly_avg', 'weekly_avg', get_weekday_average_card, None),
        ('all_langs', 'all_langs', get_alltime_languages_card, None),
        ('all_projs', 'all_projs', get_alltime_projects_card, None),
        ('ai_coding', 'ai_coding', get_ai_coding_card, None),
        ('personal_info', 'personal_info', get_personal_info_card, None),
        ('ai_agent', 'ai_agent', get_ai_agent_card, None),
        ('spedometer', 'spedometer', get_spedometer_card, None),
        ('rank', 'rank', get_star_rank_card, None),
    ]

    print(f'Generating {len(cards)} cards for user: {WAKATIME_USERNAME}')
    for name, card_type, func, opts in cards:
        generate_card(name, card_type, func, opts)

    print(f'\nDone! All SVGs saved to: {OUTPUT_DIR}')


if __name__ == '__main__':
    main()
