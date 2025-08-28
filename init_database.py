import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from src.main import app
from src.models.user import db, User, Invitation
from datetime import datetime

def init_database():
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        
        # Verificar si el Usuario Cero ya existe
        admin_user = User.query.filter_by(phone_number='+34670709259').first()
        
        if not admin_user:
            # Crear Usuario Cero (admin)
            admin_user = User(
                phone_number='+34670709259',
                is_verified=True,
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Usuario Cero creado exitosamente")
        else:
            print("Usuario Cero ya existe")
        
        # Verificar si la invitación inicial ya existe
        initial_invitation = Invitation.query.filter_by(code='MI_PRIMERA_INVITACION').first()
        
        if not initial_invitation:
            # Crear invitación inicial
            initial_invitation = Invitation(
                code='MI_PRIMERA_INVITACION',
                created_by=admin_user.id,
                is_active=True
            )
            db.session.add(initial_invitation)
            db.session.commit()
            print("Invitación inicial creada exitosamente")
        else:
            print("Invitación inicial ya existe")
        
        print("Base de datos inicializada correctamente")

if __name__ == '__main__':
    init_database()
