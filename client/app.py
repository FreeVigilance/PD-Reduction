"""
Flask клиент для взаимодействия с сервером.
"""

from flask import Flask, render_template, request, redirect, jsonify
import requests

app = Flask(__name__)
API_URL = "http://127.0.0.1:8000"


@app.route("/")
def index():
    """
    Главная страница с выбором профиля.
    """
    try:
        response_now = requests.get(f"{API_URL}/profiles")
        response_now.raise_for_status()
        profiles_now = response_now.json()
    except Exception as error:
        print(f"[ERROR] Ошибка получения профилей: {error}")
        profiles_now = []

    return render_template("index.html", profiles=profiles_now)


@app.route("/upload", methods=["POST"])
def upload():
    """
    Загрузка документов на FastAPI-сервер.
    """
    files_now = request.files.getlist("files")
    profile_id_now = request.form.get("profile_id")

    if not files_now or not profile_id_now:
        return jsonify({"error": "Некорректные данные формы"}), 400

    try:
        files_data = [
            ("files", (file_now.filename, file_now.stream, file_now.mimetype))
            for file_now in files_now
        ]
        response_now = requests.post(
            f"{API_URL}/upload",
            data={"profile_id": profile_id_now},
            files=files_data
        )
        response_now.raise_for_status()
        return jsonify(response_now.json())
    except Exception as error:
        print(f"[ERROR] Ошибка загрузки: {error}")
        return jsonify({"error": "Ошибка отправки на сервер"}), 500


@app.route("/status/<task_id>")
def status(task_id):
    """
    Получение статуса задачи.
    """
    try:
        response_now = requests.get(f"{API_URL}/status/{task_id}")
        response_now.raise_for_status()
        return jsonify(response_now.json())
    except Exception as error:
        print(f"[ERROR] Статус не получен: {error}")
        return jsonify({"error": "Ошибка получения статуса"}), 500


@app.route("/results/<task_id>")
def results(task_id):
    """
    Получение результатов задачи.
    """
    try:
        response_now = requests.get(f"{API_URL}/results/{task_id}")
        response_now.raise_for_status()
        return jsonify(response_now.json())
    except Exception as error:
        print(f"[ERROR] Ошибка получения результатов: {error}")
        return jsonify({"error": "Ошибка получения результатов"}), 500


@app.route("/download/<task_id>")
def download(task_id):
    """
    Перенаправление на скачивание архива.
    """
    return redirect(f"{API_URL}/download/{task_id}", code=302)


if __name__ == "__main__":
    app.run(debug=True)