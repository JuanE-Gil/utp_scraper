"""
Demo de AutenticaciÃ³n AutomÃ¡tica UTP+class
==========================================
Inicia sesiÃ³n en class.utp.edu.pe mediante Playwright, captura
las credenciales de sesiÃ³n (Bearer Token, User ID, Tenant ID)
e imprime el listado actual de cursos desde la API.
"""

import getpass
import json
import re
import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from playwright.sync_api import sync_playwright

console = Console()

LOGIN_URL = "https://sso.utp.edu.pe/auth/realms/Xpedition/protocol/openid-connect/auth?client_id=pao-web&redirect_uri=https%3A%2F%2Fclass.utp.edu.pe%2Fstudent%2Fcourses&state=b408bd68-fbbc-45ea-a1e3-c96428b204e5&response_mode=fragment&response_type=code&scope=openid&nonce=4de8c449-307a-4624-8556-1f6c58de61d5"
API_COURSES_URL = "https://api-pao.utpxpedition.com/course/student/courses"

import json
from playwright.sync_api import sync_playwright

def autenticar_y_extraer_utp():
    codigo = input("Ingresa tu cÃ³digo de estudiante (ej. TU_CODIGO): ").strip()
    contrasena = input("Ingresa tu contraseÃ±a: ").strip()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        datos_api = {}

        # Interceptor para capturar la respuesta JSON que la plataforma solicita al backend
        def interceptar_respuesta(response):
            if "api-pao.utpxpedition.com/course/student/courses" in response.url:
                try:
                    datos_api["cursos"] = response.json()
                except Exception:
                    pass

        page.on("response", interceptar_respuesta)

        try:
            print("\nâŒ› 1. Abriendo portal UTP+class...")
            page.goto(LOGIN_URL, wait_until="domcontentloaded")

            print("ðŸ”‘ 2. Ingresando credenciales...")
            # 1. CÃ³digo de usuario
            page.wait_for_selector('input[type="text"], input[type="email"], #username', timeout=15000)
            page.fill('input[type="text"], input[type="email"], #username', codigo)
            page.click('button[type="submit"], input[type="submit"]')

            # 2. ContraseÃ±a
            page.wait_for_selector('input[type="password"]', timeout=15000)
            page.fill('input[type="password"]', contrasena)
            page.click('button[type="submit"], input[type="submit"]')

            # 3. ConfirmaciÃ³n de sesiÃ³n activa en Microsoft (si aplica)
            try:
                page.wait_for_selector('input[id="idSIButton9"]', timeout=4000)
                page.click('input[id="idSIButton9"]')
            except Exception:
                pass

            print("â³ 3. Cargando panel principal...")
            # NUNCA usar networkidle aquÃ­. Se espera al encabezado del panel lateral
            page.wait_for_selector("text=Actividades semanales", timeout=20000)
            page.wait_for_timeout(3000)  # Margen de renderizado

            print("âœ… Â¡SesiÃ³n iniciada correctamente!")
            print("ðŸ“Š 4. Extrayendo informaciÃ³n...")

            # Si se capturÃ³ la API directamente, la muestra limpia
            if "cursos" in datos_api:
                print("\n================ CURSOS (API DIRECTA) ================")
                print(json.dumps(datos_api["cursos"], indent=4, ensure_ascii=False))
            else:
                # ExtracciÃ³n desde el DOM renderizado
                datos_dom = page.evaluate('''() => {
                    const textoPagina = document.body.innerText;
                    return { contenido: textoPagina };
                }''')
                print("\n================ DATOS EXTRAÃDOS DEL PANEL ================")
                print(datos_dom["contenido"])

        except Exception as e:
            page.screenshot(path="error_login.png")
            print(f"\nâŒ Error durante la ejecuciÃ³n: {e}")

        finally:
            browser.close()

if __name__ == "__main__":
    autenticar_y_extraer_utp()