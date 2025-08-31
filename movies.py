import db

def movies_count():
    sql = "SELECT COUNT(*) FROM movies"
    return db.query(sql)[0][0]

def add_movie(title, user_id, rating):
    #use of parametres in queries
    sql = """INSERT INTO movies (title, user_id, rating) 
             VALUES (?, ?, ?)"""
    db.execute(sql, [title, user_id, rating])
    movie_id = db.last_insert_id()
    return movie_id

def get_movies(page, page_size):
    #use of parametres in queries
    sql = """SELECT movies.id, movies.title, movies.rating, users.id user_id, users.username
             FROM movies, users
             WHERE movies.user_id = users.id
             ORDER BY movies.id DESC
             LIMIT ? OFFSET ?"""
    limit = page_size
    offset = page_size * (page - 1)
    return db.query(sql, [limit, offset])

def get_movie(movie_id):
    sql = """SELECT movies.id,
                    movies.title,
                    movies.rating,
                    users.id user_id,
                    users.username
             FROM movies, users
             WHERE movies.user_id = users.id AND
                   movies.id = ?"""
    result = db.query(sql, [movie_id])
    return result[0] if result else None

def update_movie(movie_id, title, rating):
    #vulnerable concatenated sql:
    sql = f"UPDATE movies SET title = '{title}', rating = '{rating}' WHERE id = {movie_id}"
    db.execute(sql)
    #use of parametres in queries
    #sql = "UPDATE movies SET title = ?, rating = ? WHERE id = ?"
    #db.execute(sql, [title, rating, movie_id])

def remove_movie(movie_id):
    #use of parametres in queries
    sql = "DELETE FROM movies WHERE id = ?"
    db.execute(sql, [movie_id])