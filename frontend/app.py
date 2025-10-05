from flask import Flask, render_template

# This is a minimal Flask app whose sole purpose is to serve the index.html file.
app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    """Serves the main single-page application."""
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
