#from typing import Optional
import warnings
warnings.filterwarnings("ignore")

#import numpy as np
import pandas as pd
#from plotly.subplots import make_subplots
#import plotly.graph_objects as go
from statsbombpy import sb

player_name_mapper = {
    'Luis Alberto Suárez Díaz': 'Luis Suárez',
    'Daniel Alves da Silva': 'Alves',
    'Andrés Iniesta Luján': 'Iniesta',
    'Neymar da Silva Santos Junior': 'Neymar',
    'Munir El Haddadi Mohamed': 'Munir',
    'Sergi Roberto Carnicer': 'Sergi Roberto',
    'Sandro Ramírez Castillo': 'Sandro',
    'Marc Bartra Aregall': 'Marc Bartra',
    'Jordi Alba Ramos': 'Jordi Alba',
    'Gerard Piqué Bernabéu': 'Gerard Piqué',
    'Lionel Andrés Messi Cuccittini': 'Leo Messi',
    'Adriano Correia Claro': 'Adriano',
    'Rafael Alcântara do Nascimento': 'Rafa Alcántara',
    'Sergio Busquets i Burgos': 'Sergio Busquets',
    'Javier Alejandro Mascherano': 'Mascherano',
    'Aleix Vidal Parreu': 'Aleix Vidal'
}

def minute_string_to_float(x, hours=False):
    """
    Translate the minutes from string to float (e.g. '45:30' -> 45.5)
    """
    if hours:
        return int(x.split(':')[0])*60 + int(x.split(':')[1]) + float(x.split(':')[2])/60
    else:
        return int(x.split(':')[0]) + int(x.split(':')[1])/60


def prepare_team_data(team: str = 'Barcelona'):
    """
    
    """
    
    competition_row = sb.competitions()[
        (sb.competitions()['competition_name'] == 'La Liga') 
        & (sb.competitions()['season_name'] == '2015/2016')
    ]
    competition_id = pd.unique(
        competition_row['competition_id']
    )[0]
    season_id = pd.unique(
        competition_row['season_id']
    )[0]

    matches = sb.matches(competition_id=competition_id, season_id=season_id)

    team_matches = matches[(matches['home_team'] == team) | (matches['away_team'] == team)]

    for match_id in pd.unique(team_matches['match_id']):
        all_events = sb.events(match_id=match_id)
        all_events['minutes'] = all_events[
            (all_events['type'] == 'Half End') 
            & (all_events['team'] == team)
        ]['timestamp'].apply(lambda x: minute_string_to_float(x, True)).sum()

    # events
    all_events = all_events.merge(matches[['match_id', 'match_date']], on='match_id')
    all_events.replace({'player': player_name_mapper}, inplace=True)
    all_events['x'] = all_events['location'].apply(lambda x: x[0] if not isinstance(x, float) else x)
    all_events['y'] = all_events['location'].apply(lambda x: x[1] if not isinstance(x, float) else x)
    all_events['time'] =  all_events.apply(lambda x: f"{str(x['minute']).zfill(2)}:{str(x['second']).zfill(2)}", axis=1)
    all_events['float_time'] = all_events.minute + (all_events.second/60)
    
    #Standardize shots (origin on the bottom-left corner)
    all_events['y'] = 80 - all_events['y']

    # shots
    shots = all_events.loc[
        (all_events['type'] == 'Shot') 
        & (all_events['team'] == team) 
        & (all_events['shot_type'] == 'Open Play')
    ].set_index('id')

    shots['goal'] = shots['shot_outcome'] == 'Goal'
    shots = shots[[
        'match_id', 'x', 'y', 'float_time', 'player', 'shot_outcome', 
        'shot_type', 'minutes', 'goal', 'shot_statsbomb_xg'
    ]]

    # goals
    goals = shots[shots['shot_outcome'] == 'Goal']

    return all_events[['match_id', 'match_date', 'player', 'x', 'y', 'location', 'minute', 'minutes', 'float_time', 'pass_shot_assist']], shots, goals


def get_player_shots(player:str, shots, pitch=None):

    ## Scale x to dimensions
    #shots['x'] = (shots['x'] - 0) / (shots['x'].max() - 0) * (dimensions.pitch_length_metres - 0) + 0
    #shots['y'] = (shots['y'] - 0) / (shots['y'].max() - 0) * (dimensions.pitch_width_metres - 0) + 0

    if pitch is not None:
        shots['x'] = shots['x'] / (120 - 0) * (pitch.pitch_length if not pitch.half else pitch.pitch_length*2)
        shots['y'] = shots['y'] / (80 - 0) * pitch.pitch_width
        #shots['y'] =  pitch.pitch_width - shots['y']

        shots['x'] -= pitch.pitch_length if pitch.half else 0

    if player != 'All players':
        return shots[shots['player'] == player]
    return shots


def get_player_goals(player:str, goals: pd.DataFrame, pitch=None):

    ## Scale x to dimensions
    if pitch is not None:
        goals['x'] = goals['x'] / (120 - 0) * (pitch.pitch_length if not pitch.half else pitch.pitch_length*2)
        goals['y'] = goals['y'] / (80 - 0) * pitch.pitch_width
        #goals['y'] =  pitch.pitch_width - goals['y']

        goals['x'] -= pitch.pitch_length if pitch.half else 0

    if player != 'All players':
        return goals[goals['player'] == player]

    return goals


def get_player_events(player:str, events: pd.DataFrame, pitch=None):

    ## Scale x to dimensions
    if pitch is not None:
        events['x'] = events['x'] / (120 - 0) * (pitch.pitch_length if not pitch.half else pitch.pitch_length*2)
        events['y'] = events['y'] / (80 - 0) * pitch.pitch_width
        #events['y'] =  pitch.pitch_width - events['y']

        events['x'] -= pitch.pitch_length if pitch.half else 0

    if player != 'All players':
        return events[events['player'] == player]

    return events
    
    
def get_player_asists(player:str, events: pd.DataFrame, pitch=None):
    assists = events[events['pass_shot_assist'] == True]

    ## Scale x to dimensions
    if pitch is not None:
        assists['x'] = assists['x'] / (120 - 0) * (pitch.pitch_length if not pitch.half else pitch.pitch_length*2)
        assists['y'] = assists['y'] / (80 - 0) * pitch.pitch_width
        #assists['y'] =  pitch.pitch_width - assists['y']

        assists['x'] -= pitch.pitch_length if pitch.half else 0

        # Remove first-half assists
        assists = assists[assists['x'] >= 0]

    if player != 'All players':
        return assists[assists['player'] == player]

    return assists