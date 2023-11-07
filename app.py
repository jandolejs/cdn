from flask import Flask, request, send_from_directory, render_template, make_response, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from PIL import Image
import magic
import mimetypes

app = Flask('cdn')

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://cdn:cdn@10.0.0.15/cdn'

db = SQLAlchemy(app)

def get_mime_type(file_path):
    mime, encoding = mimetypes.guess_type(file_path)
    return mime if mime else 'application/octet-stream'

class ImageEntry(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(255), unique=True, nullable=False)
    image_data = db.Column(db.LargeBinary)
    mime_type = db.Column(db.String(255), nullable=False)

@app.route('/delete_image/<int:image_id>', methods=['POST'])
def delete_image(image_id):
    entry = ImageEntry.query.get(image_id)
    if entry:
        db.session.delete(entry)
        db.session.commit()

    return redirect(url_for('manage_images'))


@app.route('/<path:image_path>')
def get_image_by_path(image_path):
    entry = ImageEntry.query.filter_by(path=image_path).first()
    if entry:
        response = make_response(entry.image_data)
        response.headers['Content-Type'] = entry.mime_type
        return response
    else:
        abort(404)


@app.route('/', methods=['GET', 'POST'])
def manage_images():
    if request.method == 'POST':
        if 'image' in request.files:
            image = request.files['image']
            path = secure_filename(image.filename)
            image_data = image.read()
            mime_type = get_mime_type(image.filename)
            new_entry = ImageEntry(path=path, image_data=image_data, mime_type=mime_type)
            db.session.add(new_entry)
            db.session.commit()
    entries = ImageEntry.query.all()
    return render_template('manage.html', entries=entries)


@app.errorhandler(404)
def not_found_error(error):
    return "404 - File not Found", 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
