#Aleksandr Polskiy
"""This script provides a sample for creating a response to an HTTP request
based on a custom json header from the body
Any problems with the script and 999 error code will be returned"""
import http.server
import socketserver
import json
import uuid
import time
import sys
import logging

#sample curl requests for bash:
#curl -X GET http://localhost:8080 -H "Content-Type: application/json"
#-d "{"caller-number": "18884400200"}"


#curl -X POST http://localhost:8080 -H "Content-Type: application/json"
# -d "{"caller-number": "18884400201"}"
#curl -X PUT http://localhost:8080 -H "Content-Type: application/json"

# -d "{"caller-number": "18884400590"}"
#curl -X DELETE http://localhost:8080 -H "Content-Type: application/json"
# -d "{"caller-number": "18884400591"}"

#curl -X PATCH http://localhost:8080 -H "Content-Type: application/json"
# -d "{"caller-number": "18884400592"}"

#sample curl requests for cmd:
#curl -X GET http://localhost:8080 -H "Content-Type: application/json" -d "{\"caller-number\": \"18884400403\"}"

#curl -X POST http://localhost:8080 -H "Content-Type: application/json"
# -d "{\"caller-number\": \"18884400201\"}"
#curl -X POST http://localhost:8080 -H "Content-Type: application/json"
# -d "{\"caller-number\": \"18884400500\"}"

#curl -X PUT http://localhost:8080 -H "Content-Type: application/json"
# -d "{\"caller-number\": \"18884400590\"}"

#curl -X DELETE http://localhost:8080 -H "Content-Type: application/json"
# -d "{\"caller-number\": \"18884400591\"}"

#curl -X PATCH http://localhost:8080 -H "Content-Type: application/json"
# -d "{\"caller-number\": \"18884400592\"}"



# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PORT = 8080
global server_instance
global httpd
server_instance = None  # Global variable to hold the server instance


class CustomRequestHandler(http.server.BaseHTTPRequestHandler):
    """Handles HTTP GET, POST, PUT, DELETE, PATCH requests with custom logic."""

    def _send_custom_response(self, status_code: int, response_data=None):
        """Sends an HTTP response with a custom status code and optional JSON body."""
        try:
            # Ensure 3-digit status code for HTTP compliance
            if status_code >= 600:
                logging.warning("Using non-standard HTTP status code {status_code}. %s",status_code)
                logging.warning("Standard practice is 3-digits less than 600.")

            self.send_response(status_code)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            if response_data is not None:
                response_bytes = json.dumps(response_data).encode('utf-8')
                self.wfile.write(response_bytes)
        except Exception as exc:
            logging.error("Error sending response: %s", exc)
            # If an error occurs here, try sending a 999 response
            try:
                self.send_response(999, "Internal Script Error")
                self.end_headers()
            except Exception as e:
                logging.error("Error sending 999 response: %s", e)
                sys.exit(1)

    def _handle_request_logic(self, method: str):
        """Processes the request to determine the status code and actions."""
        logging.info("Function _handle_request_logic received %s request.", method)
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                # Read and parse the JSON body
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)
                # Check for "caller-number" in the JSON body
                if "caller-number" in data:
                    if len(data["caller-number"]) < 3:
                        logging.error("Caller number too short. Using 999.")
                        status_code = 999
                    else:
                        if not data["caller-number"][-3:].isdigit():
                            logging.error("Caller number is not a digits. Using 999.")
                            status_code = 999
                        else:
                            status_code = int(data["caller-number"][-3:])
                else:
                    logging.error("No 'caller-number' in JSON body. Using 999.")
                    status_code = 999  # Bad Request if no code specified in JSON
            else:
                # Check the 'X-Caller-Number' header if no body
                custom_code_header = self.headers.get('X-Caller-Number', None)
                if custom_code_header:
                    status_code = int(custom_code_header)
                else:
                    logging.error("No body header calling-number and"
                                  " 'X-Caller-Number' header. Using 999.")
                    status_code = 999  # Default to 999 for simple requests, if not header
                    #and no json body

            self._process_status_code(status_code)
        except json.JSONDecodeError:
            self._send_custom_response(999, {"error": "Invalid JSON body"})
        except Exception as e:
            logging.error("Error in request handling logic: %s", e)
            self._process_status_code(999)  # General script errors generate 999

    def _process_status_code(self, code):
        """Performs actions based on the determined status code."""
        if code == 201:
            session_id = str(uuid.uuid4())
            response_data = {"session_id": session_id}
            self._send_custom_response(201, response_data)
        elif code == 590:
            logging.info("Received 590, sleeping for 120 seconds...")
            time.sleep(120)

        elif code == 591:
            logging.info("Received 591, closing port and "
                         "reopening in 60 seconds. No response sent.")

            if httpd:
                httpd.server_close()
            time.sleep(60)
            logging.info("Reopening server after 591 and 60 seconds...")
            run_server()

        elif code == 592:
            logging.info("Received 592, shutting down server completely."
                         " No response sent.")
            if httpd:
                httpd.server_close()
                sys.exit(0)

        elif code == 999:
            self._send_custom_response(999, {"error":
                                                 "Internal Script Error"})
            sys.exit(1)
        else:
            # Handle standard/other codes
            self._send_custom_response(code, {"status":
                                                  f"Response with code {code}"})

    # Implement do_* methods for all required HTTP verbs
    def do_GET(self):
        """Handles GET requests."""
        logging.info("Received GET request.")
        self._handle_request_logic("GET")


    def do_POST(self):
        """Handles POST requests."""
        self._handle_request_logic("POST")

    def do_PUT(self):
        """Handles PUT requests."""
        self._handle_request_logic("PUT")

    def do_DELETE(self):
        """Handles DELETE requests."""
        self._handle_request_logic("DELETE")

    def do_PATCH(self):
        """Handles PATCH requests."""
        self._handle_request_logic("PATCH")


def run_server():
    """Starts the HTTP server and handles 591/592 specific logic."""
    # Set SO_REUSEADDR to avoid "Address already in use" errors
    socketserver.TCPServer.allow_reuse_address = True

    while True:
        try:
            with socketserver.TCPServer(("", PORT), CustomRequestHandler) as httpd:
                #server_instance = httpd
                logging.info("Serving at port %s...", PORT)
                httpd.serve_forever()
        except Exception as e:
            logging.error("Server error: %s", e)
            if '591' in str(e):  # This part is tricky to catch the exact error
                logging.info("Reopening port in 60 seconds...")
                time.sleep(60)
                continue  # Loop to restart the server
            elif '592' in str(e):
                logging.info("Shutting down completely.")
                break  # Exit the loop and stop the script
            else:
                break  # Exit on other errors


if __name__ == "__main__":
    # The current implementation of http.server makes handling
    # 591/592 actions within the main
    # server thread difficult without more complex
    # threading or using frameworks like Flask.
    # This script uses basic http.server for simplicity.
    # The 591/592 actions are noted in the request handler
    # but cannot fully stop/restart the server within the same
    # single-threaded handler process.
    # To truly implement the 591/592 actions, a more
    # advanced framework or multi-threading is needed.
    # The script currently logs the intended action for these codes.
    try:
        logging.info("Starting server on port %s...", PORT)
        httpd = socketserver.TCPServer(("", PORT), CustomRequestHandler)
        logging.info("Server running. Use Ctrl+C to stop.")
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("Server stopped by user (Ctrl+C).")
        httpd.server_close()
    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)
        # In case of any script error during startup or serving, a 999 response should be generated
        # but the server might not be running to send it. This logs the error.
        sys.exit(1)
