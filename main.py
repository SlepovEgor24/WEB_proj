from flask import Flask, render_template, request, redirect, url_for, jsonify, \
    session as flask_session
from werkzeug.security import generate_password_hash, check_password_hash
from data.db import db, User, Message, init_db
from datetime import datetime
import os
import csv

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Константы путей к файлам
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
RESOURCES_PATH = os.path.join(DIRECTORY, 'data', 'resources.csv')


def create_initial_users():  # Создание начальных пользователей (администраторов) при первом запуске
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


def load_resources():  # Загрузка списка ресурсов из csv файла
    resources = []
    if os.path.exists(RESOURCES_PATH):
        with open(RESOURCES_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            resources = list(reader)
    return resources


init_db(app)  # Инициализация БД и создание начальных пользователей
create_initial_users()
# Список направлений физики с описанием и формулами
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


def get_current_user():  # Возвращение текущего авторизованного пользователя из сессии
    if 'user_id' in flask_session:
        return db.session.query(User).get(flask_session['user_id'])
    return None


@app.route('/')  # Главная страница приложения, которая отображает список направлений физики
def index():
    user = get_current_user()
    return render_template('index.html', directions=directions, user=user)


@app.route('/direction/<direction_id>')  # Страница определённого направления физики по его id
def direction(direction_id):
    user = get_current_user()
    direction = next((d for d in directions if d["id"] == direction_id), None)
    if direction:
        return render_template('direction.html', direction=direction, user=user,
                               directions=directions)
    return "Направление не найдено", 404


@app.route('/messages', methods=['GET', 'POST'])  # Обработка отправки сообщений администраторам
def messages():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    admins = db.session.query(User).filter_by(is_admin=1).all()

    if request.method == 'POST':
        admin_id = request.form.get('admin_id')
        subject = request.form.get('subject')
        body = request.form.get('body')

        if not all([admin_id, subject, body]):
            return jsonify({'error': 'Заполните все поля'}), 400

        admin = db.session.query(User).get(admin_id)
        if not admin or not admin.is_admin:
            return jsonify({'error': 'Выбранный администратор не найден'}), 400

        if admin.id == user.id:
            return jsonify({'error': 'Нельзя отправить сообщение самому себе'}), 400

        new_message = Message(
            sender_id=user.id,
            recipient_id=admin.id,
            subject=subject,
            body=body,
            timestamp=datetime.now()
        )
        db.session.add(new_message)
        db.session.commit()
        return jsonify({'success': True})

    return render_template('messages.html', user=user, admins=admins)


@app.route('/message/<int:message_id>')  # Просмотр конкретного сообщения по его id
def view_message(message_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    message = db.session.query(Message).get(message_id)
    if not message:
        return 'Сообщение не найдено', 404

    if message.recipient_id == user.id:
        message.is_read = True
        db.session.commit()

    if message.sender_id != user.id and message.recipient_id != user.id:
        return 'Доступ запрещен', 403

    return render_template('view_message.html', message=message, user=user)


@app.route('/reply/<int:message_id>',
           methods=['POST'])  # Отправка ответа на сообщение (доступно только администраторам)
def reply_message(message_id):
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403

    original_message = db.session.query(Message).get(message_id)
    if not original_message:
        return jsonify({'error': 'Сообщение не найдено'}), 404

    body = request.form.get('body')
    if not body:
        return jsonify({'error': 'Введите текст ответа'}), 400

    reply = Message(
        sender_id=user.id,
        recipient_id=original_message.sender_id,
        subject=original_message.subject,
        body=body,
        reply_to_id=original_message.id
    )
    db.session.add(reply)
    db.session.commit()

    return jsonify({'success': True})


@app.route('/inbox')  # Страница входящих сообщений пользователя
def inbox():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    received_messages = db.session.query(Message).filter_by(recipient_id=user.id).order_by(
        Message.timestamp.desc()).all()
    return render_template('inbox.html', messages=received_messages, user=user)


@app.route('/sent')  # Страница отправленных сообщений пользователя
def sent_messages():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    sent_messages = db.session.query(Message).filter_by(sender_id=user.id).order_by(
        Message.timestamp.desc()).all()
    return render_template('sent_messages.html', messages=sent_messages, user=user)


@app.route('/register', methods=['GET',
                                 'POST'])  # Регистрация новых пользователей с проверкой на корректный ввод данных
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        if not any(symbol.isalpha() and symbol.isascii() for symbol in name):
            return jsonify({
                'error': 'Имя должно содержать латинские буквы'
            }), 400
        if name.count('_') > 5:
            return jsonify({
                'error': 'Имя может содержать не более 5 символов _'
            }), 400
        if '__' in name:
            return jsonify({
                'error': 'Имя не может содержать подряд идущие символы _'
            }), 400
        if not all(symbol.isalnum() or symbol == '_' for symbol in name):
            return jsonify({
                'error': 'Имя может содержать только буквы, цифры и символ _'
            }), 400
        if len(name) < 8:
            return jsonify({
                'error': 'Имя должно содержать не менее 8 символов'
            }), 400
        if not any(symbol.isalpha() for symbol in name):
            return jsonify({
                'error': 'Имя должно содержать хотя бы одну букву'
            }), 400
        if not any(symbol.isdigit() for symbol in name):
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
        if not any(symbol.isalpha() for symbol in local_part):
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
        if not any(symbol.isalpha() for symbol in password):
            return jsonify({
                'error': 'Пароль должен содержать хотя бы одну букву'
            }), 400
        if not any(symbol.isdigit() for symbol in password):
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


@app.route('/login', methods=['GET', 'POST'])  # Авторизация пользователей
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


@app.route('/logout')  # Выход из системы
def logout():
    flask_session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/support', methods=['GET', 'POST'])  # Страница поддержки и администрирования
def support():
    user = get_current_user()
    admins = db.session.query(User).filter_by(is_admin=1).all()
    error_message = None
    success_message = None
    warning_message = None

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'send_message':
            admin_id = request.form.get('admin_id')
            subject = request.form.get('subject')
            body = request.form.get('body')

            if not all([admin_id, subject, body]):
                error_message = 'Заполните все поля'
            else:
                admin = db.session.query(User).get(admin_id)
                if not admin or not admin.is_admin:
                    error_message = 'Выбранный администратор не найден'
                elif admin.id == user.id:
                    error_message = 'Нельзя отправить сообщение самому себе'
                else:
                    new_message = Message(
                        sender_id=user.id,
                        recipient_id=admin.id,
                        subject=subject,
                        body=body,
                        timestamp=datetime.now()
                    )
                    db.session.add(new_message)
                    db.session.commit()
                    success_message = 'Сообщение успешно отправлено администратору'

        elif action == 'add_admin' and user and user.is_admin == 1:
            email = request.form.get('email')
            target_user = db.session.query(User).filter_by(email=email).first()
            if target_user:
                if target_user.is_admin == 1:
                    warning_message = f'Пользователь с email {email} уже является администратором'
                else:
                    target_user.is_admin = 1
                    db.session.commit()
                    success_message = f'Пользователь {email} теперь администратор'
            else:
                error_message = 'Пользователя с таким email не существует'
        elif action == 'remove_admin' and user and user.is_admin == 1:
            admin_id = request.form.get('admin_id')
            target_admin = db.session.query(User).get(admin_id)
            if target_admin:
                if target_admin.id == user.id:
                    error_message = 'Вы не можете исключить самого себя'
                else:
                    target_admin.is_admin = 0
                    db.session.commit()
                    success_message = f'Пользователь {target_admin.email} больше не администратор'
            else:
                error_message = 'Администратор не найден'

    return render_template('support.html',
                           user=user,
                           admins=admins,
                           error_message=error_message,
                           success_message=success_message,
                           warning_message=warning_message)


@app.route('/resources')  # Страница с полезными ресурсами по физике
def resources():
    user = get_current_user()
    resources = load_resources()
    filter_category = request.args.get('category')
    if filter_category:
        resources = [el for el in resources if el['category'] == filter_category]
    all_categories = sorted({el['category'] for el in load_resources()})
    return render_template('resources.html',
                           resources=resources,
                           directions=directions,
                           user=user,
                           all_categories=all_categories,
                           current_category=filter_category)


if __name__ == '__main__':
    app.run(debug=True)
