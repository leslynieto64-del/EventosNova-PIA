"""Prepara las cuentas y los datos CONTROLADOS para las pruebas manuales de la interfaz (entorno manual, PostgreSQL, puerto 8001).

    EVENTOSNOVA_E2E_ADMIN_CORREO=<correo> EVENTOSNOVA_E2E_ADMIN_CLAVE=<clave> python scripts/preparar_datos_pruebas_manuales.py [--url http://127.0.0.1:8001]

Todo se hace por la API real (con la cuenta de administrador indicada en las variables de entorno; debe existir: scripts/crear_administrador.py):
- Cuentas de prueba: un coordinador, un proveedor (vinculado a un proveedor REAL del catálogo) y una cuenta desactivada. Las contraseñas se generan al azar, se
  guardan SOLO en `scratchpad/credenciales_pruebas_manual.txt` (carpeta excluida de Git) y no se imprimen. Las cuentas existentes no se modifican.
- Proveedores del catálogo: uno que ofrece Banquete y otro que ofrece Fotografía.
- Eventos con los flujos reales (registro, propuesta, aceptación, contrato, política, firma, pago y verificación): sin inventar estados.
- Los identificadores creados se guardan en `tests/evidencias/pruebas_manuales_web/datos_controlados.json` (sin secretos) para consultarlos y limpiarlos después.
Se niega a ejecutarse dos veces (ya existe el proveedor «Banquetes Manual (prueba)»); no borra nada."""
import argparse
import json
import os
import secrets
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

RAIZ = Path(__file__).resolve().parents[1]
CREDENCIALES = RAIZ / "scratchpad" / "credenciales_pruebas_manual.txt"
DATOS = RAIZ / "tests" / "evidencias" / "pruebas_manuales_web" / "datos_controlados.json"
DOMINIO = "eventosnova.example"
CLIENTE = "CL-MANUAL"


class Sesion:
    def __init__(self, base: str):
        self.http = httpx.Client(base_url=base, timeout=30)
        self.csrf = ""

    def entrar(self, correo: str, clave: str):
        r = self.http.post("/auth/inicio-sesion", json={"correo": correo, "contrasena": clave})
        if r.status_code != 200:
            raise SystemExit(f"No se pudo iniciar sesión como {correo} ({r.status_code}): {r.json().get('detalle')}")
        self.csrf = r.json()["datos"]["csrf"]
        return self

    def pedir(self, metodo: str, ruta: str, cuerpo=None, esperado=(200, 201)):
        r = self.http.request(metodo, ruta, json=cuerpo, headers={"X-CSRF-Token": self.csrf} if metodo != "GET" else {})
        if r.status_code not in esperado:
            raise SystemExit(f"{metodo} {ruta} -> {r.status_code}: {r.text[:300]}")
        return r.json()


def clave_nueva() -> str:
    return "Manual-" + secrets.token_urlsafe(12)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8001")
    a = ap.parse_args()
    correo_admin, clave_admin = os.environ.get("EVENTOSNOVA_E2E_ADMIN_CORREO"), os.environ.get("EVENTOSNOVA_E2E_ADMIN_CLAVE")
    if not correo_admin or not clave_admin:
        raise SystemExit("Defina EVENTOSNOVA_E2E_ADMIN_CORREO y EVENTOSNOVA_E2E_ADMIN_CLAVE (administrador existente).")
    adm = Sesion(a.url).entrar(correo_admin, clave_admin)
    if any(p["nombre"] == "Banquetes Manual (prueba)" for p in adm.pedir("GET", "/proveedores")["datos"]["proveedores"]):
        raise SystemExit("Los datos controlados ya existen («Banquetes Manual (prueba)»): no se vuelven a crear.")

    # --- cuentas (el coordinador crea el catálogo; el administrador, las cuentas)
    clave_coord, clave_prov, clave_desact = clave_nueva(), clave_nueva(), clave_nueva()
    c_coord, c_prov, c_desact = (f"coordinador.manual@{DOMINIO}", f"proveedor.manual@{DOMINIO}", f"desactivada.manual@{DOMINIO}")
    adm.pedir("POST", "/usuarios", {"correo": c_coord, "nombre": "Coordinación (prueba manual)", "rol": "coordinador", "contrasena": clave_coord})
    coord = Sesion(a.url).entrar(c_coord, clave_coord)

    # --- proveedores reales del catálogo
    banq = coord.pedir("POST", "/proveedores", {"nombre": "Banquetes Manual (prueba)", "servicios": ["Banquete"], "contacto": "55 1000 0001"})["datos"]["proveedorId"]
    foto = coord.pedir("POST", "/proveedores", {"nombre": "Fotografía Manual (prueba)", "servicios": ["Fotografía"], "contacto": "55 1000 0002"})["datos"]["proveedorId"]
    adm.pedir("POST", "/usuarios", {"correo": c_prov, "nombre": "Proveedor Banquetes (prueba manual)", "rol": "proveedor", "contrasena": clave_prov, "proveedor_id": banq})
    u = adm.pedir("POST", "/usuarios", {"correo": c_desact, "nombre": "Cuenta desactivada (prueba manual)", "rol": "coordinador", "contrasena": clave_desact})["datos"]
    adm.pedir("POST", f"/usuarios/{u['usuarioId']}/estado", {"activo": False})

    # --- eventos con los flujos reales (hora de negocio de la Ciudad de México)
    ahora = datetime.now(ZoneInfo("America/Mexico_City")).replace(tzinfo=None, microsecond=0)
    fecha_evento = (ahora + timedelta(days=75)).replace(hour=18, minute=0, second=0)
    iso = lambda d: d.isoformat()                                                                  # noqa: E731
    servicios = ["Banquete", "Fotografía"]
    registro = []

    def evento(titulo: str, lugar: str):
        return coord.pedir("POST", "/eventos", {"cliente_id": CLIENTE, "datos": {"tipo": titulo, "fecha_hora": iso(fecha_evento), "lugar": lugar, "invitados_aproximados": 80}, "servicios": servicios})["evento_id"]

    def hasta_contrato(ev: str):
        prop = coord.pedir("POST", f"/eventos/{ev}/propuestas", {"servicios": servicios, "proveedores_considerados": [banq, foto], "costo_total": "10000.00", "condiciones": "Condiciones de prueba manual"})["propuesta_id"]
        coord.pedir("POST", f"/propuestas/{prop}/aceptacion", {"version_id": f"{prop}-v1"})
        return prop, coord.pedir("POST", f"/propuestas/{prop}/contrato", {"politica_incluida": True})["datos"]["contrato_id"]

    def hasta_firma(ev: str):
        prop, ct = hasta_contrato(ev)
        coord.pedir("POST", f"/contratos/{ct}/comunicacion-politica-no-reembolso", {"fecha": iso(ahora)})
        coord.pedir("POST", f"/contratos/{ct}/firma", {"fecha": iso(ahora)})
        return prop, ct

    def pagar_anticipo(ev: str, importe: str, ref: str):
        ec = adm.pedir("GET", f"/eventos/{ev}/pagos")["estadosCuenta"][0]["estadoCuentaId"]
        ob = next(p for p in adm.pedir("GET", f"/pagos-pendientes?evento_id={ev}")["pagos"] if p["concepto"] == "Anticipo")
        adm.pedir("POST", f"/estados-cuenta/{ec}/pagos", {"obligacion_id": ob["obligacionId"], "importe": importe, "fecha": iso(ahora), "comprobante": ref, "verificar_ahora": True})
        return ec

    e1 = evento("Prueba manual 01 · Evento recién registrado", "Salón Manual 01")
    registro.append({"id": "M-01", "evento": e1, "estado_esperado": "En gestión", "uso": "Crear propuesta, aceptarla, preparar contrato, comunicar la política y firmar (Coordinación)"})

    e2 = evento("Prueba manual 02 · En gestión con contrato en preparación", "Salón Manual 02")
    p2, ct2 = hasta_contrato(e2)
    registro.append({"id": "M-02", "evento": e2, "propuesta": p2, "contrato": ct2, "estado_esperado": "En gestión · contrato En preparación", "uso": "Comunicar la política y registrar la firma (Coordinación)"})

    e3 = evento("Prueba manual 03 · Contrato firmado con anticipo pendiente", "Salón Manual 03")
    p3, ct3 = hasta_firma(e3)
    registro.append({"id": "M-03", "evento": e3, "propuesta": p3, "contrato": ct3, "estado_esperado": "En gestión · contrato Firmado · anticipo Pendiente", "uso": "Registrar y verificar el anticipo (Administración); el evento pasa a En organización"})

    e4 = evento("Prueba manual 04 · En organización con solicitudes", "Salón Manual 04")
    p4, ct4 = hasta_firma(e4)
    ec4 = pagar_anticipo(e4, "3000.00", "CMP-MANUAL-04")
    for _ in range(20):
        if coord.pedir("GET", f"/eventos/{e4}/administracion")["estadoEvento"] == "En organización":
            break
        import time; time.sleep(0.4)
    sc = coord.pedir("POST", "/solicitudes-cambio", {"evento_id": e4, "contrato_id": ct4, "descripcion": "Mover el brindis a las 20:00 (prueba manual)", "tarifa_vigente": "500.00"})["datos"]
    sa = coord.pedir("POST", "/solicitudes-servicio-adicional", {"evento_id": e4, "contrato_id": ct4, "servicio": "Decoración (prueba manual)"})["datos"]
    registro.append({"id": "M-04", "evento": e4, "propuesta": p4, "contrato": ct4, "estado_cuenta": ec4, "solicitud_cambio": sc.get("solicitud_id") or sc.get("solicitudId"),
                     "solicitud_servicio_adicional": sa.get("solicitud_id") or sa.get("solicitudId"), "estado_esperado": "En organización · anticipo Liquidada (3,000.00) · saldo 7,000.00 Pendiente",
                     "uso": "Asignar proveedores (Coordinación), gestionar las solicitudes, autorizar (Administración), registrar pagos del saldo"})

    e5 = evento("Prueba manual 05 · En organización con proveedor asignado", "Salón Manual 05")
    p5, ct5 = hasta_firma(e5)
    ec5 = pagar_anticipo(e5, "3000.00", "CMP-MANUAL-05")
    for _ in range(20):
        if coord.pedir("GET", f"/eventos/{e5}/administracion")["estadoEvento"] == "En organización":
            break
        import time; time.sleep(0.4)
    serv = {s["servicio"]: s["servicioContratadoId"] for s in coord.pedir("GET", f"/eventos/{e5}/administracion")["proveedores"]}
    coord.pedir("POST", f"/eventos/{e5}/servicios/{serv['Banquete']}/proveedor", {"proveedor_id": banq})
    registro.append({"id": "M-05", "evento": e5, "propuesta": p5, "contrato": ct5, "estado_cuenta": ec5, "servicio_banquete": serv["Banquete"], "servicio_fotografia": serv["Fotografía"],
                     "estado_esperado": "En organización · Banquete «Pendiente de confirmación del proveedor» (Banquetes Manual) · Fotografía «Sin proveedor asignado»",
                     "uso": "El proveedor consulta con este identificador de evento y registra su respuesta; Coordinación asigna Fotografía"})

    DATOS.parent.mkdir(parents=True, exist_ok=True)
    DATOS.write_text(json.dumps({"creado_en": iso(ahora), "base": "eventosnova_manual_test", "cliente": CLIENTE, "proveedores": {"banquetes": banq, "fotografia": foto},
                                 "cuentas": {"administrador": correo_admin, "coordinador": c_coord, "proveedor": c_prov, "desactivada": c_desact},
                                 "eventos": registro}, ensure_ascii=False, indent=2), encoding="utf-8")
    CREDENCIALES.parent.mkdir(parents=True, exist_ok=True)
    CREDENCIALES.write_text("\n".join([
        "CREDENCIALES DE PRUEBA — ENTORNO MANUAL (http://127.0.0.1:8001/app/). Archivo local protegido: NO se versiona (scratchpad/ está en .gitignore).",
        "Cuentas temporales para probar la página; bórrelas o cambie sus contraseñas al terminar.", "",
        f"ADMINISTRADOR : {correo_admin}", f"  contraseña   : {clave_admin}", "",
        f"COORDINADOR   : {c_coord}", f"  contraseña   : {clave_coord}", "",
        f"PROVEEDOR     : {c_prov}   (proveedor: Banquetes Manual (prueba), {banq})", f"  contraseña   : {clave_prov}", "",
        f"DESACTIVADA   : {c_desact}   (debe RECHAZARSE al iniciar sesión)", f"  contraseña   : {clave_desact}", ""]), encoding="utf-8")
    print(f"Datos controlados creados: {len(registro)} eventos, 2 proveedores, 3 cuentas nuevas.")
    print(f"Identificadores: {DATOS.relative_to(RAIZ)} · Credenciales: {CREDENCIALES.relative_to(RAIZ)} (no se imprimen).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
