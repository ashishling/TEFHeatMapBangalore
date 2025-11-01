import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium

# Page config
st.set_page_config(
    page_title="Address Heatmap Dashboard",
    page_icon="📍",
    layout="wide"
)

# Cache data loading
@st.cache_data
def load_data():
    """Load and prepare the data"""
    # Load the address data
    address_df = pd.read_csv('Address Details.csv')

    # Load Google Maps pincode coordinates (more reliable than the old CSV)
    pincode_coords = pd.read_csv('pincode_coordinates_google.csv')

    # Clean pincodes
    address_df['CPA_PIN_CODE'] = pd.to_numeric(address_df['CPA_PIN_CODE'], errors='coerce')
    address_df = address_df.dropna(subset=['CPA_PIN_CODE'])

    # Parse registration date to extract year
    address_df['RegistrationDate'] = pd.to_datetime(address_df['RegistrationDate'], format='%d/%m/%y', errors='coerce')
    address_df['Year'] = address_df['RegistrationDate'].dt.year

    # Merge with Google Maps coordinates (already clean and deduplicated, 1-to-1 mapping)
    merged_df = address_df.merge(
        pincode_coords[['pincode', 'latitude', 'longitude', 'city', 'state']],
        left_on='CPA_PIN_CODE',
        right_on='pincode',
        how='left'
    )

    # Rename columns to match expected format
    merged_df = merged_df.rename(columns={
        'latitude': 'Latitude',
        'longitude': 'Longitude',
        'state': 'StateName'
    })

    # Use Google Maps city if available, otherwise fall back to address city
    merged_df['CPA_ADDR_CITY'] = merged_df['city'].fillna(merged_df['CPA_ADDR_CITY'])

    # Drop rows without coordinates
    merged_df = merged_df.dropna(subset=['Latitude', 'Longitude'])

    return merged_df

# Load data
st.title("📍 Customer Address Heatmap Dashboard")
st.markdown("Interactive visualization of customer addresses across India")

with st.spinner("Loading data..."):
    df = load_data()

# Sidebar filters
st.sidebar.header("🔍 Filters")

# Year filter
years = sorted(df['Year'].dropna().unique())
year_options = ['All Years'] + [int(year) for year in years]
selected_year = st.sidebar.selectbox("Select Year", year_options)

# Visualization type
viz_type = st.sidebar.radio(
    "Visualization Type",
    ["Clustered Markers", "Heatmap", "Both"]
)

# Display mode toggle
display_mode = st.sidebar.radio(
    "Display Mode",
    ["Absolute Count", "Percentage"]
)

# Apply filters
if selected_year != 'All Years':
    filtered_df = df[df['Year'] == selected_year]
else:
    filtered_df = df

# Aggregate data by pincode - first get total count per pincode
pincode_counts = filtered_df.groupby('CPA_PIN_CODE').size().reset_index(name='customer_count')

# For each pincode, get representative location (median of all lat/longs) and most common city/state
pincode_locations = filtered_df.groupby('CPA_PIN_CODE').agg({
    'Latitude': 'median',  # Median latitude (should be same for all rows of a pincode after initial dedup)
    'Longitude': 'median',  # Median longitude (should be same for all rows of a pincode after initial dedup)
    'CPA_ADDR_CITY': lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0],  # Most common city
    'StateName': lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0]  # Most common state
}).reset_index()

# Merge counts with locations
pincode_summary = pincode_counts.merge(pincode_locations, on='CPA_PIN_CODE')

# Calculate percentage of total customers
total_customers = len(filtered_df)
pincode_summary['percentage'] = (pincode_summary['customer_count'] / total_customers * 100)
pincode_summary = pincode_summary.sort_values('customer_count', ascending=False)

# Display statistics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Customers", f"{len(filtered_df):,}")
with col2:
    st.metric("Unique Pincodes", f"{len(pincode_summary):,}")
with col3:
    st.metric("Average per Pincode", f"{pincode_summary['customer_count'].mean():.1f}")
with col4:
    st.metric("Max at One Pincode", f"{pincode_summary['customer_count'].max():,}")

# Calculate map center
center_lat = pincode_summary['Latitude'].mean()
center_lon = pincode_summary['Longitude'].mean()

# Create map
st.subheader("🗺️ Map Visualization")

# Create base map
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=6,
    tiles='OpenStreetMap',
    control_scale=True
)

# Add markers with clustering
if viz_type in ["Clustered Markers", "Both"]:
    # Determine if we're in percentage mode
    is_percentage_mode = display_mode == "Percentage"

    # Custom cluster function to show customer count sum instead of marker count
    if is_percentage_mode:
        icon_create_function = f"""
        function(cluster) {{
            var markers = cluster.getAllChildMarkers();
            var sumCount = 0;
            var sumPct = 0;
            var totalCustomers = {total_customers};
            for (var i = 0; i < markers.length; i++) {{
                if (markers[i].options.customCount) {{
                    sumCount += markers[i].options.customCount;
                }}
                if (markers[i].options.customPercentage) {{
                    sumPct += markers[i].options.customPercentage;
                }}
            }}

            var displayText = sumPct < 1 ? '<1%' : sumPct.toFixed(1) + '%';

            var size = 'small';
            if (sumPct >= 10) size = 'large';
            else if (sumPct >= 5) size = 'medium';

            var color = 'lightblue';
            if (sumPct >= 10) color = 'red';
            else if (sumPct >= 5) color = 'orange';
            else if (sumPct >= 1) color = 'lightgreen';

            return L.divIcon({{
                html: '<div style="background-color:' + color + '; border-radius: 50%; text-align: center; color: white; font-weight: bold; border: 3px solid white; box-shadow: 0 0 10px rgba(0,0,0,0.5);"><span>' + displayText + '</span></div>',
                className: 'marker-cluster marker-cluster-' + size,
                iconSize: new L.Point(40, 40)
            }});
        }}
        """
    else:
        icon_create_function = """
        function(cluster) {
            var markers = cluster.getAllChildMarkers();
            var sum = 0;
            for (var i = 0; i < markers.length; i++) {
                if (markers[i].options.customCount) {
                    sum += markers[i].options.customCount;
                }
            }
            var size = 'small';
            if (sum >= 5000) size = 'large';
            else if (sum >= 1000) size = 'medium';

            var color = 'lightblue';
            if (sum > 1000) color = 'red';
            else if (sum > 500) color = 'orange';
            else if (sum >= 100) color = 'lightgreen';

            return L.divIcon({
                html: '<div style="background-color:' + color + '; border-radius: 50%; text-align: center; color: white; font-weight: bold; border: 3px solid white; box-shadow: 0 0 10px rgba(0,0,0,0.5);"><span>' + sum + '</span></div>',
                className: 'marker-cluster marker-cluster-' + size,
                iconSize: new L.Point(40, 40)
            });
        }
        """

    marker_cluster = MarkerCluster(
        name="Customer Locations",
        overlay=True,
        control=True,
        icon_create_function=icon_create_function
    )

    for idx, row in pincode_summary.iterrows():
        # Format percentage for display
        pct_display = "<1%" if row['percentage'] < 1 else f"{row['percentage']:.1f}%"

        # Create popup content - always show both count and percentage
        popup_html = f"""
        <div style="font-family: Arial; width: 200px;">
            <h4 style="margin: 0; color: #1f77b4;">📍 {row['CPA_ADDR_CITY']}</h4>
            <hr style="margin: 5px 0;">
            <b>Pincode:</b> {int(row['CPA_PIN_CODE'])}<br>
            <b>State:</b> {row['StateName']}<br>
            <b>Customers:</b> <span style="color: #d62728; font-weight: bold;">{row['customer_count']}</span><br>
            <b>Percentage:</b> <span style="color: #d62728; font-weight: bold;">{pct_display}</span><br>
            <b>Coordinates:</b> {row['Latitude']:.4f}, {row['Longitude']:.4f}
        </div>
        """

        # Determine what to display on marker and color based on mode
        if is_percentage_mode:
            display_text = pct_display
            # Color based on percentage thresholds
            if row['percentage'] >= 10:
                color = 'red'
            elif row['percentage'] >= 5:
                color = 'orange'
            elif row['percentage'] >= 1:
                color = 'lightgreen'
            else:
                color = 'lightblue'
            tooltip_text = f"{row['CPA_ADDR_CITY']} - {pct_display} ({row['customer_count']} customers)"
        else:
            display_text = str(row['customer_count'])
            # Color based on customer count thresholds
            if row['customer_count'] > 1000:
                color = 'red'
            elif row['customer_count'] > 500:
                color = 'orange'
            elif row['customer_count'] > 100:
                color = 'lightgreen'
            else:
                color = 'lightblue'
            tooltip_text = f"{row['CPA_ADDR_CITY']} - {row['customer_count']} customers"

        # Create custom DivIcon that shows the appropriate value
        custom_icon = folium.DivIcon(
            html=f'''
            <div style="
                background-color: {color};
                border-radius: 50%;
                width: 35px;
                height: 35px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: 11px;
                border: 3px solid white;
                box-shadow: 0 0 10px rgba(0,0,0,0.5);
            ">{display_text}</div>
            '''
        )

        # Create marker with custom properties
        marker = folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=tooltip_text,
            icon=custom_icon
        )
        # Add custom properties for customer count and percentage
        marker.options['customCount'] = int(row['customer_count'])
        marker.options['customPercentage'] = float(row['percentage'])
        marker.add_to(marker_cluster)

    marker_cluster.add_to(m)

# Add heatmap layer
if viz_type in ["Heatmap", "Both"]:
    heat_data = [
        [row['Latitude'], row['Longitude'], row['customer_count']]
        for _, row in pincode_summary.iterrows()
    ]

    HeatMap(
        heat_data,
        name="Heatmap",
        min_opacity=0.3,
        max_zoom=18,
        radius=15,
        blur=20,
        gradient={
            0.0: 'blue',
            0.5: 'lime',
            0.7: 'yellow',
            1.0: 'red'
        }
    ).add_to(m)

# Add layer control if both are shown
if viz_type == "Both":
    folium.LayerControl().add_to(m)

# Display map
st_folium(m, width=1400, height=600)

# Display top locations table
st.subheader("📊 Top 20 Locations by Customer Count")
top_locations = pincode_summary.head(20)[['CPA_ADDR_CITY', 'CPA_PIN_CODE', 'StateName', 'customer_count', 'percentage']].copy()
top_locations.columns = ['City', 'Pincode', 'State', 'Customer Count', 'Percentage']
top_locations['Pincode'] = top_locations['Pincode'].astype(int)
top_locations['Percentage'] = top_locations['Percentage'].apply(lambda x: "<1%" if x < 1 else f"{x:.1f}%")
top_locations.index = range(1, len(top_locations) + 1)
st.dataframe(top_locations, width='stretch')

# Add color legend
st.sidebar.markdown("---")
st.sidebar.markdown("### 🎨 Marker Colors")

if display_mode == "Percentage":
    st.sidebar.markdown("**Individual Pincodes & Clusters:**")
    st.sidebar.markdown("🔴 **Red:** ≥ 10%")
    st.sidebar.markdown("🟠 **Orange:** 5-10%")
    st.sidebar.markdown("🟢 **Green:** 1-5%")
    st.sidebar.markdown("🔵 **Blue:** < 1%")
else:
    st.sidebar.markdown("**Individual Pincodes & Clusters:**")
    st.sidebar.markdown("🔴 **Red:** > 1,000 customers")
    st.sidebar.markdown("🟠 **Orange:** 500-1,000 customers")
    st.sidebar.markdown("🟢 **Green:** 100-499 customers")
    st.sidebar.markdown("🔵 **Blue:** < 100 customers")
