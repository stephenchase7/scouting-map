#!/usr/bin/env python3
"""
Simple Flask server for Add Club functionality
Handles geocoding and file operations that can't be done from browser

Usage:
    python3 add_club_server.py

Then use the Add Club button in index.html
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import re
from pathlib import Path

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).parent.parent
LOGO_DIR = BASE_DIR / "scouting-map" / "MLS Logos"

# Ensure logo directory exists
LOGO_DIR.mkdir(parents=True, exist_ok=True)

def geocode_address(address):
    """Geocode address using Nominatim"""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1
        }
        headers = {
            'User-Agent': 'NYRB-Scouting-Map/1.0'
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        if not data:
            return None

        result = data[0]
        return {
            'lat': float(result['lat']),
            'lng': float(result['lon']),
            'display_name': result['display_name']
        }
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None

def extract_state(address, display_name):
    """Extract state abbreviation from address"""
    # Try to extract from input address (e.g., "PA 19428")
    match = re.search(r',?\s*([A-Z]{2})\s+\d{5}', address)
    if match:
        return match.group(1)

    # Extract from display name
    parts = display_name.split(',')
    state_map = {
        'New York': 'NY', 'New Jersey': 'NJ', 'Pennsylvania': 'PA',
        'Connecticut': 'CT', 'Massachusetts': 'MA', 'Rhode Island': 'RI',
        'New Hampshire': 'NH', 'Vermont': 'VT', 'Maine': 'ME',
        'Delaware': 'DE', 'Maryland': 'MD', 'Virginia': 'VA',
        'West Virginia': 'WV', 'North Carolina': 'NC', 'South Carolina': 'SC',
        'Georgia': 'GA', 'Florida': 'FL', 'Ohio': 'OH', 'Michigan': 'MI',
        'Illinois': 'IL', 'Indiana': 'IN', 'Wisconsin': 'WI',
        'California': 'CA', 'Texas': 'TX', 'Arizona': 'AZ', 'Nevada': 'NV'
    }

    for part in parts:
        part = part.strip()
        # Check for state abbreviation
        if re.match(r'^[A-Z]{2}$', part):
            return part
        # Check for full state name
        if part in state_map:
            return state_map[part]

    return 'XX'

def determine_division(state):
    """Determine division from state"""
    division_map = {
        'NY': 'Northeast Division', 'NJ': 'Northeast Division', 'CT': 'Northeast Division',
        'MA': 'Northeast Division', 'RI': 'Northeast Division', 'NH': 'Northeast Division',
        'VT': 'Northeast Division', 'ME': 'Northeast Division',
        'PA': 'Mid-Atlantic Division', 'DE': 'Mid-Atlantic Division',
        'MD': 'Mid-Atlantic Division', 'VA': 'Mid-Atlantic Division',
        'WV': 'Mid-Atlantic Division', 'DC': 'Mid-Atlantic Division',
        'NC': 'Southeast Division', 'SC': 'Southeast Division',
        'GA': 'Southeast Division', 'FL': 'Florida Division',
        'OH': 'Mid-America Division', 'MI': 'Mid-America Division',
        'IL': 'Mid-America Division', 'IN': 'Mid-America Division',
        'WI': 'Mid-America Division'
    }
    return division_map.get(state, 'Other')

def generate_initials(name):
    """Generate club initials"""
    words = name.split()
    if len(words) == 1:
        return words[0][:3].upper()
    return ''.join(w[0] for w in words).upper()[:4]

@app.route('/api/add-club', methods=['POST'])
def add_club():
    """Handle add club request"""
    try:
        # Get form data
        club_name = request.form.get('name')
        league = request.form.get('league')
        address = request.form.get('address')
        logo_file = request.files.get('logo')

        if not all([club_name, league, address, logo_file]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        # Geocode address
        print(f"Geocoding: {address}")
        geo_result = geocode_address(address)

        if not geo_result:
            return jsonify({'success': False, 'error': 'Failed to geocode address. Please verify it is correct.'}), 400

        lat = geo_result['lat']
        lng = geo_result['lng']
        state = extract_state(address, geo_result['display_name'])

        print(f"Geocoded: {lat}, {lng}, {state}")

        # Generate club ID
        club_id = re.sub(r'[^a-z0-9]+', '_', club_name.lower()).strip('_')

        # Save logo file
        file_ext = os.path.splitext(logo_file.filename)[1]
        logo_filename = f"{club_id}{file_ext}"
        logo_path = LOGO_DIR / logo_filename
        logo_file.save(str(logo_path))

        print(f"Saved logo: {logo_path}")

        # Determine division
        division = determine_division(state)

        # Generate club entry
        club_entry = {
            'name': club_name,
            'state': state,
            'league': league,
            'division': division,
            'lat': lat,
            'lng': lng,
            'logo': f'MLS Logos/{logo_filename}',
            'website': '',
            'driveMiles': 0,
            'driveTime': '0m',
            'initials': generate_initials(club_name),
            'isPro': False,
            'pathway': 'both' if league == 'HD' else 'u13-u15',
            'clubId': club_id
        }

        # Return success with club data
        return jsonify({
            'success': True,
            'message': f'Club "{club_name}" added successfully!',
            'club': club_entry,
            'team_html_code': f'''
  "{club_id}": {{
    "id": "{club_id}",
    "name": "{club_name}",
    "logo": "MLS Logos/{logo_filename}",
    "website": "",
    "isPro": false,
    "director": {{ "name": "", "email": "", "phone": "" }}
  }},
'''
        })

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Add Club server is running'})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("ADD CLUB SERVER STARTING")
    print("="*60)
    print(f"Base directory: {BASE_DIR}")
    print(f"Logo directory: {LOGO_DIR}")
    print(f"Server running at: http://localhost:5001")
    print("\nReady to accept Add Club requests!")
    print("Open index.html and use the '+ Add Club' button")
    print("="*60 + "\n")

    app.run(host='localhost', port=5001, debug=True)
