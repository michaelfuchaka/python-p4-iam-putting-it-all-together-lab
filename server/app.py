from flask import request, session
from flask_restful import Resource, Api
from flask_migrate import Migrate

from config import db, bcrypt, create_app
from models import User, Recipe

app = create_app()

api = Api(app)
migrate = Migrate(app, db)


# ----------- Resources -----------

class Signup(Resource):
    def post(self):
        data = request.get_json()

        username = data.get("username")
        password = data.get("password")
        image_url = data.get("image_url", "")
        bio = data.get("bio", "")

        if not username or not password:
            return {"error": "Username and password required"}, 422

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            return {"error": "Username already taken"}, 422

        try:
            new_user = User(
                username=username,
                image_url=image_url,
                bio=bio
            )
            new_user.password_hash = password  # This uses the setter to hash

            db.session.add(new_user)
            db.session.commit()

            session["user_id"] = new_user.id

            return new_user.to_dict(), 201
        
        except ValueError as e:
            db.session.rollback()
            return {"error": str(e)}, 422


class CheckSession(Resource):
    def get(self):
        user_id = session.get("user_id")
        if not user_id:
            return {"error": "Unauthorized"}, 401

        user = User.query.get(user_id)
        if not user:
            return {"error": "Unauthorized"}, 401

        return user.to_dict(), 200


class Login(Resource):
    def post(self):
        data = request.get_json()

        username = data.get("username")
        password = data.get("password")

        user = User.query.filter_by(username=username).first()
        if not user or not user.authenticate(password):
            return {"error": "Invalid username or password"}, 401

        session["user_id"] = user.id
        return user.to_dict(), 200


class Logout(Resource):
    def delete(self):
        user_id = session.get("user_id")
        
        # Check if user is logged in
        if user_id is None:
            return {"error": "Unauthorized"}, 401
        
        # Remove user from session
        session.pop("user_id", None)
        return {}, 204


class RecipeIndex(Resource):
    def get(self):
        user_id = session.get("user_id")
        if not user_id:
            return {"error": "Unauthorized"}, 401

        recipes = Recipe.query.all()
        return [recipe.to_dict() for recipe in recipes], 200

    def post(self):
        user_id = session.get("user_id")
        if not user_id:
            return {"error": "Unauthorized"}, 401

        data = request.get_json()

        try:
            new_recipe = Recipe(
                title=data.get("title"),
                instructions=data.get("instructions"),
                minutes_to_complete=data.get("minutes_to_complete"),
                user_id=user_id,
            )
            
            db.session.add(new_recipe)
            db.session.commit()

            return new_recipe.to_dict(), 201
        
        except ValueError as e:
            db.session.rollback()
            return {"error": str(e)}, 422


# ----------- Register Resources -----------
api.add_resource(Signup, "/signup")
api.add_resource(CheckSession, "/check_session")
api.add_resource(Login, "/login")
api.add_resource(Logout, "/logout")
api.add_resource(RecipeIndex, "/recipes")


if __name__ == "__main__":
    app.run(port=5555, debug=True)