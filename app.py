from flask import Flask, render_template, request, jsonify
from voice_email_logic import process_command, send_email_message, read_latest_email

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/command", methods=["POST"])
def command():
    data = request.get_json(silent=True) or {}
    user_command = data.get("command", "")
    language = data.get("language", "english")
    
    result = process_command(user_command, language)
    return jsonify(result)

@app.route("/read_mail", methods=["POST"])
def read_mail_route():
    data = request.get_json(silent=True) or {}
    language = data.get("language", "english")
    result = read_latest_email(language)
    return jsonify({
        "action": "read",
        "response": result.get("text", ""),
        "details": result,
        "lang_code": result.get("lang_code", "en"),
        "locale": result.get("locale", "en-US")
    })

@app.route("/send_mail", methods=["POST"])
def send_mail_route():
    data = request.get_json(silent=True) or {}
    receiver = data.get("receiver", "")
    subject = data.get("subject", "")
    message = data.get("message", "")
    language = data.get("language", "english")

    result = send_email_message(receiver, subject, message, language)
    return jsonify(result)

if __name__ == "__main__":
    print("Starting AI Voice Assistance System on http://127.0.0.1:5000 ...")
    app.run(debug=True, port=5000)
