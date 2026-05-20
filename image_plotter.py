import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors
import matplotlib.patches as patches
import pandas as pd
import numpy as np
import seaborn as sns
import pybaseball as pyb
from PIL import Image
import requests
from io import BytesIO
import config

# Set the theme for seaborn plots
sns.set_theme(style='whitegrid', 
              palette='deep', 
              font='DejaVu Sans', 
              font_scale=1.5, 
              color_codes=True, 
              rc=None)

# Set the resolution of the figures to 300 DPI
mpl.rcParams['figure.dpi'] = 300

# fetch_dynamic_league_averages(year: int)\

#PitchVisualizer.render_headshot(pitcher_id, ax_headshot)

#render_biographical_text(bio_data: dict, ax: plt.Axes):

#fetch_logo(pitcher_id)

def plot_logo(logo_url, ax):

    # Send a GET request to the logo URL
    response = requests.get(logo_url)

    # Open the image from the response content
    img = Image.open(BytesIO(response.content))

    # Display the image on the axis
    ax.set_xlim(0, 1.3)
    ax.set_ylim(0, 1)
    ax.imshow(img, extent=[0.3, 1.3, 0, 1], origin='upper')

    # Turn off the axis
    ax.axis('off')

def plot_fangraphs_table(df_fg_leaderboard, ax):
    """
    Renders a single-row FanGraphs seasonal leaderboard tracking metric block
    onto a dedicated matplotlib axis with a clean horizontal card layout.
    """
    # Initialize clean canvas boundaries
    ax.axis('off')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    
    if df_fg_leaderboard is None or df_fg_leaderboard.empty:
        ax.text(0.5, 0.5, "⚠️ FanGraphs tracking data unavailable.", 
                ha='center', va='center', fontsize=12, color='#A0AEC0', fontweight='bold')
        return

    # Pull the primary target index layer
    player_row = df_fg_leaderboard.iloc[0]
    cols = player_row.index
    num_cols = len(cols)
    
    # Render a subtle background card container
    bg_card = patches.Rectangle(
        (0.01, 0.05), 0.98, 0.90, 
        facecolor='#F8FAFC',       # Light Slate tint matching dashboard framework themes
        edgecolor='#E2E8F0',       # Subtle boundary border line
        linewidth=1, 
        transform=ax.transAxes, 
        zorder=1
    )
    ax.add_patch(bg_card)
    
    # 3. Dynamically slice horizontal track width partitions for clean alignment
    x_coords = np.linspace(0.08, 0.92, num_cols)
    
    # 4. Enumerate attributes and blit layers to target canvas
    for i, col_name in enumerate(cols):
        x = x_coords[i]
        val = player_row[col_name]
        
        # Gracefully process string missing tags or numeric types
        if pd.isnull(val) or val in ['—', '']:
            display_val = "—"
        else:
            try:
                numeric_val = float(val)
                # Formatter maps exactly to your Streamlit logic matrix
                if '%' in str(col_name):
                    if abs(numeric_val) < 1.0 and numeric_val != 0.0:
                        display_val = f"{numeric_val * 100:.1f}%"
                    else:
                        display_val = f"{numeric_val:.1f}%"
                elif str(col_name).upper() in ['ERA', 'FIP', 'WHIP']:
                    display_val = f"{numeric_val:.2f}"
                elif str(col_name).upper() in ['IP', 'TBF']:
                    display_val = f"{numeric_val:,.1f}" if str(col_name).upper() == 'IP' else f"{numeric_val:,.0f}"
                else:
                    display_val = f"{numeric_val:.1f}"
            except (ValueError, TypeError):
                display_val = str(val)
                
        # Top Row: Clean descriptive stat tracking headers
        ax.text(
            x, 0.62, str(col_name).upper(), 
            ha='center', va='center', 
            fontsize=10, 
            fontweight='bold', 
            color='#64748B',        # Muted charcoal labels
            zorder=2
        )
        
        # Bottom Row: Large high-contrast metric values
        ax.text(
            x, 0.32, display_val, 
            ha='center', va='center', 
            fontsize=15, 
            fontweight='bold', 
            color='#0F172A',        # Deep charcoal typography
            zorder=2
        )