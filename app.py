from flask import Flask, render_template
from flask import request, jsonify


# Create Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return "This is the About page"

@app.route("/hello/<name>")
def hello(name):
    return f"Hello {name}!"

@app.route("/json")
def json_response():
    return {"status": "success", "message": "This is JSON!"}


tasks = {}  # store tasks in memory as a dictionary
task_id_counter = 0

# GET - retrieve all tasks
@app.route("/tasks", methods=["GET"])
def get_tasks():
    return jsonify({"tasks": list(tasks.values())})

# GET - retrieve a specific task
@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    if task_id not in tasks:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"task": tasks[task_id]})

# POST - add a new task
@app.route("/tasks", methods=["POST"])
def add_task():
    global task_id_counter
    data = request.json or {}
    content = data.get("content", "").strip()
    
    if not content:
        return jsonify({"error": "Task content cannot be empty"}), 400
        
    task = {"id": task_id_counter, "content": content, "done": False}
    tasks[task_id_counter] = task
    task_id_counter += 1
    return jsonify({"message": "Task added!", "task": task}), 201

# PUT - update a task by ID
@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    if task_id not in tasks:
        return jsonify({"error": "Task not found"}), 404
        
    data = request.json or {}
    
    if "content" in data:
        content = data["content"].strip()
        if not content:
            return jsonify({"error": "Task content cannot be empty"}), 400
        tasks[task_id]["content"] = content
    
    if "done" in data:
        tasks[task_id]["done"] = bool(data["done"])
        
    return jsonify({"message": "Task updated!", "task": tasks[task_id]})

# DELETE - delete a task by ID
@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    if task_id not in tasks:
        return jsonify({"error": "Task not found"}), 404
    removed = tasks.pop(task_id)
    return jsonify({"message": "Task deleted!", "task": removed})

users = {}  # store users in memory
user_id_counter = 0

# GET - retrieve all users
@app.route("/users", methods=["GET"])
def get_users():
    return jsonify({"users": list(users.values())})

# GET - retrieve a specific user
@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": users[user_id]})

# POST - create a new user
@app.route("/users", methods=["POST"])
def create_user():
    global user_id_counter
    data = request.json or {}
    
    name = data.get("name", "").strip()
    lastname = data.get("lastname", "").strip()
    
    if not name or not lastname:
        return jsonify({"error": "Name and lastname cannot be empty"}), 400
        
    address = data.get("address", {})
    city = address.get("city", "").strip()
    country = address.get("country", "").strip()
    postal_code = address.get("postal_code", "").strip()
    
    user = {
        "id": user_id_counter,
        "name": name,
        "lastname": lastname,
        "address": {
            "city": city,
            "country": country,
            "postal_code": postal_code
        }
    }
    users[user_id_counter] = user
    user_id_counter += 1
    
    return jsonify({"message": "User created!", "user": user}), 201

# PUT - update a user by ID
@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404
        
    data = request.json or {}
    user = users[user_id]
    
    if "name" in data:
        name = data["name"].strip()
        if not name:
            return jsonify({"error": "Name cannot be empty"}), 400
        user["name"] = name
        
    if "lastname" in data:
        lastname = data["lastname"].strip()
        if not lastname:
            return jsonify({"error": "Lastname cannot be empty"}), 400
        user["lastname"] = lastname
        
    if "address" in data:
        address = data["address"]
        if "city" in address:
            user["address"]["city"] = address["city"].strip()
        if "country" in address:
            user["address"]["country"] = address["country"].strip()
        if "postal_code" in address:
            user["address"]["postal_code"] = address["postal_code"].strip()
            
    return jsonify({"message": "User updated!", "user": user})

# DELETE - delete a user by ID
@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404
        
    removed = users.pop(user_id)
    return jsonify({"message": "User deleted!", "user": removed})

if __name__ == "__main__":
    app.run(debug=True)
