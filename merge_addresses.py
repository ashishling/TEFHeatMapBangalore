import pandas as pd
from pathlib import Path

def merge_address_files():
    """Merge Address Details.csv and TNAddress.csv into a single combined CSV"""

    print("=" * 60)
    print("Merging Address CSV Files")
    print("=" * 60)

    csv_files = ['Address Details.csv', 'TNAddress.csv']
    dataframes = []

    for csv_file in csv_files:
        if Path(csv_file).exists():
            print(f"\nLoading {csv_file}...")
            df = pd.read_csv(csv_file)

            # Convert pincode to numeric
            df['CPA_PIN_CODE'] = pd.to_numeric(df['CPA_PIN_CODE'], errors='coerce')

            # Drop rows with invalid pincodes
            original_count = len(df)
            df = df.dropna(subset=['CPA_PIN_CODE'])
            dropped = original_count - len(df)

            print(f"  - Loaded {len(df)} records")
            if dropped > 0:
                print(f"  - Dropped {dropped} records with invalid pincodes")
            print(f"  - Unique pincodes: {df['CPA_PIN_CODE'].nunique()}")

            dataframes.append(df)
        else:
            print(f"\n❌ {csv_file} NOT FOUND")
            return False

    # Combine all dataframes
    print(f"\nMerging {len(dataframes)} files...")
    combined_df = pd.concat(dataframes, ignore_index=True)

    # Save to new file
    output_file = 'Combined_Address_Details.csv'
    combined_df.to_csv(output_file, index=False)

    print(f"\n✅ Successfully created {output_file}")
    print(f"   Total records: {len(combined_df):,}")
    print(f"   Unique pincodes: {combined_df['CPA_PIN_CODE'].nunique()}")
    print(f"   Columns: {', '.join(combined_df.columns)}")

    # Show sample data
    print("\nSample data (first 5 rows):")
    print(combined_df.head())

    print("\n" + "=" * 60)
    return True

if __name__ == "__main__":
    merge_address_files()
