from flask import Flask, request, jsonify, send_file, render_template
import json
import os
import hashlib
import uuid
from datetime import datetime

app = Flask(__name__)

DATA_FILE = "data.json"
DATA_DIR = "data"
version = "1.0.1"


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    else:
        return {}


def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def generate_access_key():
    return str(uuid.uuid4())


def get_login_by_access_key(access_key):
    with open("data.json", "r") as file:
        users_data = json.load(file)

    for login, user_data in users_data.items():
        if user_data["access_key"] == access_key:
            return login

    return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/status", methods=["POST"])
def status():
    user_data = request.json
    access_key = user_data.get("access_key")
    login = get_login_by_access_key(access_key)
    if not access_key:
        return jsonify({"error": "access key and slot are required"}), 400
    if login:
        return jsonify({"login": f"{login}",
                        "version": version}), 200
    else:
        return jsonify({"login": "auth error",
                        "version": version}), 401


@app.route("/auth", methods=["POST"])
def auth():
    data = load_data()
    user_data = request.json

    login = user_data.get("login")
    password = user_data.get("password")

    if not login or not password:
        return jsonify({"error": "Login and password are required"}), 400

    hashed_password = hash_password(password)

    if login in data:
        if data[login]["password"] == hashed_password:
            return jsonify({"access_key": data[login]["access_key"]}), 200
        else:
            return jsonify({"error": "Incorrect password"}), 401
    else:
        access_key = generate_access_key()
        data[login] = {
            "password": hashed_password,
            "access_key": access_key
        }

        user_dir = os.path.join(DATA_DIR, login)
        os.makedirs(user_dir, exist_ok=True)

        save_data(data)
        return jsonify({"access_key": access_key}), 201


@app.route("/info", methods=["POST"])
def info():
    user_data = request.json
    access_key = user_data.get("access_key")

    if not access_key:
        return jsonify({"error": "access key is required"}), 400

    login = get_login_by_access_key(access_key)
    json_file_path = os.path.join(DATA_DIR, login, "saves.json")

    if not os.path.exists(json_file_path):
        return jsonify({"error": "JSON file not found"}), 404

    with open(json_file_path, "r") as json_file:
        json_data = json.load(json_file)

    return jsonify(json_data), 200


@app.route("/save/download/<slot>", methods=["POST"])
def download_save(slot):
    user_data = request.json
    access_key = user_data.get("access_key")
    if not access_key or not slot:
        return jsonify({"error": "access key and slot are required"}), 400
    login = get_login_by_access_key(access_key)
    if slot == 1:
        slot = "1.zip"
    elif slot == 2:
        slot = "2.zip"
    elif slot == 2:
        slot = "3.zip"
    else:
        pass
    try:
        return send_file(f"data/{login}/{slot}.zip", as_attachment=True)
    except FileNotFoundError:
        return "File Not Found Error"


@app.route("/save/upload/<slot>", methods=["POST"])
def upload_save(slot):
    user_data = request.form
    access_key = user_data.get("access_key")
    if "file" not in request.files or not access_key or not slot:
        return jsonify({"error": "access key, slot, and file are required"}), 400

    file = request.files["file"]
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    login = get_login_by_access_key(access_key)

    if slot == "1":
        slot = "1.zip"
    elif slot == "2":
        slot = "2.zip"
    elif slot == "3":
        slot = "3.zip"
    else:
        return jsonify({"error": "Invalid slot"}), 400

    try:
        save_path = f"data/{login}/{slot}"
        file.save(save_path)

        user_dir = os.path.join(DATA_DIR, login)
        user_save_file = os.path.join(user_dir, "saves.json")

        if os.path.exists(user_save_file):
            with open(user_save_file, "r") as f:
                user_saves = json.load(f)
        else:
            user_saves = {}

        user_saves[f"save {slot[0]}"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(user_save_file, "w") as f:
            json.dump(user_saves, f)

        return jsonify({"message": "File uploaded successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/save/delite/<slot>", methods=["POST"])
def delite(slot):
    user_data = request.form
    access_key = user_data.get("access_key")

    login = get_login_by_access_key(access_key)

    if slot == "1":
        slot = "1.zip"
    elif slot == "2":
        slot = "2.zip"
    elif slot == "3":
        slot = "3.zip"
    else:
        return jsonify({"error": "Invalid slot"}), 400

    try:
        os.remove(f"data/{login}/{slot}")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    save_patch = json.loads(f"data/{login}/saves.json")
    with open(save_patch, "r") as file:
        data = json.load(file)

    if slot in [1, 2, 3]:
        key_to_remove = f"save {slot}"

        if key_to_remove in data:
            del data[key_to_remove]

            with open(save_patch, "w") as file:
                json.dump(data, file, indent=4)
    else:
        return "No correct slot"


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    app.run(host="0.0.0.0", port=5000)
