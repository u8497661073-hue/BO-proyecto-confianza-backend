from flask import Blueprint, jsonify, request
from src.models.user import User, Invitation, VerificationCode, db
from datetime import datetime, timedelta
import random
import re

auth_bp = Blueprint('auth', __name__)

def generate_verification_code():
    """Genera un código de verificación de 6 dígitos"""
    return str(random.randint(100000, 999999))

def is_valid_phone_number(phone):
    """Valida el formato del número de teléfono"""
    # Acepta números con formato +34XXXXXXXXX
    pattern = r'^\+34\d{9}$'
    return re.match(pattern, phone) is not None

@auth_bp.route('/check-invitation', methods=['POST'])
def check_invitation():
    """Verifica si un código de invitación es válido"""
    try:
        data = request.json
        invitation_code = data.get('invitation_code', '').strip()
        
        if not invitation_code:
            return jsonify({'error': 'Código de invitación requerido'}), 400
        
        # Buscar la invitación
        invitation = Invitation.query.filter_by(code=invitation_code, is_active=True).first()
        
        if not invitation:
            return jsonify({'error': 'Código de invitación inválido'}), 400
        
        if invitation.used_by:
            return jsonify({'error': 'Código de invitación ya utilizado'}), 400
        
        return jsonify({
            'valid': True,
            'message': 'Código de invitación válido'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@auth_bp.route('/send-verification', methods=['POST'])
def send_verification():
    """Envía un código de verificación por SMS"""
    try:
        data = request.json
        phone_number = data.get('phone_number', '').strip()
        invitation_code = data.get('invitation_code', '').strip()
        
        if not phone_number or not invitation_code:
            return jsonify({'error': 'Número de teléfono y código de invitación requeridos'}), 400
        
        if not is_valid_phone_number(phone_number):
            return jsonify({'error': 'Formato de número de teléfono inválido'}), 400
        
        # Verificar que la invitación sea válida
        invitation = Invitation.query.filter_by(code=invitation_code, is_active=True).first()
        if not invitation or invitation.used_by:
            return jsonify({'error': 'Código de invitación inválido o ya utilizado'}), 400
        
        # Verificar si el usuario ya existe
        existing_user = User.query.filter_by(phone_number=phone_number).first()
        if existing_user:
            return jsonify({'error': 'Este número de teléfono ya está registrado'}), 400
        
        # Generar código de verificación
        verification_code = generate_verification_code()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Eliminar códigos anteriores para este número
        VerificationCode.query.filter_by(phone_number=phone_number).delete()
        
        # Crear nuevo código de verificación
        new_verification = VerificationCode(
            phone_number=phone_number,
            code=verification_code,
            expires_at=expires_at
        )
        
        db.session.add(new_verification)
        db.session.commit()
        
        # TODO: Aquí se enviaría el SMS real
        # Por ahora, devolvemos el código en la respuesta para testing
        print(f"Código de verificación para {phone_number}: {verification_code}")
        
        return jsonify({
            'message': 'Código de verificación enviado',
            'verification_code': verification_code  # Solo para testing, remover en producción
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@auth_bp.route('/verify-code', methods=['POST'])
def verify_code():
    """Verifica el código de verificación y crea el usuario"""
    try:
        data = request.json
        phone_number = data.get('phone_number', '').strip()
        verification_code = data.get('verification_code', '').strip()
        invitation_code = data.get('invitation_code', '').strip()
        
        if not phone_number or not verification_code or not invitation_code:
            return jsonify({'error': 'Todos los campos son requeridos'}), 400
        
        # Buscar el código de verificación
        verification = VerificationCode.query.filter_by(
            phone_number=phone_number,
            code=verification_code,
            is_used=False
        ).first()
        
        if not verification:
            return jsonify({'error': 'Código de verificación inválido'}), 400
        
        if verification.expires_at < datetime.utcnow():
            return jsonify({'error': 'Código de verificación expirado'}), 400
        
        # Verificar la invitación
        invitation = Invitation.query.filter_by(code=invitation_code, is_active=True).first()
        if not invitation or invitation.used_by:
            return jsonify({'error': 'Código de invitación inválido o ya utilizado'}), 400
        
        # Crear el usuario
        new_user = User(
            phone_number=phone_number,
            is_verified=True,
            invited_by=invitation.created_by,
            invitation_code_used=invitation_code
        )
        
        db.session.add(new_user)
        
        # Marcar la invitación como usada
        invitation.used_by = new_user.id
        invitation.used_at = datetime.utcnow()
        invitation.is_active = False
        
        # Marcar el código de verificación como usado
        verification.is_used = True
        
        db.session.commit()
        
        return jsonify({
            'message': 'Usuario creado exitosamente',
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Inicia sesión con número de teléfono"""
    try:
        data = request.json
        phone_number = data.get('phone_number', '').strip()
        
        if not phone_number:
            return jsonify({'error': 'Número de teléfono requerido'}), 400
        
        if not is_valid_phone_number(phone_number):
            return jsonify({'error': 'Formato de número de teléfono inválido'}), 400
        
        # Buscar el usuario
        user = User.query.filter_by(phone_number=phone_number, is_verified=True).first()
        
        if not user:
            return jsonify({'error': 'Usuario no encontrado o no verificado'}), 404
        
        return jsonify({
            'message': 'Login exitoso',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

