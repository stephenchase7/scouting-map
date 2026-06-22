#!/usr/bin/env python3
"""
MLS NEXT Rules AI Server
Serves rules.html and provides AI-powered search via /api/ask endpoint
"""

import os
import json
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
import anthropic

# Load .env from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

PORT = 8080
RULES_DATA_DIR = os.path.join(os.path.dirname(__file__), 'rules_data')
SCOUTING_MAP_DIR = os.path.dirname(__file__)

# Load documents once at startup
documents_cache = None

# HTML document mappings
HTML_DOCUMENTS = [
    ('player_development_guidelines.html', 'Player Development Guidelines'),
    ('player_movement_guidelines.html', 'Player Movement Guidelines'),
    ('homegrown_rules_regulations.html', 'HD (Homegrown Division) Rules'),
    ('academy_rules_regulations.html', 'AD (Academy Division) Rules'),
]

def load_documents():
    """Load all documents from HTML files for better semantic search"""
    global documents_cache
    if documents_cache is not None:
        return documents_cache

    documents_cache = []

    # Load HTML documents
    for filename, doc_name in HTML_DOCUMENTS:
        filepath = os.path.join(SCOUTING_MAP_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()
                # Strip HTML tags for text extraction
                import re
                text = re.sub(r'<[^>]+>', ' ', html_content)
                text = re.sub(r'\s+', ' ', text).strip()
                documents_cache.append({
                    'name': doc_name,
                    'text': text,
                    'html': html_content
                })
                print(f"  Loaded: {doc_name} ({len(text)} chars)")
        else:
            print(f"  Warning: {filename} not found")

    # Fallback to JSON if no HTML files found
    if not documents_cache:
        rules_path = os.path.join(RULES_DATA_DIR, 'rules_web.json')
        if os.path.exists(rules_path):
            with open(rules_path, 'r') as f:
                data = json.load(f)
            documents_cache = data.get('combined', {}).get('documents', [])
            print(f"Loaded {len(documents_cache)} documents from JSON fallback")

    print(f"Total: {len(documents_cache)} documents loaded")
    return documents_cache

def ask_claude(question: str) -> dict:
    """Send question to Claude with all document context"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not found in .env"}

    documents = load_documents()
    if not documents:
        return {"error": "No documents loaded"}

    # Build context with page markers
    context = ""
    for doc in documents:
        context += f"\n\n{'='*60}\n"
        context += f"DOCUMENT: {doc['name']}\n"
        context += f"{'='*60}\n"
        context += doc['text']

    # Truncate if too long (Claude has ~200k context)
    if len(context) > 150000:
        context = context[:150000] + "\n\n[...truncated...]"

    prompt = f"""You are an expert on MLS NEXT rules and regulations. Answer the user's question based on the official documentation provided below.

The documents available are:
1. Player Development Guidelines (36 pages) - Training guidelines, age-appropriate development
2. Player Movement Guidelines (3 pages) - Player transfer windows, movement periods, roster freeze
3. HD (Homegrown Division) Rules (37 pages) - Rules for Homegrown Division clubs
4. AD (Academy Division) Rules (28 pages) - Rules for Academy Division clubs

IMPORTANT INSTRUCTIONS:
1. Search ALL FOUR documents thoroughly to find relevant information
2. Provide a clear, helpful answer summarizing key points
3. Always cite specific page numbers AND document names where the information is found
4. Format page references EXACTLY as: [Page X - Document Name] where Document Name is one of:
   - Player Development Guidelines
   - Player Movement Guidelines
   - HD (Homegrown Division) Rules
   - AD (Academy Division) Rules
5. If information appears in multiple documents, cite ALL relevant locations
6. If the answer is not in any document, say so clearly

USER QUESTION: {question}

DOCUMENTATION:
{context}"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        answer = response.content[0].text
        return {"answer": answer, "success": True}

    except Exception as e:
        return {"error": str(e), "success": False}


def generate_scouting_report(data: dict) -> dict:
    """Generate a professional scouting report using Claude"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not found in .env", "success": False}

    player_name = data.get('playerName', 'The player')
    position = data.get('position', 'Unknown')
    special_weapon = data.get('specialWeapon', '')
    notes_with_ball = data.get('notesWithBall', '')
    notes_against_ball = data.get('notesAgainstBall', '')

    # Check if there's any meaningful input
    if not notes_with_ball.strip() and not notes_against_ball.strip() and not special_weapon:
        return {"error": "Please provide some notes or select traits", "success": False}

    system_prompt = """You are a professional youth soccer scout writing a scouting report.
Convert the rough notes provided into polished, professional scouting paragraphs.

Rules:
1. Write in clear, professional scouting language
2. Be specific and reference what was observed
3. Only write about what is explicitly mentioned in the notes
4. Do NOT fabricate or assume information not provided
5. If a section has no notes, write "N/A" for that section
6. Use position-appropriate vocabulary (e.g., "distribution" for GK, "link-up play" for CAM)
7. Keep each section to 2-3 sentences
8. Do NOT use em-dashes (—), use commas or periods instead"""

    user_prompt = f"""Player: {player_name}
Position: {position}
Special Weapons: {special_weapon if special_weapon else 'None specified'}

WITH THE BALL NOTES:
{notes_with_ball if notes_with_ball.strip() else 'No notes provided'}

AGAINST THE BALL NOTES:
{notes_against_ball if notes_against_ball.strip() else 'No notes provided'}

Generate a professional scouting report with exactly two sections:

**With the Ball:**
[Professional paragraph about attacking/possession abilities based on notes above]

**Against the Ball:**
[Professional paragraph about defensive abilities based on notes above]"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": system_prompt + "\n\n" + user_prompt}
            ]
        )

        report_text = response.content[0].text

        # Parse sections from response
        with_ball = ""
        against_ball = ""

        # Try to extract sections
        if "**With the Ball:**" in report_text or "With the Ball:" in report_text:
            parts = report_text.split("Against the Ball")
            if len(parts) >= 2:
                with_ball_part = parts[0]
                # Clean up the with ball section
                with_ball = with_ball_part.replace("**With the Ball:**", "").replace("With the Ball:", "").strip()
                with_ball = with_ball.replace("**", "").strip()

                against_ball_part = parts[1]
                # Clean up the against ball section
                against_ball = against_ball_part.replace(":**", "").replace(":", "").strip()
                against_ball = against_ball.replace("**", "").strip()

        return {
            "success": True,
            "report": report_text,
            "withBall": with_ball,
            "againstBall": against_ball
        }

    except Exception as e:
        return {"error": str(e), "success": False}


class RulesHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler that serves static files and handles /api/ask"""

    def __init__(self, *args, **kwargs):
        # Serve from scouting-map directory
        super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)

    def do_POST(self):
        """Handle POST requests"""
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')

        if self.path == '/api/ask':
            try:
                data = json.loads(body)
                question = data.get('question', '')

                if not question:
                    self.send_json_response({"error": "No question provided"}, 400)
                    return

                print(f"Question: {question}")
                result = ask_claude(question)
                self.send_json_response(result)

            except json.JSONDecodeError:
                self.send_json_response({"error": "Invalid JSON"}, 400)
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)

        elif self.path == '/api/generate-report':
            try:
                data = json.loads(body)
                print(f"Generate Report: {data.get('playerName', 'Unknown')}")
                result = generate_scouting_report(data)
                self.send_json_response(result)

            except json.JSONDecodeError:
                self.send_json_response({"error": "Invalid JSON"}, 400)
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)

        else:
            self.send_error(404, "Not Found")

    def send_json_response(self, data: dict, status: int = 200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        """Custom logging"""
        try:
            msg = str(args[0]) if args else ''
            if '/api/' in msg:
                print(f"[API] {msg}")
            elif not any(ext in msg for ext in ['.js', '.css', '.png', '.ico', '.jpg']):
                print(f"[{self.address_string()}] {msg}")
        except:
            pass  # Silently ignore logging errors


def main():
    # Ensure documents are loaded
    load_documents()

    # Allow port reuse
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), RulesHandler) as httpd:
        print(f"\n{'='*50}")
        print(f"MLS NEXT Rules & Scouting Server")
        print(f"{'='*50}")
        print(f"Server running at: http://localhost:{PORT}")
        print(f"Rules page: http://localhost:{PORT}/rules.html")
        print(f"Scouts page: http://localhost:{PORT}/scouts.html")
        print(f"API endpoints:")
        print(f"  POST /api/ask - Rules Q&A")
        print(f"  POST /api/generate-report - Scout Report AI")
        print(f"{'='*50}")
        print(f"Press Ctrl+C to stop\n")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")


if __name__ == '__main__':
    main()
