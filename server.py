#!/usr/bin/env python3
"""
Flask server for the Scouting Map application.
Provides an API to add new clubs with logo upload, geocoding, and file updates.
"""

import json
import os
import re
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests

app = Flask(__name__, static_folder='.')
CORS(app)  # Enable CORS for all routes

# NYRB HQ coordinates for distance calculation
NYRB_HQ = (40.8167, -74.4028)

# Load divisions mapping
DIVISIONS_FILE = os.path.join(os.path.dirname(__file__), 'divisions.json')
with open(DIVISIONS_FILE, 'r') as f:
    DIVISIONS_DATA = json.load(f)


def geocode_address(address):
    """Geocode an address using OpenStreetMap Nominatim (free, no API key).
    Tries progressively simpler versions of the address if full address fails."""
    url = "https://nominatim.openstreetmap.org/search"
    headers = {'User-Agent': 'ScoutingMap/1.0'}

    # Try progressively simpler versions of the address
    # Remove suite/unit numbers, then try just city+state
    address_variants = [address]

    # Remove suite/unit numbers like "#266" or "Suite 100"
    simplified = re.sub(r'#\d+|Suite\s*\d+|Unit\s*\d+|Apt\.?\s*\d+', '', address, flags=re.IGNORECASE).strip()
    simplified = re.sub(r',\s*,', ',', simplified)  # Clean up double commas
    if simplified != address:
        address_variants.append(simplified)

    # Try to extract just city, state, zip
    city_state_match = re.search(r',\s*([^,]+,\s*[A-Z]{2}\s*\d{5})', address)
    if city_state_match:
        address_variants.append(city_state_match.group(1).strip())

    # Try just city and state
    city_state_match2 = re.search(r'([^,]+,\s*[A-Z]{2})', address)
    if city_state_match2:
        address_variants.append(city_state_match2.group(1).strip())

    for variant in address_variants:
        params = {
            'q': variant,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }

        resp = requests.get(url, params=params, headers=headers)
        if resp.status_code == 200 and resp.json():
            result = resp.json()[0]
            return {
                'lat': float(result['lat']),
                'lng': float(result['lon']),
                'state': result.get('address', {}).get('state', ''),
                'city': result.get('address', {}).get('city') or result.get('address', {}).get('town') or result.get('address', {}).get('village', ''),
                'state_code': get_state_code(result.get('address', {}))
            }
        time.sleep(0.5)  # Rate limit between attempts

    return None


def get_state_code(address_details):
    """Extract state code from Nominatim address details."""
    state = address_details.get('state', '')
    # Map full state names to codes
    state_map = {
        'Illinois': 'IL', 'Indiana': 'IN', 'Michigan': 'MI', 'Ohio': 'OH', 'Wisconsin': 'WI',
        'Minnesota': 'MN', 'New York': 'NY', 'New Jersey': 'NJ', 'Connecticut': 'CT',
        'Massachusetts': 'MA', 'Pennsylvania': 'PA', 'Maryland': 'MD', 'Virginia': 'VA',
        'Delaware': 'DE', 'California': 'CA', 'Texas': 'TX', 'Florida': 'FL', 'Georgia': 'GA',
        'North Carolina': 'NC', 'South Carolina': 'SC', 'Tennessee': 'TN', 'Kentucky': 'KY',
        'Alabama': 'AL', 'Colorado': 'CO', 'Arizona': 'AZ', 'Nevada': 'NV', 'Utah': 'UT',
        'New Mexico': 'NM', 'Oregon': 'OR', 'Washington': 'WA', 'Idaho': 'ID', 'Montana': 'MT',
        'Wyoming': 'WY', 'Maine': 'ME', 'Vermont': 'VT', 'New Hampshire': 'NH', 'Rhode Island': 'RI',
        'West Virginia': 'WV', 'District of Columbia': 'DC', 'Oklahoma': 'OK', 'Arkansas': 'AR',
        'Louisiana': 'LA', 'Alaska': 'AK', 'Hawaii': 'HI', 'Ontario': 'ON', 'Quebec': 'QC'
    }

    # Check if it's already a code
    if len(state) == 2:
        return state.upper()

    return state_map.get(state, state[:2].upper() if state else 'XX')


def calculate_drive_distance(lat, lng):
    """Calculate drive distance/time from NYRB HQ using OSRM (free, no API key)."""
    url = f"http://router.project-osrm.org/route/v1/driving/{NYRB_HQ[1]},{NYRB_HQ[0]};{lng},{lat}"
    params = {'overview': 'false'}

    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('routes'):
                route = data['routes'][0]
                distance_miles = round(route['distance'] / 1609.34)  # meters to miles
                duration_seconds = route['duration']
                hours = int(duration_seconds // 3600)
                minutes = int((duration_seconds % 3600) // 60)

                if hours > 0:
                    drive_time = f"{hours}h {minutes}m"
                else:
                    drive_time = f"{minutes}m"

                return distance_miles, drive_time
    except Exception as e:
        print(f"OSRM error: {e}")

    # Fallback: estimate based on straight-line distance
    from math import radians, sin, cos, sqrt, atan2
    lat1, lon1 = radians(NYRB_HQ[0]), radians(NYRB_HQ[1])
    lat2, lon2 = radians(lat), radians(lng)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance_km = 6371 * c
    distance_miles = round(distance_km * 0.621371)
    # Estimate drive time at 50 mph average
    hours = distance_miles / 50
    h = int(hours)
    m = int((hours - h) * 60)
    drive_time = f"{h}h {m}m" if h > 0 else f"{m}m"

    return distance_miles, drive_time


def generate_club_id(name):
    """Generate a club ID from the name."""
    # Remove common suffixes and clean up
    name = name.lower()
    name = re.sub(r'\s+(fc|sc|soccer|club|academy|united)$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    name = re.sub(r'\s+', '_', name.strip())
    return name


def generate_initials(name):
    """Generate 2-4 letter initials from the club name."""
    # Remove common words
    words = name.replace('FC', '').replace('SC', '').replace('Soccer', '').replace('Club', '').replace('Academy', '').split()
    words = [w for w in words if w]

    if len(words) == 1:
        return words[0][:3].upper()
    elif len(words) == 2:
        return (words[0][0] + words[1][0]).upper()
    else:
        return ''.join(w[0] for w in words[:3]).upper()


def update_index_html(club_data):
    """Add the new club to the clubs array in index.html."""
    index_path = os.path.join(os.path.dirname(__file__), 'index.html')

    with open(index_path, 'r') as f:
        content = f.read()

    # Find the end of the clubs array (before the closing ];)
    # Look for the last club entry and add after it
    pattern = r'(\{name:"[^"]+",\s*state:"[^"]+",\s*league:"[^"]+",\s*division:"[^"]+",\s*lat:[^,]+,\s*lng:[^,]+,\s*logo:"[^"]+",\s*website:"[^"]*",\s*driveMiles:\d+,\s*driveTime:"[^"]+",\s*initials:"[^"]+",\s*isPro:(?:true|false),\s*pathway:"[^"]+",\s*clubId:"[^"]+"\})\n\];'

    match = re.search(pattern, content)
    if match:
        last_club = match.group(1)
        new_club = f'''{{name:"{club_data['name']}", state:"{club_data['state']}", league:"{club_data['league']}", division:"{club_data['division']}", lat:{club_data['lat']}, lng:{club_data['lng']}, logo:"{club_data['logo']}", website:"", driveMiles:{club_data['driveMiles']}, driveTime:"{club_data['driveTime']}", initials:"{club_data['initials']}", isPro:false, pathway:"both", clubId:"{club_data['clubId']}"}}'''

        content = content.replace(
            f'{last_club}\n];',
            f'{last_club},\n  {new_club}\n];'
        )

        with open(index_path, 'w') as f:
            f.write(content)
        return True

    return False


def update_clubs_json(club_data):
    """Add the new club to data/clubs.json."""
    clubs_path = os.path.join(os.path.dirname(__file__), 'data', 'clubs.json')

    with open(clubs_path, 'r') as f:
        clubs = json.load(f)

    clubs[club_data['clubId']] = {
        "id": club_data['clubId'],
        "name": club_data['name'],
        "logo": club_data['logo'],
        "website": "",
        "location": {
            "city": club_data['city'],
            "state": club_data['state'],
            "address": club_data['address']
        },
        "conference": club_data['division'],
        "isPro": False,
        "director": {"name": "", "email": "", "phone": ""},
        "teams": {}
    }

    with open(clubs_path, 'w') as f:
        json.dump(clubs, f, indent=2)

    return True


def update_team_html(club_data):
    """Add the new club to team.html (both clubsData and playersData)."""
    team_path = os.path.join(os.path.dirname(__file__), 'team.html')

    with open(team_path, 'r') as f:
        content = f.read()

    # Add to clubsData (find the closing }; of clubsData)
    # Look for pattern: "last_club": { ... } }; var playersData
    clubs_pattern = r'(\s+"[a-z_]+":\s*\{\s*"id":\s*"[^"]+",\s*"name":\s*"[^"]+",\s*"logo":\s*"[^"]+",\s*"website":\s*"[^"]*",\s*"isPro":\s*(?:true|false),\s*"director":\s*\{[^}]*\}\s*\})\n\};\n\nvar playersData'

    clubs_match = re.search(clubs_pattern, content)
    if clubs_match:
        last_entry = clubs_match.group(1)
        new_club_entry = f''',
  "{club_data['clubId']}": {{
    "id": "{club_data['clubId']}",
    "name": "{club_data['name']}",
    "logo": "{club_data['logo']}",
    "website": "",
    "isPro": false,
    "director": {{ "name": "", "email": "", "phone": "" }}
  }}'''

        content = content.replace(
            f'{last_entry}\n}};\n\nvar playersData',
            f'{last_entry}{new_club_entry}\n}};\n\nvar playersData'
        )

    # Add to playersData (find the closing }; of playersData)
    players_pattern = r'(\s+"[a-z_]+":\s*\{[^}]*"u\d+":\s*\{[^}]*\}[^}]*\})\n\};'

    # Simpler approach: find the last entry before }; at the end
    # Look for the pattern: } }; at the end of playersData
    players_end_pattern = r'(\s+\}\n\s+\}\n\};)\s*$'
    players_match = re.search(players_end_pattern, content)

    if players_match:
        end_section = players_match.group(1)
        new_players_entry = f''',
  "{club_data['clubId']}": {{
  }}'''

        content = content.replace(
            end_section,
            f'{end_section[:-3]}{new_players_entry}\n}};'
        )

    with open(team_path, 'w') as f:
        f.write(content)

    return True


# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Serve index.html."""
    return send_from_directory('.', 'index.html')


@app.route('/<path:path>')
def static_files(path):
    """Serve static files."""
    return send_from_directory('.', path)


@app.route('/api/add-club', methods=['POST'])
def add_club():
    """Add a new club to the scouting map."""
    try:
        name = request.form.get('name')
        league = request.form.get('league', 'HD')
        address = request.form.get('address')
        logo_file = request.files.get('logo')

        if not name or not address or not logo_file:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        # Generate club ID and initials
        club_id = generate_club_id(name)
        initials = generate_initials(name)

        # Save logo
        logo_ext = os.path.splitext(logo_file.filename)[1] or '.png'
        logo_filename = f"{name}{logo_ext}"
        logo_path = os.path.join(os.path.dirname(__file__), 'MLS Logos', logo_filename)
        logo_file.save(logo_path)

        # Geocode address
        geo = geocode_address(address)
        if not geo:
            return jsonify({'success': False, 'error': 'Could not geocode address'}), 400

        # Calculate drive distance
        drive_miles, drive_time = calculate_drive_distance(geo['lat'], geo['lng'])

        # Get division from state
        state_code = geo['state_code']
        division = DIVISIONS_DATA['state_to_division'].get(state_code, 'Other')

        # Prepare club data
        club_data = {
            'name': name,
            'clubId': club_id,
            'initials': initials,
            'league': league,
            'division': division,
            'lat': geo['lat'],
            'lng': geo['lng'],
            'city': geo['city'],
            'state': state_code,
            'address': address,
            'logo': f"MLS Logos/{logo_filename}",
            'driveMiles': drive_miles,
            'driveTime': drive_time
        }

        # Update all files
        update_index_html(club_data)
        update_clubs_json(club_data)
        update_team_html(club_data)

        return jsonify({
            'success': True,
            'clubId': club_id,
            'message': f'Successfully added {name} to the scouting map'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/divisions', methods=['GET'])
def get_divisions():
    """Return the list of available divisions."""
    return jsonify(DIVISIONS_DATA)


if __name__ == '__main__':
    print("Starting Scouting Map Server...")
    print("Open http://localhost:5001 in your browser")
    app.run(host='0.0.0.0', port=5001, debug=True)
