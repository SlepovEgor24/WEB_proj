from flask import Flask, render_template, request, redirect, url_for, jsonify, \
    session as flask_session
from werkzeug.security import generate_password_hash, check_password_hash
from data.db import db, User, init_db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


def create_initial_users():
    with app.app_context():
        admin = db.session.query(User).filter_by(email='admin@example.com').first()
        if not admin:
            hashed_password = generate_password_hash('admin123')
            new_admin = User(name='Admin', email='admin@example.com', password=hashed_password,
                             is_admin=1)
            db.session.add(new_admin)

        first_user = db.session.query(User).filter_by(email='egorslepov868@gmail.com').first()
        if first_user:
            first_user.is_admin = 1
        else:
            hashed_password = generate_password_hash('password123')
            new_first = User(name='First', email='egorslepov868@gmail.com',
                             password=hashed_password, is_admin=1)
            db.session.add(new_first)

        db.session.commit()


init_db(app)
create_initial_users()

directions = [
    {"id": "механика", "name": "Механика", "description": "Изучение движения и равновесия.",
     "formulas": ["F = ma", "W = Fd"], "image": "mech.png"},
    {"id": "электричество", "name": "Электричество", "description": "Изучение зарядов и токов.",
     "formulas": ["I = U/R", "P = UI"], "image": "elec.png"},
    {"id": "термодинамика", "name": "Термодинамика", "description": "Изучение тепла и энергии.",
     "formulas": ["Q = mcΔT"], "image": "thermo.png"},
    {"id": "оптика", "name": "Оптика", "description": "Изучение света.", "formulas": ["n = c/v"],
     "image": "optic.png"},
    {"id": "силы", "name": "Силы", "description": "Сила — векторная величина.",
     "formulas": ["F = G(m1m2/r²)"],
     "image": "force.jpg"},
    {"id": "масса", "name": "Масса", "description": "Масса — мера инерции.",
     "formulas": ["m = F/a"],
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
        return render_template('direction.html', direction=direction, user=user,
                               directions=directions)
    return "Направление не найдено", 404


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        if not any(c.isalpha() and c.isascii() for c in name):
            return jsonify({
                'error': 'Имя должно содержать хотя бы одну латинскую букву'
            }), 400
        if name.count('_') > 5:
            return jsonify({
                'error': 'Имя может содержать не более 5 символов _'
            }), 400
        if not all(c.isalnum() or c == '_' for c in name):
            return jsonify({
                'error': 'Имя может содержать только буквы, цифры и символ _'
            }), 400
        if len(name) < 8:
            return jsonify({
                'error': 'Имя должно содержать не менее 8 символов'
            }), 400
        if not any(c.isalpha() for c in name):
            return jsonify({
                'error': 'Имя должно содержать хотя бы одну букву'
            }), 400
        if not any(c.isdigit() for c in name):
            return jsonify({
                'error': 'Имя должно содержать хотя бы одну цифру'
            }), 400
        email_parts = email.split('@')
        if len(email_parts) != 2:
            return jsonify({'error': 'Email должен содержать ровно один символ @'}), 400
        local_part = email_parts[0]
        domain_part = email_parts[1]
        if not local_part:
            return jsonify({'error': 'Введите часть email до символа @'}), 400
        if local_part[0].isdigit():
            return jsonify({'error': 'Email не может начинаться с цифры'}), 400
        if not any(c.isalpha() for c in local_part):
            return jsonify({'error': 'Email до @ должен содержать хотя бы одну букву'}), 400
        allowed_special = set('.-_')
        for i, char in enumerate(local_part):
            if not (char.isalnum() or char in allowed_special):
                return jsonify({'error': f'Недопустимый символ "{char}" в email'}), 400
            if char in allowed_special and i in [0, len(local_part) - 1]:
                return jsonify(
                    {'error': 'Email не может начинаться или заканчиваться на символы .-_'}), 400
            if char in allowed_special and local_part[i - 1] in allowed_special:
                return jsonify({'error': 'Символы .-_ не могут идти подряд'}), 400
        if not domain_part:
            return jsonify({'error': 'Введите домен после символа @'}), 400
        if domain_part.count('.') != 1:
            return jsonify({'error': 'После @ должна быть ровно одна точка'}), 400
        domain_parts = domain_part.split('.')
        domain_name = domain_parts[0]
        domain_zone = domain_parts[1]
        if not domain_name:
            return jsonify({'error': 'Введите доменное имя перед точкой'}), 400
        if not domain_name.isalnum():
            return jsonify(
                {'error': 'Доменное имя должно содержать только латинские буквы и цифры'}), 400
        if not domain_zone.isalpha():
            return jsonify({'error': 'Доменная зона должна содержать только латинские буквы'}), 400
        if len(domain_zone) < 2:
            return jsonify({'error': 'Доменная зона должна содержать минимум 2 символа'}), 400
        if password == name:
            return jsonify({'error': 'Пароль не должен совпадать с именем пользователя'}), 400
        if len(password) < 8:
            return jsonify({
                'error': 'Пароль должен содержать не менее 8 символов'
            }), 400
        if not any(c.isalpha() for c in password):
            return jsonify({
                'error': 'Пароль должен содержать хотя бы одну букву'
            }), 400
        if not any(c.isdigit() for c in password):
            return jsonify({
                'error': 'Пароль должен содержать хотя бы одну цифру'
            }), 400
        existing_user = db.session.query(User).filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Email уже зарегистрирован'}), 400
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flask_session['user_id'] = new_user.id
        return redirect(url_for('index'))
    return render_template('register.html', directions=directions)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        email_parts = email.split('@')
        if len(email_parts) != 2 or '.' not in email_parts[1]:
            return jsonify({
                'error': 'Введите корректный email (пример: user@example.com)'
            }), 400
        if len(password) < 8:
            return jsonify({
                'error': 'Пароль должен содержать минимум 8 символов'
            }), 400
        user = db.session.query(User).filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            flask_session['user_id'] = user.id
            return jsonify({'success': True})
        return jsonify({'error': 'Неверный email или пароль'}), 401
    return render_template('login.html', directions=directions)


@app.route('/logout')
def logout():
    flask_session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/support', methods=['GET', 'POST'])
def support():
    user = get_current_user()
    show_admin_popup = flask_session.get('show_admin_popup', False)
    show_remove_admin_popup = flask_session.get('show_remove_admin_popup', False)
    error_message = None

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_admin' and user and user.is_admin == 1:
            email = request.form.get('email')
            target_user = db.session.query(User).filter_by(email=email).first()
            if target_user:
                target_user.is_admin = 1
                db.session.commit()
                flask_session['show_admin_popup'] = False
            else:
                error_message = 'Пользователя с таким email не существует'
                flask_session['show_admin_popup'] = True
        elif action == 'remove_admin' and user and user.is_admin == 1:
            user.is_admin = 0
            db.session.commit()
            flask_session['show_remove_admin_popup'] = False
            return redirect(url_for('index'))
        elif action == 'toggle_admin_popup' and user and user.is_admin == 1:
            flask_session['show_admin_popup'] = not show_admin_popup
            flask_session['show_remove_admin_popup'] = False
        elif action == 'toggle_remove_admin_popup' and user and user.is_admin == 1:
            flask_session['show_remove_admin_popup'] = not show_remove_admin_popup
            flask_session['show_admin_popup'] = False

    return render_template('support.html', user=user, directions=directions,
                           show_admin_popup=show_admin_popup,
                           show_remove_admin_popup=show_remove_admin_popup,
                           error_message=error_message)


if __name__ == '__main__':
    app.run(debug=True)
