import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import random
import string

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS for all routes
CORS(app)

# Datos temporales en memoria (sin base de datos)
users_data = {
    "+34670709259": {
        "phone": "+34670709259",
        "is_admin": True,
        "verified": True
    }
}

invitations_data = {
    "MI_PRIMERA_INVITACION": {
        "code": "MI_PRIMERA_INVITACION",
        "is_used": False,
        "created_by": "+34670709259"
    }
}

verification_codes = {}

def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "ProConfianza Backend is running!"})

@app.route('/api/verify-invitation', methods=['POST'])
def verify_invitation():
    data = request.get_json()
    invitation_code = data.get('invitation_code', '').strip().upper()
    
    if not invitation_code:
        return jsonify({"error": "Código de invitación requerido"}), 400
    
    if invitation_code in invitations_data and not invitations_data[invitation_code]["is_used"]:
        return jsonify({"valid": True, "message": "Código de invitación válido"})
    else:
        return jsonify({"valid": False, "message": "Código de invitación inválido o ya usado"}), 400

@app.route('/api/send-verification', methods=['POST'])
def send_verification():
    data = request.get_json()
    phone = data.get('phone', '').strip()
    invitation_code = data.get('invitation_code', '').strip().upper()
    
    if not phone or not invitation_code:
        return jsonify({"error": "Teléfono y código de invitación requeridos"}), 400
    
    # Verificar código de invitación
    if invitation_code not in invitations_data or invitations_data[invitation_code]["is_used"]:
        return jsonify({"error": "Código de invitación inválido o ya usado"}), 400
    
    # Generar código de verificación
    verification_code = generate_verification_code()
    verification_codes[phone] = verification_code
    
    # Simular envío de SMS (en producción aquí iría la integración con un servicio de SMS)
    print(f"SMS enviado a {phone}: Tu código de verificación es {verification_code}")
    
    return jsonify({"message": "Código de verificación enviado", "phone": phone})

@app.route('/api/verify-code', methods=['POST'])
def verify_code():
    data = request.get_json()
    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()
    invitation_code = data.get('invitation_code', '').strip().upper()
    
    if not phone or not code or not invitation_code:
        return jsonify({"error": "Teléfono, código y código de invitación requeridos"}), 400
    
    # Verificar código de verificación
    if phone not in verification_codes or verification_codes[phone] != code:
        return jsonify({"error": "Código de verificación incorrecto"}), 400
    
    # Verificar código de invitación
    if invitation_code not in invitations_data or invitations_data[invitation_code]["is_used"]:
        return jsonify({"error": "Código de invitación inválido o ya usado"}), 400
    
    # Marcar invitación como usada
    invitations_data[invitation_code]["is_used"] = True
    
    # Crear o actualizar usuario
    users_data[phone] = {
        "phone": phone,
        "is_admin": phone == "+34670709259",
        "verified": True,
        "invitation_used": invitation_code
    }
    
    # Limpiar código de verificación
    del verification_codes[phone]
    
    return jsonify({
        "message": "Verificación exitosa",
        "user": users_data[phone]
    })

@app.route('/api/user-info', methods=['POST'])
def get_user_info():
    data = request.get_json()
    phone = data.get('phone', '').strip()
    
    if not phone:
        return jsonify({"error": "Teléfono requerido"}), 400
    
    if phone in users_data:
        return jsonify({"user": users_data[phone]})
    else:
        return jsonify({"error": "Usuario no encontrado"}), 404

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return jsonify({
                "message": "ProConfianza Backend API",
                "status": "running",
                "endpoints": [
                    "/api/health",
                    "/api/verify-invitation",
                    "/api/send-verification",
                    "/api/verify-code",
                    "/api/user-info"
                ]
            })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

