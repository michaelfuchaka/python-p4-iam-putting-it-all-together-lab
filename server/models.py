from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin

from config import db, bcrypt


class User(db.Model, SerializerMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    _password_hash = db.Column(db.String, nullable=False)
    image_url = db.Column(db.String)
    bio = db.Column(db.String)

    # relationships
    recipes = db.relationship("Recipe", back_populates="user", cascade="all, delete-orphan")

    serialize_rules = ("-recipes.user",)

    # password hashing
    @hybrid_property
    def password_hash(self):
        return self._password_hash

    @password_hash.setter
    def password_hash(self, password):
        self._password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password)

    # validations
    @validates("username")
    def validate_username(self, key, username):
        if not username or username.strip() == "":
            raise ValueError("Username must not be empty")
        return username


class Recipe(db.Model, SerializerMixin):
    __tablename__ = "recipes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    instructions = db.Column(db.String, nullable=False)
    minutes_to_complete = db.Column(db.Integer, nullable=False)

    # foreign key
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # relationship
    user = db.relationship("User", back_populates="recipes")

    serialize_rules = ("-user.recipes",)

    # validations
    @validates("title")
    def validate_title(self, key, title):
        if not title or title.strip() == "":
            raise ValueError("Recipe must have a title")
        return title

    @validates("instructions")
    def validate_instructions(self, key, instructions):
        if not instructions or len(instructions) < 50:
            raise ValueError("Instructions must be at least 50 characters long")
        return instructions

    @validates("minutes_to_complete")
    def validate_minutes(self, key, minutes):
        if minutes is None or minutes <= 0:
            raise ValueError("Minutes to complete must be positive")
        return minutes
