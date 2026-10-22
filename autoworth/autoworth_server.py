#!/usr/bin/env python3
"""AutoWorth local web app backed by SQLite (Python standard library only)."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import urlparse
from contextlib import contextmanager
import hashlib
import json
import secrets
import sqlite3
import time
import os

ROOT = Path(__file__).resolve().parent
PAGE = ROOT / 'car_valuation.html'
DB = Path(os.environ.get('AUTOWORTH_DB', ROOT / 'autoworth.sqlite3'))
HOST = os.environ.get('HOST', '127.0.0.1')
PORT = int(os.environ.get('PORT', '8765'))
PBKDF2_ROUNDS = 260_000
SESSION_SECONDS = 60 * 60 * 24 * 14


def connect():
    db = sqlite3.connect(DB, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    return db


@contextmanager
def database():
    db = connect()
    try:
        yield db
        db.commit()
    finally:
        db.close()


def init_db():
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            display_name TEXT NOT NULL,
            phone TEXT NOT NULL DEFAULT '',
            role TEXT NOT NULL CHECK(role IN ('seller','buyer')),
            password_salt BLOB NOT NULL,
            password_hash BLOB NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            expires_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY,
            seller_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER NOT NULL,
            mileage_km INTEGER NOT NULL,
            price_usd REAL NOT NULL,
            condition TEXT NOT NULL,
            fuel_type TEXT NOT NULL,
            transmission TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT NOT NULL,
            contact_phone TEXT NOT NULL DEFAULT '',
            phone_public INTEGER NOT NULL DEFAULT 0,
            image_url TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
            buyer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            seller_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS listings_active_idx ON listings(status, created_at DESC);
        CREATE INDEX IF NOT EXISTS messages_seller_idx ON messages(seller_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS messages_buyer_idx ON messages(buyer_id, created_at DESC);
        ''')


def json_bytes(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


class Handler(BaseHTTPRequestHandler):
    server_version = 'AutoWorth/1.0'

    def log_message(self, fmt, *args):
        print('%s - %s' % (self.address_string(), fmt % args))

    def reply(self, status, body, headers=None):
        self.send_response(status)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        for key, val in (headers or {}).items():
            self.send_header(key, val)
        self.end_headers()
        self.wfile.write(body)

    def json_reply(self, status, obj, headers=None):
        h = {'Content-Type': 'application/json; charset=utf-8'}
        h.update(headers or {})
        self.reply(status, json_bytes(obj), h)

    def read_json(self):
        try:
            size = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            raise ValueError('Invalid request size.')
        if size < 1 or size > 2_000_000:
            raise ValueError('Request must be between 1 byte and 2 MB.')
        try:
            data = json.loads(self.rfile.read(size).decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError('Request body must be valid JSON.')
        if not isinstance(data, dict):
            raise ValueError('Request body must be a JSON object.')
        return data

    def require_same_origin(self):
        origin = self.headers.get('Origin')
        if origin and origin.rstrip('/') != ('http://' + self.headers.get('Host', '')):
            raise PermissionError('Cross-origin requests are not accepted.')

    def current_user(self, db):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get('Cookie', ''))
            token = cookie['aw_session'].value
        except (KeyError, Exception):
            return None
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        row = db.execute('''SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id
                            WHERE s.token_hash=? AND s.expires_at>?''', (token_hash, int(time.time()))).fetchone()
        return row

    def set_session(self, db, user_id):
        token = secrets.token_urlsafe(40)
        expires = int(time.time()) + SESSION_SECONDS
        db.execute('INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(?,?,?)',
                   (hashlib.sha256(token.encode()).hexdigest(), user_id, expires))
        return {'Set-Cookie': f'aw_session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={SESSION_SECONDS}'}

    def clear_session(self, db):
        user = self.current_user(db)
        if user:
            cookie = SimpleCookie(); cookie.load(self.headers.get('Cookie', ''))
            token = cookie['aw_session'].value
            db.execute('DELETE FROM sessions WHERE token_hash=?', (hashlib.sha256(token.encode()).hexdigest(),))
        return {'Set-Cookie': 'aw_session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0'}

    def do_GET(self):
        route = urlparse(self.path).path
        if route == '/' or route == '/index.html':
            try:
                content = PAGE.read_bytes()
            except OSError:
                return self.reply(500, b'AutoWorth page is missing.', {'Content-Type':'text/plain; charset=utf-8'})
            return self.reply(200, content, {'Content-Type':'text/html; charset=utf-8'})
        with database() as db:
            if route == '/api/session':
                user = self.current_user(db)
                if not user:
                    return self.json_reply(200, {'user': None})
                return self.json_reply(200, {'user': self.user_json(user)})
            if route == '/api/listings':
                rows = db.execute('''SELECT l.*,u.display_name AS seller_name,u.email AS seller_email
                    FROM listings l JOIN users u ON u.id=l.seller_id
                    WHERE l.status='active' ORDER BY l.created_at DESC,l.id DESC''').fetchall()
                return self.json_reply(200, {'listings':[self.listing_json(r) for r in rows]})
            if route == '/api/messages':
                user = self.current_user(db)
                if not user:
                    return self.json_reply(401, {'error':'Please sign in to view messages.'})
                rows = db.execute('''SELECT m.*,l.title AS listing_title,
                    b.email AS buyer_email,b.display_name AS buyer_name,
                    s.email AS seller_email,s.display_name AS seller_name
                    FROM messages m JOIN listings l ON l.id=m.listing_id
                    JOIN users b ON b.id=m.buyer_id JOIN users s ON s.id=m.seller_id
                    WHERE m.buyer_id=? OR m.seller_id=? ORDER BY m.created_at DESC,m.id DESC''',
                    (user['id'],user['id'])).fetchall()
                return self.json_reply(200, {'messages':[dict(r) for r in rows]})
        self.json_reply(404, {'error':'Not found.'})

    @staticmethod
    def user_json(row):
        return {'id':row['id'],'email':row['email'],'name':row['display_name'],'phone':row['phone'],'role':row['role']}

    @staticmethod
    def listing_json(row):
        return {'id':row['id'],'title':row['title'],'brand':row['brand'],'model':row['model'],
                'year':row['year'],'mileage':row['mileage_km'],'price':row['price_usd'],
                'condition':row['condition'],'fuel':row['fuel_type'],'transmission':row['transmission'],
                'location':row['location'],'description':row['description'],
                'sellerName':row['seller_name'],'sellerEmail':row['seller_email'],
                'phone':row['contact_phone'] if row['phone_public'] else '',
                'imageUrl':row['image_url'],'createdAt':row['created_at']}

    def do_POST(self):
        try:
            self.require_same_origin()
            data = self.read_json()
            route = urlparse(self.path).path
            with database() as db:
                if route == '/api/register':
                    return self.register(db,data)
                if route == '/api/login':
                    return self.login(db,data)
                if route == '/api/logout':
                    headers=self.clear_session(db); db.commit()
                    return self.json_reply(200, {'ok':True},headers)
                if route == '/api/listings':
                    return self.create_listing(db,data)
                if route == '/api/messages':
                    return self.create_message(db,data)
            self.json_reply(404, {'error':'Not found.'})
        except PermissionError as e:
            self.json_reply(403, {'error':str(e)})
        except ValueError as e:
            self.json_reply(400, {'error':str(e)})
        except sqlite3.IntegrityError as e:
            self.json_reply(409, {'error':'That email already has an account.' if 'email' in str(e).lower() else 'Could not save this record.'})
        except Exception as e:
            print('Request error:', repr(e))
            self.json_reply(500, {'error':'Something went wrong. Please try again.'})

    @staticmethod
    def text(data, key, label, max_len, required=True):
        value=data.get(key,'')
        if not isinstance(value,str): raise ValueError(f'{label} must be text.')
        value=value.strip()
        if required and not value: raise ValueError(f'{label} is required.')
        if len(value)>max_len: raise ValueError(f'{label} must be {max_len} characters or fewer.')
        return value

    def register(self,db,data):
        email=self.text(data,'email','Email',254).lower()
        if '@' not in email or '.' not in email.rsplit('@',1)[-1]: raise ValueError('Enter an email address in the usual format.')
        password=self.text(data,'password','Password',200)
        if len(password)<8: raise ValueError('Password must be at least 8 characters.')
        name=self.text(data,'name','Name',100)
        phone=self.text(data,'phone','Phone',40,False)
        role=self.text(data,'role','Account type',10)
        if role not in ('seller','buyer'): raise ValueError('Choose buyer or seller account type.')
        salt=secrets.token_bytes(16)
        derived=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,PBKDF2_ROUNDS,dklen=32)
        cur=db.execute('INSERT INTO users(email,display_name,phone,role,password_salt,password_hash) VALUES(?,?,?,?,?,?)',
                       (email,name,phone,role,salt,derived))
        headers=self.set_session(db,cur.lastrowid); db.commit()
        user=db.execute('SELECT * FROM users WHERE id=?',(cur.lastrowid,)).fetchone()
        return self.json_reply(201,{'user':self.user_json(user)},headers)

    def login(self,db,data):
        email=self.text(data,'email','Email',254).lower()
        password=self.text(data,'password','Password',200)
        row=db.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
        if not row or not secrets.compare_digest(hashlib.pbkdf2_hmac('sha256',password.encode(),row['password_salt'],PBKDF2_ROUNDS,dklen=32),row['password_hash']):
            return self.json_reply(401,{'error':'Email or password is incorrect.'})
        headers=self.set_session(db,row['id']); db.commit()
        return self.json_reply(200,{'user':self.user_json(row)},headers)

    def create_listing(self,db,data):
        user=self.current_user(db)
        if not user: return self.json_reply(401,{'error':'Please sign in as a seller to post a listing.'})
        if user['role']!='seller': return self.json_reply(403,{'error':'A seller account is required to post a car.'})
        brand=self.text(data,'brand','Brand',60); model=self.text(data,'model','Model',80)
        location=self.text(data,'location','Location',100)
        condition=self.text(data,'condition','Condition',20)
        fuel=self.text(data,'fuel','Fuel type',30); trans=self.text(data,'transmission','Transmission',30)
        desc=self.text(data,'description','Description',3000,False)
        phone=self.text(data,'phone','Contact phone',40,False)
        image=self.text(data,'imageUrl','Photo URL',500,False)
        if image and not image.lower().startswith('https://'): raise ValueError('Photo URL must start with https://.')
        try:
            year=int(data.get('year')); mileage=int(data.get('mileage')); price=float(data.get('price'))
        except (ValueError,TypeError): raise ValueError('Enter a valid year, mileage, and asking price.')
        if not (1950<=year<=2027): raise ValueError('Year must be between 1950 and 2027.')
        if not (0<=mileage<=1_000_000): raise ValueError('Mileage must be between 0 and 1,000,000 km.')
        if not (1<=price<=10_000_000): raise ValueError('Asking price must be between $1 and $10,000,000.')
        if condition not in ('New','Used','Damaged'): raise ValueError('Choose a listed condition.')
        if fuel not in ('Gasoline','Diesel','Electric','Hybrid','Other'): raise ValueError('Choose a listed fuel type.')
        if trans not in ('Automatic','Manual','Other'): raise ValueError('Choose a listed transmission.')
        title=f'{year} {brand} {model}'
        cur=db.execute('''INSERT INTO listings(seller_id,title,brand,model,year,mileage_km,price_usd,condition,fuel_type,
            transmission,location,description,contact_phone,phone_public,image_url)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (user['id'],title,brand,model,year,mileage,price,condition,fuel,trans,location,desc,phone,
             1 if data.get('phonePublic') else 0,image))
        row=db.execute('''SELECT l.*,u.display_name AS seller_name,u.email AS seller_email FROM listings l
            JOIN users u ON u.id=l.seller_id WHERE l.id=?''',(cur.lastrowid,)).fetchone()
        db.commit()
        return self.json_reply(201,{'listing':self.listing_json(row)})

    def create_message(self,db,data):
        user=self.current_user(db)
        if not user: return self.json_reply(401,{'error':'Please sign in as a buyer to contact a seller.'})
        if user['role']!='buyer': return self.json_reply(403,{'error':'A buyer account is required to contact a seller.'})
        body=self.text(data,'body','Message',2000)
        try: listing_id=int(data.get('listingId'))
        except (ValueError,TypeError): raise ValueError('Choose a valid car listing.')
        listing=db.execute("SELECT * FROM listings WHERE id=? AND status='active'",(listing_id,)).fetchone()
        if not listing: return self.json_reply(404,{'error':'This listing is no longer available.'})
        if listing['seller_id']==user['id']: return self.json_reply(400,{'error':'You cannot contact yourself about your own listing.'})
        db.execute('INSERT INTO messages(listing_id,buyer_id,seller_id,body) VALUES(?,?,?,?)',
                   (listing_id,user['id'],listing['seller_id'],body))
        db.commit()
        return self.json_reply(201,{'ok':True,'message':'Your message has been sent to the seller.'})


def main():
    DB.parent.mkdir(parents=True, exist_ok=True)
    init_db()
    print(f'AutoWorth is running at http://{HOST}:{PORT}')
    print(f'SQLite database: {DB}')
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == '__main__':
    main()
