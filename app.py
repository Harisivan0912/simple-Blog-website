import os
from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='static')

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'blog'

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Folder where uploaded files will be saved
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif', 'txt', 'pdf'}  # Allowed file types


# Initialize MySQL
mysql = MySQL(app)

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Route to display all blog posts
@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM posts ORDER BY created_at DESC")
    posts = cur.fetchall()  # Fetch all posts
    cur.close()
    return render_template('index.html', posts=posts)

# Route to add a new blog post with file upload
@app.route('/add', methods=['GET', 'POST'])
def add_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        file = request.files.get('file')  # Get the uploaded file
        filename = None  # Initialize filename to None or a default value
        
        # Only process file if it's provided and allowed
        if file and allowed_file(file.filename):  
            filename = secure_filename(file.filename)  # Secure the filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)  # Save the file to static/uploads

        # Insert post with or without an image into the database
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO posts (title, content, file_path) VALUES (%s, %s, %s)", (title, content, filename))  # Use None or empty string if no file
        mysql.connection.commit()  # Commit the changes
        cur.close()

        return redirect(url_for('index'))

    return render_template('add_post.html')



# Route to serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return (app.config['UPLOAD_FOLDER'], filename)


@app.route('/delete/<int:id>', methods=['POST'])
def delete_post(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT file_path FROM posts WHERE id = %s", (id,))
    file_path = cur.fetchone()

    if file_path and file_path[0]:
        try:
            os.remove(file_path[0])  # Remove the file from the server
        except FileNotFoundError:
            pass  # If the file doesn't exist anymore, we just skip it
    
    cur.execute("DELETE FROM posts WHERE id = %s", (id,))
    mysql.connection.commit()  # Commit the changes
    cur.close()

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
