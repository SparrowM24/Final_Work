from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from models.models import db, User, Product, Order, OrderItem
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
import re
from functools import wraps
import math

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Инициализация БД (автоматически создаст таблицы при первом запуске)
with app.app_context():
    db.create_all()

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
        'fio': 'Иванов Иван Иванович',
        'group': 'ПИ-123'
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
    # Получаем первые ITEMS_PER_PAGE товаров
    products = Product.query.limit(app.config['ITEMS_PER_PAGE']).all()
    total_products = Product.query.count()
    
    # Количество товаров в корзине
    cart_count = sum(session.get('cart', {}).values()) if 'cart' in session else 0
    
    # Рассчитываем общее количество страниц
    total_pages = math.ceil(total_products / app.config['ITEMS_PER_PAGE'])
    
    return render_template('index.html', 
                         products=products,
                         total_pages=total_pages,
                         current_page=1,
                         cart_count=cart_count,
                         total_products=total_products)

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

# Удаление аккаунта
@app.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        user = User.query.get(session['user_id'])
        
        if user:
            total_users = User.query.count()
            
            if total_users > 1:
                session.clear()
                db.session.delete(user)
                db.session.commit()
                flash('Ваш аккаунт успешно удален')
                return redirect(url_for('login'))
            else:
                flash('Нельзя удалить последнего пользователя в системе')
                return redirect(url_for('index'))
    
    return render_template('delete_account.html')

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

# Удаление товара
@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get(product_id)
    
    if product:
        in_orders = OrderItem.query.filter_by(product_id=product_id).first()
        
        if in_orders:
            flash('Нельзя удалить товар, который есть в заказах')
        else:
            db.session.delete(product)
            db.session.commit()
            flash(f'Товар "{product.name}" удален')
    
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
        return jsonify({'error': 'Неверные данные'}), 400
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Товар не найден'}), 404
    
    if quantity <= 0:
        return jsonify({'error': 'Количество должно быть положительным'}), 400
    
    if quantity > product.quantity:
        return jsonify({'error': f'Недостаточно товара на складе. Доступно: {product.quantity}'}), 400
    
    if 'cart' not in session:
        session['cart'] = {}
    
    cart = session['cart']
    current_quantity = cart.get(str(product_id), 0)
    
    if current_quantity + quantity > product.quantity:
        return jsonify({'error': f'Нельзя добавить больше, чем есть на складе. Уже в корзине: {current_quantity}'}), 400
    
    cart[str(product_id)] = current_quantity + quantity
    session['cart'] = cart
    session.modified = True
    
    cart_total = sum(cart.values())
    
    return jsonify({
        'success': True, 
        'cart_total': cart_total,
        'product_name': product.name,
        'new_quantity': cart[str(product_id)]
    })

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

if __name__ == '__main__':
    app.run(debug=True)

