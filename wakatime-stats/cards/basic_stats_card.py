from datetime import datetime, timedelta
import requests
from cards.utils import waka_auth_header, parse_boolean


def format_long_date(date_str):
    dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
    day = dt.day
    suffix = (
        'st' if day % 10 == 1 and day != 11 else
        'nd' if day % 10 == 2 and day != 12 else
        'rd' if day % 10 == 3 and day != 13 else 'th'
    )
    return f'{dt.strftime("%B")} {day}{suffix}, {dt.year}'


def get_basic_stats_card(
    api_key=None,
    github_token=None,
    default_source=None,
    username=None,
    text_color='ccc',
    font_family='Arial',
    hide_daily_average=None,
    hide_total_time=None,
    hide_languages=None,
    hide_projects=None,
    hide_operating_systems=None,
    hide_most_active_day=None,
    hide_github_contributions=None,
    hide_github_commits=None,
    hide_github_prs=None,
    hide_github_issues=None,
    hide_github_reviews=None,
    hide_github_stars=None,
    hide_github_followers=None,
):
    text_color = text_color.replace('#', '')
    has_github = bool(github_token)
    source_pref = (default_source or ('combo' if has_github else 'waka')).lower()
    if not has_github:
        source_pref = 'waka'
    use_github = source_pref == 'github' and has_github
    use_combo = source_pref == 'combo' or (source_pref == 'github' and has_github)

    stats = None
    github_stats = None

    if use_github or use_combo:
        try:
            to = datetime.utcnow()
            from_dt = to - timedelta(days=365)
            stars = 0
            cursor = None
            has_next = True
            query = '''
                query basicStats($login:String!, $from:DateTime!, $to:DateTime!, $after:String) {
                  user(login:$login) {
                    followers { totalCount }
                    repositoriesContributedTo(contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, PULL_REQUEST_REVIEW], first: 1) {
                      totalCount
                    }
                    contributionsCollection(from:$from, to:$to) {
                      totalCommitContributions
                      totalPullRequestContributions
                      totalIssueContributions
                      totalPullRequestReviewContributions
                      contributionCalendar {
                        weeks { contributionDays { date contributionCount } }
                      }
                    }
                    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork:false, first:100, after:$after) {
                      nodes { stargazerCount }
                      pageInfo { hasNextPage endCursor }
                    }
                  }
                }
            '''
            while has_next:
                res = requests.post(
                    'https://api.github.com/graphql',
                    json={
                        'query': query,
                        'variables': {
                            'login': username,
                            'from': from_dt.isoformat(),
                            'to': to.isoformat(),
                            'after': cursor,
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
                user = (json_data.get('data') or {}).get('user')
                if not user:
                    raise Exception('GitHub user not found')
                if not github_stats:
                    github_stats = user
                repos_nodes = (user.get('repositories') or {}).get('nodes') or []
                for repo in repos_nodes:
                    stars += (repo or {}).get('stargazerCount', 0)
                page_info = (user.get('repositories') or {}).get('pageInfo') or {}
                has_next = page_info.get('hasNextPage', False)
                cursor = page_info.get('endCursor')
            if github_stats:
                github_stats['stars'] = stars
        except Exception as e:
            print(f'GitHub basic stats fallback to WakaTime: {e}')
            github_stats = None

    if not github_stats or use_combo or source_pref == 'waka':
        if not api_key:
            if not github_stats:
                raise Exception('Missing WAKATIME_API_KEY')
        else:
            try:
                res = requests.get(
                    f'https://wakatime.com/api/v1/users/{username}/stats/last_year',
                    headers=waka_auth_header(api_key),
                )
                stats = res.json().get('data')
            except Exception as e:
                print(f'WakaTime fetch error: {e}')
                if not github_stats:
                    raise Exception('Failed to fetch WakaTime stats')

    total = (stats or {}).get('human_readable_total', 'N/A')
    avg = (stats or {}).get('human_readable_daily_average', 'N/A')
    langs_list = ((stats or {}).get('languages') or [])[:3]
    langs = ', '.join(l['name'] for l in langs_list) or 'N/A'
    projects_list = ((stats or {}).get('projects') or [])[:3]
    projects = ', '.join(p['name'] for p in projects_list) or 'N/A'
    systems_list = ((stats or {}).get('operating_systems') or [])[:3]
    systems = ', '.join(s['name'] for s in systems_list) or 'N/A'
    date_raw = (stats or {}).get('best_day') or {}
    waka_best_value = date_raw.get('total_seconds', 0)
    date = format_long_date(date_raw['date']) if date_raw.get('date') else 'N/A'

    gh = github_stats or {}
    gh_contrib = gh.get('contributionsCollection') or {}
    gh_repos_contributed = (gh.get('repositoriesContributedTo') or {}).get('totalCount', 0)
    gh_best_day = 'N/A'
    gh_best_value = 0
    cal_weeks = (gh_contrib.get('contributionCalendar') or {}).get('weeks') or []
    if cal_weeks:
        days = []
        for w in cal_weeks:
            days.extend(w.get('contributionDays') or [])
        if days:
            best = max(days, key=lambda d: (d.get('contributionCount') or 0))
            if best.get('date'):
                gh_best_day = format_long_date(best['date'])
                gh_best_value = best.get('contributionCount', 0) or 0

    line_height = 13 * 1.7
    lines_raw = []

    def add_line(label, value):
        lines_raw.append({'label': label, 'value': value})

    gh_hide = {
        'contributions': parse_boolean(hide_github_contributions, False),
        'commits': parse_boolean(hide_github_commits, False),
        'prs': parse_boolean(hide_github_prs, False),
        'issues': parse_boolean(hide_github_issues, False),
        'reviews': parse_boolean(hide_github_reviews, False),
        'stars': parse_boolean(hide_github_stars, False),
        'followers': parse_boolean(hide_github_followers, False),
    }

    include_github = github_stats and (source_pref == 'github' or source_pref == 'combo')
    include_waka = stats and (source_pref == 'waka' or source_pref == 'combo' or (source_pref == 'github' and has_github))

    if include_github:
        if not gh_hide['stars']:
            add_line('Total Stars', (github_stats or {}).get('stars', 'N/A'))
        if not gh_hide['commits'] and not parse_boolean(hide_daily_average):
            add_line('Total Commits', (gh_contrib or {}).get('totalCommitContributions', 'N/A'))
        if not gh_hide['prs'] and not parse_boolean(hide_languages):
            add_line('Total PRs', (gh_contrib or {}).get('totalPullRequestContributions', 'N/A'))
        if not gh_hide['issues'] and not parse_boolean(hide_projects):
            add_line('Total Issues', (gh_contrib or {}).get('totalIssueContributions', 'N/A'))
        if not gh_hide['reviews'] and not parse_boolean(hide_operating_systems):
            add_line('Total Reviews', (gh_contrib or {}).get('totalPullRequestReviewContributions', 'N/A'))
        if not gh_hide['followers']:
            add_line('Total Followers', (gh.get('followers') or {}).get('totalCount', 'N/A'))
        if not gh_hide['contributions'] and not parse_boolean(hide_total_time):
            add_line('Contributed To', gh_repos_contributed or 'N/A')

    if include_waka and stats:
        if not parse_boolean(hide_total_time):
            add_line('Total Time', total)
        if not parse_boolean(hide_daily_average):
            add_line('Daily Average', avg)
        if not parse_boolean(hide_languages):
            add_line('Top Languages', langs)
        if not parse_boolean(hide_projects):
            add_line('Top Projects', projects)
        if not parse_boolean(hide_operating_systems):
            add_line('Top OS', systems)

    best_day_value = None
    if use_combo and stats and github_stats:
        if waka_best_value > 0 and gh_best_value > 0:
            best_day_value = {'label': 'Most Active Day', 'value': date}
    if stats and waka_best_value > 0:
        best_day_value = {'label': 'Most Active Day', 'value': date}
    if github_stats and gh_best_day != 'N/A':
        best_day_value = {'label': 'Most Active Day', 'value': gh_best_day}

    if not parse_boolean(hide_most_active_day) and best_day_value:
        add_line(best_day_value['label'], best_day_value['value'])

    total_lines = len(lines_raw)
    height = line_height * total_lines

    lines = []
    for i, item in enumerate(lines_raw):
        y = -(total_lines - 1 - i) * line_height
        lines.append(
            f'<text font-family="{font_family}" x="20" y="{y}" '
            f'fill="#{text_color}" font-size="13">'
            f'<tspan font-weight="bold">{item["label"]}:</tspan> {item["value"]}</text>'
        )

    translated_group = f'<g transform="translate(0, {height})">\n' + '\n'.join(lines) + '\n</g>'

    text_blocks = [f'{item["label"]}: {item["value"]}' for item in lines_raw]
    max_text_width = max((len(t) * 7 for t in text_blocks), default=0)
    final_width = max_text_width + 40

    return {
        'content': translated_group,
        'height': height,
        'width': final_width,
    }
