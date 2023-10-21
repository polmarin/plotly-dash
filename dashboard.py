import base64
import os
import re
from unidecode import unidecode

from dash import html, Dash, dcc, Input, Output, callback
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.functions import prepare_team_data, get_player_events, get_player_shots, get_player_asists
from src.classes import FootballPitch

# Constants
COLOR_SCALE = px.colors.sequential.Reds[:1] + px.colors.sequential.Sunsetdark
DIMENSIONS = (105, 68)
EVENTS, SHOTS, ASSISTS = prepare_team_data()
PLAYER_OPTIONS = ['All players'] + sorted(SHOTS['player'].unique().tolist())
IMGS = {
    img: base64.b64encode(open(os.getcwd()+'/src/img/'+img, 'rb').read()).decode('ascii')
    for img in os.listdir(os.getcwd()+'/src/img')
}
ORDERED_MATCHDAYS = EVENTS.sort_values('match_date')['match_id'].unique().tolist()

# Variables
div_factor = 3 # CONVERTIR A DROPDOWN

@callback(
    Output('player_img', 'src'),
    Input('player_dropdown', 'value')
)
def update_player_img(player):
    norm_player = unidecode(re.sub(r'\W+', '', player)).lower()

    for player_img in IMGS:
        if norm_player in player_img:
            return f'data:image/jpeg;base64,{IMGS[player_img]}'
        
    return ''

@callback(
    Output('shot_distribution', 'figure'),
    Input('player_dropdown', 'value'),
    Input('game_slider', 'value'),
    Input('minute_slider', 'value')
)
def create_shot_distribution(player, game_range, minute_range):
    pitch = FootballPitch(half=True)
    fig = pitch.plot_pitch(False, bg_color='#C1E1C1', zoom_ratio=0.8) 

    # Apply filters
    if isinstance(game_range, str):
        game_range = game_range[1:-1].split(',')
    if isinstance(minute_range, str):
        minute_range = minute_range[1:-1].split(',')
    if 90 in minute_range:
        # afegir extra time
        minute_range[1] = 130

    player_shots = get_player_shots(player, SHOTS.copy(), pitch)
    player_shots = player_shots[
        (player_shots['match_id'].isin(ORDERED_MATCHDAYS[int(game_range[0])-1:int(game_range[1])]))
        & (player_shots['float_time'].between(int(minute_range[0])-1, int(minute_range[1])))
    ]
    #print(player_shots)

    scatter_colors = ["#E7E657", "#57C8E7"]

    for i, group in enumerate([True, False]):
        fig.add_trace(go.Scatter(
            x=player_shots[player_shots['goal'] == group]['x'],
            y=player_shots[player_shots['goal'] == group]['y'],
            mode="markers",
            name='Goal' if group else 'No Goal',
            marker=dict(
                color=scatter_colors[i],
                size=8,
                line=dict(
                    color='black',
                    width=1
                )
            ),
            #marker_color=scatter_colors[i] # #E7E657 i #57C8E7  
        ))

    fig.update_layout(
    #    title='Shot distribution'
        margin=dict(l=20, r=20, t=5, b=20),
    )

    return fig


@callback(
    Output('assist_distribution', 'figure'),
    Input('player_dropdown', 'value'),
    Input('game_slider', 'value'),
    Input('minute_slider', 'value')
)
def create_assist_distribution(player, game_range, minute_range):
    pitch = FootballPitch(half=True)
    fig = pitch.plot_pitch(False, bg_color='#C1E1C1', zoom_ratio=0.8) 

    # Apply filters
    if isinstance(game_range, str):
        game_range = game_range[1:-1].split(',')
    if isinstance(minute_range, str):
        minute_range = minute_range[1:-1].split(',')
    if 90 in minute_range:
        # afegir extra time
        minute_range[1] = 130

    player_assists = get_player_asists(player, ASSISTS.copy(), pitch)
    player_assists = player_assists[
        (player_assists['match_id'].isin(ORDERED_MATCHDAYS[int(game_range[0])-1:int(game_range[1])]))
        & (player_assists['float_time'].between(int(minute_range[0])-1, int(minute_range[1])))
    ]

    scatter_colors = ["#E7E657", "#57C8E7"]
 
    fig.add_trace(go.Scatter(
        x=player_assists['x'],
        y=player_assists['y'],
        mode="markers",
        #name='Goal' if group else 'No Goal',
        marker=dict(
            color=scatter_colors[0],
            size=8,
            line=dict(
                color='black',
                width=1
            )
        ),
        #marker_color=scatter_colors[i] # #E7E657 i #57C8E7  
    ))

    fig.update_layout(
        margin=dict(l=20, r=20, t=5, b=20),
        showlegend=False
    )

    return fig


@callback(
    Output('player_heatmap', 'figure'),
    Input('player_dropdown', 'value'),
    Input('game_slider', 'value'),
    Input('minute_slider', 'value')
)
def create_player_heatmap(player, game_range, minute_range):
    pitch = FootballPitch()

    # Apply filters
    if isinstance(game_range, str):
        game_range = game_range[1:-1].split(',')
    if isinstance(minute_range, str):
        minute_range = minute_range[1:-1].split(',')
    if 90 in minute_range:
        # afegir extra time
        minute_range[1] = 130

    player_events = get_player_events(player, EVENTS.copy(), pitch)
    player_events = player_events[
        (player_events['match_id'].isin(ORDERED_MATCHDAYS[int(game_range[0])-1:int(game_range[1])]))
        & (player_events['float_time'].between(int(minute_range[0])-1, int(minute_range[1])))
    ]

    xy = div_factor * (player_events[['x', 'y', 'minutes']]/div_factor).round()
    xy = xy.groupby(['x', 'y']).count()[['minutes']]

    data = []
    for j in range(0, int(pitch.pitch_width), div_factor):
        for i in range(0, int(pitch.pitch_length), div_factor):
            #print(j, i)
            if i == 0 and j < pitch.pitch_width:
                data += [[]]
            if j < pitch.pitch_width:
                try:
                    if (i, j) in xy.index:
                        data[int(j/div_factor)].append(xy.loc[(i,j)].values[0])
                    else:
                        data[int(j/div_factor)].append(0)
                except:
                    pass
                
    data = np.asarray(data)

    if data.any():
        fig = pitch.plot_heatmap(data, zsmooth='best', zoom_ratio=0.8)
    fig.update_layout(
    #    title='Player Heatmap'
        margin=dict(l=20, r=20, t=25, b=20),
        #plot_bgcolor=COLOR_SCALE[0],
    )

    return fig


@callback(
    Output('shots_by_quarter', 'figure'),
    Input('player_dropdown', 'value'),
    Input('game_slider', 'value')
)
def create_shots_by_quarter(player, game_range):
    fig = make_subplots()

    # Apply filters
    if isinstance(game_range, str):
        game_range = game_range[1:-1].split(',')

    shots = SHOTS[
        (SHOTS['match_id'].isin(ORDERED_MATCHDAYS[int(game_range[0])-1:int(game_range[1])]))
    ]

    max_shots = 0

    for p in shots.player.unique():
        player_shots = get_player_shots(p, shots)

        xy = 15 * (player_shots[['float_time', 'minutes']]/15).round()
        xy = xy.groupby(['float_time']).count()[['minutes']]

        max_shots = xy.minutes.max() if xy.minutes.max() > max_shots else max_shots
        
        fig.add_trace(
            go.Scatter(
                name=p,
                x = xy.index, 
                y = xy.minutes,
                mode='lines',
                opacity=1 if p == player else 0.2
            )
        )

    # Add team's avg
    xy = 15 * (shots[['float_time', 'minutes']]/15).round()
    xy = xy.groupby(['float_time']).count()[['minutes']]/len(shots.player.unique())

    fig.add_trace(
        go.Scatter(
            name="Team's Average",
            x = xy.index, 
            y = xy.minutes,
            line = go.scatter.Line(dash='dash'),
            marker=None,
            mode='lines'
        )
    )

    fig.update_xaxes(range=[0, 91])
    fig.update_layout(
        #title='Shots by Quarter',
        margin=dict(l=20, r=20, t=5, b=20),
        xaxis = dict(
            tickmode = 'array',
            tickvals = xy.index.values
        ),
        height=200,
        plot_bgcolor="#F9F9F9", #COLOR_SCALE[0],
        paper_bgcolor="#F9F9F9", #COLOR_SCALE[0],
        yaxis_range=[-3,max_shots+5]
    )

    return fig


@callback(
    Output('goals_vs_xg', 'figure'),
    Input('player_dropdown', 'value'),
    Input('game_slider', 'value'),
    Input('minute_slider', 'value')
)
def create_goals_vs_xg(player, game_range, minute_range):

    # Apply filters
    if isinstance(game_range, str):
        game_range = game_range[1:-1].split(',')
    if isinstance(minute_range, str):
        minute_range = minute_range[1:-1].split(',')
    if 90 in minute_range:
        # afegir extra time
        minute_range[1] = 130

    shots = SHOTS[
        (SHOTS['match_id'].isin(ORDERED_MATCHDAYS[int(game_range[0])-1:int(game_range[1])]))
        & (SHOTS['float_time'].between(int(minute_range[0])-1, int(minute_range[1])))
    ]

    # Compute team's avg xg and cumsum it
    team_avg_xg = pd.merge(shots.groupby('match_id')[['shot_statsbomb_xg']].sum(), shots.groupby('match_id')[['player']].nunique(), on='match_id')
    team_avg_xg['team_avg_xg'] = team_avg_xg['shot_statsbomb_xg']/team_avg_xg['player']

    goals_vs_expected = team_avg_xg.copy()
    data = []

    if player != 'All players':
        player_shots = get_player_shots(player, shots)

        goals_vs_expected = player_shots.groupby(['match_id', 'player'])[['shot_statsbomb_xg', 'goal']].sum()
        
        # Add cum values
        goals_vs_expected['cum_goal'] = goals_vs_expected['goal'].cumsum()
        goals_vs_expected['cum_shot_statsbomb_xg'] = goals_vs_expected['shot_statsbomb_xg'].cumsum()

        data = [
            go.Scatter(
                name='xG over time', 
                x = [*range(len(goals_vs_expected.index.get_level_values(0)))], 
                y=goals_vs_expected['cum_shot_statsbomb_xg'],
                marker=None,
                marker_color=COLOR_SCALE[-1]
            ),
            go.Scatter(
                name='goals over time', 
                x = [*range(len(goals_vs_expected.index.get_level_values(0)))], 
                y=goals_vs_expected['cum_goal'],
                marker=None,
                marker_color=COLOR_SCALE[0]
            )
        ]

        # Team avg
        goals_vs_expected = goals_vs_expected.merge(team_avg_xg, on='match_id')
        

    goals_vs_expected['cum_team_avg_xg'] = team_avg_xg['team_avg_xg'].cumsum()
    
    fig = go.Figure(data = data + [
        go.Scatter(
            name="Team's avg xG over time", 
            x = [*range(len(goals_vs_expected.index.get_level_values(0)))], 
            y=goals_vs_expected['cum_team_avg_xg'], 
            line = go.scatter.Line(dash='dash'),
            marker_color=COLOR_SCALE[-2]
        )
    ])
    
    fig.update_layout(
    #    title='xG and goals over time',
        margin=dict(l=20, r=20, t=5, b=20),
        height=200,
        plot_bgcolor="#F9F9F9", #COLOR_SCALE[0],
        paper_bgcolor="#F9F9F9", #COLOR_SCALE[0],
        yaxis_range=[-3, goals_vs_expected['cum_team_avg_xg'].max()+5]
    )

    return fig


app = Dash(__name__) 

shot_distribution_graph = html.Div(
    [
        html.H2('Shot Distribution'),
        dcc.Graph(id='shot_distribution', figure={})
    ], 
    style={
        'grid-column-start' : 'first',
        'grid-column-end' : 'second',
        'grid-row-start': 'first-r',
        'grid-row-end': 'second-r', 
        'padding': '2%',
        'margin': 'auto',
    }
)

assist_distribution_graph = html.Div(
    [
        html.H2('Assist Distribution'), 
        dcc.Graph(id='assist_distribution', figure={})
    ], 
    style={
        'grid-column-start' : 'second',
        'grid-column-end' : 'third',
        'grid-row-start': 'first-r',
        'grid-row-end': 'second-r', 
        'padding': '2%',
        'margin': 'auto',
    }
)

filter = html.Div([
    dcc.Dropdown(PLAYER_OPTIONS,
        'All players', 
        id='player_dropdown', 
        style={'width': '200px', 'margin': '20px auto', 'text-align': 'left'}
    ),
    html.Img(
        id='player_img',
        style={'margin': '20px auto'}
    ),
    html.P(
        'Matchdays:', style={'text-align': 'left'}
    ),
    dcc.RangeSlider(
        1, 38, 1, 
        {k:str(k) for k in range(1, 38, 4)}, 
        value=[1, 38], id='game_slider', allowCross=False,
    ),
    html.P(
        'Time in match:', style={'text-align': 'left', 'margin-top': '20px'}
    ),
    dcc.RangeSlider(
        0, 90, 15, 
        {k:str(k) for k in range(0, 91, 15)}, 
        value=[1, 90], id='minute_slider', allowCross=False
    )
    ], style={
        'grid-column-start' : 'third',
        'grid-column-end' : 'span 1',
        'grid-row-start': 'first-r',
        'grid-row-end': 'second-r', 
        'padding': '2% 20%',
        'text-align': 'center'
    }
)

player_heatmap = html.Div(
    [
        html.H2('Player Heatmap'), 
        dcc.Graph(id='player_heatmap', figure={})
    ], 
    style={
        'grid-column-start' : 'first',
        'grid-column-end' : 'span 2',
        'grid-row-start': 'second-r',
        'grid-row-end': 'third-r',
        'align-self': 'center',
        'margin': '0 auto',
    }
)

heatmap_text = html.Div([
    html.P(
        children=["The player heatmap shows the areas where the player had the most" \
                "influence during the selected time period.", html.Br(), html.Br(),
                "In other words, shows where the player interacted with the ball " \
                "the most (be it assisting, passing, shooting, intercepting...)"],
        style = {
            'font-size': '25px',
        }
    )
    ],
    style={
        'grid-column-start' : 'third',
        'grid-column-end' : 'span 1',
        'grid-row-start': 'second-r',
        'grid-row-end': 'third-r',
        'align-self': 'center',
        'padding': '2%'
    }
)

shots_by_quarter = html.Div(
    [
        html.H2('Shots By Quarter', style={'margin-top': '20px'}),
        dcc.Graph(id='shots_by_quarter', figure={})
    ],
    style={
        'grid-column-start' : 'first',
        'grid-column-end' : 'span 3',
        'grid-row-start': 'third-r',
        'grid-row-end': 'fourth-r',
        'padding': '2%'
    }
)

goals_vs_xg = html.Div(
    [
        html.H2('Goals vs xG (cumulated)', style={'margin-top': '20px'}),
        dcc.Graph(id='goals_vs_xg', figure={})
    ],
    style={
        'grid-column-start' : 'first',
        'grid-column-end' : 'span 3',
        'grid-row-start': 'fourth-r',
        'grid-row-end': 'span 1',
        'padding': '2%'
    }
)

app.layout = html.Div([
    html.Div([
        shot_distribution_graph, assist_distribution_graph, filter, player_heatmap, heatmap_text, shots_by_quarter, goals_vs_xg
    ], style={
        'width': '1650px',
        #'border': '1px solid black',
        'display': 'inline-grid',
        'grid-template-columns': '[first] 550px [second] 550px [third] 550px',
        'grid-template-rows': '[first-r] 500px [second-r] 820px [third-r] 300px [fourth-r] 350px',
        'font-family': 'Tahoma, sans-serif',
        'text-align': 'left'
        #'grid-gap': '10px',
        #'align-items': 'right',
    })
], style={'text-align': 'center'})

# Run app
if __name__ == '__main__':
    app.run(debug=True)


## CREC QUE HAURE DE NORMALITZAR Y TAMBÉ ALS HEATMAPS I PLOTS DE CAMP