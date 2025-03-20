class Standing:
    def __init__(self, players, tables, get_round_count):
        self.players = players
        self.tables = tables
        starting_players = len(players) - len([entry for entry in filter(lambda p: p.late, players)])
        structure = get_round_count(starting_players, tables)
        self.rounds_day1 = structure[0]
        self.rounds_day2 = structure[1]
        self.rounds_cut = structure[2]

    def __repr__(self):
        output = f'{self.rounds_day1}/{self.rounds_day2}/{self.rounds_cut}'
        return output

    def __str__(self):
        output = f'{self.rounds_day1}/{self.rounds_day2}/{self.rounds_cut}'
        return output

