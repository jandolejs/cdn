from flask import Flask, request, send_from_directory, render_template, make_response, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask('cdn')

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://cdn:cdn@10.0.0.15/cdn'

db = SQLAlchemy(app)

class ImageEntry(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(255), unique=True, nullable=False)
    image_data = db.Column(db.LargeBinary)

@app.route('/delete_image/<int:image_id>', methods=['POST'])
def delete_image(image_id):
    entry = ImageEntry.query.get(image_id)
    if entry:
        db.session.delete(entry)
        db.session.commit()

    return redirect(url_for('manage_images'))

@app.route('/get_image/<path:image_path>')
def get_image_by_path(image_path):
    entry = ImageEntry.query.filter_by(path=image_path).first()
    if entry:
        response = make_response(entry.image_data)
        response.headers['Content-Type'] = 'image/png'  # Adjust content type as needed
        return response
    else:
        abort(404)

@app.route('/manage', methods=['GET', 'POST'])
def manage_images():
    if request.method == 'POST':
        if 'image' in request.files:
            image = request.files['image']
            path = secure_filename(image.filename)
            image_data = image.read()  # Read the image data as binary
            new_entry = ImageEntry(path=path, image_data=image_data)
            db.session.add(new_entry)
            db.session.commit()
    entries = ImageEntry.query.all()
    return render_template('manage.html', entries=entries)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0')
