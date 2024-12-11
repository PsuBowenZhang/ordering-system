from flask_login import UserMixin

from db import con_my_sql


class User(UserMixin):
    def __init__(self, user_id=None, username=None, role=None, email=None, password=None, is_active=True):
        self.userid = user_id
        self.username = username
        self.role = role
        self.email = email
        self.password = password
        self.is_active_flag = is_active

    @property
    def is_active(self):
        """Override is_active property from UserMixin if needed."""
        return self.is_active_flag

    @staticmethod
    def get_user_by_id(user_id):
        """Retrieve a user by their ID."""
        query = "SELECT * FROM users WHERE UserID = %s"
        cursor = con_my_sql(query, user_id)
        user_data = cursor.fetchone()
        cursor.close()
        if user_data:
            return User(
                user_id=user_data['UserID'],
                username=user_data['UserName'],
                role=user_data['Role'],
                email=user_data['Email'],
                password=user_data['Password'],
                is_active=user_data['IsActive']
            )
        return None

    def get_id(self):
        """Return the unique identifier for Flask-Login."""
        return str(self.userid)

    @staticmethod
    def create_user(username, role, email, password, is_active=True):
        """Create a new user."""
        query = """
        INSERT INTO users (UserName, Role, Email, Password, IsActive)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor = con_my_sql(query, (username, role, email, password, is_active))
        user_id = cursor.lastrowid
        cursor.close()
        return user_id

    @staticmethod
    def update_user(user_id, username=None, role=None, email=None, password=None, is_active=None):
        """Update a user's details."""
        fields = []
        values = []

        if username is not None:
            fields.append("UserName = %s")
            values.append(username)
        if role is not None:
            fields.append("Role = %s")
            values.append(role)
        if email is not None:
            fields.append("Email = %s")
            values.append(email)
        if password is not None:
            fields.append("Password = %s")
            values.append(password)
        if is_active is not None:
            fields.append("IsActive = %s")
            values.append(is_active)

        values.append(user_id)
        query = f"UPDATE users SET {', '.join(fields)} WHERE UserID = %s"

        cursor = con_my_sql(query, tuple(values))
        cursor.close()
        return cursor.rowcount

    @staticmethod
    def delete_user(user_id):
        """Delete a user by their ID."""
        query = "DELETE FROM users WHERE UserID = %s"
        cursor = con_my_sql(query, user_id)
        cursor.close()
        return cursor.rowcount

