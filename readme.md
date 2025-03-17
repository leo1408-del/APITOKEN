# Generador de Tokens OAuth 2.0 para Google Workspace

Esta documentación detalla el proceso completo para configurar una cuenta de servicio en Google Cloud, desarrollar una API en Flask para generar tokens OAuth 2.0, desplegarla en Render y consumirla desde clientes HTTP como Thunder Client o Postman.

---

## 1. Configuración en Google Cloud

### 1.1. Crear una Cuenta de Servicio

1. **Accede** a la [Google Cloud Console](https://console.cloud.google.com/).
2. **Navega** a **IAM y administración > Cuentas de servicio**.
3. **Crea** una nueva cuenta de servicio:
   - **Nombre**: `workspace-prueba`
4. **Activa** la **Delegación en todo el dominio**.
5. **Descarga** el archivo JSON con las credenciales de la cuenta de servicio.

### 1.2. Otorgar el Rol de Propietario a la Cuenta de Servicio

Para que la cuenta de servicio tenga permisos completos en el proyecto:

1. **Navega** a **IAM y administración > IAM** en la Google Cloud Console.
2. **Haz clic** en **"Añadir"** para agregar un nuevo miembro.
3. **Introduce** el **email** de la cuenta de servicio.
4. **Selecciona** el rol de **Propietario**.
5. **Guarda** los cambios.

_Nota:_ Otorgar el rol de **Propietario** proporciona permisos completos en el proyecto. Asegúrate de que esto sea adecuado para tu caso de uso.

### 1.3. Delegar Permisos en Google Workspace Admin

1. **Accede** al [Panel de Administración de Google Workspace](https://admin.google.com/).
2. **Navega** a **Seguridad > Acceso y control de API > Delegación en todo el dominio**.
3. **Añade** el **ID de cliente** de la cuenta de servicio.
4. **Otorga** los siguientes **alcances (scopes)**:

   ```
   https://www.googleapis.com/auth/admin.directory.user
   ```

---

## 2. Desarrollo de la API en Flask

### 2.1. Instalación de Dependencias

Ejecuta el siguiente comando para instalar las librerías necesarias:

```bash
pip install Flask Flask-Cors pyjwt google-auth requests gunicorn
```

**NOTA:** Genera un "requiriments.txt" para el despliegue.

### 2.2. Código de la API

```python
from flask import Flask, jsonify, request
from flask_cors import CORS
import jwt
import time
from google.oauth2 import service_account
import requests

app = Flask(__name__)
CORS(app)

@app.route('/get-token', methods=['POST'])
def get_token():
    try:
        data = request.json

        if 'service_account_json' not in data:
            return jsonify({"error": "Se requiere el archivo JSON de la cuenta de servicio"}), 400

        service_account_info = data['service_account_json']
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/admin.directory.user']
        )

        iss = data.get('iss')
        sub = data.get('sub')
        exp_duration = data.get('exp_duration', 3600)

        if not iss or not sub:
            return jsonify({"error": "Se requieren 'iss' y 'sub' en el cuerpo de la solicitud"}), 400

        now = int(time.time())
        payload = {
            "iss": iss,
            "scope": "https://www.googleapis.com/auth/admin.directory.user",
            "aud": "https://oauth2.googleapis.com/token",
            "sub": sub,
            "iat": now,
            "exp": now + exp_duration
        }

        signed_jwt = jwt.encode(payload, credentials.signer.key, algorithm="RS256")

        token_url = "https://oauth2.googleapis.com/token"
        params = {
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'assertion': signed_jwt
        }
        response = requests.post(token_url, data=params)

        if response.status_code == 200:
            access_token = response.json().get('access_token')
            return jsonify({"access_token": access_token})
        else:
            return jsonify({"error": response.text}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
```

---

## 3. Despliegue en Render

### 3.1. Preparar Gunicorn para Producción

Crea un archivo `render.yaml` o configura el comando de inicio personalizado:

```bash
gunicorn nombre_de_tu_archivo:app --bind 0.0.0.0:$PORT
```

Ejemplo si tu archivo se llama `app.py`:

```bash
gunicorn app:app --bind 0.0.0.0:$PORT
```

Render detectará automáticamente el puerto desde la variable `$PORT`.

### 3.2. Desplegar en Render

1. **Sube** tu código a GitHub.
2. **Conecta** tu repositorio a Render.
3. **Configura** el entorno de despliegue:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
4. **Despliega** la aplicación.

Tu API estará disponible en una URL similar a:

```
https://apitoken-b8qk.onrender.com/get-token
```

---

## 4. Consumo del API desde Thunder Client o Postman

### 4.1. Petición

**POST** `https://apitoken-b8qk.onrender.com/get-token`

**Headers:**

```
Content-Type: application/json
```

**Body:**

```json
{
  "service_account_json": {
    "type": "service_account",
    "project_id": "pruebas-451320",
    "private_key_id": "...",
    "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
    "client_email": "workspace-prueba@pruebas-451320.iam.gserviceaccount.com",
    ...
  },
  "iss": "workspace-prueba@pruebas-451320.iam.gserviceaccount.com",
  "sub": "admin@TU-DOMINIO.COM",
  "exp_duration": 3600
}
```

### 4.2. Respuesta Esperada

```json
{
  "access_token": "ya29.a0AfH6SMC..."
}
```

**Errores Comunes:**

- Si envías datos incorrectos, puedes recibir:

  ```json
  {
    "error": "Incorrect padding"
  }
  ```

  Esto indica un formato incorrecto en el JSON o en la clave privada.

---

## 5. Uso del Token OAuth 2.0 en Google Workspace API

### Ejemplo para Listar Usuarios

**GET**

```
https://admin.googleapis.com/admin/directory/v1/users?domain=tu-dominio.com
```

**Headers:**

```
Authorization: Bearer {ACCESS_TOKEN}
```

---

## Resumen del Flujo Completo

1. Configurar la cuenta de servicio en Google Cloud.
2. Otorgar el rol de Propietario a la cuenta de servicio.
3. Delegar permisos en Google Workspace Admin.
4. Desarrollar la API en Flask para generar tokens.
5. Configurar Gunicorn para producción.
6. Desplegar la API en Render.
7. Consumir la API desde Thunder Client o Postman.
8. Utilizar el token para realizar peticiones autenticadas a Google Workspace.

---

✨ ¡Listo para integrarlo en tus proyectos! 🎉
