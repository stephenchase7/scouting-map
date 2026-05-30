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

# Load documents once at startup
documents_cache = None

def load_documents():
    """Load all documents from rules_data/rules_web.json"""
    global documents_cache
    if documents_cache is not None:
        return documents_cache

    rules_path = os.path.join(RULES_DATA_DIR, 'rules_web.json')
    if not os.path.exists(rules_path):
        print(f"Warning: {rules_path} not found")
        return None

    with open(rules_path, 'r') as f:
        data = json.load(f)

    documents_cache = data.get('combined', {}).get('documents', [])
    print(f"Loaded {len(documents_cache)} documents")
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

IMPORTANT INSTRUCTIONS:
1. Provide a clear, helpful summary answering the question
2. Always cite specific page numbers and document names where the information is found
3. Format page references as: [Page X - Document Name]
4. If information spans multiple pages or documents, cite all relevant locations
5. If the answer is not in the documents, say so clearly

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


class RulesHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler that serves static files and handles /api/ask"""

    def __init__(self, *args, **kwargs):
        # Serve from scouting-map directory
        super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)

    def do_POST(self):
        """Handle POST requests to /api/ask"""
        if self.path == '/api/ask':
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')

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
        if '/api/' in args[0] if args else False:
            print(f"[API] {args[0]}")
        elif not any(ext in str(args) for ext in ['.js', '.css', '.png', '.ico']):
            print(f"[{self.address_string()}] {args[0]}")


def main():
    # Ensure documents are loaded
    load_documents()

    # Allow port reuse
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), RulesHandler) as httpd:
        print(f"\n{'='*50}")
        print(f"MLS NEXT Rules Server")
        print(f"{'='*50}")
        print(f"Server running at: http://localhost:{PORT}")
        print(f"Rules page: http://localhost:{PORT}/rules.html")
        print(f"API endpoint: POST http://localhost:{PORT}/api/ask")
        print(f"{'='*50}")
        print(f"Press Ctrl+C to stop\n")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")


if __name__ == '__main__':
    main()
