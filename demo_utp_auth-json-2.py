"""
AutenticaciÃ³n y ExtracciÃ³n DinÃ¡mica UTP+class
=============================================
Obtiene los tokens de sesiÃ³n reales desde las peticiones HTTP del navegador
y consulta la API de UTP para extraer la lista de cursos sin datos hardcodeados.
"""

import json
import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from playwright.sync_api import sync_playwright

console = Console()

LOGIN_URL = "https://sso.utp.edu.pe/auth/realms/Xpedition/protocol/openid-connect/auth?client_id=pao-web&redirect_uri=https%3A%2F%2Fclass.utp.edu.pe%2Fstudent%2Fcourses&state=b408bd68-fbbc-45ea-a1e3-c96428b204e5&response_mode=fragment&response_type=code&scope=openid&nonce=4de8c449-307a-4624-8556-1f6c58de61d5"
API_COURSES_URL = "https://api-pao.utpxpedition.com/course/student/courses"


def main():
    console.print(Panel.fit("[bold cyan]ðŸ”‘ AutenticaciÃ³n y ExtracciÃ³n DinÃ¡mica UTP+class[/bold cyan]", border_style="cyan"))

    codigo = input("Ingresa tu cÃ³digo institucional (ej. TU_CODIGO): ").strip()
    contrasena = input("Ingresa tu contraseÃ±a: ").strip()

    captured_headers = {}
    api_courses_response = None

    console.print("\n[yellow]â³ Iniciando navegador y autenticando en UTP+class...[/yellow]")

    with sync_playwright() as p:
        # headless=False para monitorear la ejecuciÃ³n en tiempo real
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Interceptador para capturar los headers de autorizaciÃ³n y la respuesta JSON directa
        def handle_response(response):
            nonlocal api_courses_response
            url = response.url
            if "api-pao.utpxpedition.com" in url:
                req_headers = response.request.headers
                if "authorization" in req_headers and "user-id" in req_headers:
                    captured_headers["authorization"] = req_headers.get("authorization")
                    captured_headers["user-id"] = req_headers.get("user-id")
                    captured_headers["x-tenant-id"] = req_headers.get("x-tenant-id", "")

                # Capturar la respuesta JSON de los cursos en tiempo real
                if "/course/student/courses" in url and response.status == 200:
                    try:
                        api_courses_response = response.json()
                    except Exception:
                        pass

        page.on("response", handle_response)

        try:
            # domcontentloaded para evitar bloqueos por banners o carruseles
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)

            # 1. Ingresar cÃ³digo
            page.wait_for_selector("input[type='text'], input[type='email'], #username", timeout=15000)
            page.fill("input[type='text'], input[type='email'], #username", codigo)
            page.click("input[type='submit'], button[type='submit']")

            # 2. Ingresar contraseÃ±a
            page.wait_for_selector("input[type='password']", timeout=15000)
            page.fill("input[type='password']", contrasena)
            page.click("input[type='submit'], button[type='submit']")

            # 3. ConfirmaciÃ³n "Mantener sesiÃ³n iniciada" (Microsoft SSO)
            try:
                page.wait_for_selector("input[id='idSIButton9']", timeout=4000)
                page.click("input[id='idSIButton9']")
            except Exception:
                pass

            # 4. Esperar a que la SPA cargue y la API responda
            page.wait_for_selector("text=Actividades semanales", timeout=25000)
            page.wait_for_timeout(3000)

            console.print("\n[bold green]âœ… Â¡Inicio de sesiÃ³n exitoso![/bold green]\n")

        except Exception as e:
            console.print(f"[bold red]âŒ Error durante el inicio de sesiÃ³n:[bold red] {e}")
            page.screenshot(path="error_login.png")
            browser.close()
            return

        browser.close()

    # --- VALIDACIÃ“N DE CREDENCIALES CAPTURADAS ---
    if not captured_headers.get("authorization"):
        console.print("[bold red]âŒ No se pudieron interceptar los tokens de autenticaciÃ³n.[/bold red]")
        return

    raw_auth = captured_headers["authorization"]
    auth_token = raw_auth.replace("Bearer ", "").strip() if raw_auth.startswith("Bearer ") else raw_auth
    user_id = captured_headers.get("user-id", "")
    tenant_id = captured_headers.get("x-tenant-id", "")

    # --- TABLA DE CREDENCIALES EXTRAÃDAS EN TIEMPO REAL ---
    cred_table = Table(title="ðŸ”‘ Credenciales de SesiÃ³n Capturadas", border_style="cyan")
    cred_table.add_column("Variable", style="bold cyan", no_wrap=True)
    cred_table.add_column("Valor Capturado", style="magenta")

    cred_table.add_row("AUTH_TOKEN", f"{auth_token[:30]}...{auth_token[-20:]}")
    cred_table.add_row("USER_ID", user_id)
    cred_table.add_row("TENANT_ID", tenant_id)
    console.print(cred_table)
    console.print("")

    # --- OBTENCIÃ“N DINÃMICA DE CURSOS DE LA API ---
    courses_data = []

    if api_courses_response and isinstance(api_courses_response, dict):
        courses_data = api_courses_response.get("data", [])
    else:
        # Consulta HTTP limpia usando los headers capturados si no se capturÃ³ al vuelo
        console.print("[yellow]ðŸ“¡ Solicitando informaciÃ³n de cursos a la API PAO...[/yellow]")
        headers_req = {
            "accept": "*/*",
            "authorization": f"Bearer {auth_token}",
            "origin": "https://class.utp.edu.pe",
            "referer": "https://class.utp.edu.pe/",
            "user-id": user_id,
            "user-role": "STUDENT",
            "x-tenant-id": tenant_id,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        try:
            res = requests.get(API_COURSES_URL, headers=headers_req, timeout=15)
            res.raise_for_status()
            courses_data = res.json().get("data", [])
        except Exception as e:
            console.print(f"[bold red]âŒ Error al consultar la API de cursos: {e}[/bold red]")

    # --- RENDERIZADO DE CURSOS OBTENIDOS ---
    if courses_data:
        course_table = Table(title="ðŸ“š Cursos ExtraÃ­dos DinÃ¡micamente de la API", border_style="green", header_style="bold green")
        course_table.add_column("Nombre del Curso", style="bold white")
        course_table.add_column("ID del Curso", style="yellow", justify="center")
        course_table.add_column("SecciÃ³n / CÃ³digo", style="cyan", justify="center")

        for course in courses_data:
            nombre = course.get("name") or course.get("courseName") or "Sin Nombre"
            course_id = str(course.get("id") or course.get("courseId") or "-")
            seccion = str(course.get("section") or course.get("sectionCode") or course.get("sectionId") or "-")

            course_table.add_row(nombre, course_id, seccion)

        console.print(course_table)
        console.print("")

        # Muestra el JSON exacto retornado por la API
        console.print("[bold cyan]ðŸ“„ JSON de la Respuesta Real de la API:[/bold cyan]")
        console.print_json(data=courses_data)
    else:
        console.print("[bold red]âŒ No se encontraron datos de cursos en la API.[/bold red]")


if __name__ == "__main__":
    main()