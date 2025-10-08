#!/usr/bin/env python3
"""Ultra-simple test server"""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    print("Starting test server on port 8000...")
    from waitress import serve
    serve(app, host='127.0.0.1', port=8000, _quiet=False)
