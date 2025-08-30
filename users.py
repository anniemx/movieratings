#import security libraries for encyption/password hash
from werkzeug.security import generate_password_hash, check_password_hash
import db

def get_user(user_id):
    sql = "SELECT id, username FROM users WHERE id = ?" #use of parametres in queries
    result = db.query(sql, [user_id])
    return result[0] if result else None

def get_movies(user_id):
    sql = "SELECT id, title FROM movies WHERE user_id = ? ORDER BY id DESC" #use of parametres in queries
    return db.query(sql, [user_id])

def create_user(username, password):
    password_hash = generate_password_hash(password) #this function encrypts the password with a hash function
    sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)" #use of parametres in queries
    db.execute(sql, [username, password_hash])

def check_login(username, password):
    sql = "SELECT id, password_hash FROM users WHERE username = ?" #use of parametres in queries
    result = db.query(sql, [username])
    if not result:
        return None

    user_id = result[0]["id"]
    password_hash = result[0]["password_hash"] #use of hashed passwords instead of user input string
    if check_password_hash(password_hash, password):
        return user_id
    return None
