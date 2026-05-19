import pandas as pd
import numpy as np
from config import DICT_PITCH, DICT_COLOR

class StatcastProcessor:
    SWING_CLASSIFICATIONS = ['foul_bunt','foul','hit_into_play','swinging_strike', 'foul_tip', 'swinging_strike_blocked','missed_bunt','bunt_foul_tip']
    WHIFF_CLASSIFICATIONS = ['swinging_strike', 'foul_tip', 'swinging_strike_blocked']

    @classmethod
    def clean_and_augment(cls, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df = df.copy()
        df['swing'] = df['description'].isin(cls.SWING_CLASSIFICATIONS)
        df['whiff'] = df['description'].isin(cls.WHIFF_CLASSIFICATIONS)
        df['in_zone'] = df['zone'] < 10
        df['out_zone'] = df['zone'] >= 10
        df['chase'] = (df['in_zone'] == False) & (df['swing'] == True)
        
        if 'pfx_z' in df.columns: df['pfx_z'] = df['pfx_z'] * 12
        if 'pfx_x' in df.columns: df['pfx_x'] = df['pfx_x'] * 12
        return df

    @classmethod
    def aggregate_pitch_metrics(cls, df: pd.DataFrame):
        """Converts raw logs into pitch aggregation matrices for the data table."""
        if df.empty:
            return pd.DataFrame(), []
            
        df_group = df.groupby(['pitch_type']).agg(
            pitch=('pitch_type','count'),
            release_speed=('release_speed','mean'),
            pfx_z=('pfx_z','mean'),
            pfx_x=('pfx_x','mean'),
            release_spin_rate=('release_spin_rate','mean'),
            release_pos_x=('release_pos_x','mean'),
            release_pos_z=('release_pos_z','mean'),
            release_extension=('release_extension','mean'),
            delta_run_exp=('delta_run_exp','sum'),
            swing=('swing','sum'),
            whiff=('whiff','sum'),
            in_zone=('in_zone','sum'),
            out_zone=('out_zone','sum'),
            chase=('chase','sum'),
            xwoba=('estimated_woba_using_speedangle','mean'),
        ).reset_index()

        df_group['pitch_description'] = df_group['pitch_type'].map(DICT_PITCH)
        df_group['pitch_usage'] = df_group['pitch'] / df_group['pitch'].sum()
        df_group['whiff_rate'] = df_group['whiff'] / df_group['swing']
        df_group['in_zone_rate'] = df_group['in_zone'] / df_group['pitch']
        df_group['chase_rate'] = df_group['chase'] / df_group['out_zone']
        df_group['delta_run_exp_per_100'] = -df_group['delta_run_exp'] / df_group['pitch'] * 100
        df_group['color'] = df_group['pitch_type'].map(DICT_COLOR)

        df_group = df_group.sort_values(by='pitch_usage', ascending=False)
        color_list = df_group['color'].fillna('#808080').tolist()

        # Build 'All' summary breakdown row
        all_row = pd.DataFrame([{
            'pitch_type': 'All', 'pitch_description': 'All', 'pitch': df['pitch_type'].count(),
            'pitch_usage': 1.0, 'release_speed': np.nan, 'pfx_z': np.nan, 'pfx_x': np.nan,
            'release_spin_rate': np.nan, 'release_pos_x': np.nan, 'release_pos_z': np.nan,
            'release_extension': df['release_extension'].mean(),
            'delta_run_exp_per_100': (df['delta_run_exp'].sum() / df['pitch_type'].count() * -100),
            'whiff_rate': df['whiff'].sum() / df['swing'].sum() if df['swing'].sum() > 0 else 0,
            'in_zone_rate': df['in_zone'].sum() / df['pitch_type'].count(),
            'chase_rate': df['chase'].sum() / df['out_zone'].sum() if df['out_zone'].sum() > 0 else 0,
            'xwoba': df['estimated_woba_using_speedangle'].mean()
        }])
        
        return pd.concat([df_group, all_row], ignore_index=True), color_list

    @classmethod
    def filter_matchup_matrix(cls, pitcher_df: pd.DataFrame, batter_id: int) -> pd.DataFrame:
        if pitcher_df.empty or 'batter' not in pitcher_df.columns:
            return pitcher_df
        return pitcher_df[pitcher_df['batter'] == batter_id]