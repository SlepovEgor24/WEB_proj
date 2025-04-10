from flask import Flask, render_template, request, redirect, url_for, jsonify, session as flask_session
from werkzeug.security import generate_password_hash, check_password_hash
from data.db import db, User, init_db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Замени на свой ключ
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

init_db(app)

directions = [
    {"id": "механика", "name": "Механика", "description": "Изучение движения и равновесия.",
     "formulas": ["F = ma", "W = Fd"], "image": "mech.png"},
    {"id": "электричество", "name": "Электричество", "description": "Изучение зарядов и токов.",
     "formulas": ["I = U/R", "P = UI"], "image": "elec.png"},
    {"id": "термодинамика", "name": "Термодинамика", "description": "Изучение тепла и энергии.",
     "formulas": ["Q = mcΔT"], "image": "thermo.png"},
    {"id": "оптика", "name": "Оптика", "description": "Изучение света.", "formulas": ["n = c/v"], "image": "optic.png"},
    {"id": "силы", "name": "Силы", "description": "Сила — векторная величина.", "formulas": ["F = G(m1m2/r²)"],
     "image": "force.png"},
    {"id": "масса", "name": "Масса", "description": "Масса — мера инерции.", "formulas": ["m = F/a"],
     "image": "mass.png"}
]


def get_current_user():
    if 'user_id' in flask_session:
        return db.session.query(User).get(flask_session['user_id'])
    return None


@app.route('/')
def index():
    user = get_current_user()
    return render_template('index.html', directions=directions, user=user)


@app.route('/direction/<direction_id>')
def direction(direction_id):
    user = get_current_user()
    direction = next((d for d in directions if d["id"] == direction_id), None)
    if direction:
        return render_template('direction.html', direction=direction, user=user)
    return "Направление не найдено", 404


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        existing_user = db.session.query(User).filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Email уже зарегистрирован'}), 400

        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # Автоматический вход
        flask_session['user_id'] = new_user.id
        return redirect(url_for('index'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = db.session.query(User).filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            flask_session['user_id'] = user.id
            return redirect(url_for('index'))
        return jsonify({'error': 'Неверный email или пароль'}), 401

    return render_template('login.html')


@app.route('/logout')
def logout():
    flask_session.pop('user_id', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)