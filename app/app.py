
from os import environ
from flask import Flask, request, send_from_directory, render_template, make_response, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from PIL import Image
import magic
import hashlib
import time
import mimetypes
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import quote

app = Flask('cdn')
#app.debug = True
auth = HTTPBasicAuth()

users = {
    environ.get('HTTP_USER'): generate_password_hash(environ.get('HTTP_PASS'))
}

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{environ.get('DATABASE_USER')}:{environ.get('DATABASE_PASS')}@{environ.get('DATABASE_URL')}/{environ.get('DATABASE_NAME')}"

db = SQLAlchemy(app)

@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username

def get_mime_type(file_name):
    mime, encoding = mimetypes.guess_type(file_name)
    return mime if mime else 'application/octet-stream'

class ImageEntry(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    hash = db.Column(db.String(255), unique=True, nullable=False)
    image_data = db.Column(db.LargeBinary)
    mime_type = db.Column(db.String(255), nullable=False)

@app.route('/delete_image/<int:image_id>', methods=['POST'])
@auth.login_required
def delete_image(image_id):
    entry = ImageEntry.query.get(image_id)
    if entry:
        db.session.delete(entry)
        db.session.commit()

    return redirect(url_for('manage_images'))

@app.route('/<hash>')
def get_image_by_hash(hash):
    entry = ImageEntry.query.filter_by(hash=hash).first()
    if entry:
        response = make_response(entry.image_data)
        response.headers['Content-Type'] = entry.mime_type
        return response
    else:
        abort(404)


@app.route('/', methods=['GET', 'POST'])
@auth.login_required
def manage_images():
    if request.method == 'POST':
        for image in request.files.getlist('images'):
            name = image.filename
            mime_type = get_mime_type(name)
            image_data = image.read()
            hash = hashlib.md5(image_data).hexdigest()
            new_entry = ImageEntry(name=name, hash=hash, image_data=image_data, mime_type=mime_type)
            db.session.add(new_entry)
            db.session.commit()
        return redirect(url_for('manage_images'))
    entries = ImageEntry.query.all()
    return render_template('manage.html', entries=entries)


@app.errorhandler(404)
def not_found_error(error):
    return "404 - File not Found", 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0')
