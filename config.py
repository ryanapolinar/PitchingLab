import matplotlib as mpl
import seaborn as sns
import matplotlib.colors as mcolors

# Set global graphic resolution properties
mpl.rcParams['figure.dpi'] = 300

FONT_PROPERTIES = {'family': 'DejaVu Sans', 'size': 11}
FONT_PROPERTIES_TITLES = {'family': 'DejaVu Sans', 'size': 14, 'weight': 'bold'}
FONT_PROPERTIES_AXES = {'family': 'DejaVu Sans', 'size': 12}

def init_plotting_theme():
    sns.set_theme(style='whitegrid', font='DejaVu Sans', font_scale=1.0)

PITCH_COLORS = {
    'FF': {'color': '#FF007D', 'name': '4-Seam Fastball'},
    'FA': {'color': '#FF007D', 'name': 'Fastball'},
    'SI': {'color': '#98165D', 'name': 'Sinker'},
    'FC': {'color': '#BE5FA0', 'name': 'Cutter'},
    'CH': {'color': '#F79E70', 'name': 'Changeup'},
    'FS': {'color': '#FE6100', 'name': 'Splitter'},
    'SC': {'color': '#F08223', 'name': 'Screwball'},
    'FO': {'color': '#FFB000', 'name': 'Forkball'},
    'SL': {'color': '#67E18D', 'name': 'Slider'},
    'ST': {'color': '#1BB999', 'name': 'Sweeper'},
    'SV': {'color': '#376748', 'name': 'Slurve'},
    'KC': {'color': '#311D8B', 'name': 'Knuckle Curve'},
    'CU': {'color': '#3025CE', 'name': 'Curveball'},
    'CS': {'color': '#274BFC', 'name': 'Slow Curve'},
    'EP': {'color': '#648FFF', 'name': 'Eephus'},
    'KN': {'color': '#867A08', 'name': 'Knuckleball'},
    'PO': {'color': '#472C30', 'name': 'Pitch Out'},
    'UN': {'color': '#9C8975', 'name': 'Unknown'},
}

DICT_COLOR = {k: v['color'] for k, v in PITCH_COLORS.items()}
DICT_PITCH = {k: v['name'] for k, v in PITCH_COLORS.items()}

# Diverging color ramps for cell benchmark highlighting
CMAP_SUM = mcolors.LinearSegmentedColormap.from_list("", ['#648FFF','#FFFFFF','#FFB000'])
CMAP_SUM_R = mcolors.LinearSegmentedColormap.from_list("", ['#FFB000','#FFFFFF','#648FFF'])
COLOR_STATS_TO_HIGHLIGHT = ['release_speed', 'release_extension', 'delta_run_exp_per_100', 'whiff_rate', 'in_zone_rate', 'chase_rate', 'xwoba']

# FanGraphs Metadata Configuration Lookup Map
FANGRAPHS_STATS = ['IP','TBF','WHIP','ERA', 'FIP', 'K%', 'BB%', 'K-BB%']
FANGRAPHS_STATS_DICT = {
    'IP': {'table_header': r'$\bf{IP}$', 'format': '.1f'},
    'TBF': {'table_header': r'$\bf{PA}$', 'format': '.0f'},
    'AVG': {'table_header': r'$\bf{AVG}$', 'format': '.3f'},
    'K/9': {'table_header': r'$\bf{K\/9}$', 'format': '.2f'},
    'BB/9': {'table_header': r'$\bf{BB\/9}$', 'format': '.2f'},
    'K/BB': {'table_header': r'$\bf{K\/BB}$', 'format': '.2f'},
    'HR/9': {'table_header': r'$\bf{HR\/9}$', 'format': '.2f'},
    'K%': {'table_header': r'$\bf{K\%}$', 'format': '.1%'},
    'BB%': {'table_header': r'$\bf{BB\%}$', 'format': '.1%'},
    'K-BB%': {'table_header': r'$\bf{K-BB\%}$', 'format': '.1%'},
    'WHIP': {'table_header': r'$\bf{WHIP}$', 'format': '.2f'},
    'BABIP': {'table_header': r'$\bf{BABIP}$', 'format': '.3f'},
    'LOB%': {'table_header': r'$\bf{LOB\%}$', 'format': '.1%'},
    'xFIP': {'table_header': r'$\bf{xFIP}$', 'format': '.2f'},
    'FIP': {'table_header': r'$\bf{FIP}$', 'format': '.2f'},
    'ERA': {'table_header': r'$\bf{ERA}$', 'format': '.2f'}
}

# Statcast Pitch Presentation Matrix Rules
PITCH_STATS_DICT = {
    'pitch': {'table_header': r'$\bf{Count}$', 'format': '.0f'},
    'release_speed': {'table_header': r'$\bf{Velocity}$', 'format': '.1f'},
    'pfx_z': {'table_header': r'$\bf{iVB}$', 'format': '.1f'},
    'pfx_x': {'table_header': r'$\bf{HB}$', 'format': '.1f'},
    'release_spin_rate': {'table_header': r'$\bf{Spin}$', 'format': '.0f'},
    'release_pos_x': {'table_header': r'$\bf{hRel}$', 'format': '.1f'},
    'release_pos_z': {'table_header': r'$\bf{vRel}$', 'format': '.1f'},
    'release_extension': {'table_header': r'$\bf{Ext.}$', 'format': '.1f'},
    'xwoba': {'table_header': r'$\bf{xwOBA}$', 'format': '.3f'},
    'pitch_usage': {'table_header': r'$\bf{Pitch\%}$', 'format': '.1%'},
    'whiff_rate': {'table_header': r'$\bf{Whiff\%}$', 'format': '.1%'},
    'in_zone_rate': {'table_header': r'$\bf{Zone\%}$', 'format': '.1%'},
    'chase_rate': {'table_header': r'$\bf{Chase\%}$', 'format': '.1%'},
    'delta_run_exp_per_100': {'table_header': r'$\bf{RV\//100}$', 'format': '.1f'}
}

TABLE_COLUMNS = [
    'pitch_description', 'pitch', 'pitch_usage', 'release_speed', 'pfx_z', 'pfx_x',
    'release_spin_rate', 'release_pos_x', 'release_pos_z', 'release_extension',
    'delta_run_exp_per_100', 'whiff_rate', 'in_zone_rate', 'chase_rate', 'xwoba'
]

MLB_TEAMS_LOGOS = {
    "AZ": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/ari.png&h=500&w=500",
    "ATL": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/atl.png&h=500&w=500",
    "BAL": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/bal.png&h=500&w=500",
    "BOS": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/bos.png&h=500&w=500",
    "CHC": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/chc.png&h=500&w=500",
    "CWS": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/chw.png&h=500&w=500",
    "CIN": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/cin.png&h=500&w=500",
    "CLE": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/cle.png&h=500&w=500",
    "COL": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/col.png&h=500&w=500",
    "DET": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/det.png&h=500&w=500",
    "HOU": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/hou.png&h=500&w=500",
    "KC": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/kc.png&h=500&w=500",
    "LAA": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/laa.png&h=500&w=500",
    "LAD": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/lad.png&h=500&w=500",
    "MIA": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/mia.png&h=500&w=500",
    "MIL": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/mil.png&h=500&w=500",
    "MIN": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/min.png&h=500&w=500",
    "NYM": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/nym.png&h=500&w=500",
    "NYY": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/nyy.png&h=500&w=500",
    "OAK": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/oak.png&h=500&w=500",
    "PHI": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/phi.png&h=500&w=500",
    "PIT": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/pit.png&h=500&w=500",
    "SD": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/sd.png&h=500&w=500",
    "SF": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/sf.png&h=500&w=500",
    "SEA": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/sea.png&h=500&w=500",
    "STL": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/stl.png&h=500&w=500",
    "TB": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/tb.png&h=500&w=500",
    "TEX": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/tex.png&h=500&w=500",
    "TOR": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/tor.png&h=500&w=500",
    "WSH": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/wsh.png&h=500&w=500"
}