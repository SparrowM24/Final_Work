from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from models.models import db, User, Product, Order, OrderItem
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
import re
from functools import wraps
import math
import logging

logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Автоматическая инициализация БД с тестовыми данными
def init_database():
    """Проверяет и инициализирует базу данных"""
    with app.app_context():
        try:
            # Создаем таблицы, если их нет
            db.create_all()
            
            # Проверяем, есть ли пользователи в базе
            user_count = User.query.count()
            product_count = Product.query.count()
            
            print(f"Проверка базы данных: {user_count} пользователей, {product_count} товаров")
            
            # Если база пуста (нет пользователей), создаем тестовые данные
            if user_count == 0:
                print("=" * 60)
                print("БАЗА ДАННЫХ ПУСТА. СОЗДАЮ ТЕСТОВЫЕ ДАННЫЕ...")
                print("=" * 60)
                
                # Создаем тестовых пользователей
                users = [
                    ("admin", "storekeeper123", "admin"),
                    ("ivanov", "password123", "storekeeper"),
                    ("petrov", "secure456", "storekeeper"),
                    ("sidorov", "test789", "storekeeper"),
                    ("manager", "manager123", "storekeeper")
                ]
                
                print("\n👥 СОЗДАЮ ПОЛЬЗОВАТЕЛЕЙ:")
                for username, password, role in users:
                    user = User(username=username, role=role)
                    user.set_password(password)
                    db.session.add(user)
                    print(f"  ✓ {username} ({role})")
                
                # Создаем 50 тестовых товаров
                products = [
                    # Холодильники (5)
                    ("RF-1001", "Холодильник Samsung RB33", 15),
                    ("RF-1002", "Холодильник LG GA-B459", 12),
                    ("RF-1003", "Холодильник Bosch KGN39", 8),
                    ("RF-1004", "Холодильник Haier C2F636", 10),
                    ("RF-1005", "Холодильник Indesit DF 4180", 5),
                    
                    # Стиральные машины (5)
                    ("WM-2001", "Стиральная машина Bosch WAN28281", 22),
                    ("WM-2002", "Стиральная машина LG F2J3", 18),
                    ("WM-2003", "Стиральная машина Samsung WW90T554", 15),
                    ("WM-2004", "Стиральная машина Electrolux EW6S4R06W", 12),
                    ("WM-2005", "Стиральная машина Beko WUE 6511 XBW", 9),
                    
                    # Плиты (5)
                    ("ST-3001", "Электрическая плита Gorenje EC 5121 WG", 11),
                    ("ST-3002", "Электрическая плита Bosch HCE644253", 7),
                    ("ST-3003", "Газовая плита Gefest 1200 С7", 14),
                    ("ST-3004", "Индукционная плита Hansa BHI69307", 6),
                    ("ST-3005", "Плита электрическая Darina 1E EM281 404 W", 8),
                    
                    # Микроволновые печи (5)
                    ("MW-4001", "Микроволновая печь Samsung MS23K3515AK", 28),
                    ("MW-4002", "Микроволновая печь LG MS2042DB", 22),
                    ("MW-4003", "Микроволновая печь Bosch BFL524MS0", 16),
                    ("MW-4004", "Микроволновая печь Panasonic NN-ST34", 19),
                    ("MW-4005", "Микроволновая печь Scarlett SC-1706", 25),
                    
                    # Пылесосы (5)
                    ("VC-5001", "Пылесос Samsung VCC4520S36", 20),
                    ("VC-5002", "Пылесос Philips FC9353", 17),
                    ("VC-5003", "Робот-пылесок Xiaomi Mi Robot Vacuum", 9),
                    ("VC-5004", "Пылесос вертикальный Dyson V11", 4),
                    ("VC-5005", "Пылесос моющий Karcher SE 4001", 6),
                    
                    # Электрочайники (5)
                    ("KT-6001", "Электрочайник Bosch TWK 3P413", 35),
                    ("KT-6002", "Электрочайник Philips HD9358", 28),
                    ("KT-6003", "Электрочайник Tefal KI770D38", 22),
                    ("KT-6004", "Электрочайник Polaris PWK 1713C", 30),
                    ("KT-6005", "Электрочайник Scarlett SC-EK27G35", 25),
                    
                    # Кофейное оборудование (5)
                    ("CF-7001", "Кофемашина De'Longhi ECAM 22.110", 5),
                    ("CF-7002", "Кофемашина Philips EP1220", 7),
                    ("CF-7003", "Кофеварка Bosch TKA3A031", 9),
                    ("CF-7004", "Кофемолка Maestro MR-1069", 12),
                    ("CF-7005", "Френч-пресс Borner Classic", 18),
                    
                    # Кухонные комбайны (5)
                    ("BL-7006", "Блендер погружной Philips HR3655", 14),
                    ("BL-7007", "Блендер стационарный Bosch MSM66110", 18),
                    ("KC-7008", "Кухонный комбайн Kenwood FP925", 6),
                    ("KC-7009", "Кухонный комбайн Moulinex Masterchef", 8),
                    ("KC-7010", "Мясорубка Zelmer 987.8", 11),
                    
                    # Миксеры и тостеры (5)
                    ("MX-7011", "Миксер ручной Braun MQ 5037", 20),
                    ("MX-7012", "Миксер стационарный Kitfort КТ-1341", 12),
                    ("TV-7013", "Тостер Tefal TT450D38", 25),
                    ("TV-7014", "Тостер-сэндвич Rolsen RSA-259", 17),
                    ("WA-7015", "Вафельница Marta MT-1943", 13),
                    
                    # Климатическая техника (5)
                    ("AC-8001", "Кондиционер Ballu BSW-07HN1", 6),
                    ("AC-8002", "Кондиционер Mitsubishi Electric MSZ-HJ25VA", 4),
                    ("AC-8003", "Кондиционер LG P07EP2", 5),
                    ("AH-8004", "Увлажнитель воздуха Philips HU4803", 12),
                    ("AH-8005", "Очиститель воздуха Xiaomi Mi Air Purifier 3H", 10),
                    
                    # Техника для ухода за одеждой (5)
                    ("IR-9001", "Утюг Philips GC4523", 27),
                    ("IR-9002", "Утюг паровой Tefal FV2838E0", 23),
                    ("SG-9003", "Отпариватель Philips GC392", 15),
                    ("SG-9004", "Парогенератор Tefal IS6200", 8),
                    ("DW-9005", "Посудомоечная машина Bosch SMS 4HVI33E", 9),
                    
                    # Техника для личного ухода (5)
                    ("SH-0010", "Электробритва Braun Series 3", 18),
                    ("SH-0011", "Триммер Philips BT5500", 22),
                    ("SH-0012", "Фен Rowenta CV 7120", 25),
                    ("SH-0013", "Эпилятор Braun Silk-épil 9", 14),
                    ("SH-0014", "Массажер для лица Foreo Luna 3", 7),
                    
                    # Водонагреватели (5)
                    ("WC-0020", "Водонагреватель Ariston ABS VLS Evo 50", 6),
                    ("WC-0021", "Очиститель воды Аквафор Осмо 50", 8),
                    ("WC-0022", "Кулер для воды HotFrost HFC-351A", 4),
                    ("WC-0023", "Фильтр для воды Барьер Эксперт", 20),
                    ("WC-0024", "Водонагреватель Thermex Flat Plus 50", 7),
                    
                    # Электроника (5)
                    ("ST-0025", "Стабилизатор напряжения Ресанта АСН-5000", 9),
                    ("GE-0026", "Генератор Hyundai HY 3000 LE", 3),
                    ("CA-0027", "Камера видеонаблюдения Reolink RLC-510A", 11),
                    ("RO-0028", "Розетка умная Xiaomi Smart Socket", 35),
                    ("RO-0029", "Умная лампочка Philips Hue White", 24),
                    
                    # Кухонные приборы (5)
                    ("GR-0030", "Гриль электрический GFgrill GF-060", 8),
                    ("MK-0031", "Мультиварка Redmond RMC-M90", 15),
                    ("YR-0032", "Йогуртница Moulinex YG230", 12),
                    ("SB-0033", "Соковыжималка Philips HR1832", 9),
                    ("AF-0034", "Фритюрница Tefal FZ7000", 6),
                    
                    # Обогреватели (5)
                    ("HE-0035", "Обогреватель масляный Electrolux EOH/M", 14),
                    ("HE-0036", "Тепловентилятор Timberk TFH T20XC", 18),
                    ("VE-0037", "Вентилятор напольный Scarlett SC-1132", 22),
                    ("VE-0038", "Вентилятор колонный Dyson AM07", 5),
                    ("HE-0039", "Обогреватель инфракрасный Ballu BIH-LW", 11),
                    
                    # Умный дом (5)
                    ("SM-0040", "Умная колонка Яндекс Станция", 16),
                    ("SM-0041", "Робот-мойщик окон Hobot 298", 4),
                    ("SM-0042", "Умные весы Xiaomi Mi Smart Scale 2", 19),
                    ("SM-0043", "Метеостанция Ea2 EN209", 13),
                    ("SM-0044", "Умный дверной звонок Ezviz DB1", 8),
                    
                    # Аксессуары (6)
                    ("AC-0045", "Кабель HDMI 2.0 3м", 45),
                    ("AC-0046", "Удлинитель электрический IEK", 30),
                    ("AC-0047", "Сетевой фильтр APC PM5U-RS", 17),
                    ("AC-0048", "Аккумуляторы AA Duracell", 60),
                    ("AC-0049", "Зарядное устройство", 21),
                    ("AC-0050", "Пульт универсальный HUAYU HY-308", 28)
                ]
                
                print("\n📦 СОЗДАЮ ТОВАРЫ:")
                created_count = 0
                for article, name, quantity in products:
                    # Проверяем, не существует ли уже товар
                    existing = Product.query.filter_by(article=article).first()
                    if not existing:
                        product = Product(article=article, name=name, quantity=quantity)
                        db.session.add(product)
                        created_count += 1
                        if created_count % 10 == 0:
                            print(f"  ✓ Создано {created_count} товаров...")
                
                db.session.commit()
                
                # Проверяем итоговое количество
                final_product_count = Product.query.count()
                final_user_count = User.query.count()
                
                print("\n" + "=" * 60)
                print("✅ ТЕСТОВЫЕ ДАННЫЕ СОЗДАНЫ УСПЕШНО!")
                print("=" * 60)
                print(f"👥 Пользователей: {final_user_count}")
                print(f"📦 Товаров: {final_product_count}")
                print("\n🔐 ДАННЫЕ ДЛЯ ВХОДА:")
                print("-" * 40)
                print("Логин: admin | Пароль: storekeeper123")
                print("Логин: ivanov | Пароль: password123")
                print("=" * 60)
            else:
                print(f"✓ База данных уже содержит {user_count} пользователей и {product_count} товаров")
                
        except Exception as e:
            print(f"❌ Ошибка при инициализации базы данных: {e}")
            db.session.rollback()

# Автоматически инициализируем БД при импорте
# Это сработает и на PythonAnywhere, и при локальном запуске
init_database()

# Декоратор для проверки авторизации
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Контекстный процессор
@app.context_processor
def inject_user_info():
    student_info = {
        'fio': 'Дьячкова Алиса Дмитриевна',
        'group': 'ФБИ-32'
    }
    
    user_info = {}
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            user_info = {
                'username': user.username,
                'role': user.role
            }
    
    return dict(student_info=student_info, user_info=user_info)

# Валидация
def validate_credentials(username, password):
    pattern = r'^[A-Za-z0-9@#$%^&+=!.,;:]*$'
    if not username or not password:
        return False, 'Логин и пароль не могут быть пустыми'
    
    if len(username) < 3 or len(username) > 50:
        return False, 'Логин должен быть от 3 до 50 символов'
    
    if len(password) < 6:
        return False, 'Пароль должен быть не менее 6 символов'
    
    if not re.match(pattern, username) or not re.match(pattern, password):
        return False, 'Логин и пароль должны содержать только латинские буквы, цифры и знаки препинания'
    
    return True, ''

# Главная страница - начальная загрузка
@app.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = app.config['ITEMS_PER_PAGE']  # 50 товаров на странице
    
    # Пагинация товаров (новые первыми)
    pagination = Product.query.order_by(Product.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    products = pagination.items
    
    # Количество товаров в корзине
    cart_count = sum(session.get('cart', {}).values()) if 'cart' in session else 0
    
    return render_template('index.html', 
                         products=products,
                         pagination=pagination,
                         cart_count=cart_count)

# API для загрузки следующих товаров (AJAX)
@app.route('/load_more_products', methods=['GET'])
@login_required
def load_more_products():
    page = request.args.get('page', 1, type=int)
    items_per_page = app.config['ITEMS_PER_PAGE']
    
    # Рассчитываем смещение
    offset = (page - 1) * items_per_page
    
    # Получаем товары для текущей страницы
    products = Product.query.offset(offset).limit(items_per_page).all()
    
    # Преобразуем товары в словари для JSON
    products_data = []
    for product in products:
        products_data.append({
            'id': product.id,
            'article': product.article,
            'name': product.name,
            'quantity': product.quantity
        })
    
    # Проверяем, есть ли еще товары
    has_more = (offset + len(products)) < Product.query.count()
    
    return jsonify({
        'success': True,
        'products': products_data,
        'has_more': has_more,
        'current_page': page
    })

# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        is_valid, error_msg = validate_credentials(username, password)
        if not is_valid:
            flash(error_msg)
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Пароли не совпадают')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким логином уже существует')
            return render_template('register.html')
        
        try:
            new_user = User(username=username, role='storekeeper')
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Регистрация успешна! Теперь вы можете войти в систему.')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при регистрации: {str(e)}')
            return render_template('register.html')
    
    return render_template('register.html')

# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        if not username or not password:
            flash('Заполните все поля')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль')
    
    return render_template('login.html')

# Выход
@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Вы вышли из системы')
    return redirect(url_for('login'))
    if request.method == 'GET':
        # Просто показываем форму
        return render_template('delete_account.html')
    
    elif request.method == 'POST':
        try:
            # Получаем текущего пользователя
            user = User.query.get(session['user_id'])
            
            if not user:
                flash('Пользователь не найден')
                return redirect(url_for('index'))
            
            # Проверяем подтверждение логина
            confirm_username = request.form.get('confirm_username', '').strip()
            
            if confirm_username != user.username:
                flash('Введенный логин не совпадает с вашим')
                return render_template('delete_account.html')
            
            # Проверяем, не последний ли это пользователь
            total_users = User.query.count()
            
            if total_users <= 1:
                flash('Нельзя удалить последнего пользователя в системе')
                return redirect(url_for('profile'))
            
            # Если пользователь admin, проверяем есть ли другие админы
            if user.username == 'admin':
                other_admins = User.query.filter(
                    User.username != 'admin',
                    User.role == 'admin'
                ).count()
                if other_admins == 0:
                    flash('Нельзя удалить последнего администратора')
                    return redirect(url_for('profile'))
            
            # Удаляем пользователя
            username = user.username
            session.clear()  # Сначала очищаем сессию
            db.session.delete(user)
            db.session.commit()
            
            flash(f'Аккаунт {username} успешно удален')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при удалении аккаунта: {str(e)}')
            print(f"Ошибка удаления аккаунта: {e}")
            import traceback
            traceback.print_exc()
            return redirect(url_for('profile'))

# Добавление товара
@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        article = request.form['article'].strip()
        name = request.form['name'].strip()
        quantity = request.form['quantity']
        
        if not article or not name:
            flash('Заполните все обязательные поля')
            return render_template('add_product.html')
        
        try:
            quantity = int(quantity)
            if quantity < 0:
                flash('Количество не может быть отрицательным')
                return render_template('add_product.html')
        except ValueError:
            flash('Введите корректное количество')
            return render_template('add_product.html')
        
        existing_product = Product.query.filter_by(article=article).first()
        
        if existing_product:
            existing_product.quantity += quantity
            db.session.commit()
            flash(f'Количество товара "{existing_product.name}" увеличено на {quantity}')
        else:
            new_product = Product(article=article, name=name, quantity=quantity)
            db.session.add(new_product)
            db.session.commit()
            flash(f'Товар "{name}" добавлен в базу')
        
        return redirect(url_for('index'))
    
    return render_template('add_product.html')

# Удаление товара (улучшенная версия с информативными сообщениями)
@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    try:
        print(f"=== DEBUG: Удаление товара ID: {product_id} ===")
        
        product = Product.query.get(product_id)
        
        if not product:
            flash('❌ Товар не найден')
            return redirect(url_for('index'))
        
        # 1. Проверяем, есть ли товар в заказах
        order_items = OrderItem.query.filter_by(product_id=product_id).all()
        print(f"Найдено записей в order_item: {len(order_items)}")
        
        if order_items:
            # Собираем информацию о заказах для пользователя
            orders_info = []
            paid_orders_count = 0
            unpaid_orders_count = 0
            
            for item in order_items:
                print(f"  OrderItem ID: {item.id}, Order ID: {item.order_id}")
                if item.order:
                    print(f"    Статус заказа: {item.order.status}")
                    orders_info.append({
                        'order_id': item.order.id,
                        'status': item.order.status,
                        'date': item.order.created_at.strftime('%d.%m.%Y %H:%M'),
                        'quantity': item.quantity
                    })
                    
                    if item.order.status == 'оплачен':
                        paid_orders_count += 1
                    else:
                        unpaid_orders_count += 1
            
            # Проверяем, есть ли оплаченные заказы
            if paid_orders_count > 0:
                # Формируем детальное сообщение
                order_details = ""
                for info in orders_info:
                    if info['status'] == 'оплачен':
                        order_details += f"№{info['order_id']} ({info['date']}, {info['quantity']} шт.), "
                
                if order_details:
                    order_details = order_details[:-2]  # Убираем последнюю запятую
                
                flash(f'❌ Нельзя удалить товар "{product.name}"!<br>'
                      f'Товар находится в <strong>оплаченных заказах</strong>: {order_details}.<br>'
                      f'Всего найдено в {len(order_items)} заказах: {paid_orders_count} оплаченных, {unpaid_orders_count} неоплаченных.')
                return redirect(url_for('index'))
            
            # Если есть только неоплаченные заказы - можно удалить, но с предупреждением
            flash(f'⚠️ Внимание! Товар "{product.name}" находится в {len(order_items)} неоплаченных заказах.<br>'
                  f'Все связанные заказы будут автоматически удалены.', 'warning')
            
            # 2. Удаляем ВСЕ связанные OrderItem записи
            print("Удаляем связанные OrderItem записи...")
            deleted_orders = set()  # Для отслеживания удаленных заказов
            
            for item in order_items:
                # Удаляем OrderItem
                db.session.delete(item)
                print(f"  Удален OrderItem ID: {item.id}")
                deleted_orders.add(item.order_id)
            
            # 3. Проверяем, остались ли пустые заказы
            for order_id in deleted_orders:
                # Проверяем, есть ли другие товары в этом заказе
                other_items = OrderItem.query.filter_by(order_id=order_id).all()
                
                # Если заказ пустой - удаляем и сам заказ
                if not other_items:
                    order = Order.query.get(order_id)
                    if order:
                        db.session.delete(order)
                        print(f"  Удален пустой Order ID: {order.id}")
                        flash(f'🗑️ Удален пустой заказ №{order.id}', 'info')
        
        # 4. Удаляем товар из корзины всех пользователей
        if 'cart' in session and str(product_id) in session['cart']:
            session['cart'].pop(str(product_id))
            session.modified = True
            print(f"Удален из корзины")
        
        # 5. Удаляем сам товар
        print(f"Удаляем товар: {product.name}")
        db.session.delete(product)
        
        # 6. Фиксируем изменения
        db.session.commit()
        
        if order_items:
            flash(f'✅ Товар "{product.name}" удален вместе с {len(order_items)} связанными заказами')
        else:
            flash(f'✅ Товар "{product.name}" успешно удален')
        
        print("Удаление завершено успешно!")
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Ошибка при удалении товара: {str(e)}')
        print(f"Ошибка удаления товара: {e}")
        import traceback
        traceback.print_exc()
    
    return redirect(url_for('index'))

# Корзина
@app.route('/cart')
@login_required
def view_cart():
    cart = session.get('cart', {})
    
    cart_items = []
    total_items = 0
    
    for product_id_str, quantity in cart.items():
        product = Product.query.get(int(product_id_str))
        if product:
            cart_items.append({
                'product': product,
                'quantity': quantity
            })
            total_items += quantity
    
    return render_template('cart.html', cart_items=cart_items, total_items=total_items)

# Добавление товара в корзину
@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    product_id = request.form.get('product_id')
    quantity = request.form.get('quantity', 1)
    
    try:
        product_id = int(product_id)
        quantity = int(quantity)
    except (ValueError, TypeError):
        flash('Неверные данные')
        return redirect(url_for('index'))
    
    product = Product.query.get(product_id)
    if not product:
        flash('Товар не найден')
        return redirect(url_for('index'))
    
    if quantity <= 0:
        flash('Количество должно быть положительным')
        return redirect(url_for('index'))
    
    if quantity > product.quantity:
        flash(f'Недостаточно товара на складе. Доступно: {product.quantity}')
        return redirect(url_for('index'))
    
    if 'cart' not in session:
        session['cart'] = {}
    
    cart = session['cart']
    current_quantity = cart.get(str(product_id), 0)
    
    if current_quantity + quantity > product.quantity:
        flash(f'Нельзя добавить больше, чем есть на складе. Уже в корзине: {current_quantity}')
        return redirect(url_for('index'))
    
    cart[str(product_id)] = current_quantity + quantity
    session['cart'] = cart
    session.modified = True
    
    flash(f'Товар "{product.name}" добавлен в корзину!')
    return redirect(url_for('index'))  # Перезагрузка страницы

# Удаление товара из корзины
@app.route('/remove_from_cart/<product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    
    if str(product_id) in cart:
        cart.pop(str(product_id))
        session['cart'] = cart
        session.modified = True
        flash('Товар удален из корзины')
    
    return redirect(url_for('view_cart'))

# Очистка корзины
@app.route('/clear_cart', methods=['POST'])
@login_required
def clear_cart():
    if 'cart' in session:
        session.pop('cart')
        flash('Корзина очищена')
    
    return redirect(url_for('view_cart'))

# Создание заказа
@app.route('/create_order', methods=['POST'])
@login_required
def create_order():
    if 'cart' not in session or not session['cart']:
        flash('Корзина пуста')
        return redirect(url_for('view_cart'))
    
    cart = session['cart']
    
    try:
        order = Order(status='неоплачен')
        db.session.add(order)
        
        for product_id_str, quantity in cart.items():
            product = Product.query.get(int(product_id_str))
            
            if not product:
                flash(f'Товар с ID {product_id_str} не найден')
                continue
            
            if product.quantity < quantity:
                flash(f'Недостаточно товара "{product.name}" на складе. Доступно: {product.quantity}')
                db.session.rollback()
                return redirect(url_for('view_cart'))
            
            order_item = OrderItem(order=order, product=product, quantity=quantity)
            db.session.add(order_item)
        
        db.session.commit()
        
        session.pop('cart', None)
        session.modified = True
        
        flash(f'Заказ №{order.id} успешно создан! Статус: {order.status}')
        return redirect(url_for('view_orders'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при создании заказа: {str(e)}')
        return redirect(url_for('view_cart'))

# Просмотр заказов
@app.route('/orders')
@login_required
def view_orders():
    page = request.args.get('page', 1, type=int)
    pagination = Order.query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False
    )
    orders = pagination.items
    
    return render_template('orders.html', orders=orders, pagination=pagination)

# Отметка заказа как оплаченного
@app.route('/mark_paid/<int:order_id>', methods=['POST'])
@login_required
def mark_paid(order_id):
    order = Order.query.get(order_id)
    
    if not order:
        flash('Заказ не найден')
        return redirect(url_for('view_orders'))
    
    if order.status == 'оплачен':
        flash('Заказ уже оплачен')
        return redirect(url_for('view_orders'))
    
    order.status = 'оплачен'
    
    for item in order.items:
        product = item.product
        product.quantity -= item.quantity
        
        if product.quantity < 0:
            product.quantity = 0
    
    db.session.commit()
    
    flash(f'Заказ №{order.id} отмечен как оплаченный. Количество товаров на складе обновлено.')
    return redirect(url_for('view_orders'))

# Профиль пользователя
@app.route('/profile')
@login_required
def profile():
    user = User.query.get(session['user_id'])
    
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='неоплачен').count()
    completed_orders = Order.query.filter_by(status='оплачен').count()
    
    return render_template('profile.html', 
                          user=user,
                          total_orders=total_orders,
                          pending_orders=pending_orders,
                          completed_orders=completed_orders)

# Маршрут для проверки состояния базы данных
@app.route('/check-db')
def check_db():
    """Проверка состояния базы данных"""
    user_count = User.query.count()
    product_count = Product.query.count()
    order_count = Order.query.count()
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Проверка БД</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            h1 {{ color: #333; }}
            .stats {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
            .stat-item {{ margin: 10px 0; font-size: 18px; }}
            .success {{ color: green; font-weight: bold; }}
            .warning {{ color: orange; }}
            .danger {{ color: red; }}
            .btn {{ 
                display: inline-block; 
                padding: 10px 20px; 
                background: #4CAF50; 
                color: white; 
                text-decoration: none; 
                border-radius: 4px; 
                margin-top: 20px;
            }}
            .btn:hover {{ background: #45a049; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Состояние базы данных</h1>
            <div class="stats">
                <div class="stat-item">👥 Пользователей: <span class="{'success' if user_count > 0 else 'danger'}">{user_count}</span></div>
                <div class="stat-item">📦 Товаров: <span class="{'success' if product_count >= 50 else 'warning'}">{product_count}</span></div>
                <div class="stat-item">📋 Заказов: <span class="{'success' if order_count >= 0 else 'warning'}">{order_count}</span></div>
            </div>
            
            <h2>Действия:</h2>
            <a href="/" class="btn">На главную</a>
            <a href="/login" class="btn">Войти в систему</a>
            
            <h2>Тестовые пользователи:</h2>
            <ul>
                <li><strong>admin</strong> / storekeeper123 (администратор)</li>
                <li><strong>ivanov</strong> / password123 (кладовщик)</li>
                <li><strong>petrov</strong> / secure456 (кладовщик)</li>
                <li><strong>sidorov</strong> / test789 (кладовщик)</li>
                <li><strong>manager</strong> / manager123 (кладовщик)</li>
            </ul>
        </div>
    </body>
    </html>
    """
# Редактирование аккаунта
@app.route('/edit_account', methods=['POST'])
@login_required
def edit_account():
    try:
        user = User.query.get(session['user_id'])
        
        if not user:
            flash('Пользователь не найден', 'error')
            return redirect(url_for('profile'))
        
        new_username = request.form.get('username', '').strip()
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        
        # Проверяем текущий пароль
        if not user.check_password(current_password):
            flash('Неверный текущий пароль', 'error')
            return redirect(url_for('profile'))
        
        # Проверяем логин
        if not new_username:
            flash('Логин не может быть пустым', 'error')
            return redirect(url_for('profile'))
        
        # Проверяем, не занят ли логин другим пользователем
        existing_user = User.query.filter(
            User.username == new_username,
            User.id != user.id
        ).first()
        
        if existing_user:
            flash('Этот логин уже занят другим пользователем', 'error')
            return redirect(url_for('profile'))
        
        # Обновляем логин
        user.username = new_username
        
        # Обновляем пароль, если он указан
        if new_password:
            # Проверяем длину пароля
            if len(new_password) < 6:
                flash('Пароль должен быть не менее 6 символов', 'error')
                return redirect(url_for('profile'))
            
            user.set_password(new_password)
        
        db.session.commit()
        
        # Обновляем данные в сессии
        session['username'] = user.username
        
        flash('Данные аккаунта успешно обновлены!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при обновлении данных: {str(e)}', 'error')
    
    return redirect(url_for('profile'))

# Удаление аккаунта
@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    try:
        user = User.query.get(session['user_id'])
        
        if not user:
            flash('Пользователь не найден', 'error')
            return redirect(url_for('index'))
        
        confirm_username = request.form.get('confirm_username', '').strip()
        
        if confirm_username != user.username:
            flash('Введенный логин не совпадает с вашим', 'error')
            return redirect(url_for('profile'))
        
        # Проверяем, не последний ли это пользователь
        total_users = User.query.count()
        
        if total_users <= 1:
            flash('Нельзя удалить последнего пользователя в системе', 'error')
            return redirect(url_for('profile'))
        
        # Если пользователь admin, проверяем есть ли другие админы
        if user.username == 'admin':
            other_admins = User.query.filter(
                User.username != 'admin',
                User.role == 'admin'
            ).count()
            if other_admins == 0:
                flash('Нельзя удалить последнего администратора', 'error')
                return redirect(url_for('profile'))
        
        username = user.username
        
        # Удаляем пользователя
        session.clear()
        db.session.delete(user)
        db.session.commit()
        
        flash(f'Аккаунт "{username}" успешно удален', 'success')
        return redirect(url_for('login'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении аккаунта: {str(e)}', 'error')
        return redirect(url_for('profile'))
    
# Маршрут для принудительной инициализации БД
@app.route('/init-db')
def init_db_route():
    """Принудительная инициализация базы данных"""
    try:
        init_database()
        return """
        <h1>База данных инициализирована</h1>
        <p>Тестовые данные созданы успешно!</p>
        <p><a href="/check-db">Проверить состояние БД</a></p>
        <p><a href="/">На главную</a></p>
        """
    except Exception as e:
        return f"<h1>Ошибка</h1><p>{str(e)}</p>"

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 ЗАПУСК ПРИЛОЖЕНИЯ ДЛЯ УПРАВЛЕНИЯ СКЛАДОМ")
    print("=" * 60)
    print("Сервер запущен: http://127.0.0.1:5000")
    print("Для проверки базы данных: http://127.0.0.1:5000/check-db")
    print("Для входа используйте: admin / storekeeper123")
    print("=" * 60)
    app.run(debug=True)