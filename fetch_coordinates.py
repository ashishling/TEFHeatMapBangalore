import pandas as pd
import googlemaps
from dotenv import load_dotenv
import os
import time
from pathlib import Path

# Load environment variables
load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Initialize Google Maps client
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

# Output cache file
CACHE_FILE = 'pincode_coordinates_google.csv'

def get_coordinates_for_pincode(pincode):
    """Fetch lat/long for a given Indian pincode using Google Maps Geocoding API"""
    try:
        # Query format: "Pincode XXXXXX, India"
        geocode_result = gmaps.geocode(f"Pincode {int(pincode)}, India")

        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            address_components = geocode_result[0]['address_components']

            # Extract city/locality and state
            city = None
            state = None
            for component in address_components:
                if 'locality' in component['types']:
                    city = component['long_name']
                elif 'administrative_area_level_1' in component['types']:
                    state = component['long_name']

            return {
                'pincode': int(pincode),
                'latitude': location['lat'],
                'longitude': location['lng'],
                'city': city,
                'state': state,
                'formatted_address': geocode_result[0]['formatted_address']
            }
        else:
            print(f"  ❌ No results for pincode {int(pincode)}")
            return None
    except Exception as e:
        print(f"  ❌ Error fetching pincode {int(pincode)}: {e}")
        return None

def main():
    print("=" * 60)
    print("Google Maps Pincode Coordinate Fetcher")
    print("=" * 60)

    # Check if cache exists
    if Path(CACHE_FILE).exists():
        print(f"\n⚠️  Cache file '{CACHE_FILE}' already exists!")
        response = input("Do you want to (U)se existing, (A)ppend new pincodes, or (R)efetch all? [U/A/R]: ").strip().upper()

        if response == 'U':
            print(f"✅ Using existing cache file: {CACHE_FILE}")
            cached_df = pd.read_csv(CACHE_FILE)
            print(f"   Found {len(cached_df)} cached pincodes")
            return
        elif response == 'A':
            cached_df = pd.read_csv(CACHE_FILE)
            cached_pincodes = set(cached_df['pincode'].values)
            print(f"   Found {len(cached_pincodes)} cached pincodes, will fetch new ones only")
        else:
            cached_pincodes = set()
            print("   Will refetch all pincodes")
    else:
        cached_pincodes = set()

    # Load address data
    print("\nLoading address data...")
    address_df = pd.read_csv('Address Details.csv')
    address_df['CPA_PIN_CODE'] = pd.to_numeric(address_df['CPA_PIN_CODE'], errors='coerce')
    address_df = address_df.dropna(subset=['CPA_PIN_CODE'])

    # Get unique pincodes
    unique_pincodes = sorted(address_df['CPA_PIN_CODE'].unique())
    print(f"Found {len(unique_pincodes)} unique pincodes in Address Details.csv")

    # Filter out already cached pincodes
    pincodes_to_fetch = [p for p in unique_pincodes if p not in cached_pincodes]
    print(f"Need to fetch {len(pincodes_to_fetch)} pincodes from Google Maps API")

    if len(pincodes_to_fetch) == 0:
        print("\n✅ All pincodes already cached!")
        return

    print(f"\n⚠️  This will make {len(pincodes_to_fetch)} API calls")
    print(f"   Google Maps API pricing: https://developers.google.com/maps/billing-and-pricing/pricing")
    print(f"   Geocoding API: $5 per 1000 requests (after free tier)")

    confirm = input("\nProceed? [y/N]: ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled")
        return

    # Fetch coordinates
    print("\nFetching coordinates from Google Maps...")
    results = []

    for i, pincode in enumerate(pincodes_to_fetch, 1):
        print(f"[{i}/{len(pincodes_to_fetch)}] Fetching pincode {int(pincode)}...", end='')

        result = get_coordinates_for_pincode(pincode)
        if result:
            results.append(result)
            print(f" ✅ {result['latitude']:.6f}, {result['longitude']:.6f}")

        # Rate limiting: Google Maps allows 50 requests/second, but let's be conservative
        if i % 10 == 0:
            time.sleep(1)  # Pause every 10 requests

    # Combine with cached data if appending
    if cached_pincodes:
        cached_df = pd.read_csv(CACHE_FILE)
        new_df = pd.DataFrame(results)
        combined_df = pd.concat([cached_df, new_df], ignore_index=True)
    else:
        combined_df = pd.DataFrame(results)

    # Save to cache
    combined_df.to_csv(CACHE_FILE, index=False)
    print(f"\n✅ Saved {len(results)} new coordinates to {CACHE_FILE}")
    print(f"   Total pincodes in cache: {len(combined_df)}")

    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Total pincodes processed: {len(results)}")
    print(f"  Successful: {len(results)}")
    print(f"  Cache file: {CACHE_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    main()
