import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from src.agent import SupportAgent

agent = None

class SupportAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "agent_loaded": agent is not None}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/process":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
                message = data.get("message", "")
                result = agent.process_message(message)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silence standard HTTP logs for clean output
        return


def run_server(port: int = 8001):
    global agent
    print("Pre-warming SupportAgent...")
    agent = SupportAgent().initialize()
    print(f"Agent loaded. Starting HTTP bridge on port {port}...")
    server = HTTPServer(("127.0.0.1", port), SupportAPIHandler)
    server.serve_forever()


if __name__ == "__main__":
    run_server()
