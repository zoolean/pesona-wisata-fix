
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from flask import Flask, render_template, request, redirect, flash, jsonify, make_response, session
from datetime import datetime, timedelta
from bson import ObjectId
import hashlib
import os
import jwt
from flask_session import Session
from babel.numbers import format_currency



uri = "mongodb://zulian:zulian@ac-tgzteyv-shard-00-00.ttjbb4o.mongodb.net:27017,ac-tgzteyv-shard-00-01.ttjbb4o.mongodb.net:27017,ac-tgzteyv-shard-00-02.ttjbb4o.mongodb.net:27017/?ssl=true&replicaSet=atlas-j68xbk-shard-0&authSource=admin&retryWrites=true&w=majority"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db = client['pesona-wisata']

SECRET_KEY = 'secret1141'
TOKEN_KEY = 'mytoken'

# Create flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'f3cfe9ed8fae309f02079dbf'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

def check_not_admin():
    if session == None or session['category'] != 'admin' :
        return True
    else:
        return False

@app.route('/', methods=['GET'])
def index():
    print(session)
    wisatas = db.wisata.find()

    return render_template('index.html', wisatas=wisatas)
    # return session.get("name")
    # return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('name'):
        return redirect('/')

    if request.method == 'GET':
        return render_template('register.html')

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        password_hash = hashlib.sha256(password. encode('utf-8')).hexdigest()

        doc = {
            "name": name,
            "email": email,
            "category": 'visitor',
            "password": password_hash
        }
        db.users.insert_one(doc)

        flash('Register successful')
        return redirect('/register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('name'):
        return redirect('/')

    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        email = request.form["email"]
        password = request.form["password"]
        pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        result = db.users.find_one(
            {
                "email": email,
                "password": pw_hash,
            }
        )

        print(result)

        if result:
            session['user_id'] = result['_id']
            session["name"] = result['name']
            session["email"] = result['email']
            session["category"] = result['category']

            flash('Login successful')

            if result['category'] == 'admin':
                return redirect('/admin-wisata')
            else:
                return redirect('/')

        else:
            flash("Username dan password tidak sesuai")
            return redirect('/login')
        
@app.route('/logout', methods=['GET'])
def logout():
    session["name"] = None
    session["email"] = None
    session["category"] = None
    flash('Logout successful')

    return redirect("/")

@app.route('/admin-wisata', methods=['POST', 'GET'])
def wisata():
    if check_not_admin():
        return redirect('/')
    
    wisatas = db.wisata.find()
    return render_template('admin-wisata.html', wisatas=wisatas)

@app.route('/admin-add-wisata', methods=['POST', 'GET'])
def add_wisata():
    if check_not_admin():
        return redirect('/')
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        location = request.form.get('location')
        category = request.form.get('category')

        # total_tickets = int(request.form.get('total_tickets'))

        today = datetime.now()
        mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
        file = request.files['image_wisata']
        extension = file.filename.split('.')[-1]
        filename = f'static/images/wisata-{name}-{mytime}.{extension}'
        file.save(filename)

        price = float(request.form.get('price'))
        # formatted_price = format_currency(price, 'IDR', locale='id_ID')
        db.wisata.insert_one({
            'name': name,
            'categoy': category,
            'description': description,
            'location': location,
            'price': price,
            'image_wisata': filename,
        })
        return redirect('/admin-wisata')

    if request.method == 'GET':
        return render_template('admin-add-wisata.html')

@app.route('/admin-edit-wisata/<id>', methods=['POST', 'GET'])
def edit_wisata(id):
     if check_not_admin():
         return redirect('/')
     
     wisata = db.wisata.find_one({'_id': ObjectId(id)})
     if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        location = request.form.get('location')
        category = request.form.get('category')

        # total_tickets = int(request.form.get('total_tickets'))

        today = datetime.now()
        mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
        file = request.files['image_wisata']

        if file:
            # Hapus file lama jika file dirubah
            if 'image_wisata' in wisata:
                existing_file_path = wisata['image_wisata']
                if os.path.exists(existing_file_path):
                    os.remove(existing_file_path)
            extension = file.filename.split('.')[-1]
            filename = f'static/images/wisata-{name}-{mytime}.{extension}'
            file.save(filename)
        else:
            # Menjaga file jika tidak ada file baru
            filename = wisata.get('image_wisata')

        price = float(request.form.get('price'))
        # formatted_price = format_currency(price, 'IDR', locale='id_ID')
        db.wisata.update_one(
            {'_id': ObjectId(id)},
            {
                '$set': {
                    'name': name,
                    'categoy': category,
                    'description': description,
                    'location': location,
                    'price': price,
                    'image_wisata': filename,
                }
            }
        )
        return redirect('/admin-wisata')
     
     if request.method == 'GET':
        return render_template('admin-edit-wisata.html', wisata=wisata)

@app.route('/admin-delete-wisata/<id>', methods=['GET'])
def delete_wisata(id):
    if check_not_admin():
        return redirect('/')
    
    existing_wisata = db.wisata.find_one({'_id': ObjectId(id)})
    existing_file_path = existing_wisata['image_wisata']
    os.remove(existing_file_path)
    result = db.wisata.delete_one({'_id': ObjectId(id)})    
    if result.deleted_count > 0:
        # berhasil hapus
        return redirect('/admin-wisata')        
    else:
        # GAGAL HAPUS
        return redirect('/admin-wisata') 

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')


@app.route('/wisata-domestic', methods=['GET'])
def domestic():
    wisatas = db.wisata.find({
        'categoy' : 'domestic'
    })
    return render_template('domestic.html', wisatas=wisatas)

@app.route('/wisata-international', methods=['GET'])
def international():
    wisatas = db.wisata.find({
        'categoy' : 'international'
    })
    return render_template('international.html', wisatas=wisatas)

@app.route('/wisata/<id>', methods=['GET'])
def detail_wisata(id): 
     wisata = db.wisata.find_one({'_id': ObjectId(id)})
     return render_template('detail-wisata.html', wisata=wisata)

@app.route('/booking-wisata', methods=['POST'])
def booking_wisata():
    wisata_id = request.form.get('wisata_id')
    user_id = request.form.get('user_id')
    tiket = request.form.get('tiket')

    wisata = db.wisata.find_one({'_id': ObjectId(wisata_id)})

    total_harga = int(tiket) * wisata['price']

    db.booking.insert_one({
        'wisata_id' : wisata_id,
        'wisata_name' : wisata['name'],
        'user_id' : user_id,
        'tiket' : int(tiket),
        'total_harga' : total_harga,
        'bukti' : '',
        'status' : 'pending' # pending, acc, cancel
    })
    return redirect('/')

@app.route('/pesanan', methods=['GET'])
def pesanan():
    bookings = db.booking.find({
        'user_id' : str(session['user_id'])
    })

    return render_template('pesanan.html', bookings=bookings)

@app.route('/admin-pesanan', methods=['GET'])
def admin_pesanan():
    if check_not_admin():
        return redirect('/')
    bookings = db.booking.find()

    return render_template('admin-pesanan.html', bookings=bookings)

@app.route('/admin-pesanan/update-status/<booking_id>', methods=['POST'])
def admin_update_status(booking_id):
    if check_not_admin():
        return redirect('/')
    status = request.form.get('status')
    db.booking.update_one(
        {'_id' : ObjectId(booking_id)},
        {
            '$set': {
                'status' : status
            }
        }
    )

    return redirect('/admin-pesanan')

@app.route('/pesanan/upload-bukti', methods=['POST'])
def upload_bukti():
    booking_id = request.form.get('booking_id')
    booking = db.booking.find_one({'_id' : ObjectId(booking_id)})
    file = request.files['bukti']

    if file:
        # Hapus file lama jika file dirubah
        if 'bukti' in booking:
            existing_file_path = booking['bukti']
            if os.path.exists(existing_file_path):
                os.remove(existing_file_path)
        extension = file.filename.split('.')[-1]
        filename = f'static/images/bukti-{booking_id}.{extension}'
        file.save(filename)
    else:
        # Menjaga file jika tidak ada file baru
        filename = booking.get('bukti')

    db.booking.update_one(
        {'_id' : ObjectId(booking_id)},
        {
            '$set': {
                'bukti' : filename
            }
        }
    )

    return redirect('/pesanan')

@app.route('/cetak-pesanan/<booking_id>', methods=['GET'])
def cetak_pesanan(booking_id):
    booking = db.booking.find_one({'_id' : ObjectId(booking_id)})

    return render_template('cetak-pesanan.html', booking=booking)



if __name__ == '__main__':
    app.run('0.0.0.0', port=3000, debug=True)