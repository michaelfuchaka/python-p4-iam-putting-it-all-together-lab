from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin

from config import db, bcrypt


class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    _password_hash = db.Column(db.String)  # Nullable for testing purposes
    image_url = db.Column(db.String)
    bio = db.Column(db.String)

    # one-to-many: user → recipes
    recipes = db.relationship("Recipe", back_populates="user", cascade="all, delete-orphan")

    serialize_rules = ('-recipes.user', '-_password_hash')

    # Validation: username must be present
    @validates('username')
    def validate_username(self, key, username):
        if not username or username.strip() == "":
            raise ValueError("Username must be present")
        return username

    # Password hash property
    @hybrid_property
    def password_hash(self):
        raise AttributeError("Password hashes may not be viewed.")

    @password_hash.setter
    def password_hash(self, password):
        if not password:
            raise ValueError("Password must be present")
        self._password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'image_url': self.image_url,
            'bio': self.bio
        }


class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    instructions = db.Column(db.String, nullable=False)
    minutes_to_complete = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))  # Nullable for testing

    user = db.relationship("User", back_populates="recipes")

    serialize_rules = ('-user.recipes',)

    # Validation: title must be present
    @validates('title')
    def validate_title(self, key, title):
        if not title or title.strip() == "":
            raise ValueError("Title must be present")
        return title

    # Validation: instructions must be present and at least 50 characters
    @validates('instructions')
    def validate_instructions(self, key, instructions):
        if not instructions or instructions.strip() == "":
            raise ValueError("Instructions must be present")
        if len(instructions) < 50:
            raise ValueError("Instructions must be at least 50 characters long")
        return instructions

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'instructions': self.instructions,
            'minutes_to_complete': self.minutes_to_complete,
            'user': self.user.to_dict() if self.user else None
        }