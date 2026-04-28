"""
correcciones.py — Obtiene sugerencias de corrección usando Azure OpenAI.
Usa la REST API directamente con 'requests' (sin SDK adicional).

Variables de entorno requeridas (en .env o en Railway):
    AZURE_OPENAI_ENDPOINT    → https://<recurso>.cognitiveservices.azure.com
    AZURE_OPENAI_API_KEY     → clave del recurso Azure
    AZURE_OPENAI_DEPLOYMENT  → nombre del deployment (ej: gpt-4.1-mini)
    AZURE_OPENAI_API_VERSION → versión de la API (ej: 2024-05-01-preview)
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()  # Carga .env en desarrollo local


def obtener_correcciones(results):
    """
    Recibe el dict de resultados del escáner y devuelve una cadena JSON
    con las correcciones sugeridas por Azure OpenAI.

    Formato de 'results':
        {"SQL Injection": ("Vulnerable", "High"), "XSS": ("Safe", "Low"), ...}

    Devuelve:
        str — JSON de correcciones, o mensaje de error con prefijo ❌
    """
    # ── Leer configuración de Azure OpenAI ──
    endpoint   = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
    api_key    = os.getenv("AZURE_OPENAI_API_KEY", "")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")

    if not endpoint or not api_key:
        return "❌ Error: AZURE_OPENAI_ENDPOINT o AZURE_OPENAI_API_KEY no están configuradas."

    # ── Construir texto de vulnerabilidades ──
    if not isinstance(results, dict):
        return "❌ Error: 'results' no es un dict, es " + str(type(results))

    texto_vulnerabilidades = "\n".join(
        f"- {vuln}: {estado} (Riesgo: {riesgo})"
        for vuln, (estado, riesgo) in results.items()
    )

    # ── Prompt ──
    prompt_usuario = f"""
Vulnerabilidades detectadas en el escaneo:

{texto_vulnerabilidades}

Responde ÚNICAMENTE con un array JSON válido con esta estructura exacta (sin texto adicional):

[
  {{
    "vulnerabilidad": "nombre exacto de la vulnerabilidad",
    "riesgo": "nivel de riesgo",
    "correcciones": [
      "Paso 1 concreto...",
      "Paso 2 concreto...",
      "Paso 3 concreto..."
    ]
  }}
]
"""

    # ── URL de la REST API de Azure OpenAI ──
    url = (
        f"{endpoint}/openai/deployments/{deployment}"
        f"/chat/completions?api-version={api_version}"
    )

    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }

    body = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres un experto en ciberseguridad. "
                    "Respondes SOLO con JSON válido, sin texto sadicional, "
                    "sin bloques de código markdown."
                ),
            },
            {
                "role": "user",
                "content": prompt_usuario,
            },
        ],
        "temperature": 0.3,
        "max_tokens": 2000,
    }

    # ── Llamada HTTP ──
    try:
        response = requests.post(url, headers=headers, json=body, timeout=45)

        if response.status_code != 200:
            return (
                f"❌ Error HTTP {response.status_code} de Azure OpenAI: "
                f"{response.text[:500]}"
            )

        data = response.json()
        print("🔍 Respuesta Azure OpenAI:", data)  # debug en consola Flask

        correcciones = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        # Limpiar posibles bloques de markdown que el modelo añada
        if correcciones.startswith("```"):
            correcciones = correcciones.split("```")[1]
            if correcciones.startswith("json"):
                correcciones = correcciones[4:]
            correcciones = correcciones.strip()

        return correcciones or "⚠️ Azure OpenAI no devolvió contenido."

    except requests.exceptions.Timeout:
        return "❌ Timeout: Azure OpenAI tardó demasiado en responder."
    except Exception as e:
        return f"❌ Error al comunicarse con Azure OpenAI: {str(e)}"
