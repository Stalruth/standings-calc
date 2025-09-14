import math

# Day 1 rounds, Day 2 rounds, Min # Cut
round_structures = [
        (3, 0, None),   # 4-8
        (4, 0, 2),      # 9-16
        (6, 0, 4),      # 17-32
        (7, 0, 6),      # 33-64
        (6, 2, 8),      # 65-128
        (7, 2, 8),      # 129-256
        (8, 2, 8),      # 257-512
        (8, 3, 8),      # 513-1024
        (8, 4, 8),      # 1025-2048
        (9, 4, 8),      # 2049-4096
        (9, 5, 8)       # 4097+
]


def get_round_count(players, tables):
    index = 0
    if players > 4096:
        index = 10
    elif players > 2048:
        index = 9
    elif players > 1024:
        index = 8
    elif players > 512:
        index = 7
    elif players > 256:
        index = 6
    elif players > 128:
        index = 5
    elif players > 64:
        index = 4
    elif players > 32:
        index = 3
    elif players > 16:
        index = 2
    elif players > 8:
        index = 1

    (rounds_day1, rounds_day2, has_cut) = round_structures[index]
    rounds_swiss = rounds_day1 + rounds_day2
    rounds_cut = 0
    if has_cut and len(tables) >= (rounds_swiss + 1):
        rounds_cut = math.ceil(math.log2(len(tables[rounds_swiss]) * 2))

    return (rounds_day1, rounds_day2, rounds_cut)


# Calculates a player's W/L
# Source: "Tournament Rules Handbook" at the following webpage:
# https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources
def calculate_winrate(player, stages, current_round):
    if len(player.matches) < current_round:
        return

    results = {
        'W': 0,
        'L': 0,
        'T': 0
    }
    for match in player.matches[0 : stages[0] + stages[1]]:
        if match.player.name == 'BYE' or match.status is None:
            continue
        results[match.status] += 1

    total = results['W'] + results['T'] + results['L']
    if total == 0:
        player.win_percentage = 0.25
        return

    raw_result = (results['W'] + (results['T'] / 2)) / total
    result = max(0.25, raw_result)

    if player.drop_round not in [
            None,
            stages[0],
            stages[0] + stages[1]
            ]:
        result = min(0.75, result)

    player.win_percentage = result


# Calculates a player's first resistance tiebreaker.
# Run after calculate_winrate above.
def calculate_opp_winrate(player, stages, current_round):
    if len(player.matches) < current_round:
        return

    total = 0
    count = 0

    for match in player.matches:
        if match.player is None or match.player.id == 0:
            continue

        total += match.player.win_percentage
        count += 1

    if count == 0:
        player.opp_win_percentage = 0.25
        return

    player.opp_win_percentage = max(total / count, 0.25)


# Calculates a player's second resistance tiebreaker.
# Run after calculate_opp_winrate above.
def calculate_opp_opp_winrate(player, stages, current_round):
    if len(player.matches) < current_round:
        return

    total = 0
    count = 0

    for match in player.matches:
        if match.player is None or match.player.id == 0:
            continue

        total += match.player.opp_win_percentage
        count += 1

    if count == 0:
        player.oppopp_win_percentage = 0.25
        return

    player.oppopp_win_percentage = max(total / count, 0.25)


# Compare records.
def hash_player_standing(player):
    return (
        player.is_dqed,
        player.get_points(),
        round(player.opp_win_percentage * 100, 2),
        round(player.oppopp_win_percentage * 100, 2)
    )


def apply_points(division):
    cutoff = 1
    player_count = len(division.players)
    if player_count >= 2049:
        cutoff = 1024
    elif player_count >= 1025:
        cutoff = 512
    elif player_count >= 513:
        cutoff = 256
    elif player_count >= 257:
        cutoff = 128
    elif player_count >= 129:
        cutoff = 64
    elif player_count >= 65:
        cutoff = 32
    elif player_count >= 33:
        cutoff = 16
    elif player_count >= 17:
        cutoff = 8
    elif player_count >= 8:
        cutoff = 4
    elif player_count >= 4:
        cutoff = 2

    for i in range(cutoff):
        division.players[i].awards_placement = 2 ** math.ceil(math.log2(i + 1))

def get_round_set_names(structure):
    if structure[1] == 0:
        if structure[2] == 0:
            return ['Swiss']
        return ['Swiss', 'Top Cut']
    return ['Swiss Day 1', 'Swiss Day 2', 'Top Cut']

