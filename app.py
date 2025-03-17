from flask import Flask, jsonify, request
from flask_cors import CORS  # Importar CORS
import jwt
import time
from google.oauth2 import service_account
import requests
import json

app = Flask(__name__)
CORS(app)  # Habilitar CORS para toda la aplicación

# Endpoint para obtener el token
@app.route('/get-token', methods=['POST'])
def get_token():
    try:
        # Obtener los datos del cuerpo de la solicitud
        data = request.json

        # Verificar que el usuario haya enviado el JSON de la cuenta de servicio
        if 'service_account_json' not in data:
            return jsonify({"error": "Se requiere el archivo JSON de la cuenta de servicio"}), 400

        # Cargar las credenciales desde el JSON proporcionado por el usuario
        service_account_info = data['service_account_json']
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/admin.directory.user']
        )

        # Obtener los datos adicionales del usuario (iss, sub, exp_duration)
        iss = data.get('iss')
        sub = data.get('sub')
        exp_duration = data.get('exp_duration', 3600)  # Tiempo de expiración en segundos (por defecto 1 hora)

        if not iss or not sub:
            return jsonify({"error": "Se requieren 'iss' y 'sub' en el cuerpo de la solicitud"}), 400

        # Preparar JWT
        now = int(time.time())
        payload = {
            "iss": iss,
            "scope": "https://www.googleapis.com/auth/admin.directory.user",
            "aud": "https://oauth2.googleapis.com/token",
            "sub": sub,
            "iat": now,
            "exp": now + exp_duration
        }

        # Firmar JWT
        signed_jwt = jwt.encode(payload, credentials.signer.key, algorithm="RS256")

        # Solicitar el token de acceso
        token_url = "https://oauth2.googleapis.com/token"
        params = {
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'assertion': signed_jwt
        }
        response = requests.post(token_url, data=params)

        # Devolver el token
        if response.status_code == 200:
            access_token = response.json().get('access_token')
            return jsonify({"access_token": access_token})
        else:
            return jsonify({"error": response.text}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)