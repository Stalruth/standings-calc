import math

# Day 1 rounds, Day 2 rounds, Top Cut rounds
round_structures = [
        (3, 0, 0),  # 4-8
        (4, 0, 2),  # 9-12
        (5, 0, 2),  # 13-20
        (5, 0, 3),  # 21-32
        (6, 0, 3),  # 33-64
        (7, 0, 3),  # 65-128
        (8, 0, 3),  # 129-226
        (9, 5, 3),  # 227-799
        (9, 6, 3)   # 800+
]


# NOTE: there are instances where late players count to the total.
# make sure this result matches the tournament in practice, and
# bump up if necessary.
def get_round_count(players, tables):
    index = 0
    if players > 800:
        index = 8
    elif players > 226:
        index = 7
    elif players > 128:
        index = 6
    elif players > 64:
        index = 5
    elif players > 32:
        index = 4
    elif players > 20:
        index = 3
    elif players > 12:
        index = 2
    elif players > 8:
        index = 1

    return round_structures[index]


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

    start = 0 if current_round <= stages[0] else stages[0]
    end = stages[0] if current_round <= stages[0] else stages[0] + stages[1]

    if current_round < start or current_round > end:
        return

    for match in player.matches[start:end]:
        if match.player.name == 'BYE' or match.status is None:
            continue
        results[match.status] += 1

    total = results['W'] + results['L'] + results['T']
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

    start = 0 if current_round <= stages[0] else stages[0]
    end = stages[0] if current_round <= stages[0] else stages[0] + stages[1]

    if current_round < start or current_round > end:
        return

    total = 0
    count = 0

    for match in player.matches[start:end]:
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

    start = 0 if current_round <= stages[0] else stages[0]
    end = stages[0] if current_round <= stages[0] else stages[0] + stages[1]

    if current_round < start or current_round > end:
        return

    total = 0
    count = 0

    for match in player.matches[start:end]:
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
        not player.is_dqed,
        player.get_points(),
        not player.is_late,
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

