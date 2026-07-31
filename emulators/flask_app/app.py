"""Aleksandr Polskiy practice flask app that returns error codes depending on url
default page displays error supported codes table"""

from flask import Flask, abort, render_template_string
from werkzeug.exceptions import HTTPException
app = Flask(__name__)

SUPPORTED_ERROR_CODES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Request Entity Too Large",
    414: "Request-URI Too Long",
    415: "Unsupported Media Type",
    416: "Requested Range Not Satisfiable",
    417: "Expectation Failed",
    419: "Insufficient Space on Resource",
    500: "Internal Server Error",
    501: "Not Implemented",
    503: "Service Unavailable",
    600: "Custom Error"
}
app = Flask(__name__)
@app.route('/')

def index():
    """Displays default page with error codes table"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: sans-serif; margin: 20px; }
            /* Force table to fit screen width and prevent horizontal scrolling */
            .table-container {
                width: 100%;
                max-width: 800px; /* Optional: keeps table from getting too wide on desktop */
                margin: auto;
            }
            table {
                width: 100%;
                table-layout: fixed; /* Ensures columns respect the width */
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
                word-wrap: break-word; /* Prevents long text from pushing table width */
                overflow: hidden;
            }
            tr:nth-child(even) { background-color: #f9f9f9; }
            th { background-color: #4CAF50; color: white; }
        </style>
    </head>
    <body>
        <h1 align="center">HTTP Error Code Simulator</h1>
        <p align="center">Click a link below to see the error page and its status code or go to /error/code url:</p>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th style="width: 20%;">Code</th>
                        <th style="width: 50%;">Description</th>
                        <th style="width: 30%";>Link</th>
                    </tr>
                 </thead>   
                <tbody>
                    {% for code, desc in codes.items() %}
                    <tr>
                        <td>{{ code }}</td>
                        <td>{{ desc }}</td>
                        <td><a href="/error/{{ code }}">Test {{ code }} code</a></td>
                    </tr>
                    {% endfor %}
                 </tbody>   
            </table>
        </div>
    </body>
        """

    return render_template_string(html_template, codes=SUPPORTED_ERROR_CODES)

@app.route('/error/<int:code>')
def return_status_code(code):
    """
    Returns the specified HTTP error code.
    If the code is not supported or invalid, it defaults to a 404.
    """
    if code in SUPPORTED_ERROR_CODES:
        # Use abort() to raise the HTTPException which can be handled by an error handler,
        # or simply return the message and status code as a tuple.
        # For simplicity and direct status code return:

        description = SUPPORTED_ERROR_CODES[code]
        return f"<h1>{code} - {description}</h1>", code

    # If the return code is not on the list
    abort(404)


@app.errorhandler(Exception)
def handle_exception(error):
    """
    This function safely handles both manual abort() calls
    and unexpected Python errors.
    """
    # 1. If it's a Flask HTTP error (like from abort(404)), use its own data
    if isinstance(error, HTTPException):
        # Access .code and .name safely from the HTTPException object
        return f"<h1>{error.code}: {error.name}</h1><p>{error.description}</p>", error.code

    # 2. If it's a real code error (e.g., ZeroDivisionError), return a 500
    # This prevents the handler from crashing and hiding the real issue
    return ("<h1>500: Internal Server Error</h1><p>The "
            "server encountered an unexpected condition.</p>"), 500

if __name__ == "__main__":
    app.run(debug=True)
