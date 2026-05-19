import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pandas as pd
import altair as alt
import numpy as np
from config import init_plotting_theme, DICT_PITCH, DICT_COLOR
from data_provider import (
    lookup_player_id, fetch_pitcher_telemetry, 
    fetch_biographical_metadata, fetch_fangraphs_leaderboard,
    fetch_dynamic_league_averages, fetch_logo
)
from processor import StatcastProcessor
from visualizer import PitchVisualizer

# Enforce wide mode dashboard frame space layout optimization natively
st.set_page_config(page_title="Pitching Lab Engine", layout="wide")
init_plotting_theme()

st.title("🔬 Pitching Lab")
st.caption("Enter a pitcher's first and last name in the side bar to get a quick analytics summary of their performance.")

# ==============================================================================
# SIDEBAR CONFIGURATION MATRIX
# ==============================================================================
st.sidebar.header("Control Filter Matrices")
pitcher_name = st.sidebar.text_input("Target Pitcher Name", value="Mason Miller")
season_year = st.sidebar.number_input("Target Season Year", min_value=2021, max_value=2026, value=2026)

# ==============================================================================
# CORE DATA PROCESSING PIPELINE
# ==============================================================================
try:
    pitcher_id = lookup_player_id(pitcher_name)
    df_raw = fetch_pitcher_telemetry(pitcher_id, season_year)
    bio_meta = fetch_biographical_metadata(pitcher_id)
    df_fg_leaderboard = fetch_fangraphs_leaderboard(season_year, pitcher_id)
    df_statcast_group = fetch_dynamic_league_averages(year=season_year)
    logo_url = fetch_logo(pitcher_id)

    if df_raw.empty:
        st.error(f"No tracking metrics returned matching input configurations.")
        st.stop()

    df_processed = StatcastProcessor.clean_and_augment(df_raw)

    if df_processed.empty:
        st.warning("No tracking instances found matching specified parameter matrix dimensions.")
        st.stop()

    df_group, pitch_colors_list = StatcastProcessor.aggregate_pitch_metrics(df_processed)

except Exception as exc:
    st.error(f"Core Pipeline Engine Fault: {str(exc)}")
    st.stop()


# ==============================================================================
# TOP BANNER: HEADSHOT, BIOGRAPHICAL CARD, & FANGRAPHS METRICS GRID
# ==============================================================================
with st.container():
    col_img, col_bio, col_logo = st.columns([1.2, 3.5, 1.2])
    
    with col_img:
        fig_headshot, ax_headshot = plt.subplots(figsize=(2, 2))
        PitchVisualizer.render_headshot(pitcher_id, ax_headshot)
        st.pyplot(fig_headshot)
    
    with col_bio:
        fig_bio, ax_bio = plt.subplots(figsize=(6, 2))
        PitchVisualizer.render_biographical_text(bio_meta, season_year, "", ax_bio)
        st.pyplot(fig_bio)
        
    with col_logo:
        # Create an identical 2x2 bounding canvas for symmetric scaling
        fig_logo, ax_logo = plt.subplots(figsize=(2, 2))
        ax_logo.axis('off')
        
        if logo_url:
            try:
                import requests
                from PIL import Image
                from io import BytesIO
                
                response = requests.get(logo_url, timeout=5)
                img = Image.open(BytesIO(response.content))
                
                ax_logo.set_xlim(0, 1.3)
                ax_logo.set_ylim(0, 1)
                ax_logo.imshow(img, extent=[0.15, 1.15, 0, 1], origin='upper')
            except Exception:
                ax_logo.text(0.5, 0.5, "Logo\nLoad Error", ha='center', va='center', color='#A0AEC0')
        else:
            ax_logo.text(0.5, 0.5, "No Team\nLogo", ha='center', va='center', color='#A0AEC0')
            
        st.pyplot(fig_logo)

# ==============================================================================
# FANGRAPHS METRICS GRID (DIRECT RENDER OVER PRE-MAPPED SUMMARY ROW)
# ==============================================================================
st.markdown("### Seasonal Performance Metrics")

if df_fg_leaderboard is not None and not df_fg_leaderboard.empty:
    # Pull the first row since it's already mapped and isolated for this pitcher
    player_row = df_fg_leaderboard.iloc[0]
    
    # Create the horizontal metric track columns matching your exact dataset columns
    fg_cols = st.columns(len(player_row.index))
    
    for i, col_name in enumerate(player_row.index):
        val = player_row[col_name]
        
        # Handle empty/missing values gracefully
        if pd.isnull(val) or val == '—' or val == '':
            display_val = "—"
        else:
            try:
                numeric_val = float(val)
                # Auto-append '%' symbol if the header contains percent markers
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
                
        fg_cols[i].metric(label=str(col_name), value=display_val)
else:
    st.caption("⚠️ FanGraphs data-store tracking records currently unavailable.")

st.markdown("---")

# ==============================================================================
# MAIN AREA: CLEAN VERTICAL STREAMLINED LAYOUT 
# ==============================================================================
st.subheader("Interactive Pitch Analytics")

# Data preparation
df_chart_base = df_processed.copy()
df_chart_base['release_speed'] = pd.to_numeric(df_chart_base['release_speed'], errors='coerce')
df_chart_base['pitch_type'] = df_chart_base['pitch_type'].astype(str).str.upper().str.strip()
df_chart_base = df_chart_base.dropna(subset=['release_speed'])

pitch_order = df_chart_base['pitch_type'].value_counts().index.tolist()
active_colors = {p: DICT_COLOR[p] for p in pitch_order if p in DICT_COLOR}


# 🌟 NEW LAYOUT MATRIX: 25% Left Space | 50% Center Graphs | 25% Right Space
# This limits desktop chart width to 50% while maintaining mobile vertical responsiveness.
col_left_spacer, col_graph_canvas, col_right_spacer = st.columns([1, 2, 1])

# Create a dynamic formatting expression for all pitch types in DICT_PITCH
js_legend_mapping = ""
for k, v in DICT_PITCH.items():
    js_legend_mapping += f"datum.label == '{k}' ? '{k} ({v})' : "
js_legend_mapping += "datum.label"

with col_graph_canvas:

    # --------------------------------------------------------------------------
    # VELOCITY DISTRIBUTIONS (50% DESKTOP WIDTH / 100% MOBILE WIDTH)
    # --------------------------------------------------------------------------
    st.markdown("### ⚡ Velocity Distribution Grid")
    st.caption("Visualizes velocity of each pitch type, categorized by the pitch thrown.")

    v_selection = alt.selection_point(fields=['pitch_type'], bind='legend')

    base_density = alt.Chart(df_chart_base).transform_density(
        'release_speed',
        as_=['release_speed', 'density'],
        groupby=['pitch_type'],
        steps=200
    ).encode(
        x=alt.X('release_speed:Q', title='Velocity (mph)', scale=alt.Scale(zero=False), axis=alt.Axis(grid=True, gridColor='#E2E8F0', labelFontSize=10)),
        y=alt.Y('density:Q', title='', axis=alt.Axis(labels=False, values=[], ticks=False)),
        color=alt.Color(
            'pitch_type:N',
            title='Pitch Type',
            sort=pitch_order,
            scale=alt.Scale(domain=list(active_colors.keys()), range=list(active_colors.values())),
            legend=alt.Legend(
                orient='top', 
                columns=3,
                labelExpr=js_legend_mapping  # ← Injects 'FF (4 Seam Fastball)' format
            )
        ),
        row=alt.Row(
            'pitch_type:N', 
            title=None, 
            header=alt.Header(labelAngle=0, labelAlign='left', labelFontWeight='bold', labelFontSize=11), 
            sort=pitch_order
        ),
        opacity=alt.condition(v_selection, alt.value(0.75), alt.value(0.10)),
        tooltip=[
            alt.Tooltip('pitch_type:N', title='Pitch Class'),
            alt.Tooltip('release_speed:Q', title='Velocity (mph)', format='.1f')
        ]
    ).properties(width='container', height=50).add_params(v_selection)

    interactive_distribution = base_density.mark_area(filled=True, stroke='#FFFFFF', strokeWidth=1)

    if df_statcast_group is not None and not df_statcast_group.empty:
        df_base_filtered = df_statcast_group[df_statcast_group['pitch_type'].isin(pitch_order)].copy()
        df_base_filtered['release_speed'] = pd.to_numeric(df_base_filtered['release_speed'], errors='coerce')
        
        if not df_base_filtered.empty:
            baseline_rules = alt.Chart(df_base_filtered).mark_rule(stroke='#4A5568', strokeDash=[4, 4], strokeWidth=1.5).encode(
                x='release_speed:Q',
                row=alt.Row('pitch_type:N', sort=pitch_order)
            ).properties(width='container')
            interactive_distribution = alt.layer(interactive_distribution, baseline_rules).resolve_scale(x='shared')
            
    st.altair_chart(interactive_distribution.configure_view(strokeWidth=0), use_container_width=True)

    st.markdown("---")

    # --------------------------------------------------------------------------
    # ROLLING USAGE TIMELINE (EXPANDED STRETCH FOR READABILITY)
    # --------------------------------------------------------------------------
    st.markdown("### 📈 5-Game Rolling Pitch Usage Trend")
    st.caption("Traces evolution of pitch selection mixes over time.")

    df_rolling = df_processed.copy()
    df_rolling['game_date'] = pd.to_datetime(df_rolling['game_date'])

    df_game_mix = df_rolling.groupby(['game_date', 'pitch_type']).size().unstack(fill_value=0)
    df_game_mix = df_game_mix.div(df_game_mix.sum(axis=1), axis=0) * 100
    df_game_mix = df_game_mix.rolling(window=5, min_periods=1).mean().reset_index()

    df_melted_usage = df_game_mix.melt(id_vars=['game_date'], var_name='pitch_type', value_name='Usage %')
    df_melted_usage['pitch_type'] = df_melted_usage['pitch_type'].astype(str).str.upper().str.strip()
    df_melted_usage = df_melted_usage[df_melted_usage['pitch_type'].isin(pitch_order)]

    max_usage_val = float(df_melted_usage['Usage %'].max()) if not df_melted_usage.empty else 100.0
    y_max_bound = min(100.0, max_usage_val + 3.0)

    u_selection = alt.selection_point(fields=['pitch_type'], bind='legend')

    base_trend = alt.Chart(df_melted_usage).encode(
        x=alt.X(
            'game_date:T', 
            title='Timeline', 
            axis=alt.Axis(grid=True, gridColor='#E2E8F0', format='%b %d', labelAngle=-45, labelFontSize=10, tickCount=10)
        ),
        y=alt.Y(
            'Usage %:Q', 
            title='Usage Mix %', 
            scale=alt.Scale(domain=[0, y_max_bound]), 
            axis=alt.Axis(grid=True, gridColor='#E2E8F0', labelFontSize=10)
        ),
        color=alt.Color(
            'pitch_type:N', 
            sort=pitch_order, 
            scale=alt.Scale(domain=list(active_colors.keys()), range=list(active_colors.values())),
            legend=alt.Legend(
                orient='bottom',      # ← Shifted to bottom to give the lines more room
                columns=4,           # ← Expanded grid spacing for the full names
                titleFontWeight='bold',
                labelExpr=js_legend_mapping
            )
        ),
    )

    usage_lines = base_trend.mark_line(strokeWidth=3, interpolate='monotone').encode(
        opacity=alt.condition(u_selection, alt.value(0.85), alt.value(0.10))
    )

    usage_dots = base_trend.mark_circle(size=65, filled=True).encode(
        opacity=alt.condition(u_selection, alt.value(0.95), alt.value(0.10)),
        tooltip=[
            alt.Tooltip('game_date:T', title='Game Date', format='%b %d'),
            alt.Tooltip('pitch_type:N', title='Pitch Type'),
            alt.Tooltip('Usage %:Q', title='Usage %', format='.1f')
        ]
    )

    # Combined layers into a taller 420px frame to flatten out crowded step curves
    rolling_line_chart = alt.layer(usage_lines, usage_dots).properties(
        width='container', 
        height=420            # ← Changed from 280 to 420 for clear resolution
    ).add_params(u_selection)
    
    st.altair_chart(rolling_line_chart.configure_view(strokeWidth=0), use_container_width=True)

    st.markdown("---")

    # --------------------------------------------------------------------------
    # MOVEMENT BREAK SCATTER PLOT (STRICT 1:1 MATPLOTLIB BOUNDS)
    # --------------------------------------------------------------------------
    st.markdown("### 🎯 Pitch Movement Scatter Plot")
    st.caption("Tracks Induced Vertical Break (iVB) and Horizontal Break. We use iVB to track movement based on the spin of the ball, and not gravity. Horizontal break is adjusted to glove side and arm side based on the pitcher's handedness.")

    # 1. Allocate a dedicated square bounding canvas frame seed
    fig_break, ax_break = plt.subplots(figsize=(5, 5))

    # 2. Route your processed pipeline data layer into your visualizer class
    PitchVisualizer.render_break_plot(df_processed, ax_break, bio_meta)

    # 3. CRITICAL: Pass use_container_width=False so Streamlit respects the square dimensions
    st.pyplot(fig_break, width='content')

# ==============================================================================
# STATCAST ARSENAL METRICS SUMMARY GRID (STAYS UNCONSTRAINED FULL-WIDTH Below)
# ==============================================================================
st.markdown("---")
st.subheader("📊 Statcast Arsenal Performance Summary")
st.caption("Comprehensive pitch metrics aggregated by pitch type. Highlighted cells indicate better performance for a given pitch.")

if df_group is not None and not df_group.empty:
    display_columns = {
        'pitch_description': 'Pitch Name',
        'pitch_type': 'Abbreviation',
        'pitch': 'Count',
        'pitch_usage': 'Usage',
        'release_speed': 'Velocity',
        'release_spin_rate': 'Spin (rpm)',
        'pfx_z': 'iVB (in)',
        'pfx_x': 'HB (in)',
        'in_zone_rate': 'Zone %',
        'chase_rate': 'Chase %',
        'whiff_rate': 'Whiff %',
        'xwoba': 'xwOBA',
        'delta_run_exp_per_100': 'RV/100'
    }
    
    df_display = df_group[list(display_columns.keys())].rename(columns=display_columns)
    
    formatted_grid = df_display.style.format({
        'Count': "{:,}",
        'Usage': "{:.1%}",
        'Velocity': lambda x: f"{x:.1f} mph" if pd.notnull(x) else "—",
        'Spin (rpm)': lambda x: f"{x:,.0f}" if pd.notnull(x) else "—",
        'iVB (in)': lambda x: f"{x:+.1f}" if pd.notnull(x) else "—",
        'HB (in)': lambda x: f"{x:+.1f}" if pd.notnull(x) else "—",
        'Zone %': "{:.1%}",
        'Chase %': "{:.1%}",
        'Whiff %': "{:.1%}",
        'xwOBA': lambda x: f".{int(x*1000):03d}" if pd.notnull(x) else "—",
        'RV/100': lambda x: f"{x:+.2f}" if pd.notnull(x) else "—"
    })
    
    yellow_cmap = mcolors.LinearSegmentedColormap.from_list("scout_yellow", ["#FFFFFF", "#FACC15"])
    yellow_cmap_r = yellow_cmap.reversed()
    formatted_grid = formatted_grid.background_gradient(cmap=yellow_cmap, subset=['Whiff %', 'Chase %',])
    formatted_grid = formatted_grid.background_gradient(cmap=yellow_cmap_r, subset=['xwOBA'])
    formatted_grid = formatted_grid.background_gradient(cmap=yellow_cmap_r, subset=['RV/100'])
    
    # Keeping table full-width as it contains 13 dense data attributes
    st.dataframe(
        formatted_grid,
        use_container_width=True,
        hide_index=True
    )
    
    # --------------------------------------------------------------------------
    # FOOTER ANALYTICAL GUIDE (COMPREHENSIVE METRIC BREAKDOWN)
    # --------------------------------------------------------------------------
    st.info(
        "🔬 **Analytical Guide & Metric Glossary:**\n\n"
        "* **Pitch Name & Abbreviation:** The tracking class configuration (e.g., FF = Four-Seam Fastball, SL = Slider) mapped directly from telemetry tags.\n"
        "* **Count & Usage:** Total pitch volume tracked for the specified timeline and its relative percentage share of the pitcher's total arsenal mix.\n"
        "* **Velocity:** Average release speed measured in miles per hour (mph) at the out-of-hand release point.\n"
        "* **Spin (rpm):** Average raw revolutions per minute measured immediately after release.\n"
        "* **iVB (Induced Vertical Break):** The vertical movement of the pitch relative to a spinless baseline, measured in inches. Positive values indicate 'ride' or 'rise' (defying gravity), while negative values signify heavy sink or drop.\n"
        "* **HB (Horizontal Break):** The horizontal movement of the pitch relative to a spinless baseline, measured in inches. Positive values track movement toward the pitcher's arm-side, while negative values track glove-side break.\n"
        "* **Zone %:** The percentage of pitches that passed through the boundaries of the rulebook strike zone.\n"
        "* **Chase %:** The percentage of pitches thrown *outside* the strike zone that the batter swung at.\n"
        "* **Whiff %:** The percentage of total swings where the batter missed the ball completely (Whiffs / Total Swings). A primary metric for isolating pure put-away stuff.\n"
        "* **xwOBA (Expected Weighted On-Base Average):** A premium Statcast quality-of-contact metric that formulates what the opponent's wOBA *should* be based strictly on exit velocity and launch angle, stripping out defensive luck. Lower numbers favor the pitcher.\n"
        "* **RV/100 (Run Value per 100 Pitches):** The net run expectancy impact generated by the pitch, scaled per 100 throws. **Negative values favor the pitcher** (suppressing runs), while positive values favor the batter (generating offense)."
    )
else:
    st.warning("Telemetry data groups are currently empty or missing.")