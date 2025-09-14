from datetime import datetime, timezone
import json
import math


class Division:
    def __init__(self, players, tables, get_round_count, get_round_set_names):
        self.players = players
        self.tables = tables
        starting_players = len([p for p in players if not p.is_late])
        self.structure = get_round_count(starting_players, tables)
        self.round_set_names = get_round_set_names(self.structure)
        self.winner = None

    def total_swiss_rounds(self):
        return self.structure[0] + self.structure[1]

    def __repr__(self):
        return f'{self.structure[0]} + {self.structure[1]} + {self.structure[2]}'


class Event:
    def __init__(self, event_id, name, start_date, end_date, platform,
                 tour_id, season, divisions):
        self.event_id = event_id
        self.name = name
        self.date_start = start_date
        self.date_end = end_date
        self.last_updated = datetime.now(timezone.utc).isoformat()
        self.platform = platform
        self.tour_id = tour_id
        self.season = season
        self.divisions = divisions

    def get_tournament_status(self):
        if (self.divisions['juniors'].winner is not None
                and self.divisions['seniors'].winner is not None
                and self.divisions['masters'].winner is not None):
            return 'finished'

        if (len(self.divisions['juniors'].players) > 0
                or len(self.divisions['seniors'].players) > 0
                or len(self.divisions['masters'].players) > 0):
            return 'in-progress'

        return 'not-started'

    def to_dict(self):
        result = {
            'id': self.event_id,
            'name': self.name,
            'date': {
                'start': self.date_start,
                'end': self.date_end
            },
            'players': {
                div: len(self.divisions[div].players) for div in ['juniors', 'seniors', 'masters']
            },
            'winners': {
                div: self.divisions[div].winner for div in ['juniors', 'seniors', 'masters']
            },
            'tournamentStatus': self.get_tournament_status(),
            'roundNumbers': {
                div: len(self.divisions[div].tables) for div in ['juniors', 'seniors', 'masters']
            },
            'tournamentStructure': {
                div: {
                    'swissDay1': self.divisions[div].structure[0],
                    'swissDay2': self.divisions[div].structure[1],
                    'topCut': self.divisions[div].structure[2]
                } for div in ['juniors', 'seniors', 'masters']
            },
            "lastUpdated": self.last_updated,
            "season": self.season,
        }

        if self.platform == 'rk9':
            result['rk9link'] = self.tour_id
        if self.platform == 'playlatam':
            result['playlatamlink'] = self.tour_id
        return result

    def add_to_index(self, index_filename):
        index_data = []

        try:
            with open(index_filename, 'r') as indexFile:
                index_data = json.load(indexFile)
        except OSError:
            pass

        for (i, tour) in enumerate(index_data):
            if tour['id'] == self.event_id:
                index_data[i] = {
                    'id': self.event_id,
                    'name': self.name
                }
                break
        else:
            index_data.append({
                'id': self.event_id,
                'name': self.name
            })

        with open(index_filename, 'w') as indexFile:
            json.dump(index_data, indexFile)

