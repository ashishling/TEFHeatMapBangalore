import pandas as pd
import folium
from folium.plugins import HeatMap

print("Loading CSV files...")

# Load the address details
address_df = pd.read_csv('Address Details.csv')
print(f"Loaded {len(address_df)} address records")

# Load the pincode lat/long reference data
pincode_df = pd.read_csv('pincode_with_lat-long.csv', low_memory=False)
print(f"Loaded {len(pincode_df)} pincode records")

print("\nData Preview:")
print("\nAddress Details columns:", address_df.columns.tolist())
print("Address Details sample:")
print(address_df.head())

print("\nPincode Data columns:", pincode_df.columns.tolist())
print("Pincode Data sample:")
print(pincode_df.head())

# Clean the data
print("\nCleaning data...")
# Remove any leading/trailing whitespace and convert pincodes to integers
address_df['CPA_PIN_CODE'] = pd.to_numeric(address_df['CPA_PIN_CODE'], errors='coerce')
pincode_df['Pincode'] = pd.to_numeric(pincode_df['Pincode'], errors='coerce')

# Convert Latitude and Longitude to numeric (handle mixed types)
pincode_df['Latitude'] = pd.to_numeric(pincode_df['Latitude'], errors='coerce')
pincode_df['Longitude'] = pd.to_numeric(pincode_df['Longitude'], errors='coerce')

# Drop rows with missing pincodes
address_df = address_df.dropna(subset=['CPA_PIN_CODE'])
pincode_df = pincode_df.dropna(subset=['Pincode', 'Latitude', 'Longitude'])

print(f"After cleaning: {len(address_df)} address records, {len(pincode_df)} pincode records")

# Merge the dataframes
print("\nMerging data...")
merged_df = address_df.merge(
    pincode_df[['Pincode', 'Latitude', 'Longitude', 'OfficeName', 'District', 'StateName']],
    left_on='CPA_PIN_CODE',
    right_on='Pincode',
    how='left'
)

# Check merge success
print(f"Merged {len(merged_df)} records")
print(f"Records with valid coordinates: {merged_df[['Latitude', 'Longitude']].notna().all(axis=1).sum()}")

# Remove rows without coordinates
merged_df = merged_df.dropna(subset=['Latitude', 'Longitude'])
print(f"Final records with coordinates: {len(merged_df)}")

# Aggregate data - count addresses per location
print("\nAggregating data by location...")
location_counts = merged_df.groupby(['Latitude', 'Longitude']).size().reset_index(name='count')
print(f"Unique locations: {len(location_counts)}")
print(f"Total addresses mapped: {location_counts['count'].sum()}")

# Create the heatmap
print("\nCreating heatmap...")

# Calculate center of map based on data
center_lat = location_counts['Latitude'].mean()
center_lon = location_counts['Longitude'].mean()

# Create base map
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=6,
    tiles='OpenStreetMap'
)

# Prepare data for heatmap - [latitude, longitude, weight]
heat_data = [
    [row['Latitude'], row['Longitude'], row['count']]
    for _, row in location_counts.iterrows()
]

# Add heatmap layer
HeatMap(
    heat_data,
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

# Save the map
output_file = 'address_heatmap.html'
m.save(output_file)
print(f"\nHeatmap saved to: {output_file}")

# Print statistics
print("\nStatistics:")
print(f"- Total unique locations: {len(location_counts)}")
print(f"- Total addresses: {location_counts['count'].sum()}")
print(f"- Average addresses per location: {location_counts['count'].mean():.2f}")
print(f"- Max addresses at one location: {location_counts['count'].max()}")
print(f"- Map center: ({center_lat:.4f}, {center_lon:.4f})")

# Show top 10 locations
print("\nTop 10 locations by address count:")
top_locations = merged_df.groupby(['CPA_ADDR_CITY', 'CPA_PIN_CODE', 'Latitude', 'Longitude']).size().reset_index(name='count').sort_values('count', ascending=False).head(10)
for idx, row in top_locations.iterrows():
    print(f"  {row['CPA_ADDR_CITY']}, PIN: {int(row['CPA_PIN_CODE'])} - {row['count']} addresses")

print("\nDone! Open 'address_heatmap.html' in a web browser to view the heatmap.")
