#!/usr/bin/env python3
"""
Skrypt do utworzenia użytkownika admin
"""
import sys
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.utils.security import get_password_hash

# Utworzenie tabel
Base.metadata.create_all(bind=engine)


def create_admin(username: str, password: str):
    """Utworzenie użytkownika admin"""
    db: Session = SessionLocal()
    
    try:
        # Sprawdzenie czy użytkownik już istnieje
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"Użytkownik {username} już istnieje!")
            return
        
        # Utworzenie użytkownika
        hashed_password = get_password_hash(password)
        admin_user = User(
            username=username,
            password_hash=hashed_password,
            role=UserRole.ADMIN
        )
        db.add(admin_user)
        db.commit()
        print(f"Utworzono użytkownika admin: {username}")
        
    except Exception as e:
        print(f"Błąd: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Użycie: python create_admin.py <username> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    create_admin(username, password)

