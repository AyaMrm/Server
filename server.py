from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>Mon serveur Python fonctionne! 🎉</h1>'

@app.route('/api')
def api():
    return {'message': 'API en marche!', 'status': 'success'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)