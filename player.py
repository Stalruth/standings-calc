# class Match : VS a player, with a status [W/L/T -> 2/0/1] and a table number
class Match:
    def __init__(self, player, status, table):
        self.player = player
        self.status = status
        self.table = table

    def __repr__(self):
        return f'STATUS {self.status} PLAYER {self.player} TABLE {self.table}'


# class Player
class Player:
    def __init__(self, name, division, player_id, is_late, is_dqed):
        self.name = name
        self.division = division

        self.wins = 0
        self.ties = 0
        self.losses = 0

        self.matches = []
        self.id = int(player_id)

        self.win_percentage = 0.25
        self.opp_win_percentage = 0.25
        self.oppopp_win_percentage = 0.25

        # Round the player (was) dropped from the tournament
        # Integer if the player (was) dropped; None otherwise.
        self.drop_round = None

        self.top_placement = 0
        # Top XX placement the player achieved. (e.g. 32 for Top 32)
        # Integer if the player got an awarded plcement; None otherwise.
        self.awards_placement = None

        self.is_late = is_late
        self.is_dqed = is_dqed

    # addMatch function : adding a game versus another player
    # player : Opponent: Player or None (if Bye/Late)
    # status : None if still playing; String ('W'/'L'/'T') if completed.
    # drop : True if the player dropped after this game
    # table : table #
    def add_match(self, player, status, dropped, table):
        if self.drop_round is not None:
            # reset for late players
            self.drop_round = None
        if status == 'L':
            self.losses += 1
        if status == 'T':
            self.ties += 1
        if status == 'W':
            self.wins += 1

        if player is None:
            player = Player('BYE' if status == 'W' else 'LATE',
                            'none', 0, False, False)

        self.matches.append(Match(player, status, table))
        if dropped:
            self.drop_round = len(self.matches)

    def get_points(self):
        return self.wins * 3 + self.ties

    # special logging/debug methods to output some data
    def __repr__(self):
        output = f"({self.id}) {self.name}{'*' if self.is_late else ''} ({self.division}) {self.wins}-{self.losses}-{self.ties} -- {self.get_points()}pts"
        return output

    def __str__(self):
        output = f"{self.name} ({self.division}) {self.wins}-{self.losses}-{self.ties} -- {self.get_points()}pts"
        return output

    # toJson
    def to_json(self, division):
        matches = [
            {
                'id': getattr(match.player, 'id', 0),
                'result': match.status,
                'table': int(match.table)
            } for match in self.matches
        ]
        round_sets = []
        round_sets.append({
            'name': division.round_set_names[0],
            'rounds': matches[:division.structure[0]]
        })

        if division.structure[1] > 0 and len(matches) > division.structure[0]:
            round_sets.append({
                'name': division.round_set_names[1],
                'rounds': matches[division.structure[0] : division.total_swiss_rounds()]
            })

        if division.structure[2] != 0 and len(matches) > division.total_swiss_rounds():
            round_sets.append({
                'name': division.round_set_names[-1],
                'rounds': matches[division.total_swiss_rounds():]
            })

        result = {
            'id': self.id,
            'name': self.name,
            'placing': self.top_placement,
            'top': self.awards_placement,
            'record': {
                'wins': self.wins,
                'losses': self.losses,
                'ties': self.ties
            },
            'resistances': {
                'self': self.win_percentage,
                'opp': self.opp_win_percentage,
                'oppopp': self.oppopp_win_percentage
            },
            'drop': self.drop_round if self.drop_round is not None else -1,
            'rounds': round_sets
        }

        return result

