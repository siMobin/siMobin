import os
import re
import math
import base64
import requests
from cards.calculate_rank import calculate_rank, get_medians
from cards.utils import safe_fetch_json, waka_auth_header, parse_hours

_icon_cache = {}


def load_clean_single_path(filename, mode, rank_color):
    rank_color = rank_color.lstrip('#')
    static_dir = os.path.join(os.getcwd(), 'static')
    filepath = os.path.join(static_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        raw = f.read()
    match = re.search(r'<path\s+([^>]*)\/?>', raw, re.I)
    if not match:
        raise ValueError('No <path> tag')
    attrs = re.sub(r'/$', '', match.group(1))
    attrs = re.sub(
        r'\b(?:fill|stroke|stroke-width|stroke-linecap|stroke-linejoin)\s*=\s*[\'"][^\'"]*[\'"]',
        '', attrs, flags=re.I
    ).strip()
    if mode == 'fill':
        color_attrs = f'fill="#{rank_color}"'
    else:
        color_attrs = f'stroke="#{rank_color}" fill="none" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"'
    prefix = f' {attrs} ' if attrs else ' '
    return f'<path{prefix}{color_attrs} />'


def parse_time_text_to_seconds(time_text):
    hr_match = re.search(r'(\d+)\s*hrs?', time_text, re.I)
    min_match = re.search(r'(\d+)\s*mins?', time_text, re.I)
    hours = int(hr_match.group(1)) if hr_match else 0
    minutes = int(min_match.group(1)) if min_match else 0
    return hours * 3600 + minutes * 60


def load_icon(name, rank_color):
    key = f'{name}-{rank_color}'
    if key in _icon_cache:
        return _icon_cache[key]
    icons_dir = os.path.join(os.getcwd(), 'static', 'icons')
    filepath = os.path.join(icons_dir, f'{name}.svg')
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            raw = f.read()
    except FileNotFoundError:
        return None
    viewbox_match = re.search(r'viewBox="([^"]+)"', raw, re.I)
    viewbox = viewbox_match.group(1) if viewbox_match else '0 0 512 512'
    parts = viewbox.split(' ')
    vb_width = float(parts[2]) if len(parts) > 2 else 512
    vb_height = float(parts[3]) if len(parts) > 3 else 512
    inner = re.sub(r'<\?xml[^>]*>', '', raw, flags=re.I)
    inner = re.sub(r'<!DOCTYPE[^>]*>', '', inner, flags=re.I)
    inner = re.sub(r'<svg[^>]*>', '', inner, flags=re.I)
    inner = inner.replace('</svg>', '')
    colored = re.sub(r'currentColor', f'#{rank_color}', inner, flags=re.I)
    colored = re.sub(r'stroke="([^"]*)"', lambda m: m.group(0) if 'none' in m.group(1) else f'stroke="#{rank_color}"', colored, flags=re.I)
    colored = re.sub(r'fill="currentColor"', f'fill="#{rank_color}"', colored, flags=re.I)
    icon = {'body': colored, 'vbWidth': vb_width, 'vbHeight': vb_height}
    _icon_cache[key] = icon
    return icon


GITHUB_TIER_THRESHOLDS = [
    {'tier': 6, 'maxPercentile': 1},
    {'tier': 5, 'maxPercentile': 10},
    {'tier': 4, 'maxPercentile': 30},
    {'tier': 3, 'maxPercentile': 55},
    {'tier': 2, 'maxPercentile': 75},
    {'tier': 1, 'maxPercentile': 90},
    {'tier': 0, 'maxPercentile': 100}
]


def map_github_percentile_to_tier(percentile):
    match = next((e for e in GITHUB_TIER_THRESHOLDS if percentile <= e['maxPercentile']), GITHUB_TIER_THRESHOLDS[-1])
    next_tier = next((e for e in GITHUB_TIER_THRESHOLDS if e['tier'] == match['tier'] + 1), None)
    return {'current': match, 'next': next_tier}


def fetch_github_stats(username, github_token):
    if not github_token:
        raise ValueError('Missing GITHUB_TOKEN for GitHub rank calculation')
    base_user = None
    stars = 0
    has_next_page = True
    cursor = None
    query = '''
    query userStats($login: String!, $after: String) {
      user(login: $login) {
        followers { totalCount }
        repositoriesContributedTo(contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, PULL_REQUEST_REVIEW], first: 1) {
          totalCount
        }
        contributionsCollection {
          totalCommitContributions
          restrictedContributionsCount
          totalPullRequestContributions
          totalIssueContributions
          totalPullRequestReviewContributions
        }
        repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100, after: $after) {
          nodes { stargazerCount }
          pageInfo { hasNextPage endCursor }
        }
      }
    }
    '''
    while has_next_page:
        resp = requests.post(
            'https://api.github.com/graphql',
            json={'query': query, 'variables': {'login': username, 'after': cursor}},
            headers={'Authorization': f'Bearer {github_token}'}
        )
        json_data = resp.json()
        if json_data.get('errors'):
            raise ValueError('; '.join(e['message'] for e in json_data['errors']))
        user = json_data.get('data', {}).get('user')
        if not user:
            raise ValueError('GitHub user not found')
        if not base_user:
            base_user = user
        repos = (user.get('repositories') or {}).get('nodes') or []
        for repo in repos:
            stars += repo.get('stargazerCount', 0) or 0
        page_info = (user.get('repositories') or {}).get('pageInfo') or {}
        has_next_page = page_info.get('hasNextPage', False)
        cursor = page_info.get('endCursor')
    cc = (base_user or {}).get('contributionsCollection') or {}
    return {
        'commits': (cc.get('totalCommitContributions', 0) or 0) + (cc.get('restrictedContributionsCount', 0) or 0),
        'prs': cc.get('totalPullRequestContributions', 0) or 0,
        'issues': cc.get('totalIssueContributions', 0) or 0,
        'reviews': cc.get('totalPullRequestReviewContributions', 0) or 0,
        'repos': (base_user or {}).get('repositoriesContributedTo', {}).get('totalCount', 0) or 0,
        'stars': stars,
        'followers': (base_user or {}).get('followers', {}).get('totalCount', 0) or 0
    }


def format_num(n):
    if n is None:
        return 'N/A'
    return f'{n:,}'


def compute_percentile(stats_obj):
    return calculate_rank(all_commits=True, **stats_obj)['percentile']


def render_two_column_lines(lines, y_start=35, row_height=22, with_icons=False, text_color='', font_family='', rank_color=''):
    icon_pad = 18 if with_icons else 0
    col_width = 110 + icon_pad
    split = (len(lines) + 1) // 2
    result = []
    for idx, line in enumerate(lines):
        col = 1 if idx >= split else 0
        row = idx - split if col else idx
        x = 160 + col * (col_width + 10)
        y = y_start + row * row_height
        icon_markup = ''
        if with_icons and line.get('icon'):
            icon = load_icon(line['icon'], rank_color)
            if icon:
                icon_scale = 12 / max(icon['vbWidth'], icon['vbHeight'])
                icon_markup = f'<g transform="translate({x},{y - 10}) scale({icon_scale})" fill="#{rank_color}" stroke="#{rank_color}">{icon["body"]}</g>'
        text_x = x + (18 if icon_markup else 0)
        label_part = f'<tspan font-weight="bold">{line["label"]}</tspan>' if line.get('label') else ''
        spacer = ' ' if line.get('label') and line.get('value') else ''
        value_part = line.get('value', '') or ''
        text = f'<text x="{text_x}" y="{y}" font-size="12" fill="#{text_color}" font-family="{font_family}">{label_part}{spacer}{value_part}</text>'
        result.append(f'{icon_markup}{text}')
    return '\n'.join(result)


def get_star_rank_card(
    api_key=None,
    github_token=None,
    default_source=None,
    mode='level',
    username='',
    text_color='',
    font_family='',
    rank_color='',
    hide_title=False,
    show_icons=False,
):
    rank_color = rank_color.lstrip('#')
    text_color = text_color.lstrip('#')
    card_mode = 'level' if (default_source and default_source.lower() == 'waka' and mode != 'level') else mode
    tier_cutoffs = {
        6: [1, 50],
        5: [51, 300],
        4: [301, 1000],
        3: [1001, 2500],
        2: [2501, 5000],
        1: [5001, 8000],
        0: [8001, 10000]
    }
    current_rank = -1
    rhs_x = 160
    bar_width = 160
    progress_bar_width = bar_width + 30 if card_mode == 'progress' else bar_width
    progress_bar_width += 35 if show_icons else 0
    star_pos = [
        [0, -32], [28, -16], [28, 16], [0, 32], [-28, 16], [-28, -16], [0, 0]
    ]
    rank_titles = ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Ascendant', 'Mythic']
    full_star = load_clean_single_path('fullStar.svg', 'fill', rank_color)
    empty_star = load_clean_single_path('emptyStar.svg', 'stroke', rank_color)
    tier = 0
    level_target = 1
    level_value = 0
    tier_thresholds = {}
    tier_rank_estimate = 'N/A'
    is_unranked = False
    rank_title = 'Unranked'
    range_text = ''
    rank_display = 'N/A'
    progress = 0
    github_tier_info = None
    active_source_github_stats = None
    has_github_token = bool(github_token or os.environ.get('GITHUB_TOKEN'))
    source_pref = (default_source or ('combo' if has_github_token else 'waka')).lower()
    if not has_github_token:
        source_pref = 'waka'
    elif source_pref == 'combo':
        source_pref = 'github'
    active_source = 'github' if source_pref == 'github' else 'waka'
    if active_source == 'github':
        try:
            stats = fetch_github_stats(username, github_token or os.environ.get('GITHUB_TOKEN', ''))
            rank_result = calculate_rank(all_commits=True, **stats)
            percentile = rank_result['percentile']
            score = max(0, 100 - percentile)
            github_tier_info = map_github_percentile_to_tier(percentile)
            tier = github_tier_info['current']['tier']
            rank_title = rank_titles[tier]
            range_text = f'<= {github_tier_info["current"]["maxPercentile"]}%'
            target_score = github_tier_info['next']['maxPercentile'] if github_tier_info['next'] else (score or 1)
            level_target = 100 - target_score if github_tier_info['next'] else (score or 1)
            level_value = score
            progress = min(score / level_target, 1) if level_target > 0 else 1
            rank_display = f'{percentile:.1f}%'
            active_source = 'github'
            active_source_github_stats = {**stats, 'percentile': percentile}
        except Exception as e:
            print(f'GitHub rank calculation failed, falling back to WakaTime: {e}')
            active_source = 'waka'
    if active_source == 'waka':
        try:
            api_key_val = api_key or ''
            if not api_key_val:
                raise ValueError('Missing WAKATIME_API_KEY')
            auth_headers = waka_auth_header(api_key_val)
            resp = requests.get(
                f'https://wakatime.com/api/v1/users/{username}/summaries?range=last_7_days',
                headers=auth_headers
            )
            json_data = resp.json()
            total_time_text = json_data['cumulative_total']['text']
            total_seconds = parse_time_text_to_seconds(total_time_text)
            level_hours = total_seconds / 3600
            level_value = level_hours
            user_info = safe_fetch_json('https://wakatime.com/api/v1/leaders', headers=auth_headers)
            pass
            if user_info.get('current_user') and user_info['current_user'].get('rank') is not None:
                current_rank = user_info['current_user']['rank']
            else:
                matched_user = next(
                    (u for u in (user_info.get('data') or []) if u.get('user', {}).get('username', '').lower() == username.lower()),
                    None
                )
                if matched_user and matched_user.get('rank') is not None:
                    current_rank = matched_user['rank']
                else:
                    print('Could not determine rank via current_user or fallback search. Using default.')
                    current_rank = -1
            required_ranks = [v for pair in tier_cutoffs.values() for v in pair]
            required_pages = list(set((rank - 1) // 100 + 1 for rank in required_ranks))
            pages = []
            for page in required_pages:
                try:
                    pages.append(safe_fetch_json(f'https://wakatime.com/api/v1/leaders?page={page}', headers=auth_headers))
                except Exception:
                    pages.append({'data': []})
            rank_map = {}
            for page in pages:
                for user_entry in page.get('data') or []:
                    r = user_entry.get('rank')
                    hrt = user_entry.get('running_total', {}).get('human_readable_total')
                    if r and hrt:
                        rank_map[r] = parse_hours(hrt)
            tier_thresholds = {}
            for t_str, (min_r, max_r) in tier_cutoffs.items():
                t = int(t_str)
                min_h = rank_map.get(min_r, 0)
                max_h = rank_map.get(max_r, min_h)
                tier_thresholds[t] = {'minR': min_r, 'maxR': max_r, 'minH': min_h, 'maxH': max_h}
            find_tier = None
            if current_rank >= 1:
                for t_str, (lo, hi) in tier_cutoffs.items():
                    if lo <= current_rank <= hi:
                        find_tier = int(t_str)
                        break
            if find_tier is not None:
                tier = find_tier
            else:
                min_hours_bronze = tier_thresholds.get(0, {}).get('minH', 0)
                if level_hours < min_hours_bronze:
                    is_unranked = True
                    tier = -1
                else:
                    tier = 0
            next_tier = tier + 1
            if next_tier in tier_thresholds:
                level_target = tier_thresholds[next_tier]['minH']
            elif tier in tier_thresholds:
                level_target = tier_thresholds[tier].get('maxH', level_hours)
            else:
                level_target = level_hours
            if is_unranked:
                level_target = tier_thresholds.get(0, {}).get('minH', 1)
            tier_range = tier_cutoffs.get(tier)
            if tier_range and level_hours > 0:
                tier_min_rank, tier_max_rank = tier_range
                low = tier_min_rank
                high = tier_max_rank
                candidate_rank = tier_max_rank
                while low <= high:
                    mid = (low + high) // 2
                    mid_hours = rank_map.get(mid)
                    if mid_hours is None:
                        high = mid - 1
                        continue
                    if level_hours > mid_hours:
                        candidate_rank = mid
                        high = mid - 1
                    else:
                        low = mid + 1
                tier_rank_estimate = candidate_rank
            tt = tier_thresholds.get(tier) if tier >= 0 else None
            progress = min(max(level_hours / level_target, 0), 1) if level_target > 0 else 1
            rank_title = 'Unranked' if is_unranked else rank_titles[tier]
            range_text = 'Below 10000' if is_unranked else f'{tt["minR"]}-{tt["maxR"]}' if tt else ''
            if current_rank >= 1:
                rank_display = current_rank
            elif is_unranked:
                rank_display = 'Unranked'
            else:
                rank_display = tier_rank_estimate
        except Exception as e:
            print(f'Error computing rank card: {e}')
            is_unranked = True
            tier = -1
            rank_title = 'Unranked'
            range_text = 'Unavailable'
            rank_display = 'N/A'
            level_target = 1
            level_value = 0
            progress = 0
    glow_filter = ''
    if tier >= 4:
        glow_filter = f'''
    <defs>
      <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur in="SourceGraphic" stdDeviation="{(tier - 3) * 1.5}" />
      </filter>
    </defs>'''
    stars_svg = []
    for i, (dx, dy) in enumerate(star_pos):
        if i == 6 and tier != 6:
            stars_svg.append('')
            continue
        is_full = i <= tier
        svg = full_star if is_full else empty_star
        glow_attr = 'filter="url(#glow)"' if tier >= 4 else ''
        stars_svg.append(f'<g transform="translate({60 + dx},{40 + dy}) scale(0.6)" {glow_attr}>{svg}</g>')
    is_github_source = active_source == 'github'
    progress_text = ''
    if is_github_source:
        if github_tier_info and github_tier_info['next']:
            progress_text = f'Rank Up in {level_value:.1f}/{level_target:.1f} pts'
        else:
            progress_text = f'Score {level_value:.1f}'
    else:
        if is_unranked:
            progress_text = f'Reach {level_target:.1f} hrs'
        else:
            progress_text = f'{level_value:.1f}/{level_target:.1f} hrs'
    if is_github_source:
        rank_line = f'<tspan font-size="11">Percentile </tspan><tspan font-size="15" font-weight="bold">{rank_display}</tspan>'
    else:
        rank_line = f'<tspan font-size="11">Rank </tspan><tspan font-size="9">#</tspan><tspan font-size="15" font-weight="bold">{rank_display}</tspan>'
    if is_github_source:
        tier_line = f'{rank_title} Tier: {range_text}'
    else:
        range_part = f'#<tspan font-size="10">{range_text}</tspan>' if not is_unranked else range_text
        tier_line = f'{rank_title} Tier: {range_part}'
    right_content = ''
    right_block_height = 0
    if is_github_source and card_mode == 'stats' and active_source_github_stats:
        icon_names = {
            'stars': 'stars',
            'commits': 'commits',
            'prs': 'pullRequests',
            'issues': 'issues',
            'reviews': 'reviews',
            'followers': 'followers',
            'repos': 'contributions'
        }
        lines = [
            {'label': 'Total Stars:', 'value': format_num(active_source_github_stats.get('stars')), 'icon': icon_names['stars']},
            {'label': 'Total Commits:', 'value': format_num(active_source_github_stats.get('commits')), 'icon': icon_names['commits']},
            {'label': 'Total PRs:', 'value': format_num(active_source_github_stats.get('prs')), 'icon': icon_names['prs']},
            {'label': 'Total Issues:', 'value': format_num(active_source_github_stats.get('issues')), 'icon': icon_names['issues']},
            {'label': 'Total Reviews:', 'value': format_num(active_source_github_stats.get('reviews')), 'icon': icon_names['reviews']},
            {'label': 'Followers:', 'value': format_num(active_source_github_stats.get('followers')), 'icon': icon_names['followers']},
            {'label': 'Contributed to:', 'value': format_num(active_source_github_stats.get('repos')), 'icon': icon_names['repos']},
        ]
        stats_lines = render_two_column_lines(lines, 35, 18, show_icons, text_color, font_family, rank_color)
        right_content = f'''
      <text x="{rhs_x}" y="15" font-size="11" fill="#{text_color}" font-family="{font_family}" font-weight="bold">GitHub Stats</text>
      {stats_lines}
    '''
        row_count = math.ceil(len(lines) / 2)
        last_line_y = 35 + (row_count - 1) * 18
        right_block_height = (last_line_y - 15) + 18
    elif is_github_source and card_mode == 'progress' and active_source_github_stats:
        labels = {
            'repos': 'Total Repos',
            'commits': 'Total Commits',
            'prs': 'Total PRs',
            'issues': 'Total Issues',
            'reviews': 'Total Reviews',
            'stars': 'Total Stars',
            'followers': 'Total Followers'
        }
        icon_names = {
            'repos': 'contributions',
            'commits': 'commits',
            'prs': 'pullRequests',
            'issues': 'issues',
            'reviews': 'reviews',
            'stars': 'stars',
            'followers': 'followers'
        }
        target_percentile = github_tier_info['next']['maxPercentile'] if github_tier_info and github_tier_info['next'] else None
        progress_plan = None
        if target_percentile is not None:
            medians = get_medians(True)
            metric_order = ['reviews', 'repos', 'followers', 'issues', 'prs', 'stars', 'commits']
            sorted_metrics = sorted(metric_order, key=lambda k: medians[k])
            working = dict(active_source_github_stats)
            added = {k: 0 for k in sorted_metrics}
            max_steps = 20000
            iterations = 0
            current_percentile = compute_percentile(working)
            if current_percentile <= target_percentile:
                progress_plan = {'added': added}
            else:
                while current_percentile > target_percentile and iterations < max_steps:
                    best_key = None
                    best_pct = current_percentile
                    for key in sorted_metrics:
                        trial = dict(working)
                        trial[key] = (trial.get(key, 0) or 0) + 1
                        trial_pct = compute_percentile(trial)
                        if trial_pct < best_pct:
                            best_pct = trial_pct
                            best_key = key
                    if not best_key:
                        break
                    working[best_key] = (working.get(best_key, 0) or 0) + 1
                    added[best_key] += 1
                    current_percentile = best_pct
                    iterations += 1
                reached = current_percentile <= target_percentile
                progress_plan = {'added': added, 'reached': reached, 'capped': not reached}
        lines = []
        if target_percentile is None or not progress_plan:
            lines.append({'label': 'Status:', 'value': 'Top tier reached'})
        else:
            added_data = progress_plan.get('added', {})
            medians = get_medians(True)
            used = sorted(
                [(k, v) for k, v in added_data.items() if v > 0],
                key=lambda x: medians[x[0]]
            )
            total_added = sum(v for _, v in used)
            if total_added == 0 and progress_plan.get('reached', True):
                lines.append({'label': 'Status:', 'value': 'Already at next tier'})
            elif used:
                for key, count in used:
                    lines.append({'label': f'{labels[key]}:', 'value': f'+{format_num(count)}', 'icon': icon_names[key]})
                if progress_plan.get('capped'):
                    lines.append({'label': 'Note:', 'value': 'Approximate; may need more'})
            else:
                lines.append({'label': 'Suggestion:', 'value': 'Add activity to lowest medians'})
        progress_lines = render_two_column_lines(lines, 35, 18, show_icons, text_color, font_family, rank_color)
        row_count = max(1, math.ceil(len(lines) / 2))
        bar_y = 35 + row_count * 18 + 10
        bar_block = f'''
      <rect x="{rhs_x}" y="{bar_y}" width="{progress_bar_width}" height="8" fill="#{rank_color}" rx="4" opacity="0.3"/>
      <rect x="{rhs_x}" y="{bar_y}" width="{progress * progress_bar_width}" height="8" fill="#{rank_color}" rx="4"/>
      <text x="{rhs_x + progress_bar_width}" y="{bar_y + 25}" font-size="11" text-anchor="end" fill="#{text_color}" font-family="{font_family}">
        {progress_text}
      </text>
    '''
        right_content = f'''
      <text x="{rhs_x}" y="15" font-size="11" fill="#{text_color}" font-family="{font_family}" font-weight="bold">Progress to next tier</text>
      {progress_lines}
      {bar_block}
    '''
        right_block_height = (bar_y + 25) - 15 + 12
    else:
        right_content = f'''
    <text x="{rhs_x}" y="30" fill="#{text_color}" font-family="{font_family}">
      {rank_line}
    </text>
    <text x="{rhs_x}" y="50" font-size="11" fill="#{text_color}" font-family="{font_family}">
      {tier_line}
    </text>
    <rect x="{rhs_x}" y="65" width="{bar_width}" height="8" fill="#{rank_color}" rx="4" opacity="0.3"/>
    <rect x="{rhs_x}" y="65" width="{progress * bar_width}" height="8" fill="#{rank_color}" rx="4"/>
    <text x="{rhs_x + bar_width}" y="95" font-size="11" text-anchor="end" fill="#{text_color}" font-family="{font_family}">
      {progress_text}
    </text>'''
        right_block_height = (95 - 30) + 16
    component_title = 'Yearly Ranking' if active_source == 'github' else 'Weekly Ranking'
    card_width = rhs_x + bar_width + (28 if card_mode == 'progress' else 0) + (42 if card_mode == 'stats' else 0) + (35 if show_icons else 0)
    title_svg = ''
    if not hide_title:
        title_svg = f'<text x="{card_width / 2}" y="25" font-size="16" text-anchor="middle" fill="#{text_color}" font-family="{font_family}" font-weight="bold">{component_title}</text>'
    title_offset = 0 if hide_title else 35
    available_height = 85 if card_mode == 'level' else 115
    right_y_offset = max(0, (available_height - right_block_height) / 2)
    return {
        'content': f'''
    {glow_filter}
    {title_svg}
    <g transform="translate(0, {title_offset})">{chr(10).join(stars_svg)}</g>
    <text x="67.5" y="110" transform="translate(0, {title_offset})" font-size="15" text-anchor="middle" fill="#{text_color}" font-family="{font_family}">
      {rank_title}
    </text>
    <g transform="translate(0, {title_offset + right_y_offset})">{right_content}</g>
  ''',
        'height': 120 + title_offset,
        'width': card_width
    }
