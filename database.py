from app import app, db
from models.models import User, Product
from werkzeug.security import generate_password_hash

def init_db():
    """Инициализация базы данных"""
    with app.app_context():
        # Создаем таблицы
        print("Создаю таблицы базы данных...")
        db.create_all()
        
        # Создаем пользователей
        create_users()
        
        # Создаем товары
        create_products()
        
        print("✓ База данных успешно инициализирована!")
        print_summary()

def create_users():
    """Создание пользователей"""
    users = [
        ("admin", "storekeeper123", "admin"),
        ("ivanov", "password123", "storekeeper"),
        ("petrov", "secure456", "storekeeper"),
        ("sidorov", "test789", "storekeeper")
    ]
    
    print("Создаю пользователей...")
    for username, password, role in users:
        if not User.query.filter_by(username=username).first():
            user = User(username=username, role=role)
            user.set_password(password)
            db.session.add(user)
            print(f"  ✓ {username}")
    
    db.session.commit()

def create_products():
    """Создание 10 товаров для каталога"""
    products = [
        ("RF-1001", "Холодильник Samsung RB33", 15),
        ("WM-2001", "Стиральная машина Bosch WAN28281", 22),
        ("ST-3001", "Электрическая плита Gorenje EC 5121 WG", 11),
        ("MW-4001", "Микроволновая печь Samsung MS23K3515AK", 28),
        ("VC-5001", "Пылесос Samsung VCC4520S36", 20),
        ("KT-6001", "Электрочайник Bosch TWK 3P413", 35),
        ("CF-7001", "Кофемашина De'Longhi ECAM 22.110", 5),
        ("IR-8001", "Утюг Philips GC4523", 27),
        ("AC-9001", "Кондиционер Ballu BSW-07HN1", 6),
        ("DW-0010", "Посудомоечная машина Bosch SMS 4HVI33E", 9)
    ]
    
    print("Создаю товары...")
    created = 0
    for article, name, quantity in products:
        if not Product.query.filter_by(article=article).first():
            product = Product(article=article, name=name, quantity=quantity)
            db.session.add(product)
            created += 1
            print(f"  ✓ {article}: {name} ({quantity} шт.)")
    
    db.session.commit()
    
    if created == 0:
        print("  Все товары уже существуют в базе")
    else:
        print(f"✓ Создано {created} товаров")

def print_summary():
    """Вывод итоговой информации"""
    with app.app_context():
        users_count = User.query.count()
        products_count = Product.query.count()
        
        print("\n" + "="*60)
        print("ИТОГИ СОЗДАНИЯ БАЗЫ ДАННЫХ")
        print("="*60)
        print(f"👥 Пользователей: {users_count}")
        print(f"📦 Товаров: {products_count}")
        
        if products_count > 0:
            print("\n📋 Список всех товаров:")
            print("-" * 60)
            all_products = Product.query.all()
            for i, product in enumerate(all_products, 1):
                print(f"{i:2}. {product.article} - {product.name} ({product.quantity} шт.)")
        
        print("\n🔐 ДАННЫЕ ДЛЯ ВХОДА:")
        print("-" * 40)
        print("admin / storekeeper123 (администратор)")
        print("ivanov / password123 (кладовщик)")
        print("petrov / secure456 (кладовщик)")
        print("sidorov / test789 (кладовщик)")
        print("="*60)

if __name__ == "__main__":
    try:
        print("="*60)
        print("ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ДЛЯ СКЛАДА")
        print("="*60)
        init_db()
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        print("\nВозможные причины:")
        print("1. Файл базы данных заблокирован - закройте приложение Flask")
        print("2. Проблемы с импортами - проверьте структуру файлов")
        print("3. Нет прав на запись - проверьте права доступа к папке")