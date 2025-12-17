from app import app, db
from models.models import User, Product, Order, OrderItem

def check_database():
    """Проверка текущего состояния базы данных"""
    with app.app_context():
        try:
            users_count = User.query.count()
            products_count = Product.query.count()
            orders_count = Order.query.count()
            
            print("=" * 60)
            print("ПРОВЕРКА СОСТОЯНИЯ БАЗЫ ДАННЫХ")
            print("=" * 60)
            print(f"👥 Пользователей: {users_count}")
            print(f"📦 Товаров: {products_count}")
            print(f"📋 Заказов: {orders_count}")
            
            # Выводим первых 5 пользователей
            if users_count > 0:
                print("\n📋 Первые 5 пользователей:")
                print("-" * 40)
                users = User.query.limit(5).all()
                for i, user in enumerate(users, 1):
                    print(f"{i}. {user.username} ({user.role})")
            
            # Выводим первые 5 товаров
            if products_count > 0:
                print("\n📦 Первые 5 товаров:")
                print("-" * 40)
                products = Product.query.limit(5).all()
                for i, product in enumerate(products, 1):
                    print(f"{i}. {product.article} - {product.name} ({product.quantity} шт.)")
            
            # Выводим первые 5 заказов
            if orders_count > 0:
                print("\n📋 Первые 5 заказов:")
                print("-" * 40)
                orders = Order.query.limit(5).all()
                for i, order in enumerate(orders, 1):
                    print(f"{i}. Заказ #{order.id} - {order.status}")
            
            print("\n" + "=" * 60)
            
            # Даем рекомендации
            if users_count == 0:
                print("⚠️  РЕКОМЕНДАЦИЯ: В базе нет пользователей!")
                print("   Запустите приложение Flask - оно автоматически создаст тестовых пользователей")
            
            if products_count == 0:
                print("⚠️  РЕКОМЕНДАЦИЯ: В базе нет товаров!")
                print("   Запустите приложение Flask - оно автоматически создаст 50 тестовых товаров")
                
        except Exception as e:
            print(f"❌ Ошибка при проверке базы данных: {e}")
            print("   Возможно, таблицы еще не созданы.")
            print("   Запустите приложение Flask для создания таблиц.")

def reset_database():
    """Очистка всей базы данных (осторожно!)"""
    with app.app_context():
        try:
            print("=" * 60)
            print("⚠️  ОПАСНАЯ ОПЕРАЦИЯ: ОЧИСТКА БАЗЫ ДАННЫХ")
            print("=" * 60)
            
            # Подсчитываем данные перед удалением
            users_count = User.query.count()
            products_count = Product.query.count()
            orders_count = Order.query.count()
            
            print(f"Будет удалено:")
            print(f"  👥 Пользователей: {users_count}")
            print(f"  📦 Товаров: {products_count}")
            print(f"  📋 Заказов: {orders_count}")
            
            confirmation = input("\nВведите 'ДА' для подтверждения удаления: ")
            
            if confirmation == 'ДА':
                print("\n🧹 Удаляю данные...")
                
                # Удаляем в правильном порядке из-за внешних ключей
                OrderItem.query.delete()
                Order.query.delete()
                Product.query.delete()
                User.query.delete()
                
                db.session.commit()
                print("✅ База данных очищена!")
                print("\nℹ️  Теперь запустите приложение Flask для создания новых данных.")
            else:
                print("❌ Операция отменена")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Ошибка при очистке базы: {e}")

def backup_database():
    """Создание резервной копии данных в текстовом формате"""
    import os
    from datetime import datetime
    
    with app.app_context():
        try:
            # Создаем имя файла с датой
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_{timestamp}.txt"
            
            print(f"📋 Создаю резервную копию в файл: {filename}")
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("РЕЗЕРВНАЯ КОПИЯ БАЗЫ ДАННЫХ СКЛАДА\n")
                f.write(f"Дата создания: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")
                
                # Пользователи
                users = User.query.all()
                f.write("👥 ПОЛЬЗОВАТЕЛИ:\n")
                f.write("-" * 40 + "\n")
                for user in users:
                    f.write(f"  {user.id}. {user.username} ({user.role})\n")
                f.write(f"Всего: {len(users)} пользователей\n\n")
                
                # Товары
                products = Product.query.all()
                f.write("📦 ТОВАРЫ:\n")
                f.write("-" * 40 + "\n")
                for product in products:
                    f.write(f"  {product.id}. {product.article} - {product.name} ({product.quantity} шт.)\n")
                f.write(f"Всего: {len(products)} товаров\n\n")
                
                # Заказы
                orders = Order.query.all()
                f.write("📋 ЗАКАЗЫ:\n")
                f.write("-" * 40 + "\n")
                for order in orders:
                    f.write(f"  Заказ #{order.id} - {order.status} ({order.created_at})\n")
                f.write(f"Всего: {len(orders)} заказов\n")
                
            print(f"✅ Резервная копия создана успешно!")
            print(f"   Файл: {filename}")
            print(f"   Размер: {os.path.getsize(filename)} байт")
            
        except Exception as e:
            print(f"❌ Ошибка при создании резервной копии: {e}")

def repair_database():
    """Попытка восстановления базы данных"""
    with app.app_context():
        try:
            print("🔧 Проверяю и восстанавливаю базу данных...")
            
            # Создаем таблицы, если их нет
            db.create_all()
            print("✅ Таблицы проверены/созданы")
            
            # Проверяем подключение
            test_query = db.session.query(User).first()
            print("✅ Подключение к базе данных работает")
            
            print("\n✅ База данных в порядке!")
            
        except Exception as e:
            print(f"❌ Ошибка при восстановлении базы: {e}")

def show_menu():
    """Отображение меню утилиты"""
    print("=" * 60)
    print("УТИЛИТА ДЛЯ УПРАВЛЕНИЯ БАЗОЙ ДАННЫХ СКЛАДА")
    print("=" * 60)
    print("\nВыберите действие:")
    print("1. Проверить состояние базы данных")
    print("2. Создать резервную копию")
    print("3. Восстановить/проверить базу данных")
    print("4. Очистить всю базу данных (опасно!)")
    print("5. Выйти")
    
    choice = input("\nВаш выбор (1-5): ").strip()
    
    if choice == '1':
        check_database()
    elif choice == '2':
        backup_database()
    elif choice == '3':
        repair_database()
    elif choice == '4':
        reset_database()
    elif choice == '5':
        print("Выход...")
        return False
    else:
        print("❌ Неверный выбор. Попробуйте снова.")
    
    input("\nНажмите Enter для продолжения...")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 ЗАПУСК УТИЛИТЫ ДЛЯ УПРАВЛЕНИЯ БАЗОЙ ДАННЫХ")
    print("=" * 60)
    print("ℹ️  Основные данные создаются автоматически при запуске app.py")
    print("ℹ️  Эта утилита только проверяет и управляет существующей БД")
    print("=" * 60)
    
    try:
        while show_menu():
            pass
    except KeyboardInterrupt:
        print("\n\nЗавершение работы...")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")