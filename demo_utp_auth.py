"""
Demo de AutenticaciÃ³n AutomÃ¡tica UTP+class
==========================================
Inicia sesiÃ³n en class.utp.edu.pe mediante Playwright, captura
las credenciales de sesiÃ³n (Bearer Token, User ID, Tenant ID)
e imprime el listado actual de cursos desde la API.
"""

import getpass

import requests
from playwright.sync_api import sync_playwright
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

LOGIN_URL = "https://sso.utp.edu.pe/auth/realms/Xpedition/protocol/openid-connect/auth?client_id=pao-web&redirect_uri=https%3A%2F%2Fclass.utp.edu.pe%2Fstudent%2Fcourses&state=b408bd68-fbbc-45ea-a1e3-c96428b204e5&response_mode=fragment&response_type=code&scope=openid&nonce=4de8c449-307a-4624-8556-1f6c58de61d5"
API_COURSES_BASE = "https://api-pao.utpxpedition.com/course/student/courses"


def main():
    console.print(
        Panel.fit("[bold cyan]ðŸ”‘ AutenticaciÃ³n y ExtracciÃ³n Directa UTP+class[/bold cyan]", border_style="cyan"))

    codigo = input("Ingresa tu cÃ³digo institucional (ej. TU_CODIGO): ").strip()
    contrasena = getpass.getpass("Ingresa tu contraseÃ±a: ").strip()

    captured_headers = {}
    captured_api_responses = []

    console.print("\n[yellow]â³ Iniciando navegador y capturando red...[/yellow]")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Listener global para interceptar todo el trÃ¡fico JSON de la API
        def handle_response(response):
            url = response.url
            if "api-pao.utpxpedition.com" in url:
                req_headers = response.request.headers
                if "authorization" in req_headers and "user-id" in req_headers:
                    captured_headers["authorization"] = req_headers.get("authorization")
                    captured_headers["user-id"] = req_headers.get("user-id")
                    captured_headers["x-tenant-id"] = req_headers.get("x-tenant-id", "")

                if response.status == 200:
                    try:
                        content_type = response.headers.get("content-type", "")
                        if "application/json" in content_type:
                            data = response.json()
                            captured_api_responses.append({"url": url, "data": data})
                    except Exception:
                        pass

        page.on("response", handle_response)

        try:
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)

            # 1. Ingreso de cÃ³digo
            page.wait_for_selector("input[type='text'], input[type='email'], #username", timeout=15000)
            page.fill("input[type='text'], input[type='email'], #username", codigo)
            page.click("input[type='submit'], button[type='submit']")

            # 2. Ingreso de contraseÃ±a
            page.wait_for_selector("input[type='password']", timeout=15000)
            page.fill("input[type='password']", contrasena)
            page.click("input[type='submit'], button[type='submit']")

            # 3. ConfirmaciÃ³n "Mantener sesiÃ³n iniciada" (Microsoft SSO)
            try:
                page.wait_for_selector("input[id='idSIButton9']", timeout=4000)
                page.click("input[id='idSIButton9']")
            except Exception:
                pass

            # 4. Esperar a la carga completa del panel principal
            page.wait_for_selector("text=Actividades semanales", timeout=25000)

            # Tiempo adicional para asegurar que todas las llamadas asÃ­ncronas finalicen
            page.wait_for_timeout(6000)

            console.print("\n[bold green]âœ… Â¡Inicio de sesiÃ³n y captura de red exitosos![/bold green]\n")

            # Si no se capturaron cursos en trÃ¡fico, hacer un fetch nativo dentro de la pÃ¡gina
            period_id = None
            for item in captured_api_responses:
                data = item.get("data", {})
                if isinstance(data, dict) and "academicPeriods" in data.get("data", {}):
                    periods = data["data"]["academicPeriods"]
                    for period in periods:
                        if period.get("type") == "CURRENT_PERIOD" and period.get("period") != "9999":
                            period_id = period.get("id")
                            break

            if period_id:
                # Realizar fetch desde dentro del navegador usando la misma sesiÃ³n activa
                browser_fetched_courses = page.evaluate(f'''async () => {{
                    try {{
                        const response = await fetch("https://api-pao.utpxpedition.com/course/student/courses?academicPeriodId={period_id}");
                        return await response.json();
                    }} catch (e) {{
                        return null;
                    }}
                }}''')

                if browser_fetched_courses:
                    captured_api_responses.append({
                        "url": f"https://api-pao.utpxpedition.com/course/student/courses?academicPeriodId={period_id}",
                        "data": browser_fetched_courses
                    })

        except Exception as e:
            console.print(f"[bold red]âŒ Error durante la ejecuciÃ³n:[bold red] {e}")
            page.screenshot(path="error_login.png")
            browser.close()
            return

        browser.close()

    # --- MOSTRAR CREDENCIALES OBTENIDAS ---
    if captured_headers.get("authorization"):
        raw_auth = captured_headers["authorization"]
        auth_token = raw_auth.replace("Bearer ", "").strip() if raw_auth.startswith("Bearer ") else raw_auth
        user_id = captured_headers.get("user-id", "")
        tenant_id = captured_headers.get("x-tenant-id", "")

        cred_table = Table(title="ðŸ”‘ Credenciales de SesiÃ³n Capturadas", border_style="cyan")
        cred_table.add_column("Variable", style="bold cyan", no_wrap=True)
        cred_table.add_column("Valor Capturado", style="magenta")

        cred_table.add_row("AUTH_TOKEN", f"{auth_token[:30]}...{auth_token[-20:]}")
        cred_table.add_row("USER_ID", user_id)
        cred_table.add_row("TENANT_ID", tenant_id)
        console.print(cred_table)
        console.print("")

    # --- BUSCAR Y RENDERIZAR LA RESPUESTA DE CURSOS ---
    courses_data_json = None

    for item in captured_api_responses:
        data = item.get("data", {})
        # Identificar la respuesta que contiene la lista real de cursos
        if isinstance(data, dict):
            inner_data = data.get("data")
            if isinstance(inner_data, list) and len(inner_data) > 0:
                # Verificar que contenga campos propios de asignaturas
                first_item = inner_data[0]
                if isinstance(first_item, dict) and (
                        "name" in first_item or "courseName" in first_item or "code" in first_item):
                    courses_data_json = data
                    break

    if courses_data_json:
        courses_list = courses_data_json.get("data", [])

        course_table = Table(title="ðŸ“š Cursos ExtraÃ­dos DinÃ¡micamente de la API", border_style="green",
                             header_style="bold green")
        course_table.add_column("Nombre del Curso", style="bold white")
        course_table.add_column("Course ID / CÃ³digo", style="yellow", justify="center")
        course_table.add_column("SecciÃ³n ID", style="cyan", justify="center")

        for course in courses_list:
            nombre = course.get("name") or course.get("courseName") or course.get("title") or "Sin Nombre"
            c_id = str(course.get("id") or course.get("courseId") or course.get("code") or "-")
            sec = str(course.get("sectionId") or course.get("sectionCode") or course.get("section") or "-")
            course_table.add_row(nombre, c_id, sec)

        console.print(course_table)
        console.print("")

        console.print("[bold cyan]ðŸ“„ JSON Completo de Cursos Obtenciones:[/bold cyan]")
        console.print_json(data=courses_data_json)
    else:
        console.print(
            "[bold red]âŒ No se encontrÃ³ la respuesta con la lista de cursos entre los paquetes de red capturados.[/bold red]")


if __name__ == "__main__":
    main()