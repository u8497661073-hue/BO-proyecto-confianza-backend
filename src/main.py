from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "ProConfianza Backend is running!"

@app.route('/health')
def health():
    return {"status": "ok", "message": "Backend is healthy"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

