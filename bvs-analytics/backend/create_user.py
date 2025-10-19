"""
Скрипт для создания пользователей в системе BVS Analytics
"""
import sys
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.auth import User
from app.api.auth import get_password_hash

def create_user(username: str, password: str, email: str = None, role: int = 1, 
                first_name: str = None, last_name: str = None, patronymic: str = None):
    """
    Создает нового пользователя
    
    Args:
        username: Имя пользователя (логин)
        password: Пароль (будет захеширован)
        email: Email (опционально)
        role: Роль (0 - нет доступа, 1 - пользователь, 2 - админ)
        first_name: Имя
        last_name: Фамилия
        patronymic: Отчество
    """
    db = SessionLocal()
    try:
        # Проверяем, существует ли пользователь
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"❌ Пользователь '{username}' уже существует!")
            return False
        
        # Создаем нового пользователя
        hashed_password = get_password_hash(password)
        new_user = User(
            username=username,
            password=hashed_password,
            email=email,
            role=role,
            first_name=first_name,
            last_name=last_name,
            patronymic=patronymic
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        role_name = {0: "нет доступа", 1: "пользователь", 2: "администратор"}
        print(f"✅ Пользователь '{username}' успешно создан!")
        print(f"   ID: {new_user.user_id}")
        print(f"   Роль: {role_name.get(role, 'неизвестно')}")
        if email:
            print(f"   Email: {email}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при создании пользователя: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def list_users():
    """Выводит список всех пользователей"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        if not users:
            print("📋 Пользователей в системе нет")
            return
        
        print(f"\n📋 Список пользователей ({len(users)}):")
        print("-" * 80)
        role_name = {0: "нет доступа", 1: "пользователь", 2: "администратор"}
        
        for user in users:
            print(f"ID: {user.user_id}")
            print(f"  Логин: {user.username}")
            print(f"  Роль: {role_name.get(user.role, 'неизвестно')}")
            if user.email:
                print(f"  Email: {user.email}")
            if user.first_name or user.last_name:
                full_name = f"{user.last_name or ''} {user.first_name or ''} {user.patronymic or ''}".strip()
                print(f"  ФИО: {full_name}")
            print("-" * 80)
            
    except Exception as e:
        print(f"❌ Ошибка при получении списка пользователей: {e}")
    finally:
        db.close()


def delete_user(username: str):
    """Удаляет пользователя"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            print(f"❌ Пользователь '{username}' не найден!")
            return False
        
        db.delete(user)
        db.commit()
        print(f"✅ Пользователь '{username}' успешно удален!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при удалении пользователя: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """Главная функция с интерактивным меню"""
    # Создаем таблицы, если их нет
    Base.metadata.create_all(bind=engine)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            list_users()
        
        elif command == "create":
            if len(sys.argv) < 4:
                print("Использование: python create_user.py create <username> <password> [role] [email]")
                print("Роли: 0 - нет доступа, 1 - пользователь (по умолчанию), 2 - администратор")
                return
            
            username = sys.argv[2]
            password = sys.argv[3]
            role = int(sys.argv[4]) if len(sys.argv) > 4 else 1
            email = sys.argv[5] if len(sys.argv) > 5 else None
            
            create_user(username, password, email, role)
        
        elif command == "delete":
            if len(sys.argv) < 3:
                print("Использование: python create_user.py delete <username>")
                return
            
            username = sys.argv[2]
            delete_user(username)
        
        elif command == "init":
            # Создаем тестовых пользователей
            print("🔧 Инициализация тестовых пользователей...")
            create_user("admin", "admin123", "admin@bvs.ru", role=2, 
                       first_name="Администратор", last_name="Системы")
            create_user("user", "user123", "user@bvs.ru", role=1,
                       first_name="Тестовый", last_name="Пользователь")
            print("\n✅ Тестовые пользователи созданы!")
            print("\nДанные для входа:")
            print("  Администратор: admin / admin123")
            print("  Пользователь: user / user123")
        
        else:
            print(f"❌ Неизвестная команда: {command}")
            print_help()
    else:
        print_help()


def print_help():
    """Выводит справку"""
    print("""
🔐 Управление пользователями BVS Analytics

Использование:
  python create_user.py <команда> [параметры]

Команды:
  init                              - Создать тестовых пользователей (admin/user)
  list                              - Показать список всех пользователей
  create <username> <password> [role] [email] - Создать нового пользователя
  delete <username>                 - Удалить пользователя

Роли:
  0 - нет доступа
  1 - пользователь (по умолчанию)
  2 - администратор

Примеры:
  python create_user.py init
  python create_user.py list
  python create_user.py create admin password123 2 admin@example.com
  python create_user.py create user password123 1
  python create_user.py delete testuser
""")


if __name__ == "__main__":
    main()
