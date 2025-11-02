# Streamlit Cloud Deployment Guide

## Files Needed for Deployment

✅ **Created:**
- `requirements.txt` - Lists all Python dependencies
- `.gitignore` - Excludes sensitive files from git
- `app.py` - Main Streamlit application
- `pincode_coordinates_google.csv` - Pre-fetched coordinates from Google Maps API

## Deployment Steps

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit - Customer Address Heatmap Dashboard"
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 2. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io/)
2. Sign in with your GitHub account
3. Click "New app"
4. Select your repository and branch
5. Set main file path: `app.py`
6. Click "Deploy"

### 3. Configure Secrets (Optional)

If you plan to use the Google Maps API fetcher in production:

1. In Streamlit Cloud dashboard, click on your app
2. Click "⋮" menu → "Settings" → "Secrets"
3. Add your secrets in TOML format:

```toml
GOOGLE_MAPS_API_KEY = "your-api-key-here"
```

## Important Notes

- **CSV Files:** The app requires these CSV files to be in the repository:
  - `Address Details.csv` (your customer data)
  - `pincode_coordinates_google.csv` (pre-fetched coordinates)

- **File Size Limits:**
  - GitHub has a 100MB file limit per file
  - If your CSVs are larger, consider using Git LFS or alternative storage

- **Google Maps API:**
  - The coordinates are already fetched and cached in `pincode_coordinates_google.csv`
  - You only need the API key if you want to refresh/add new pincodes
  - The app does NOT call the API during runtime (only uses the cached CSV)

## Testing Locally

```bash
# Activate virtual environment
source venv/bin/activate

# Run the app
streamlit run app.py
```

## Troubleshooting

**ModuleNotFoundError:**
- Make sure `requirements.txt` is committed to the repository
- Streamlit Cloud automatically installs packages from `requirements.txt`

**Data Not Loading:**
- Ensure CSV files are committed to the repository
- Check file paths in `app.py` are correct (relative paths)

**Map Not Displaying:**
- Clear browser cache
- Check browser console for JavaScript errors
