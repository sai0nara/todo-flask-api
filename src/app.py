from flask import Flask, jsonify, request

from repository import (
    close_db,
    create_todo,
    delete_todo,
    get_all_todos,
    get_todo_by_id,
    init_db,
    update_todo,
)

app = Flask(__name__)
app.teardown_appcontext(close_db)

with app.app_context():
    init_db()


# --- Routes ---
@app.get("/todos")
def get_todos():
    return jsonify(get_all_todos()), 200


@app.get("/todos/<int:todo_id>")
def get_todo(todo_id):
    todo = get_todo_by_id(todo_id)
    if todo is None:
        return jsonify({"error": "Todo not found"}), 404
    return jsonify(todo), 200


@app.post("/todos")
def create_todo_route():
    data = request.get_json()
    if not data or not data.get("title") or not data["title"].strip():
        return jsonify({"error": "Title is required"}), 400
    title = data["title"].strip()
    if len(title) > 200:
        return jsonify({"error": "Title must be under 200 characters"}), 400
    todo = create_todo(title, data.get("description", ""))
    return jsonify(todo), 201


def _handle_update(todo_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    if "title" in data:
        title = data["title"]
        if not title or not title.strip():
            return jsonify({"error": "Title is required"}), 400
        title = title.strip()
        if len(title) > 200:
            return jsonify({"error": "Title must be under 200 characters"}), 400
        data = {**data, "title": title}
    todo = update_todo(todo_id, data)
    if todo is None:
        return jsonify({"error": "Todo not found"}), 404
    return jsonify(todo), 200


@app.put("/todos/<int:todo_id>")
def update_todo_route(todo_id):
    return _handle_update(todo_id)


@app.patch("/todos/<int:todo_id>")
def patch_todo(todo_id):
    return _handle_update(todo_id)


@app.delete("/todos/<int:todo_id>")
def delete_todo_route(todo_id):
    if not delete_todo(todo_id):
        return jsonify({"error": "Todo not found"}), 404
    return jsonify({"message": "Todo deleted"}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
