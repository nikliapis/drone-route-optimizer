import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import random
import time

from utils import generate_points, dist, compute_metrics
from algorithms import nearest_neighbor, genetic_algorithm, simulated_annealing


# Page config
st.set_page_config(
    page_title="Drone Delivery Optimizer",
    page_icon="🚁",
    layout="wide",
)

st.title("Drone Delivery Route Optimizer")
st.caption( "Find the most efficient delivery route using three classic optimisation algorithms.")

# Sidebar 
with st.sidebar:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.header("Configuration")
    num_points = st.slider("Delivery points", 4, 20, 8)
    battery_capacity = st.slider("Battery capacity (min)", 20, 90, 60)
    max_speed = st.slider("Drone speed (km/h)", 10, 50, 30)
    payload_capacity = st.slider("Payload capacity (kg)", 0.5, 5.0, 2.0, step=0.5)

    algorithm = st.selectbox(
        "Optimisation algorithm",
        ["Nearest neighbor", "Genetic algorithm", "Simulated annealing"],
    )

    regenerate = st.button("🔄  Regenerate points")
    
    st.divider()
    st.caption("Tip: regenerate points to compare algorithms on a different scenario.")

# Data Generation

# Generate new random numbers
if "seed" not in st.session_state or regenerate:
    st.session_state["seed"] = random.randint(0, 99_999)

delivery_points = generate_points(num_points, st.session_state["seed"], payload_capacity)
#print(delivery_points)

with st.spinner(f"Running {algorithm}…"):
    if algorithm == "Nearest neighbor":
        route = nearest_neighbor(delivery_points)
    elif algorithm == "Genetic algorithm":
        route = genetic_algorithm(delivery_points)
    else:
        route = simulated_annealing(delivery_points)


# Display Metrics
m = compute_metrics(delivery_points, route, max_speed, battery_capacity)

# Create presentation columns and the equivalent status
st.subheader("Summary:")
status = m["status"]
r1_col1, r1_col2, r1_col3 = st.columns(3)

with r1_col1:
    st.metric("Total distance", f"{m['distance']:.2f} km")
with r1_col2:
    st.metric("Flight time", f"{m['time']:.1f} min")
with r1_col3:
    st.metric("Total weight", f"{m['weight']:.1f} kg")

# Add a slight visual gap between rows (optional)
st.write("") 

# Create the second row with 3 columns
r2_col1, r2_col2, r2_col3 = st.columns(3)

with r2_col1:
    st.metric("Battery used", f"{m['battery_used']:.1f} min")
with r2_col2:
    st.metric("Battery remaining", f"{m['battery_remaining']:.1f} min")
with r2_col3:
    st.metric("Status", f"{status} {'✅' if status == 'OK' else '🚨'}")
if status == "OK":
    st.success("Battery is sufficient for all deliveries.")
else:
    st.warning("⚠️Battery will be depleted before completing this route.")


# Map
st.subheader("🗺️ Route map")

fig_map = go.Figure()

# Get coordinates in route order
route_points = delivery_points.iloc[route]
#print(f"Route points: \n {route_points}")

lats = route_points["latitude"].tolist()
lons = route_points["longitude"].tolist()
#print(f"Latitudes: {lats}")

# Return to starting point
if lats:
    lats.append(lats[0])
    lons.append(lons[0])

# Points Map
fig_map.add_trace(
    go.Scattermap(
        lat=[delivery_points.iloc[route[i]]["latitude"] for i in range(1, len(route))],
        lon=[delivery_points.iloc[route[i]]["longitude"] for i in range(1, len(route))],
        mode="markers+text",
        marker=dict(size=12, color="#2b78d6", opacity=0.9),
        text=[str(i + 1) for i in range(1, len(route))],
        textposition="top right",
        textfont=dict(size=17,color="#2a78d6"),
        name="Delivery stops",
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Lat: %{lat:.3f}<br>Lon: %{lon:.3f}<extra></extra>"
        ),
    )
)
# Draw route
fig_map.add_trace(
    go.Scattermap(
        lat=lats,
        lon=lons,
        mode="lines",
        line=dict(
            width=3,
            color="#2a78d6"
        ),
        name="Route"
    )
)

# Depot-start
depot = delivery_points.iloc[route[0]]
#print(depot)
fig_map.add_trace(
    go.Scattermap(
        lat=[depot["latitude"]], lon=[depot["longitude"]],
        mode="markers+text",
        marker=dict(size=18, color="#e34948"),
        text=["Depot"],
        textposition="top right",
        textfont=dict(size=12, color="#e34948"),
        name="Depot",
    )
)
# Map Settings
fig_map.update_layout(
    map_style="open-street-map",
    map_zoom=10.9,
    map_center={
        "lat": delivery_points["latitude"].mean(),
        "lon": delivery_points["longitude"].mean(),
    },
    height=450,
    margin=dict(l=0, r=0, t=0, b=0),
    legend=dict(orientation="h", y=0., x=0),
)
st.plotly_chart(fig_map, width='stretch')
st.divider()

# Battery timeline + delivery table
col_battery, col_info = st.columns([1, 1], gap="large")

with col_battery:
    st.subheader("🔋Battery timeline")

    # Calculate cumulative timeline
    times = [0.0]
    battery = [battery_capacity]
    
    for k in range(0, len(route)):
        dt = (dist(delivery_points, route[k - 1], route[k]) / max_speed) * 60
        times.append(times[-1] + dt)
        battery.append(battery[-1] - dt)
    # print(times)
    # Build streamlined visual
    reserve = battery_capacity * 0.2
    is_safe = battery[-1] >= reserve
    
    # Theme colors
    line_color = "#10b981" if is_safe else "#ef4444"
    fill_color = "rgba(16, 185, 129, 0.08)" if is_safe else "rgba(239, 68, 68, 0.08)"

    fig = go.Figure()

    # Safety reserve zone (<20%)
    fig.add_hrect(
        y0=0, y1=reserve,
        fillcolor="rgba(239, 68, 68, 0.08)", 
        line_width=1, line_color="rgba(239, 68, 68, 0.3)", line_dash="dash",
        annotation_text="20% Reserve", 
        annotation_position="bottom left",
        annotation_font=dict(color="#ef4444", size=11)
    )
    # Discharge curve
    fig.add_trace(go.Scatter(
        x=times, y=battery,
        mode="lines+markers",
        line=dict(color=line_color, width=3),
        marker=dict(size=7, color="#ffffff", line=dict(color=line_color, width=2)),
        fill="tozeroy",
        fillcolor=fill_color,
        hovertemplate="<b>%{y:.1f}</b> left at %{x:.1f} min<extra></extra>"
    ))

    # Figure layout
    fig.update_layout(
        height=280,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        xaxis=dict(
            title="Time (min)", 
            showgrid=True, 
            gridcolor="rgba(128,128,128,0.15)", 
            zeroline=False
        ),
        yaxis=dict(
            title="Battery Capacity", 
            showgrid=True, 
            gridcolor="rgba(128,128,128,0.15)", 
            zeroline=False
        )
    )
    st.plotly_chart(fig, width='stretch')

with col_info:
    st.subheader("📋 Delivery Info")

    # 1. Efficiently slice points in route order
    pts = delivery_points.iloc[route].reset_index(drop=True)

    route_df = pd.DataFrame({
        "Step": [f"#{i+1}" for i in range(len(route))],
        "Stop": ["Depot (Start)" if i == 0 else pts.loc[i, "label"] for i in range(len(route))],
        "Coords": [f"{lat:.3f}, {lon:.3f}" for lat, lon in zip(pts["latitude"], pts["longitude"])],
        "Payload": pts["weight"].astype(float),
    })

    # Visual payload bars
    max_payload = max(route_df["Payload"].max(), 1.0)

    st.dataframe(
        route_df,
        column_config={
            "Step": st.column_config.TextColumn("Stop", width="small"),
            "Stop": st.column_config.TextColumn("Location", width="medium"),
            "Coords": st.column_config.TextColumn("GPS (Lat, Lon)", width="medium"),
            "Payload": st.column_config.ProgressColumn(
                "Weight",
                format="%.1f kg",
                min_value=0,
                max_value=float(max_payload),
                color="#f0f0f0",
            ),
        },
        hide_index=True,
        width='stretch',
        height=260,  
    )

st.divider()

# Algorithm comparison 
st.subheader("Algorithm comparison")
st.caption("All three algorithms run on the same scenario.")

with st.spinner("Running comparison…"):
    cmp_rows = []
    for alg_name, fn in [
        ("Nearest neighbor", nearest_neighbor),
        ("Genetic algorithm", genetic_algorithm),
        ("Simulated annealing", simulated_annealing),
    ]:
        # Start a stopwatch to measure CPU time
        start_time = time.time()
        r = fn(delivery_points)
        end_time = time.time()
        exec_time_ms = (end_time - start_time) * 1000  # Convert to milliseconds
        
        me = compute_metrics(delivery_points, r, max_speed, battery_capacity)
        
        # Calculate status manually if it isn't in your compute_metrics function
        current_status = me.get("status", "OK" if me["battery_remaining"] >= 0 else "Fail")
        
        cmp_rows.append(
            {
                "Algorithm": alg_name,
                "Distance (km)": round(me["distance"], 2),
                "Time (min)": round(me["time"], 1),
                "Battery used (min)": round(me["battery_used"], 1),
                "Battery remaining (min)": round(me["battery_remaining"], 1),          
                "Compute Time (ms)": round(exec_time_ms, 2),   
                "Status": current_status,
            }
        )

cmp_df = pd.DataFrame(cmp_rows)
best_dist = cmp_df["Distance (km)"].min()

# Create two columns for the side-by-side bar charts
col_dist, col_time = st.columns(2)

with col_dist:
    st.markdown("**Route Quality (Distance)**")
    fig_dist = px.bar(
        cmp_df, x="Algorithm", y="Distance (km)",
        color="Algorithm",
        color_discrete_sequence=["#c0c0c0", "#FF6B35", "#f7fc6f"],
        text="Distance (km)",
    )
    fig_dist.update_traces(texttemplate="%{text:.2f} km", textposition="outside")
    fig_dist.update_layout(
        height=280, showlegend=False,
        margin=dict(l=0, r=0, t=10, b=0),
        yaxis_title="Total distance (km)",
    )
    st.plotly_chart(fig_dist, width='stretch')

with col_time:
    st.markdown("**Computational Cost (Execution Time)**")
    fig_time = px.bar(
        cmp_df, x="Algorithm", y="Compute Time (ms)",
        color="Algorithm",
        color_discrete_sequence=["#c0c0c0", "#FF6B35", "#f7fc6f"],
        text="Compute Time (ms)",
    )
    fig_time.update_traces(texttemplate="%{text:.1f} ms", textposition="outside")
    fig_time.update_layout(
        height=280, showlegend=False,
        margin=dict(l=0, r=0, t=10, b=0),
        yaxis_title="Time to calculate (ms)",
    )
    st.plotly_chart(fig_time, width='stretch')

# Highlight the row with the best distance
def highlight_best(row):
    if row["Distance (km)"] == best_dist:
        return ["background-color: #429E49; color: #ffffff; font-weight: bold;"] * len(row)
    return [""] * len(row)

# Apply highlight and change number format
st.dataframe(
    cmp_df.style.apply(highlight_best, axis=1),
    column_config={
        "Distance (km)": st.column_config.NumberColumn(format="%.2f"),
        "Time (min)": st.column_config.NumberColumn(format="%.2f"),        
        "Compute Time (ms)": st.column_config.NumberColumn(format="%.2f"),
        "Battery used (min)": st.column_config.NumberColumn(format="%.2f"),
        "Battery remaining (min)": st.column_config.NumberColumn(format="%.2f"),
    },
    width='stretch',
    hide_index=True,
)