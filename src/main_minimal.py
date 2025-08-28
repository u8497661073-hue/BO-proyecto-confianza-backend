#!/usr/bin/env python3
"""
ProConfianza Backend - Versión Mínima
Backend mínimo para verificar que Render funciona correctamente
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import random
import string

app = Flask(__name__)
CORS(app)

# Datos en memoria para pruebas
users_db = {
    "+34670709259": {
        "phone": "+34670709259",
        "is_admin": True,
        "name": "Usuario Cero",
        "created_at": "2025-08-28"
    }
}

invitations_db = {
    "MI_PRIMERA_INVITACION": {
        "code": "MI_PRIMERA_INVITACION",
        "is_used": False,
        "created_by": "+34670709259"
    }
}

# Códigos de verificación temporales (en memoria)
verification_codes = {}

def generate_verification_code():
    """Genera un código de verificación de 6 dígitos"""
    return ''.join(random.choices(string.digits, k=6))

@app.route('/', methods=['GET'])
def health_check():
    """Endpoint de verificación de salud"""
    return jsonify({
        "status": "ok",
        "message": "ProConfianza Backend está funcionando",
        "version": "1.0.0-minimal"
    })

@app.route('/api/health', methods=['GET'])
def api_health():
    """Endpoint de salud de la API"""
    return jsonify({
        "status": "healthy",
        "service": "ProConfianza API",
        "users_count": len(users_db),
        "invitations_count": len(invitations_db)
    })

@app.route('/api/verify-invitation', methods=['POST'])
def verify_invitation():
    """Verifica si un código de invitación es válido"""
    try:
        data = request.get_json()
        invitation_code = data.get('invitation_code', '').strip().upper()
        
        if not invitation_code:
            return jsonify({
                "success": False,
                "message": "Código de invitación requerido"
            }), 400
        
        # Verificar si el código existe y no ha sido usado
        if invitation_code in invitations_db:
            invitation = invitations_db[invitation_code]
            if not invitation['is_used']:
                return jsonify({
                    "success": True,
                    "message": "Código de invitación válido",
                    "invitation_code": invitation_code
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "Este código de invitación ya ha sido utilizado"
                }), 400
        else:
            return jsonify({
                "success": False,
                "message": "Código de invitación no válido"
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error interno del servidor: {str(e)}"
        }), 500

@app.route('/api/send-verification', methods=['POST'])
def send_verification():
    """Envía un código de verificación por SMS (simulado)"""
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        invitation_code = data.get('invitation_code', '').strip().upper()
        
        if not phone or not invitation_code:
            return jsonify({
                "success": False,
                "message": "Teléfono y código de invitación requeridos"
            }), 400
        
        # Verificar que la invitación sea válida
        if invitation_code not in invitations_db or invitations_db[invitation_code]['is_used']:
            return jsonify({
                "success": False,
                "message": "Código de invitación no válido o ya utilizado"
            }), 400
        
        # Generar código de verificación
        verification_code = generate_verification_code()
        verification_codes[phone] = {
            "code": verification_code,
            "invitation_code": invitation_code,
            "attempts": 0
        }
        
        # Simular envío de SMS (en logs)
        print(f"📱 SMS SIMULADO para {phone}: Tu código de verificación es {verification_code}")
        
        return jsonify({
            "success": True,
            "message": f"Código de verificación enviado a {phone}",
            "phone": phone
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error interno del servidor: {str(e)}"
        }), 500

@app.route('/api/verify-code', methods=['POST'])
def verify_code():
    """Verifica el código de verificación SMS"""
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        code = data.get('code', '').strip()
        
        if not phone or not code:
            return jsonify({
                "success": False,
                "message": "Teléfono y código requeridos"
            }), 400
        
        # Verificar si existe un código para este teléfono
        if phone not in verification_codes:
            return jsonify({
                "success": False,
                "message": "No se encontró código de verificación para este teléfono"
            }), 400
        
        verification_data = verification_codes[phone]
        
        # Verificar el código
        if verification_data['code'] == code:
            # Código correcto - crear/actualizar usuario
            invitation_code = verification_data['invitation_code']
            
            # Marcar invitación como usada
            invitations_db[invitation_code]['is_used'] = True
            
            # Crear o actualizar usuario
            users_db[phone] = {
                "phone": phone,
                "is_admin": phone == "+34670709259",
                "name": "Usuario Cero" if phone == "+34670709259" else f"Usuario {phone[-4:]}",
                "created_at": "2025-08-28",
                "invitation_used": invitation_code
            }
            
            # Limpiar código de verificación
            del verification_codes[phone]
            
            return jsonify({
                "success": True,
                "message": "Verificación exitosa",
                "user": users_db[phone]
            })
        else:
            # Código incorrecto
            verification_data['attempts'] += 1
            if verification_data['attempts'] >= 3:
                del verification_codes[phone]
                return jsonify({
                    "success": False,
                    "message": "Demasiados intentos fallidos. Solicita un nuevo código."
                }), 400
            
            return jsonify({
                "success": False,
                "message": f"Código incorrecto. Intentos restantes: {3 - verification_data['attempts']}"
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error interno del servidor: {str(e)}"
        }), 500

@app.route('/api/user/<phone>', methods=['GET'])
def get_user(phone):
    """Obtiene información de un usuario"""
    try:
        if phone in users_db:
            return jsonify({
                "success": True,
                "user": users_db[phone]
            })
        else:
            return jsonify({
                "success": False,
                "message": "Usuario no encontrado"
            }), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error interno del servidor: {str(e)}"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

