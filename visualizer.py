import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
import math
import requests
import matplotlib.colors as mcolors
from PIL import Image
from io import BytesIO
import matplotlib.gridspec as gridspec
from config import (
    DICT_PITCH, DICT_COLOR, FANGRAPHS_STATS_DICT, PITCH_STATS_DICT, 
    TABLE_COLUMNS, CMAP_SUM, CMAP_SUM_R, COLOR_STATS_TO_HIGHLIGHT,
    FONT_PROPERTIES, FONT_PROPERTIES_TITLES, FONT_PROPERTIES_AXES
)
import math

class PitchVisualizer:
    @staticmethod
    def render_headshot(player_id: int, ax: plt.Axes):
        url = f'https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_640,q_auto:best/v1/people/{player_id}/headshot/silo/current.png'
        try:
            res = requests.get(url, timeout=5)
            img = Image.open(BytesIO(res.content))
            ax.imshow(img, extent=[0, 1, 0, 1], origin='upper')
        except Exception:
            ax.text(0.5, 0.5, "Photo N/A", ha='center', va='center')
        ax.axis('off')

    @staticmethod
    def render_logo(logo_url, ax: plt.Axes):
        if logo_url:
            try:
                response = requests.get(logo_url, timeout=5)
                img = Image.open(BytesIO(response.content))
                
                ax.set_xlim(0, 1.3)
                ax.set_ylim(0, 1)
                ax.imshow(img, extent=[0.15, 1.15, 0, 1], origin='upper')
            except Exception:
                ax.text(0.5, 0.5, "Logo\nLoad Error", ha='center', va='center', color='#A0AEC0')
        else:
            ax.text(0.5, 0.5, "No Team\nLogo", ha='center', va='center', color='#A0AEC0')
        ax.axis('off')

    @staticmethod
    def render_biographical_text(bio_data: dict, ax: plt.Axes):
        name = bio_data.get('fullName', 'Unknown Profile')
        hand = bio_data.get('pitchHand', {}).get('code', 'R')
        age = bio_data.get('currentAge', '--')
        height = bio_data.get('height', '--')
        weight = bio_data.get('weight', '--')

        ax.text(0.5, 0.95, name, va='top', ha='center', fontsize=22, weight='bold')
        ax.text(0.5, 0.60, f'{hand}HP\nAge: {age}\nHeight: {height}\nWeight: {weight}', va='top', ha='center', fontsize=12)
        ax.axis('off')

    @staticmethod
    def render_fangraphs_table(pitcher_id: int, df_leaderboard: pd.DataFrame, stats: list, ax: plt.Axes):
        """Draws the FanGraphs season summary banner block."""
        if df_leaderboard.empty:
            ax.text(0.5, 0.5, "FanGraphs Baseline Matrix N/A", ha='center', va='center')
            ax.axis('off')
            return

        matched_row = df_leaderboard[df_leaderboard['xMLBAMID'] == pitcher_id]
        if matched_row.empty:
            ax.text(0.5, 0.5, f"No FanGraphs Stats Found For This Season", ha='center', va='center')
            ax.axis('off')
            return

        df_row = matched_row[stats].reset_index(drop=True).astype(object)
        for col in stats:
            val = df_row.loc[0, col]
            fmt_str = FANGRAPHS_STATS_DICT.get(col, {}).get('format', '.2f')
            df_row.loc[0, col] = format(float(val), fmt_str) if (pd.notnull(val) and val != '---') else '---'

        table_fg = ax.table(cellText=df_row.values, colLabels=stats, cellLoc='center', bbox=[0, 0, 1, 1])
        table_fg.set_fontsize(12)
        
        for i, col in enumerate(stats):
            hdr = FANGRAPHS_STATS_DICT.get(col, {}).get('table_header', col)
            table_fg.get_celld()[(0, i)].get_text().set_text(hdr)
        ax.axis('off')

    @staticmethod
    def render_velocity_distributions(df: pd.DataFrame, ax, fig, df_statcast_league_averages: pd.DataFrame = None):
        """Plots vertically aligned pitch distributions sharing a uniform horizontal velocity axis scale."""
        counts = df['pitch_type'].value_counts().sort_values(ascending=False)
        pitch_types = counts.index.tolist()
        if not pitch_types: return
        ax.set_title('Pitch Velocity Distribution', fontdict=FONT_PROPERTIES_TITLES)

        # Hide grid lines
        ax.axis('off')
        

        # Set up inner grids
        inner_gs = gridspec.GridSpecFromSubplotSpec(
            nrows=len(pitch_types), 
            ncols=1, 
            subplot_spec=ax.get_subplotspec()
        )
        
        # Plot each pitch type's velocity histogram
        ax_number = 0
        ax_top = []
        for inner in inner_gs:
            ax_top.append(fig.add_subplot(inner))
        for pitch in pitch_types:
            # Check if all release speeds for the pitch type are the same
            if np.unique(df[df['pitch_type'] == pitch]['release_speed']).size == 1:
                # Plot a single line if all values are the same
                ax_top[ax_number].plot([np.unique(df[df['pitch_type'] == pitch]['release_speed']),
                                        np.unique(df[df['pitch_type'] == pitch]['release_speed'])], [0, 1], linewidth=4,
                                    color=DICT_COLOR[df[df['pitch_type'] == pitch]['pitch_type'].values[0]], zorder=20)
            else:
                # Plot the KDE for the release speeds
                sns.kdeplot(df[df['pitch_type'] == pitch]['release_speed'], ax=ax_top[ax_number], fill=True,
                            clip=(df[df['pitch_type'] == pitch]['release_speed'].min(), df[df['pitch_type'] == pitch]['release_speed'].max()),
                            color=DICT_COLOR[df[df['pitch_type'] == pitch]['pitch_type'].values[0]])
            
            # Plot the mean release speed for the current data
            df_average = df[df['pitch_type'] == pitch]['release_speed']
            ax_top[ax_number].plot([df_average.mean(), df_average.mean()],
                                [ax_top[ax_number].get_ylim()[0], ax_top[ax_number].get_ylim()[1]],
                                color=DICT_COLOR[df[df['pitch_type'] == pitch]['pitch_type'].values[0]],
                                linestyle='--')

            # Plot the mean release speed for the statcast group data (league mean)
            speed_name = f"{pitch.lower()}_avg_speed"
            spin_name = f"{pitch.lower()}_avg_spin"
            league_avg_speed = getattr(df_statcast_league_averages, speed_name, np.nan)
            # @TODO: use avg_spin somewhere!
            league_avg_spin  = getattr(df_statcast_league_averages, spin_name, np.nan)
            ax_top[ax_number].plot([league_avg_speed, league_avg_speed],
                                [ax_top[ax_number].get_ylim()[0], ax_top[ax_number].get_ylim()[1]],
                                color=DICT_COLOR[df[df['pitch_type'] == pitch]['pitch_type'].values[0]],
                                linestyle=':')

            # Set the x-axis limits
            ax_top[ax_number].set_xlim(math.floor(df['release_speed'].min() / 5) * 5, math.ceil(df['release_speed'].max() / 5) * 5)
            ax_top[ax_number].set_xlabel('')
            ax_top[ax_number].set_ylabel('')

            # Hide the top, right, and left spines for all but the last subplot
            if ax_number < len(pitch_types) - 1:
                ax_top[ax_number].spines['top'].set_visible(False)
                ax_top[ax_number].spines['right'].set_visible(False)
                ax_top[ax_number].spines['left'].set_visible(False)
                ax_top[ax_number].tick_params(axis='x', colors='none')

            # Set the x-ticks and y-ticks
            ax_top[ax_number].set_xticks(range(math.floor(df['release_speed'].min() / 5) * 5, math.ceil(df['release_speed'].max() / 5) * 5, 5))
            ax_top[ax_number].set_yticks([])
            ax_top[ax_number].grid(axis='x', linestyle='--')

            # Add text label for the pitch type
            ax_top[ax_number].text(-0.01, 0.5, pitch, transform=ax_top[ax_number].transAxes,
                                fontsize=14, va='center', ha='right')
            
            # Make background white 
            #ax_top[ax_number].set_facecolor('none')
            #fig.patch.set_facecolor('none')

            # Trim width by -5% to avoid overlap
            pos_1 = ax_top[ax_number].get_position()
            ax_top[ax_number].set_position([pos_1.x0, pos_1.y0, pos_1.width * 0.90, pos_1.height])

            # Increment
            ax_number += 1
        # Hide the top, right, and left spines for the last subplot
        ax_top[-1].spines['top'].set_visible(False)
        ax_top[-1].spines['right'].set_visible(False)
        ax_top[-1].spines['left'].set_visible(False)

        # Set the x-ticks and x-label for the last subplot
        ax_top[-1].set_xticks(list(range(math.floor(df['release_speed'].min() / 5) * 5, math.ceil(df['release_speed'].max() / 5) * 5, 5)))
        ax_top[-1].set_xlabel('Velocity (mph)')

    @staticmethod
    def render_rolling_pitch_usage(df: pd.DataFrame, ax: plt.Axes, window: int = 5):
        """
        Renders the game-by-game rolling pitch usage trend chart matching 
        the original implementation exactly, aligned with dashboard configuration styles.
        """
        try:
            from matplotlib.ticker import MaxNLocator
            import matplotlib.ticker as mtick

            # Calculate the proportion of each pitch type per game
            df_game_group = pd.DataFrame((df.groupby(['game_pk', 'game_date', 'pitch_type'])['release_speed'].count() /
                                    df.groupby(['game_pk', 'game_date'])['release_speed'].count()).reset_index())

            # Create a complete list of games
            all_games = pd.Series(df_game_group['game_pk'].unique())

            # Create a complete list of pitch types
            all_pitch_types = pd.Series(df_game_group['pitch_type'].unique())

            # Create a DataFrame with all combinations of games and pitch types
            all_combinations = pd.MultiIndex.from_product([all_games, all_pitch_types], names=['game_pk', 'pitch_type']).to_frame(index=False)

            # Merge this DataFrame with your original DataFrame to ensure all combinations are included
            df_complete = pd.merge(all_combinations, df_game_group, on=['game_pk', 'pitch_type'], how='left')

            # Fill missing values with 0
            df_complete['release_speed'] = df_complete['release_speed'].fillna(0)

            # Create mappings for game numbers and game dates
            game_list = df.sort_values(by='game_date')['game_pk'].unique()
            range_list = list(range(1, len(game_list) + 1))
            game_to_range = dict(zip(game_list, range_list))
            game_to_date = df.set_index('game_pk')['game_date'].to_dict()

            # Map game dates and game numbers to the complete DataFrame
            df_complete['game_date'] = df_complete['game_pk'].map(game_to_date)
            df_complete = df_complete.sort_values(by='game_date')
            df_complete['game_number'] = df_complete['game_pk'].map(game_to_range)

            # Plot the rolling pitch usage for each pitch type
            sorted_value_counts = df['pitch_type'].value_counts().sort_values(ascending=False)
            items_in_order = sorted_value_counts.index.tolist()
            max_roll = []

            for i in items_in_order:
                # Filter to match specific color mapping keys safely
                pitch_color_key = df[df['pitch_type'] == i]['pitch_type'].values[0]
                color_hex = DICT_COLOR.get(pitch_color_key, '#808080')
                
                sns.lineplot(
                    x=range(1, max(df_complete[df_complete['pitch_type'] == i]['game_number']) + 1),
                    y=df_complete[df_complete['pitch_type'] == i]['release_speed'].rolling(window).sum() / window,
                    color=color_hex,
                    ax=ax, 
                    linewidth=3
                )
                max_roll.append(np.max(df_complete[df_complete['pitch_type'] == i]['release_speed'].rolling(window).sum() / window))

            # Adjust x-axis limits to start from the window size
            ax.set_xlim(window, len(game_list))
            
            # Prevent empty slice runtime errors on y-limits if history is short
            if max_roll and not np.isnan(np.max(max_roll)):
                ax.set_ylim(0, math.ceil(np.max(max_roll) * 10) / 10)
            else:
                ax.set_ylim(0, 1.0)

            # Set axis labels and title using matching global configuration font properties
            ax.set_xlabel('Game', fontdict=FONT_PROPERTIES_AXES)
            ax.set_ylabel('Pitch Usage', fontdict=FONT_PROPERTIES_AXES)
            ax.set_title(f"{window} Game Rolling Pitch Usage", fontdict=FONT_PROPERTIES_TITLES)

            # Set x-axis to show integer values only
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))

            # Set y-axis ticks as percentages
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1, decimals=0))
            ax.grid(True, linestyle='--', alpha=0.5)

        except Exception as e:
            ax.text(0.5, 0.5, f"Usage Trend Render Error: {str(e)}", ha='center', va='center')

    @staticmethod
    def render_break_plot(df_processed: pd.DataFrame, ax: plt.Axes, bio_meta: dict = None):
        """
        Renders a 1:1 geometric aspect ratio pitch movement profile complete with 
        symmetrical coordinate boundaries, a strike zone box, and handedness-aware axis labels.
        """
        # Base grid line configuration & structural markers
        ax.axhline(0, color='#E2E8F0', linestyle='--', linewidth=1, zorder=1)
        ax.axvline(0, color='#E2E8F0', linestyle='--', linewidth=1, zorder=1)
        
        # Handle empty/missing data scenarios gracefully 
        if df_processed is None or df_processed.empty or 'pfx_x' not in df_processed.columns or 'pfx_z' not in df_processed.columns:
            ax.text(0.5, 0.5, "No Telemetry Break Data Available", ha='center', va='center', transform=ax.transAxes, color='#A0AEC0')
            return

        # Filter out missing pitch types or blank rows
        df_clean = df_processed[df_processed['pitch_type'].notnull() & (df_processed['pitch_type'].astype(str).str.strip() != '')].copy()
        
        # Force coordinates to numeric arrays
        df_clean['pfx_x'] = pd.to_numeric(df_clean['pfx_x'], errors='coerce')
        df_clean['pfx_z'] = pd.to_numeric(df_clean['pfx_z'], errors='coerce')
        df_clean = df_clean.dropna(subset=['pfx_x', 'pfx_z'])

        # Determine sorting order based on volume
        pitch_order = df_clean['pitch_type'].value_counts().index.tolist()
        
        # Scatter plot tracking points by grouped pitch classification
        for p_type in pitch_order:
            group = df_clean[df_clean['pitch_type'] == p_type]
            p_upper = str(p_type).upper().strip()
            label_display = DICT_PITCH.get(p_upper, p_upper)
            color_display = DICT_COLOR.get(p_upper, '#808080')
            
            ax.scatter(
                group['pfx_x'], 
                group['pfx_z'], 
                label=label_display,
                color=color_display,
                alpha=0.65,
                edgecolors='#FFFFFF',
                linewidths=0.4,
                s=45,
                zorder=3
            )
            
        # Lock the physical canvas aspect ratio to a true 1:1 scale
        ax.set_aspect('equal', adjustable='box')
        
        # Lock boundaries symmetrically
        ax.set_xlim(-25, 25)
        ax.set_ylim(-25, 25)
        
        # DYNAMIC AXIS LABELS: Parse handedness safely
        # Default to RHP orientation if metadata lookup fails or is missing
        throws = "R"
        if bio_meta and isinstance(bio_meta, dict):
            # Check if it's a nested dict structure or a direct string value
            hand_data = bio_meta.get('throws', bio_meta.get('pitchHand', 'R'))
            if isinstance(hand_data, dict):
                throws = hand_data.get('code', 'R')
            else:
                throws = str(hand_data)
        
        throws = throws.upper().strip()

        if throws == "L":
            x_label_text = "← Arm Side | Horizontal Break (in) | Glove Side →"
        else:
            x_label_text = "← Glove Side | Horizontal Break (in) | Arm Side →"
        
        # 5. Formatting axis typography and structural labels
        ax.set_xlabel(x_label_text, fontsize=10, labelpad=5, fontweight='semibold', color='#4A5568')
        ax.set_ylabel("Induced Vertical Break (in)", fontsize=10, labelpad=5, fontweight='semibold', color='#4A5568')
        
        # Standardize step interval grid markers
        ax.set_xticks(np.arange(-20, 21, 10))
        ax.set_yticks(np.arange(-20, 21, 10))
        
        # Light clean aesthetic grid behind the drawings
        ax.grid(True, which='both', color='#F1F5F9', linestyle=':', linewidth=0.5, zorder=0)
        ax.legend(loc='upper right', fontsize=8, framealpha=0.9, facecolor='#FFFFFF', edgecolor='#E2E8F0')

    @staticmethod
    def render_pitch_metrics_table(df_group: pd.DataFrame, df_statcast_league_averages: pd.DataFrame, color_list: list, ax: plt.Axes):
        """Restores the detailed stats spreadsheet with conditional cell shading relative to league averages."""
        if df_group.empty:
            ax.axis('off')
            return

        df_formatted = df_group[TABLE_COLUMNS].copy().fillna('—')
        for col, props in PITCH_STATS_DICT.items():
            if col in df_formatted.columns:
                df_formatted[col] = df_formatted[col].apply(lambda x: format(x, props['format']) if isinstance(x, (int, float)) else x)

        cell_colors = []
        for _, row in df_group.iterrows():
            row_colors = []
            pitch = row['pitch_type']
            
            speed_name = f"{pitch.lower()}_avg_speed"
            spin_name = f"{pitch.lower()}_avg_spin"
            league_avg_speed = getattr(df_statcast_league_averages, speed_name, np.nan)
            # @TODO: use avg_spin somewhere!
            league_avg_spin  = getattr(df_statcast_league_averages, spin_name, np.nan)
            
            '''
            if df_statcast_league_averages is not None and not df_statcast_league_averages.empty and 'pitch_type' in df_statcast_league_averages.columns:
                select_df = df_statcast_league_averages[df_statcast_league_averages['pitch_type'] == pitch]
            else:
                select_df = pd.DataFrame()
            ''' 
            for col in TABLE_COLUMNS:
                if col in COLOR_STATS_TO_HIGHLIGHT and isinstance(row[col], (int, float)) and not np.isnan(row[col]):
                    '''
                    if not select_df.empty and col in select_df.columns:
                        b_mean = pd.to_numeric(select_df[col], errors='coerce').mean()
                    else:
                        b_mean = row[col]
                    
                    if not pd.notnull(b_mean) or b_mean == 0:
                        b_mean = row[col]
                    
                    if col == 'release_speed':
                        norm = mcolors.Normalize(vmin=b_mean * 0.95, vmax=b_mean * 1.05)
                        c = CMAP_SUM(norm(row[col]))
                    elif col == 'delta_run_exp_per_100':
                        norm = mcolors.Normalize(vmin=-1.5, vmax=1.5)
                        c = CMAP_SUM(norm(row[col]))
                    elif col == 'xwoba':
                        norm = mcolors.Normalize(vmin=b_mean * 0.7, vmax=b_mean * 1.3)
                        c = CMAP_SUM_R(norm(row[col]))
                    else:
                        norm = mcolors.Normalize(vmin=b_mean * 0.7, vmax=b_mean * 1.3)
                        c = CMAP_SUM(norm(row[col]))
                    '''
                    row_colors.append(mcolors.to_hex('#ffffff'))#c))
                else:
                    row_colors.append('#ffffff')
            cell_colors.append(row_colors)

        table = ax.table(
            cellText=df_formatted.values, colLabels=TABLE_COLUMNS, cellLoc='center', 
            bbox=[0, -0.1, 1, 1.1], colWidths=[2.5] + [1.0] * (len(TABLE_COLUMNS) - 1),
            cellColours=cell_colors
        )
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1, 0.5)

        headers = [r'$\bf{Pitch\ Name}$'] + [PITCH_STATS_DICT[x]['table_header'] for x in TABLE_COLUMNS[1:]]
        for idx, h_text in enumerate(headers):
            table.get_celld()[(0, idx)].get_text().set_text(h_text)

        for r_idx in range(len(df_formatted)):
            table.get_celld()[(r_idx + 1, 0)].get_text().set_fontweight('bold')
            if r_idx < len(color_list):
                c_cell = table.get_celld()[(r_idx + 1, 0)]
                c_cell.set_facecolor(color_list[r_idx])
                pitch_text = df_formatted.iloc[r_idx]['pitch_description']
                if pitch_text in ['Split-Finger', 'Slider', 'Changeup']:
                    c_cell.set_text_props(color='#000000', fontweight='bold')
                else:
                    c_cell.set_text_props(color='#ffffff', fontweight='bold')

        ax.axis('off')