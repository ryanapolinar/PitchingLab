import pandas as pd
import requests
import pybaseball as pyb
import streamlit as st
import numpy as np
import config

@st.cache_data(show_spinner=False)
def lookup_player_id(full_name: str) -> int:
    tokens = full_name.strip().split()
    if len(tokens) < 2:
        raise ValueError("Entity names require both First and Last parameters.")
    first_name, last_name = tokens[0], " ".join(tokens[1:])
    player_df = pyb.playerid_lookup(last_name, first_name)
    if player_df.empty:
        fuzzy_df = pyb.playerid_lookup(last_name, first_name, fuzzy=True)
        if not fuzzy_df.empty:
            return int(fuzzy_df.iloc[0]['key_mlbam'])
        raise ValueError(f"No entry tracking key found for: {full_name}")
    return int(player_df.iloc[0]['key_mlbam'])

@st.cache_data(show_spinner=False)
def fetch_pitcher_telemetry(pitcher_id: int, season: int) -> pd.DataFrame:
    return pyb.statcast_pitcher(f'{season}-01-01', f'{season}-12-31', pitcher_id)

@st.cache_data(show_spinner=False)
def fetch_biographical_metadata(player_id: int) -> dict:
    url = f"https://statsapi.mlb.com/api/v1/people?personIds={player_id}&hydrate=currentTeam"
    try:
        response = requests.get(url, timeout=10).json()
        if 'people' in response and len(response['people']) > 0:
            return response['people'][0]
    except Exception:
        pass
    return {}

def _calculate_fip(hr_count: int, bb_count: int, hbp_count: int, k_count: int, ip_str: str) -> str:
    """
    Helper function to mathematically compute Fielding Independent Pitching (FIP)
    from raw counting metrics using traditional standard tracking constraints.
    """
    try:
        # Convert Innings Pitched string fraction (e.g. "45.2") to actual true base-3 decimals
        if '.' in str(ip_str):
            parts = str(ip_str).split('.')
            ip_calc = float(parts[0]) + (float(parts[1]) / 3.0)
        else:
            ip_calc = float(ip_str)
    except Exception:
        ip_calc = 0.0

    if ip_calc > 0:
        fip_constant = 3.15  # Baseline normalization coefficient targeting standard league ERA tracks
        fip_val = (((13 * hr_count) + (3 * (bb_count + hbp_count)) - (2 * k_count)) / ip_calc) + fip_constant
        return f"{fip_val:.2f}"
    return "—"


@st.cache_data(show_spinner=False)
def fetch_fangraphs_leaderboard(season: int, pitcher_id: int) -> pd.DataFrame:
    """
    Direct endpoint tracking logic querying the official MLB Stats API for 
    isolated player summaries. Delegates FIP math out to a dedicated helper function.
    """
    try:
        url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats?stats=season&group=pitching&season={season}"
        response = requests.get(url, timeout=5).json()
        
        if 'stats' in response and response['stats']:
            splits = response['stats'][0]['splits']
            if splits:
                stats_data = splits[0]['stat']
                
                # Extract core metrics natively provided
                ip_str = stats_data.get('inningsPitched', '0.0')
                tbf = stats_data.get('battersFaced', 0)
                whip = stats_data.get('whip', '—')
                era = stats_data.get('era', '—')
                
                # Extract raw counts needed for ratios and helper function
                k_count = stats_data.get('strikeOuts', 0)
                bb_count = stats_data.get('baseOnBalls', 0)
                hr_count = stats_data.get('homeRuns', 0)
                hbp_count = stats_data.get('hitByPitch', 0)
                
                # Leverage the helper function for FIP tracking
                fip_display = _calculate_fip(hr_count, bb_count, hbp_count, k_count, ip_str)
                
                # Compute plate appearance rates matching FanGraphs definitions
                k_pct = (k_count / tbf * 100) if tbf > 0 else 0.0
                bb_pct = (bb_count / tbf * 100) if tbf > 0 else 0.0
                
                # Format into a clean table structure matching configuration metrics
                return pd.DataFrame([{
                    'IP': ip_str,
                    'TBF': tbf,
                    'WHIP': whip,
                    'ERA': era,
                    'FIP': fip_display,
                    'K%': f"{k_pct:.1f}%",
                    'BB%': f"{bb_pct:.1f}%",
                    'K-BB%': f"{(k_pct - bb_pct):.1f}%"
                }])
                
        return pd.DataFrame()
    except Exception as e:
        print(f"Direct backend API data collection fault: {e}")
        return pd.DataFrame()
    

@st.cache_data(show_spinner=False)
def fetch_statcast_group_averages() -> pd.DataFrame:
    import os
    if os.path.exists('statcast_2024_grouped.csv'):
        return pd.read_csv('statcast_2024_grouped.csv')
    return pd.DataFrame()

@st.cache_data(show_spinner="Fetching league baseline averages from Statcast...")
def fetch_dynamic_league_averages(year: int) -> pd.DataFrame:
    """
    Programmatically queries seasonal player arsenals from Baseball Savant 
    and transforms them into a structured DataFrame matching the legacy group layout.
    """
    try:
        # 1. Fetch player-level average speeds and spin rates
        speed_df = pyb.statcast_pitcher_pitch_arsenal(year, arsenal_type='avg_speed')
        spin_df = pyb.statcast_pitcher_pitch_arsenal(year, arsenal_type='avg_spin')
        
        # 2. Force Pandas to only calculate the mean for NUMERIC columns
        # This completely prevents string concatenation errors on name columns
        avg_speeds = speed_df.select_dtypes(include=['number']).mean()
        avg_spins = spin_df.select_dtypes(include=['number']).mean()
        
        # Combine the columns we successfully calculated
        all_columns = set(avg_speeds.index).union(set(avg_spins.index))
        records = []
        
        # 3. Filter out numeric metadata columns (like pitcher_id or year)
        # Statcast pitch types are typically 2 letters (e.g., 'ff', 'sl', 'ch')
        ignore_cols = {'pitcher_id', 'player_id', 'year'}
        valid_pitches = [col for col in all_columns if col not in ignore_cols and len(str(col)) <= 2]
        
        for p in valid_pitches:
            records.append({
                'pitch_type': p.upper(), # Map to 'FF', 'SL', etc.
                'release_speed': avg_speeds.get(p, np.nan),
                'spin_rate': avg_spins.get(p, np.nan),
                # Legacy placeholders to ensure visualization logic doesn't break
                'xwoba': np.nan,
                'delta_run_exp_per_100': np.nan
            })
            
        return pd.DataFrame(records)

    except Exception as e:
        st.warning(f"Could not load live league averages for {year} ({e}). Falling back to empty framework.")
        return pd.DataFrame(columns=['pitch_type', 'release_speed', 'spin_rate', 'xwoba', 'delta_run_exp_per_100'])
    
@st.cache_data(show_spinner=False)
def fetch_logo(pitcher_id: int) -> str:
    """
    Fetches the team logo URL for a target pitcher using the MLB Stats API 
    and mapping it to team ESPN scoreboard asset links.
    """
    try:
        # 1. Fetch player metadata to discover hydration team keys
        url = f"https://statsapi.mlb.com/api/v1/people?personIds={pitcher_id}&hydrate=currentTeam"
        data = requests.get(url).json()
        
        # 2. Extract relative endpoint link to the team file
        team_link = data['people'][0]['currentTeam']['link']
        url_team = f"https://statsapi.mlb.com{team_link}"
        data_team = requests.get(url_team).json()
        
        # 3. Read abbreviation code string
        team_abb = data_team['teams'][0]['abbreviation']
        
        # 4. Extract URL string mapping or fall back to a safe transparent block if absent
        return config.MLB_TEAMS_LOGOS.get(team_abb, "")
        
    except Exception:
        # Fail gracefully to avoid application runtime layout crashes
        return ""