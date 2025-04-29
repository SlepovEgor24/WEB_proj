from flask import Flask, render_template, request, redirect, url_for, jsonify, session as flask_session, Blueprint
from werkzeug.security import generate_password_hash, check_password_hash
from data.db import db, User, Message, Direction, Law, init_db
from datetime import datetime
import os
import csv
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'EKKOKS'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Константы путей к файлам
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
RESOURCES_PATH = os.path.join(DIRECTORY, 'data', 'resources.csv')
UPLOAD_FOLDER = os.path.join(DIRECTORY, 'static', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def create_initial_users():  # Создание начальных пользователей (администраторов) при первом запуске
    with app.app_context():
        admin = db.session.query(User).filter_by(email='admin@example.com').first()
        if not admin:
            hashed_password = generate_password_hash('admin123')
            new_admin = User(name='Админ', email='admin@example.com', password=hashed_password,
                             is_admin=1, show_email=True)
            db.session.add(new_admin)

        first_user = db.session.query(User).filter_by(email='egorslepov868@gmail.com').first()
        if first_user:
            first_user.is_admin = 1
            first_user.show_email = True
        else:
            hashed_password = generate_password_hash('password123')
            new_first = User(name='First', email='egorslepov868@gmail.com',
                             password=hashed_password, is_admin=1, show_email=True)
            db.session.add(new_first)

        db.session.commit()


def create_initial_directions():  # Создание начальных направлений и законов
    with app.app_context():
        if not db.session.query(Direction).first():
            initial_directions = [
                {"name": "Механика", "image_path": "mech.png", "description": "Изучение движения и равновесия.", "laws": [
                    {"name": "Первый закон Ньютона", "description": "Тело остаётся в покое или движется равномерно, если на него не действуют силы.", "text": "∑F = 0 => a = 0"},
                    {"name": "Второй закон Ньютона", "description": "Ускорение тела пропорционально равнодействующей силе.", "text": "F = m * a"}
                ]},
                {"name": "Электричество", "image_path": "elec.png", "description": "Изучение зарядов и токов.", "laws": [
                    {"name": "Закон Ома", "description": "Сила тока пропорциональна напряжению.", "text": "I = U / R"},
                    {"name": "Закон Кулона", "description": "Сила взаимодействия зарядов пропорциональна их величине.", "text": "F = k * (q1 * q2) / r^2"}
                ]},
                {"name": "Термодинамика", "image_path": "thermo.png", "description": "Изучение тепла и энергии.", "laws": [
                    {"name": "Первое начало термодинамики", "description": "Изменение внутренней энергии равно теплоте минус работа.", "text": "ΔU = Q - W"},
                    {"name": "Второе начало термодинамики", "description": "Энтропия изолированной системы возрастает.", "text": "S >= 0"}
                ]},
                {"name": "Оптика", "image_path": "optic.png", "description": "Изучение света.", "laws": [
                    {"name": "Закон преломления", "description": "Отношение синусов углов преломления равно показателю преломления.", "text": "n1 * sin(θ1) = n2 * sin(θ2)"},
                    {"name": "Закон отражения", "description": "Угол падения равен углу отражения.", "text": "θi = θr"}
                ]},
                {"name": "Силы", "image_path": "force.jpg", "description": "Сила — векторная величина.", "laws": [
                    {"name": "Закон Гука", "description": "Сила упругости пропорциональна деформации.", "text": "F = -k * x"},
                    {"name": "Сила трения", "description": "Сила трения пропорциональна нормальной силе.", "text": "Fтр = μ * N"}
                ]},
                {"name": "Масса", "image_path": "mass.png", "description": "Масса — мера инерции.", "laws": [
                    {"name": "Закон сохранения массы", "description": "Масса веществ до и после реакции одинакова.", "text": "m1 + m2 = m3 + m4"},
                    {"name": "Масса и энергия", "description": "Масса эквивалентна энергии.", "text": "E = mc^2"}
                ]}
            ]
            for direction_data in initial_directions:
                new_direction = Direction(
                    name=direction_data["name"],
                    image_path=direction_data["image_path"],
                    description=direction_data["description"]
                )
                db.session.add(new_direction)
                db.session.flush()  # Получаем ID направления
                for law_data in direction_data["laws"]:
                    new_law = Law(
                        name=law_data["name"],
                        direction_id=new_direction.id,
                        description=law_data["description"],
                        text=law_data["text"]
                    )
                    db.session.add(new_law)
            db.session.commit()


def load_resources():  # Загрузка списка ресурсов из csv файла
    resources = []
    if os.path.exists(RESOURCES_PATH):
        with open(RESOURCES_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            resources = list(reader)
    return resources


def load_directions():  # Загрузка направлений из базы данных
    return db.session.query(Direction).all()


init_db(app)  # Инициализация БД
create_initial_users()
create_initial_directions()


def get_current_user():  # Возвращение текущего авторизованного пользователя из сессии
    if 'user_id' in flask_session:
        return db.session.get(User, flask_session['user_id'])
    return None


# Создание Blueprint для API
api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/directions', methods=['GET'])
def get_directions_api():
    directions = load_directions()
    directions_list = [
        {"id": d.id, "name": d.name, "image_path": d.image_path, "description": d.description}
        for d in directions
    ]
    return jsonify(directions_list)


@api_bp.route('/laws/<direction_name>', methods=['GET'])
def get_laws_api(direction_name):
    direction = db.session.query(Direction).filter_by(name=direction_name).first()
    if not direction:
        return jsonify({"error": "Направление не найдено"}), 404
    laws = db.session.query(Law).filter_by(direction_id=direction.id).all()
    laws_list = [
        {"id": law.id, "name": law.name, "description": law.description, "text": law.text}
        for law in laws
    ]
    return jsonify(laws_list)


@api_bp.route('/law/<int:law_id>', methods=['GET'])
def get_law_api(law_id):
    law = db.session.get(Law, law_id)
    if not law:
        return jsonify({"error": "Закон не найден"}), 404
    return jsonify({
        "id": law.id,
        "name": law.name,
        "description": law.description,
        "text": law.text
    })


# Регистрация Blueprint
app.register_blueprint(api_bp)


@app.route('/')  # Главная страница приложения, которая отображает список направлений физики
def index():
    user = get_current_user()
    directions = load_directions()
    print("Directions:", [(d.id, d.name, d.image_path, d.description) for d in directions])  # Отладочный вывод
    print("User:", user)  # Отладочный вывод
    return render_template('index.html', directions=directions, user=user)


@app.route('/direction/<direction_name>')  # Страница направления с карточками законов
def direction(direction_name):
    user = get_current_user()
    direction = db.session.query(Direction).filter_by(name=direction_name).first()
    if not direction:
        return "Направление не найдено", 404
    laws = db.session.query(Law).filter_by(direction_id=direction.id).all()
    directions = load_directions()
    return render_template('direction.html', direction=direction, laws=laws, user=user, directions=directions)


@app.route('/law/<int:law_id>')  # Страница конкретного закона
def law(law_id):
    user = get_current_user()
    law = db.session.get(Law, law_id)
    if not law:
        return "Закон не найден", 404
    directions = load_directions()
    return render_template('law.html', law=law, user=user, directions=directions)


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

        if admin_id == 'all':
            # Отправка сообщения всем администраторам
            recipients = db.session.query(User).filter_by(is_admin=1).all()
            recipients = [admin for admin in recipients if admin.id != user.id]  # Исключаем себя
            if not recipients:
                return jsonify({'error': 'Нет доступных администраторов'}), 400
            for admin in recipients:
                new_message = Message(
                    sender_id=user.id,
                    recipient_id=admin.id,
                    subject=subject,
                    body=body,
                    timestamp=datetime.now()
                )
                db.session.add(new_message)
        else:
            admin = db.session.get(User, admin_id)
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

    directions = load_directions()
    return render_template('messages.html', user=user, admins=admins, directions=directions)


@app.route('/message/<int:message_id>')  # Просмотр конкретного сообщения по его id
def view_message(message_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    message = db.session.get(Message, message_id)
    if not message:
        return 'Сообщение не найдено', 404

    if message.recipient_id == user.id:
        message.is_read = True
        db.session.commit()

    if message.sender_id != user.id and message.recipient_id != user.id:
        return 'Доступ запрещен', 403

    directions = load_directions()
    return render_template('view_message.html', message=message, user=user, directions=directions)


@app.route('/reply/<int:message_id>', methods=['POST'])  # Отправка ответа на сообщение
def reply_message(message_id):
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403

    original_message = db.session.get(Message, message_id)
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


@app.route('/rate_message/<int:message_id>/<action>', methods=['POST'])  # Изменение рейтинга за сообщение
def rate_message(message_id, action):
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403

    message = db.session.get(Message, message_id)
    if not message:
        return jsonify({'error': 'Сообщение не найдено'}), 404

    if message.rating_changed:
        return jsonify({'error': 'Рейтинг уже изменён для этого сообщения'}), 400

    sender = message.sender
    if action == 'up':
        sender.rating += 1
        message.rating_change = 1
    elif action == 'down':
        sender.rating -= 1
        message.rating_change = -1
    else:
        return jsonify({'error': 'Недопустимое действие'}), 400

    message.rating_changed = True
    db.session.commit()

    return jsonify({'success': True, 'new_rating': sender.rating})


@app.route('/inbox')  # Страница входящих сообщений пользователя
def inbox():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    received_messages = db.session.query(Message).filter_by(recipient_id=user.id).order_by(
        Message.timestamp.desc()).all()
    directions = load_directions()
    return render_template('inbox.html', messages=received_messages, user=user, directions=directions)


@app.route('/sent')  # Страница отправленных сообщений пользователя
def sent_messages():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    sent_messages = db.session.query(Message).filter_by(sender_id=user.id).order_by(
        Message.timestamp.desc()).all()
    directions = load_directions()
    return render_template('sent_messages.html', messages=sent_messages, user=user, directions=directions)


@app.route('/register', methods=['GET', 'POST'])  # Регистрация новых пользователей
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        print(f"Registering user with name: {name}, email: {email}")  # Отладочный вывод

        # Проверка имени
        if name.count('_') > 5:
            return jsonify({
                'error': 'Имя может содержать не более 5 символов _'
            }), 400
        if '__' in name:
            return jsonify({
                'error': 'Имя не может содержать подряд идущие символы _'
            }), 400
        if len(name) < 5:
            return jsonify({
                'error': 'Имя должно содержать не менее 5 символов'
            }), 400

        # Проверка email
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

        # Проверка пароля
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

        # Проверка на уникальность email
        existing_user = db.session.query(User).filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Email уже зарегистрирован'}), 400

        # Регистрация пользователя
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_password, show_email=True)
        db.session.add(new_user)
        db.session.commit()
        flask_session['user_id'] = new_user.id
        return redirect(url_for('index'))
    directions = load_directions()
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
    directions = load_directions()
    return render_template('login.html', directions=directions)


@app.route('/logout')  # Выход из системы
def logout():
    flask_session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/support', methods=['GET', 'POST'])  # Страница поддержки и администрирования
def support():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    admins = db.session.query(User).filter_by(is_admin=1).all()
    directions = load_directions()
    error_message = success_message = warning_message = None

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'send_message':
            admin_id = request.form.get('admin_id')
            subject = request.form.get('subject')
            body = request.form.get('body')

            if not all([admin_id, subject, body]):
                error_message = 'Заполните все поля'
            else:
                if admin_id == 'all':
                    recipients = [admin for admin in admins if admin.id != user.id]
                    if not recipients:
                        error_message = 'Нет доступных администраторов'
                    else:
                        for admin in recipients:
                            new_message = Message(
                                sender_id=user.id,
                                recipient_id=admin.id,
                                subject=subject,
                                body=body,
                                timestamp=datetime.now()
                            )
                            db.session.add(new_message)
                        success_message = 'Сообщение успешно отправлено всем администраторам'
                else:
                    admin = db.session.get(User, admin_id)
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
                        success_message = 'Сообщение успешно отправлено администратору'
                db.session.commit()

        elif action == 'add_admin' and user.is_admin:
            email = request.form.get('email')
            target_user = db.session.query(User).filter_by(email=email).first()
            if target_user:
                if target_user.is_admin:
                    warning_message = f'Пользователь с email {email} уже является администратором'
                else:
                    target_user.is_admin = 1
                    db.session.commit()
                    success_message = f'Пользователь {email} теперь администратор'
            else:
                error_message = 'Пользователя с таким email не существует'

        elif action == 'remove_admin' and user.is_admin:
            admin_id = request.form.get('admin_id')
            target_admin = db.session.get(User, admin_id)
            if target_admin:
                if target_admin.id == user.id:
                    error_message = 'Вы не можете исключить самого себя'
                else:
                    target_admin.is_admin = 0
                    db.session.commit()
                    success_message = f'Пользователь {target_admin.email} больше не администратор'
            else:
                error_message = 'Администратор не найден'

        elif action == 'add_content' and user.is_admin:
            content_type = request.form.get('content_type')
            name = request.form.get('name')
            description = request.form.get('description')

            if not all([content_type, name, description]):
                error_message = 'Заполните все поля'
            elif content_type == 'direction':
                image = request.files.get('image')
                if not image or not allowed_file(image.filename):
                    error_message = 'Загрузите изображение в формате PNG, JPG, JPEG или GIF'
                else:
                    filename = secure_filename(image.filename)
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image.save(image_path)
                    new_direction = Direction(
                        name=name,
                        image_path=filename,
                        description=description
                    )
                    db.session.add(new_direction)
                    success_message = f'Направление "{name}" успешно добавлено'
                    db.session.commit()
            elif content_type == 'law':
                direction_id = request.form.get('direction_id')
                text = request.form.get('text')
                if not direction_id or not text:
                    error_message = 'Выберите направление и введите текст закона'
                else:
                    new_law = Law(
                        name=name,
                        direction_id=direction_id,
                        description=description,
                        text=text
                    )
                    db.session.add(new_law)
                    success_message = f'Закон "{name}" успешно добавлен'
                    db.session.commit()

    return render_template('support.html',
                           user=user,
                           admins=admins,
                           directions=directions,
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
    directions = load_directions()
    return render_template('resources.html',
                           resources=resources,
                           directions=directions,
                           user=user,
                           all_categories=all_categories,
                           current_category=filter_category)


if __name__ == '__main__':
    app.run(debug=True)