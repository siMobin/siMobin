MEDIANS = {
    'commits': {'all': 1000, 'recent': 250},
    'prs': 50,
    'issues': 25,
    'reviews': 2,
    'repos': 5,
    'stars': 50,
    'followers': 10
}


def get_medians(all_commits):
    return {
        'commits': MEDIANS['commits']['all'] if all_commits else MEDIANS['commits']['recent'],
        'prs': MEDIANS['prs'],
        'issues': MEDIANS['issues'],
        'reviews': MEDIANS['reviews'],
        'repos': MEDIANS['repos'],
        'stars': MEDIANS['stars'],
        'followers': MEDIANS['followers']
    }


def exponential_cdf(x):
    return 1 - 2 ** -x


def log_normal_cdf(x):
    return x / (1 + x)


def calculate_rank(all_commits=False, commits=0, prs=0, issues=0, reviews=0, repos=0, stars=0, followers=0):
    medians = get_medians(all_commits)
    COMMITS_MEDIAN = medians['commits']
    COMMITS_WEIGHT = 2
    PRS_MEDIAN = medians['prs']
    PRS_WEIGHT = 3
    ISSUES_MEDIAN = medians['issues']
    ISSUES_WEIGHT = 1
    REVIEWS_MEDIAN = medians['reviews']
    REVIEWS_WEIGHT = 1
    REPOS_MEDIAN = medians['repos']
    REPOS_WEIGHT = 2
    STARS_MEDIAN = medians['stars']
    STARS_WEIGHT = 4
    FOLLOWERS_MEDIAN = medians['followers']
    FOLLOWERS_WEIGHT = 1

    TOTAL_WEIGHT = (COMMITS_WEIGHT + PRS_WEIGHT + ISSUES_WEIGHT +
                    REVIEWS_WEIGHT + REPOS_WEIGHT + STARS_WEIGHT + FOLLOWERS_WEIGHT)

    THRESHOLDS = [1, 12.5, 25, 37.5, 50, 62.5, 75, 87.5, 100]
    LEVELS = ["S", "A+", "A", "A-", "B+", "B", "B-", "C+", "C"]

    rank = 1 - (
        COMMITS_WEIGHT * exponential_cdf(commits / COMMITS_MEDIAN) +
        PRS_WEIGHT * exponential_cdf(prs / PRS_MEDIAN) +
        ISSUES_WEIGHT * exponential_cdf(issues / ISSUES_MEDIAN) +
        REVIEWS_WEIGHT * exponential_cdf(reviews / REVIEWS_MEDIAN) +
        REPOS_WEIGHT * log_normal_cdf(repos / REPOS_MEDIAN) +
        STARS_WEIGHT * log_normal_cdf(stars / STARS_MEDIAN) +
        FOLLOWERS_WEIGHT * log_normal_cdf(followers / FOLLOWERS_MEDIAN)
    ) / TOTAL_WEIGHT

    level_idx = next((i for i, t in enumerate(THRESHOLDS) if rank * 100 <= t), len(LEVELS) - 1)
    level = LEVELS[level_idx]

    return {'level': level, 'percentile': rank * 100}
