from flask import Flask, request, jsonify, render_template
from models import db, Task, User
import config

def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_BINDS"] = config.SQLALCHEMY_BINDS
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config["SECRET_KEY"] = config.SECRET_KEY

    # Initialize database with app context
    db.init_app(app)

    # Automatically create tables if they don't exist yet
    with app.app_context():
        db.create_all()

    # ---------- Health & Root ----------
    @app.route("/")
    def root():
        # Return the HTML dashboard so the frontend works
        return render_template("index.html")

    @app.route("/healthz")
    def health():
        # Lightweight health check
        return jsonify({"status": "ok"}), 200

    # ---------- CRUD: Tasks ----------
    @app.route("/tasks", methods=["GET"])
    def list_tasks():
        """List all tasks with pagination and search."""
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        search_query = request.args.get('query', '', type=str)

        query = Task.query.filter(Task.deleted_at.is_(None))
        
        if search_query:
            query = query.filter(Task.content.ilike(f"%{search_query}%"))
            
        paginated_tasks = query.order_by(Task.created_at.desc()).paginate(page=page, per_page=limit, error_out=False)
        
        return jsonify({
            "tasks": [t.to_dict() for t in paginated_tasks.items],
            "total": paginated_tasks.total,
            "pages": paginated_tasks.pages,
            "current_page": paginated_tasks.page
        }), 200

    @app.route("/tasks/<int:task_id>", methods=["GET"])
    def get_task(task_id):
        """Get a single task by id."""
        task = Task.query.filter_by(id=task_id, deleted_at=None).first()
        if not task:
            return jsonify({"error": "Task not found"}), 404
        return jsonify({"task": task.to_dict()}), 200

    @app.route("/tasks", methods=["POST"])
    def create_task():
        """Create a new task."""
        payload = request.get_json(silent=True) or {}
        content = payload.get("content", "").strip()

        if not content:
            return jsonify({"error": "Field 'content' is required and cannot be empty."}), 400

        task = Task(
            content=content, 
            done=bool(payload.get("done", False)),
            user_id=payload.get("user_id")
        )
        db.session.add(task)
        db.session.commit()
        return jsonify({"message": "Task added!", "task": task.to_dict()}), 201

    @app.route("/tasks/<int:task_id>", methods=["PUT"])
    def update_task(task_id):
        """Update content/done for an existing task."""
        task = Task.query.filter_by(id=task_id, deleted_at=None).first()
        if not task:
            return jsonify({"error": "Task not found"}), 404

        payload = request.get_json(silent=True) or {}

        # Only update provided fields
        if "content" in payload:
            new_content = str(payload["content"]).strip()
            if not new_content:
                return jsonify({"error": "Field 'content' cannot be empty."}), 400
            task.content = new_content

        if "done" in payload:
            task.done = bool(payload["done"])
            
        if "user_id" in payload:
            task.user_id = payload.get("user_id")

        db.session.commit()
        return jsonify({"message": "Task updated!", "task": task.to_dict()}), 200

    @app.route("/tasks/<int:task_id>", methods=["DELETE"])
    def delete_task(task_id):
        """Soft delete a task by id."""
        from datetime import datetime
        task = Task.query.filter_by(id=task_id, deleted_at=None).first()
        if not task:
            return jsonify({"error": "Task not found"}), 404
        
        task.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Task deleted (soft)"}), 200

    # ---------- Convenience Filters ----------
    @app.route("/tasks/done", methods=["GET"])
    def list_done():
        tasks = Task.query.filter_by(done=True, deleted_at=None).order_by(Task.updated_at.desc()).all()
        return jsonify([t.to_dict() for t in tasks]), 200

    @app.route("/tasks/pending", methods=["GET"])
    def list_pending():
        tasks = Task.query.filter_by(done=False, deleted_at=None).order_by(Task.created_at.desc()).all()
        return jsonify([t.to_dict() for t in tasks]), 200

    # ---------- CRUD: Users ----------
    @app.route("/users", methods=["GET"])
    def list_users():
        users = User.query.filter(User.deleted_at.is_(None)).order_by(User.created_at.desc()).all()
        return jsonify({"users": [u.to_dict() for u in users]}), 200

    @app.route("/users/<int:user_id>", methods=["GET"])
    def get_user(user_id):
        user = User.query.filter_by(id=user_id, deleted_at=None).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        user_dict = user.to_dict()
        user_dict["tasks"] = [t.to_dict() for t in user.tasks if t.deleted_at is None]
        return jsonify({"user": user_dict}), 200

    @app.route("/users", methods=["POST"])
    def create_user():
        payload = request.get_json(silent=True) or {}
        
        name = payload.get("name", "").strip()
        lastname = payload.get("lastname", "").strip()
        
        if not name or not lastname:
            return jsonify({"error": "Name and lastname cannot be empty"}), 400
            
        address = payload.get("address", {})
        
        user = User(
            name=name,
            lastname=lastname,
            city=address.get("city", "").strip(),
            country=address.get("country", "").strip(),
            postal_code=address.get("postal_code", "").strip()
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({"message": "User created!", "user": user.to_dict()}), 201

    @app.route("/users/<int:user_id>", methods=["PUT"])
    def update_user(user_id):
        user = User.query.filter_by(id=user_id, deleted_at=None).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        payload = request.get_json(silent=True) or {}
        
        if "name" in payload:
            name = str(payload["name"]).strip()
            if not name:
                return jsonify({"error": "Name cannot be empty"}), 400
            user.name = name
            
        if "lastname" in payload:
            lastname = str(payload["lastname"]).strip()
            if not lastname:
                return jsonify({"error": "Lastname cannot be empty"}), 400
            user.lastname = lastname
            
        if "address" in payload:
            address = payload["address"]
            if "city" in address:
                user.city = str(address["city"]).strip()
            if "country" in address:
                user.country = str(address["country"]).strip()
            if "postal_code" in address:
                user.postal_code = str(address["postal_code"]).strip()
                
        db.session.commit()
        return jsonify({"message": "User updated!", "user": user.to_dict()}), 200

    @app.route("/users/<int:user_id>", methods=["DELETE"])
    def delete_user(user_id):
        """Soft delete a user by id."""
        from datetime import datetime
        user = User.query.filter_by(id=user_id, deleted_at=None).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        user.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "User deleted (soft)!"}), 200

    return app

# Dev entrypoint
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

