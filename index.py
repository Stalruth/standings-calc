from datetime import datetime, timezone
import json
import argparse
import os

from player import Player
from event import Event, Division

import structures.season2024
import structures.season2025


def get_last_round(matches):
    result = []
    player_count = len(matches) * 2
    for match in matches:
        flip = False
        for player in match:
            if flip:
                result.append((player_count*2 - player - 1, player))
            else:
                result.append((player, player_count*2 - player - 1))
            flip = not flip
    return result


# returns a list of the higher ranked player in each match of the first round
# used to determine bracket seeding
def single_elim_order(players):
    matches = [(0, 1)]
    while len(matches) * 2 < players:
        matches = get_last_round(matches)
    return [min(match[0], match[1]) for match in matches]


def create_event(base_dir, season, get_round_count):
    with open(f'{base_dir}/tournament.json', 'r') as infile:
        raw_tour = json.load(infile)
    divisions = {}
    for division in ['juniors', 'seniors', 'masters']:
        try:
            with (open(f'{base_dir}/{division}/players.json') as players_json,
                  open(f'{base_dir}/{division}/tables.json') as tables_json):
                counter = 2
                players = [
                           Player(p['name'], p['division'], k, p['late'],
                                  p['dqed'])
                           for k, p
                           in json.load(players_json).items()
                          ]
                tables = json.load(tables_json)
                divisions[division] = Division(players, tables, get_round_count)
        except FileNotFoundError:
            divisions[division] = Division([], [], get_round_count)

    if 'rk9link' in raw_tour:
        return Event(raw_tour['id'], raw_tour['name'],
                     raw_tour['date']['start'], raw_tour['date']['end'],
                     'rk9', raw_tour['rk9link'], int(season), divisions)
    elif 'playlatamlink' in raw_tour:
        return Event(raw_tour['id'], raw_tour['name'],
                     raw_tour['date']['start'], raw_tour['date']['end'],
                     'playlatam', raw_tour['playlatamlink'], int(season),
                     divisions)


def match_record(table_player, candidate):
    if table_player['result'] is None and (
            candidate.wins == table_player['record']['wins'] and
            candidate.losses <= table_player['record']['losses'] and
            candidate.ties == table_player['record']['ties']):
        return True
    elif table_player['result'] == 'L' and (
            candidate.wins == table_player['record']['wins'] and
            candidate.losses + 1 <= table_player['record']['losses'] and
            candidate.ties == table_player['record']['ties']):
        return True
    elif table_player['result'] == 'T' and (
            candidate.wins == table_player['record']['wins'] and
            candidate.losses <= table_player['record']['losses'] and
            candidate.ties + 1 == table_player['record']['ties']):
        return True
    elif table_player['result'] == 'W' and (
            candidate.wins + 1 == table_player['record']['wins'] and
            candidate.losses <= table_player['record']['losses'] and
            candidate.ties == table_player['record']['ties']):
        return True
    return False


def main_worker(tour_id, output_dir, input_dir, season, structure):
    base_input_dir = f'{input_dir}/{tour_id}'
    base_output_dir = f'{output_dir}/{tour_id}'
    tour_data = create_event(base_input_dir, season, structure.get_round_count)

    for division_name in tour_data.divisions:
        print(f'{tour_id}/{division_name}')

        division = tour_data.divisions[division_name]
        print(f'{len(division.players)} | {division.structure[0]}+{division.structure[1]}+{division.structure[2]}')

        division_input_dir = f'{base_input_dir}/{division_name}'
        division_output_dir = f'{base_output_dir}/{division_name}'
        os.makedirs(division_output_dir, exist_ok=True)

        if len(division.players) == 0:
            continue

        winner = None
        swiss = []
        top_cut = None

        try:
            with open(f'{division_input_dir}/overrides.json') as infile:
                overrides = json.load(infile)
        except FileNotFoundError:
            overrides = {}

        try:
            with open(
                    f'{division_input_dir}/published_standings.txt') as infile:
                published_standings = [
                    line.strip() for line in infile.readlines()
                ]
        except FileNotFoundError:
            published_standings = []

        players_dictionary = {}
        for player in division.players:
            counter = 0
            key = f'{player.name}#{counter}'
            while key in players_dictionary:
                counter += 1
                key = f'{player.name}#{counter}'
            players_dictionary[key] = player

        for (i, tables) in enumerate(division.tables):
            current_round = i + 1

            print(f'{tour_id}/{division_name}/{current_round}')

            matched_dictionary = {
                key : False for key in players_dictionary.keys()
            }
            top_cut_round = []

            for table in tables:
                table_players = []
                for (p, player) in enumerate(table['players']):
                    match = None
                    override_key = f'{current_round}/{table["table"]}'
                    if override_key in overrides:
                        player_id = overrides[override_key][p]
                        match = next((player for player in division.players
                                      if player.id == player_id), None)
                        print(f'Override: {override_key}, {match.name}')

                    if match is None:
                        result = []
                        counter = 0
                        key = f'{player["name"]}#{counter}'
                        while key in players_dictionary:
                            if not matched_dictionary[key]:
                                result.append((key, players_dictionary[key]))
                            counter += 1
                            key = f'{player["name"]}#{counter}'

                        for (key, candidate) in result:
                            if match_record(player, candidate):
                                match = candidate

                            if match:
                                matched_dictionary[key] = True
                                break
                        else:
                            match = Player(player['name'], division_name,
                                                len(division.players) + 2,
                                                True, False);
                            division.players.append(match)
                            print(f'Added new player: {current_round} {match}')

                        for i in range(current_round - match.wins -
                                       match.losses - match.ties - 1):
                            print(f'Missed round: {i}/{current_round} {match}')
                            match.add_match(None, 'L', False, 0)

                    table_players.append((match, player['result'],
                                          player['dropped']))

                try:
                    if len(table_players) == 1 and table_players[0][0] is not None:
                        table_players[0][0].add_match(None, table_players[0][1],
                                                table_players[0][2], table['table'])
                    else:
                        table_players[0][0].add_match(table_players[1][0], table_players[0][1],
                                                table_players[0][2], table['table'])
                        table_players[1][0].add_match(table_players[0][0], table_players[1][1],
                                                table_players[1][2], table['table'])
                except AttributeError as e:
                    print(table_players, table)
                    raise e

                if current_round >= division.total_swiss_rounds():
                    if top_cut_round is None:
                        top_cut_round = []
                    try:
                        game_winner = [player['result'] for player in
                                       table['players']].index('W')
                    except ValueError:
                        game_winner = None

                    top_cut_round.append({
                        'players': [
                            player[0] for player in table_players
                        ],
                        'winner': game_winner
                    })

            for calc in [
                    structure.calculate_winrate,
                    structure.calculate_opp_winrate,
                    structure.calculate_opp_opp_winrate
            ]:
                for player in division.players:
                    calc(player, division.structure, current_round)

            if current_round <= division.total_swiss_rounds():
                division.players.sort(key=structure.hash_player_standing,
                                      reverse=True)
                placement = 1
                for player in division.players:
                    if not player.is_dqed:
                        player.top_placement = placement
                        placement = placement + 1
                    else:
                        player.top_placement = None

                swiss.append([{
                            'id': player.id,
                            'record': {
                                'wins': player.wins,
                                'losses': player.losses,
                                'ties': player.ties,
                            },
                            'resistances': {
                                'self': player.win_percentage,
                                'opp': player.opp_win_percentage,
                                'oppopp': player.oppopp_win_percentage
                            }
                        } for player in division.players])

            else:
                round_players = [p for p in division.players if not p.is_dqed and len(p.matches) == current_round]
                round_players.sort(key=lambda p: (p.matches[-1].status == 'W', *structure.hash_player_standing(p)), reverse=True)

                for (i, player) in enumerate(round_players):
                    player.top_placement = i + 1

                division.players = [*round_players, *division.players[len(round_players):]]

            division.players.sort(key=lambda p: p.is_dqed)

            if current_round == division.total_swiss_rounds() + 1:
                top_cut = [[]]
                for match in top_cut_round:
                    top_cut[0].append({
                        'players': [
                            {
                                'name': player.name,
                                'id': player.id
                            } for player in match['players']
                        ],
                        'winner': match['winner']
                    })

            if current_round >= division.total_swiss_rounds() + 2:
                last_round = top_cut[-1]
                this_round = []
                this_round_ids = []
                for table in last_round:
                    winner_id = table['players'][table['winner']]['id']
                    if winner_id in this_round_ids:
                        continue
                    this_table = next((match for match in top_cut_round if winner_id
                                  in [player.id for player in match['players']]), None)
                    this_round.append({
                        'players': [
                            {
                                'name': player.name,
                                'id': player.id
                            } for player in this_table['players']
                        ],
                        'winner': this_table['winner']
                    })
                    this_round_ids = [
                        *this_round_ids,
                        *[player.id for player in this_table['players']]
                    ]
                top_cut.append(this_round)

            still_playing = len([p for p in division.players
                                 if p.matches[-1].status is None])
            if (current_round == division.total_swiss_rounds()
                                 + division.structure[2]
                    and still_playing == 0):
                winner = division.players[0]
                if not "World" in tour_data.name:
                    structure.apply_points(division)

        if len(division.players) > 0:
            division.player_count = len(division.players)
            division.round_number = len(division.tables)
            if winner is not None:
                division.winner = winner.name

        if top_cut is not None:
            with open(f'{division_output_dir}/top-cut.json', 'w') as outfile:
                json.dump({
                    'totalRounds': division.structure[2],
                    'rounds': top_cut
                }, outfile, separators=(',',':'), ensure_ascii=False)

        with open(f'{division_output_dir}/standings.json', 'w') as outfile:
            json.dump([player.id for player in division.players],
                      outfile, separators=(',',':'), ensure_ascii=False)

        with open(f'{division_output_dir}/players.json', 'w') as outfile:
            json.dump({player.id: player for player in division.players},
                      outfile, default=lambda o: o.to_json(division),
                      separators=(',',':'), ensure_ascii=False)

        with open(f'{division_output_dir}/round_standings.json', 'w') as outfile:
            json.dump(swiss, outfile, separators=(',',':'),
                      ensure_ascii=False)

        if len(published_standings) > 0:
            with open(f'{division_output_dir}/discrepancy.txt', 'w') as outfile:
                for player in division.players:
                    if player.top_placement is None:
                        continue
                    index = player.top_placement - 1
                    if (index < len(published_standings)
                            and player.name != published_standings[index]):
                        outfile.write(
                                f'{index + 1}: {player.name} RK9: {published_standings[index]}\n'
                        )

    tour_data.last_updated = datetime.now(timezone.utc).isoformat()
    tour_data.add_to_index(f'{output_dir}/tournaments.json')

    with open(f'{base_output_dir}/tournament.json', 'w') as outfile:
        json.dump(tour_data.to_dict(), outfile, separators=(',',':'),
                  ensure_ascii=False)

    print(f'Ending at: {datetime.now().strftime("%Y/%m/%d - %H:%M:%S")}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url')
    parser.add_argument('--id')
    parser.add_argument('--output-dir', help='output directory', default='.')
    parser.add_argument('--input-dir', help='input directory', default='.')
    parser.add_argument(
        '--season',
        help='VGC season the tournament is for',
        default='2025'
    )
    parser.add_argument(
        '--structure',
        help='Tournament Structure',
        default='2025'
    )

    args = parser.parse_args()

    '''
    example: (Barcelona)
    id = 'special-barcelona'
    url = 'BA189xznzDvlCdfoQlBC'
    '''
    os.makedirs(args.output_dir, exist_ok=True)

    if args.structure == '2025':
        structure = structures.season2025
    elif args.structure == '2024':
        structure = structures.season2024

    main_worker(
            args.id,
            args.output_dir,
            args.input_dir,
            args.season,
            structure
    )

