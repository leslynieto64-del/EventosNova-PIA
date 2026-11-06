"""Siembra los datos de DEMOSTRACIÓN de Eventos Nova mediante la API real (nunca con INSERT directos ni con los CSV oficiales).

    python scripts/sembrar_datos_demo.py --base-url http://127.0.0.1:8002 --entorno local --admin-correo <correo>                 # --simular (por omisión)
    python scripts/sembrar_datos_demo.py ... --verificar-estado                                                                  # inicia sesión y hace solo GET
    python scripts/sembrar_datos_demo.py ... --aplicar                                                                           # escribe

Modos (excluyentes):
- --simular (por omisión): NO inicia sesión y NO escribe. Valida argumentos y el destino, muestra el plan y consulta solo /health y /ready (públicos).
- --verificar-estado: inicia sesión como administrador (POST /auth/inicio-sesion: REGISTRA UNA SESIÓN y ACTUALIZA EL ÚLTIMO ACCESO de la cuenta) y
  hace únicamente GET de negocio para informar qué existe, qué falta y qué sería ambiguo. No ejecuta ningún POST de negocio. Con --entorno produccion
  exige antes escribir exactamente «VERIFICAR ESTADO EN <host>»; sin esa frase no hace ningún login ni GET privado.
- --aplicar: crea lo que falte. Antes de cada POST consulta el estado real; nunca sobrescribe; se detiene ante datos ambiguos.

Reglas (especificación aprobada):
- El primer administrador YA debe existir (scripts/crear_administrador.py); este script nunca lo crea. Se usa su sesión para crear las demás cuentas.
- Las contraseñas se piden con getpass (nunca por argumento, variable de entorno ni archivo). Si la cuenta existe se pide su contraseña para iniciar sesión;
  nunca se restablece. Un inicio de sesión fallido (o un 429) detiene el script SIN reintentos.
- Identificación determinista: cuentas, proveedores y eventos llevan la marca [DEMO]; los eventos tienen fechas FIJAS de 2027 y cliente_id CL-DEMO-01/02/03.
- Pasos no repetibles (política de no reembolso, firma, anticipo, cancelación, revisión administrativa): se registra la intención en el archivo de progreso
  ANTES de ejecutarlos. Solo se reintenta automáticamente un paso si la ausencia de su efecto se comprueba por GET. La comunicación de la política y la
  revisión administrativa NO son consultables por la API: si quedaron a medias, el script se detiene y exige una recuperación explícita
  (--reanudar-politica CL-DEMO-0N / --reanudar-revision), con confirmación escrita; reenviar solo reescribe la fecha registrada.
- Progreso y candado en scratchpad/ (ignorado por Git), sin contraseñas, cookies ni tokens. Una ejecución a la vez (candado con creación exclusiva);
  un candado huérfano lo retira una persona, nunca el script.
- Producción: --base-url explícita (https, dominio público), confirmación escrita del dominio, Origin = la URL real, sin redirecciones y sin peticiones a
  otro dominio. Con --entorno local solo se admite loopback. Nada de pagos reales ni servicios externos: la verificación de pagos es simulada por diseño.

Códigos de salida: 0 correcto · 1 detenido para revisión (datos ambiguos, candado, paso no verificable) · 2 argumentos o destino no válidos ·
3 fallo de autenticación · 4 error de red o respuesta inesperada de la API."""
from __future__ import annotations

import argparse
import getpass
import ipaddress
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

import httpx

RAIZ = Path(__file__).resolve().parents[1]
DIRECTORIO_ESTADO = RAIZ / "scratchpad"            # ignorado por Git (.gitignore)

# ------------------------------------------------------------------------------------------------ datos de demostración (fijos)
DOMINIO = "eventosnova.example"                    # dominio reservado (RFC 2606): no existe
CORREO_COORDINADOR = f"coordinador.demo@{DOMINIO}"
NOMBRE_COORDINADOR = "[DEMO] Coordinación de demostración"
CORREO_PROVEEDOR = f"proveedor.demo@{DOMINIO}"
NOMBRE_CUENTA_PROVEEDOR = "[DEMO] Cuenta del proveedor de Banquete"
SERVICIO_BANQUETE = "Banquete"                     # nombre exacto del servicio de alimentos

PROVEEDORES: Tuple[Tuple[str, str, str], ...] = (       # (servicio, nombre, contacto)
    ("Salón", "[DEMO] Salón Jardín Nova", "[DEMO] contacto ficticio 01 · demo.salon@eventosnova.example"),
    ("Banquete", "[DEMO] Banquetes Nova", "[DEMO] contacto ficticio 02 · demo.banquete@eventosnova.example"),
    ("Mobiliario", "[DEMO] Mobiliario Nova", "[DEMO] contacto ficticio 03 · demo.mobiliario@eventosnova.example"),
    ("Música", "[DEMO] Música en Vivo Nova", "[DEMO] contacto ficticio 04 · demo.musica@eventosnova.example"),
    ("Decoración", "[DEMO] Decoración Nova", "[DEMO] contacto ficticio 05 · demo.decoracion@eventosnova.example"),
    ("Fotografía", "[DEMO] Fotografía Nova", "[DEMO] contacto ficticio 06 · demo.fotografia@eventosnova.example"),
)

# Fechas FIJAS (no se recalculan): sábados de 2027 a las 18:00, muy posteriores a cualquier plazo del dominio (anticipo: 3 días hábiles tras la
# firma; saldo: 3 días hábiles antes del evento) y sin llegada de T durante la demostración.
VENTANA_DESDE = "2027-01-01T00:00:00"
VENTANA_HASTA = "2027-12-31T23:59:59"
LIMITE_VALIDEZ = datetime(2027, 3, 13, 0, 0, 0)    # una semana antes del primer evento: después de esta fecha el script se niega a sembrar
CONDICIONES = "[DEMO] Condiciones de demostración"
MOTIVO_CANCELACION = "[DEMO] El Cliente solicitó cancelar el evento"
RESULTADO_REVISION = "[DEMO] Sin reembolso (política de no reembolso)"
FRASE_POLITICA = "ACEPTO NUEVA FECHA DE COMUNICACIÓN"
FRASE_REVISION = "ACEPTO NUEVA FECHA DE REVISIÓN"
ESPERA_ORGANIZACION_S = 30


@dataclass(frozen=True)
class EventoDemo:
    etq: str
    cliente_id: str
    tipo: str
    fecha_hora: str
    lugar: str
    invitados: int
    servicios: Tuple[str, ...]
    costo: str
    avanza: str                                     # propuesta | organizacion | cancelado
    anticipo: Optional[str] = None
    comprobante: Optional[str] = None


EVENTOS: Tuple[EventoDemo, ...] = (
    EventoDemo("E1", "CL-DEMO-01", "[DEMO] Boda · escenario 1 (en gestión)", "2027-03-20T18:00:00", "[DEMO] Salón Jardín Nova", 80,
               ("Salón", "Banquete"), "12000.00", "propuesta"),
    EventoDemo("E2", "CL-DEMO-02", "[DEMO] Graduación · escenario 2 (en organización)", "2027-04-17T18:00:00", "[DEMO] Salón Jardín Nova", 120,
               ("Banquete", "Fotografía"), "10000.00", "organizacion", "3000.00", "DEMO-ANT-02"),
    EventoDemo("E3", "CL-DEMO-03", "[DEMO] Evento empresarial · escenario 3 (cancelado)", "2027-05-22T18:00:00", "[DEMO] Salón Jardín Nova", 60,
               ("Salón", "Música"), "10000.00", "cancelado", "3000.00", "DEMO-ANT-03"),
)

OK, REVISION, ARGUMENTOS, AUTENTICACION, RED = 0, 1, 2, 3, 4


class Detener(Exception):
    """Detiene el script con un mensaje y un código de salida. Nunca incluye contraseñas, cookies ni tokens."""
    def __init__(self, codigo: int, mensaje: str):
        super().__init__(mensaje)
        self.codigo, self.mensaje = codigo, mensaje


# ------------------------------------------------------------------------------------------------ destino
@dataclass(frozen=True)
class Destino:
    entorno: str
    esquema: str
    host: str
    puerto: int
    netloc: str

    @property
    def base_url(self) -> str:
        return f"{self.esquema}://{self.netloc}"

    @property
    def origin(self) -> str:
        return self.base_url

    @property
    def clave(self) -> str:
        return re.sub(r"[^A-Za-z0-9_.-]", "_", f"{self.host}_{self.puerto}")


def _es_loopback(host: str) -> bool:
    if host == "localhost" or host.endswith(".localhost"):
        return True
    try:
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


def _es_literal_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host.strip("[]"))
        return True
    except ValueError:
        return False


def validar_destino(base_url: str, entorno: str) -> Destino:
    """Política del destino. `local`: solo loopback por http. `produccion`: solo https y un nombre de dominio público (se rechazan localhost,
    direcciones IP, nombres sin punto y sufijos internos)."""
    if entorno not in ("local", "produccion"):
        raise Detener(ARGUMENTOS, "--entorno debe ser «local» o «produccion».")
    try:
        p = urlsplit((base_url or "").strip())
        puerto = p.port
    except ValueError:
        raise Detener(ARGUMENTOS, "La --base-url no es válida.")
    if p.scheme not in ("http", "https") or not p.hostname:
        raise Detener(ARGUMENTOS, "La --base-url debe comenzar con http:// o https:// e indicar el servidor.")
    if p.username or p.password:
        raise Detener(ARGUMENTOS, "La --base-url no puede incluir usuario ni contraseña.")
    if p.path not in ("", "/") or p.query or p.fragment:
        raise Detener(ARGUMENTOS, "La --base-url debe ser solo el origen (esquema, servidor y puerto), sin ruta, consulta ni fragmento.")
    host = p.hostname.lower()
    if host.endswith("."):
        raise Detener(ARGUMENTOS, "El servidor de la --base-url no puede terminar en punto (evita evadir las comprobaciones de dominio).")
    if entorno == "produccion" and not _es_literal_ip(host) and not re.fullmatch(
            r"[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*", host):
        raise Detener(ARGUMENTOS, "El servidor de la --base-url no es un nombre de dominio válido.")
    if entorno == "local":
        if not _es_loopback(host):
            raise Detener(ARGUMENTOS, "Con --entorno local el destino debe ser loopback (localhost, 127.0.0.1 o ::1).")
        if p.scheme != "http":
            raise Detener(ARGUMENTOS, "Con --entorno local la URL debe usar http.")
    else:
        if p.scheme != "https":
            raise Detener(ARGUMENTOS, "Con --entorno produccion la URL debe usar https.")
        if _es_loopback(host) or _es_literal_ip(host) or "." not in host or host.endswith(
                (".local", ".localhost", ".internal", ".lan", ".localdomain", ".home.arpa", ".corp")):
            raise Detener(ARGUMENTOS, "Con --entorno produccion el destino debe ser un nombre de dominio público: se rechazan localhost, direcciones IP y "
                                       "nombres internos.")
    return Destino(entorno, p.scheme, host, puerto or (443 if p.scheme == "https" else 80), p.netloc.lower())


# ------------------------------------------------------------------------------------------------ estado local (progreso y candado)
def verificar_directorio_ignorado(directorio: Path, raiz: Path = RAIZ) -> None:
    """Si el directorio está dentro del repositorio, Git debe ignorarlo (el progreso no se versiona). Si no puede comprobarse, se detiene."""
    directorio = Path(directorio).resolve()
    try:
        directorio.relative_to(raiz.resolve())
    except ValueError:
        return                                                          # fuera del repositorio: no hay nada que versionar
    try:
        r = subprocess.run(["git", "-C", str(raiz), "check-ignore", "-q", "--", str(directorio / "sembrado_demo_progreso.json")],
                           capture_output=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        raise Detener(ARGUMENTOS, "No se pudo comprobar con Git que la carpeta del progreso esté ignorada.")
    if r.returncode != 0:
        raise Detener(ARGUMENTOS, f"La carpeta del progreso ({directorio.name}/) no está ignorada por Git: no se escribirá en ella.")


class EstadoLocal:
    """Archivo de progreso (JSON sin secretos) y candado de ejecución única, por destino."""
    def __init__(self, directorio: Path, destino: Destino, reloj: Callable[[], datetime]):
        self.directorio = Path(directorio)
        self.ruta = self.directorio / f"sembrado_demo_progreso_{destino.clave}.json"
        self.ruta_candado = self.directorio / f"sembrado_demo_{destino.clave}.lock"
        self.reloj, self._candado = reloj, False
        self.datos: Dict[str, dict] = {"version": 1, "destino": destino.netloc, "entorno": destino.entorno, "pasos": {}, "ids": {}}
        self.destino = destino

    # -- lectura (también en --simular: no escribe)
    def cargar(self) -> None:
        if not self.ruta.is_file():
            return
        try:
            datos = json.loads(self.ruta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise Detener(REVISION, f"El archivo de progreso ({self.ruta.name}) no se puede leer: revíselo antes de continuar.")
        if not isinstance(datos, dict) or datos.get("version") != 1 or datos.get("destino") != self.destino.netloc:
            raise Detener(REVISION, "El archivo de progreso no corresponde a este destino: revíselo antes de continuar.")
        pasos, ids = datos.get("pasos"), datos.get("ids")
        if (not isinstance(pasos, dict) or not isinstance(ids, dict)
                or any(not isinstance(p, dict) or p.get("estado") not in ("intencion", "hecho") for p in pasos.values())
                or any(not isinstance(v, dict) for v in ids.values())):
            raise Detener(REVISION, "El archivo de progreso tiene una estructura no válida (¿editado o dañado?): revíselo; el script no lo corrige.")
        self.datos = datos

    def preparar_escritura(self) -> None:
        verificar_directorio_ignorado(self.directorio)
        self.directorio.mkdir(parents=True, exist_ok=True)

    def adquirir_candado(self) -> None:
        self.preparar_escritura()
        try:
            fd = os.open(self.ruta_candado, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise Detener(REVISION, f"Existe el candado {self.ruta_candado.name}: otra ejecución está en curso o quedó una interrumpida. Compruebe que no "
                                    "haya otra y retire el archivo manualmente; el script no lo borra.")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"pid": os.getpid(), "inicio": self.reloj().isoformat(timespec="seconds")}, f)
        self._candado = True

    def liberar_candado(self) -> None:
        if self._candado:
            try:
                self.ruta_candado.unlink()
            except OSError:
                pass
            self._candado = False

    # -- escritura atómica
    def guardar(self) -> None:
        self.preparar_escritura()
        fd, tmp = tempfile.mkstemp(prefix=".progreso_", suffix=".tmp", dir=str(self.directorio))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.datos, f, ensure_ascii=False, indent=1, sort_keys=True)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.ruta)
            try:
                os.chmod(self.ruta, 0o600)
            except OSError:
                pass
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def paso(self, nombre: str) -> Optional[dict]:
        return self.datos["pasos"].get(nombre)

    def marcar(self, nombre: str, estado: str, **extra) -> None:
        for v in extra.values():
            if not (v is None or isinstance(v, (str, int, bool))):
                raise TypeError("el progreso solo admite valores simples")
        self.datos["pasos"][nombre] = {"estado": estado, "t": self.reloj().isoformat(timespec="seconds"), **extra}
        self.guardar()

    def id(self, grupo: str, clave: str) -> Optional[object]:
        return self.datos["ids"].get(grupo, {}).get(clave)

    def registrar_id(self, grupo: str, clave: str, valor) -> None:
        self.datos["ids"].setdefault(grupo, {})[clave] = valor
        self.guardar()


# ------------------------------------------------------------------------------------------------ sesión HTTP por rol
def fabrica_httpx(destino: Destino) -> httpx.Client:
    """Cliente HTTP real: sin redirecciones, sin proxies del entorno, con verificación TLS y tiempo de espera."""
    return httpx.Client(base_url=destino.base_url, timeout=30.0, follow_redirects=False, trust_env=False, verify=True)


class Sesion:
    def __init__(self, rol: str, destino: Destino, cliente, registro: List[tuple]):
        self.rol, self.destino, self.http, self.registro = rol, destino, cliente, registro
        self.csrf: Optional[str] = None
        self.usuario: dict = {}

    def _enviar(self, metodo: str, ruta: str, params=None, cuerpo=None) -> httpx.Response:
        if not ruta.startswith("/") or ruta.startswith("//") or "://" in ruta:
            raise Detener(ARGUMENTOS, "Ruta de la API no permitida.")
        cabeceras: Dict[str, str] = {}
        if metodo != "GET":
            cabeceras["Origin"] = self.destino.origin
            if self.csrf:
                cabeceras["X-CSRF-Token"] = self.csrf
        try:
            r = self.http.request(metodo, ruta, params=params, json=cuerpo, headers=cabeceras)
        except httpx.HTTPError as e:
            raise Detener(RED, f"No se pudo contactar con el destino ({type(e).__name__}).")
        self.registro.append((self.rol, metodo, ruta.split("?")[0], r.status_code))
        if 300 <= r.status_code < 400:
            raise Detener(RED, "El destino respondió con una redirección: se rechaza (no se sigue a otros dominios).")
        if r.url.host.lower() != self.destino.host or r.url.scheme != self.destino.esquema:
            raise Detener(RED, "La respuesta no proviene del destino autorizado.")
        return r

    @staticmethod
    def _json(r: httpx.Response) -> dict:
        try:
            j = r.json()
        except ValueError:
            raise Detener(RED, "La API devolvió una respuesta que no es JSON.")
        return j if isinstance(j, dict) else {"datos": j}

    def get(self, ruta: str, params=None) -> dict:
        r = self._enviar("GET", ruta, params=params)
        if r.status_code == 401:
            raise Detener(AUTENTICACION, f"La sesión de {self.rol} no es válida (401).")
        if r.status_code != 200:
            raise Detener(RED, f"GET {ruta.split('?')[0]} respondió {r.status_code}.")
        return self._json(r)

    def post(self, ruta: str, cuerpo: Optional[dict], que: str, esperado=(200, 201)) -> dict:
        r = self._enviar("POST", ruta, cuerpo=cuerpo if cuerpo is not None else {})
        if r.status_code in esperado:
            return self._json(r)
        detalle = ""
        try:
            j = r.json()
            detalle = str(j.get("detalle") or j.get("mensaje") or "")[:200] if isinstance(j, dict) else ""
        except ValueError:
            pass
        codigo = AUTENTICACION if r.status_code == 401 else (REVISION if r.status_code in (403, 409, 422) else RED)
        raise Detener(codigo, f"{que}: la API respondió {r.status_code}{(' · ' + detalle) if detalle else ''}.")

    def entrar(self, correo: str, contrasena: str) -> None:
        """UN solo intento. Un fallo o un bloqueo (429) detiene el script sin reintentar."""
        r = self._enviar("POST", "/auth/inicio-sesion", cuerpo={"correo": correo, "contrasena": contrasena})
        if r.status_code == 429:
            raise Detener(AUTENTICACION, f"La cuenta de {self.rol} está temporalmente bloqueada por intentos fallidos (429). Espere antes de reintentar.")
        if r.status_code != 200:
            raise Detener(AUTENTICACION, f"No se pudo iniciar sesión como {self.rol} ({r.status_code}). No se reintenta.")
        datos = self._json(r).get("datos", {})
        self.csrf, self.usuario = datos.get("csrf"), datos.get("usuario", {})
        if not self.csrf:
            raise Detener(RED, "El inicio de sesión no devolvió el token CSRF.")


# ------------------------------------------------------------------------------------------------ informe
class Informe:
    def __init__(self):
        self.lineas: List[Tuple[str, str, str, str]] = []

    def agregar(self, accion: str, tipo: str, nombre: str, ident: str = "") -> None:
        self.lineas.append((accion, tipo, nombre, ident))

    def creado(self, tipo, nombre, ident=""): self.agregar("CREADO", tipo, nombre, ident)
    def encontrado(self, tipo, nombre, ident=""): self.agregar("ENCONTRADO", tipo, nombre, ident)
    def omitido(self, tipo, nombre, ident=""): self.agregar("OMITIDO", tipo, nombre, ident)
    def pendiente(self, tipo, nombre, ident=""): self.agregar("PENDIENTE", tipo, nombre, ident)

    def cuenta(self, accion: str) -> int:
        return sum(1 for linea in self.lineas if linea[0] == accion)

    def imprimir(self, salida: Callable[[str], None]) -> None:
        salida("")
        salida("RESUMEN (solo identificadores; nada confidencial)")
        for accion, tipo, nombre, ident in self.lineas:
            salida(f"  {accion:<11} {tipo:<20} {nombre}{('  ' + ident) if ident else ''}")
        salida(f"  Total: {self.cuenta('CREADO')} creados · {self.cuenta('ENCONTRADO')} encontrados · {self.cuenta('OMITIDO')} omitidos · "
               f"{self.cuenta('PENDIENTE')} pendientes")


# ------------------------------------------------------------------------------------------------ utilidades
def validar_contrasena_local(contrasena: str, correo: str, nombre: str) -> Optional[str]:
    """Las mismas reglas que aplica el servidor (se comprueban antes de enviar para no gastar intentos)."""
    if len(contrasena) < 12:
        return "La contraseña debe tener al menos 12 caracteres."
    if len(contrasena) > 256:
        return "La contraseña es demasiado larga (máximo 256 caracteres)."
    if len(set(contrasena)) < 4:
        return "La contraseña es demasiado simple: use más caracteres distintos."
    if contrasena.lower() in (correo.lower(), correo.split("@")[0].lower()):
        return "La contraseña no puede ser igual al correo."
    if contrasena.lower() == nombre.lower():
        return "La contraseña no puede ser igual al nombre."
    return None


def _dec(valor) -> Optional[Decimal]:
    try:
        return Decimal(str(valor))
    except (InvalidOperation, ValueError):
        return None


def pedir_confirmacion(io: "EntradaSalida", frase: str) -> bool:
    """True solo si se escribe EXACTAMENTE la frase. Una respuesta vacía o la falta de entrada (EOF) cuentan como confirmación ausente."""
    try:
        texto = io.input(f"Escriba exactamente «{frase}» para confirmar: ")
    except EOFError:
        return False
    return texto.strip() == frase


def reloj_negocio() -> datetime:
    """Hora de pared de la Ciudad de México, sin zona (la misma que usan la API y el trabajador)."""
    return datetime.now(ZoneInfo("America/Mexico_City")).replace(tzinfo=None, microsecond=0)


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


@dataclass
class EntradaSalida:
    getpass: Callable[[str], str]
    input: Callable[[str], str]
    salida: Callable[[str], None]
    esperar: Callable[[float], None]


# ------------------------------------------------------------------------------------------------ siembra
class Sembrador:
    def __init__(self, destino: Destino, modo: str, estado: EstadoLocal, io: EntradaSalida, fabrica, ahora: Callable[[], datetime],
                 admin_correo: str, registro: List[tuple], responder_proveedor: bool = False, incluir_proveedor: bool = False,
                 reanudar_politica: Optional[str] = None, reanudar_revision: bool = False):
        self.d, self.modo, self.estado, self.io, self.fabrica, self.ahora = destino, modo, estado, io, fabrica, ahora
        self.escribe = modo == "aplicar"
        self.admin_correo = admin_correo.strip().lower()
        self.registro, self.informe = registro, Informe()
        self.responder_proveedor, self.incluir_proveedor = responder_proveedor, incluir_proveedor
        self.reanudar_politica, self.reanudar_revision = reanudar_politica, reanudar_revision
        self.admin: Optional[Sesion] = None
        self.coord: Optional[Sesion] = None
        self.prov: Optional[Sesion] = None
        self.ids_prov: Dict[str, str] = {}                       # servicio → proveedor_id
        self._claves_nuevas: Dict[str, str] = {}                 # solo en memoria, hasta iniciar sesión

    # -- sesiones
    def _sesion(self, rol: str) -> Sesion:
        return Sesion(rol, self.d, self.fabrica(self.d), self.registro)

    def _pedir_clave(self, rol: str, correo: str, nueva: bool) -> str:
        if not nueva:
            clave = self.io.getpass(f"Contraseña de la cuenta de {rol} ({correo}): ")
            if not clave:
                raise Detener(ARGUMENTOS, f"No se indicó la contraseña de la cuenta de {rol}.")
            return clave
        clave = self.io.getpass(f"Defina la contraseña NUEVA de la cuenta de {rol} ({correo}; mínimo 12 caracteres): ")
        if clave != self.io.getpass(f"Repita la contraseña de la cuenta de {rol}: "):
            raise Detener(ARGUMENTOS, f"Las contraseñas de la cuenta de {rol} no coinciden.")
        return clave

    def _login_admin(self) -> Sesion:
        self.io.salida("AVISO: iniciar sesión REGISTRA UNA SESIÓN y ACTUALIZA EL ÚLTIMO ACCESO de la cuenta. "
                       + ("Solo se harán consultas GET de negocio." if not self.escribe else "Después se escribirá lo que falte."))
        s = self._sesion("administrador")
        s.entrar(self.admin_correo, self._pedir_clave("administrador", self.admin_correo, False))
        if s.usuario.get("rol") != "administrador" or not s.usuario.get("activo", True):
            raise Detener(REVISION, "La cuenta indicada no es un administrador activo.")
        self.admin = s
        return s

    # -- cuentas
    def _comprobar_cuenta(self, u: dict, nombre: str, rol: str, proveedor_id: Optional[str]) -> None:
        if u.get("rol") != rol or u.get("nombre") != nombre or not u.get("activo"):
            raise Detener(REVISION, f"La cuenta {u.get('correo')} ya existe pero sus datos difieren de los esperados (rol, nombre o estado): no se modifica.")
        if rol == "proveedor" and proveedor_id and u.get("proveedorId") != proveedor_id:
            raise Detener(REVISION, f"La cuenta {u.get('correo')} está vinculada a otro proveedor: no se modifica.")

    def _asegurar_cuenta(self, usuarios: Dict[str, dict], correo: str, nombre: str, rol: str, proveedor_id: Optional[str]) -> Optional[dict]:
        u = usuarios.get(correo)
        if u is not None:
            self._comprobar_cuenta(u, nombre, rol, proveedor_id)
            self.informe.encontrado("cuenta " + rol, correo, u.get("usuarioId", ""))
            self.estado_registrar("cuentas", rol, u.get("usuarioId"))
            return u
        if rol == "proveedor" and not proveedor_id and not self.escribe:
            self.informe.pendiente("cuenta " + rol, correo, "(depende del proveedor de Banquete)")
            return None
        if not self.escribe:
            self.informe.pendiente("cuenta " + rol, correo)
            return None
        clave = self._pedir_clave(rol, correo, True)
        problema = validar_contrasena_local(clave, correo, nombre)
        if problema:
            raise Detener(ARGUMENTOS, problema)
        paso = f"cuenta.{rol}"
        self.estado.marcar(paso, "intencion")
        cuerpo = {"correo": correo, "nombre": nombre, "rol": rol, "contrasena": clave}
        if rol == "proveedor":
            cuerpo["proveedor_id"] = proveedor_id
        r = self.admin.post("/usuarios", cuerpo, f"Crear la cuenta de {rol}", (201,))
        u = r["datos"]
        self._claves_nuevas[rol] = clave
        self.estado.marcar(paso, "hecho", usuario_id=u.get("usuarioId"))
        self.estado_registrar("cuentas", rol, u.get("usuarioId"))
        self.informe.creado("cuenta " + rol, correo, u.get("usuarioId", ""))
        return u

    def estado_registrar(self, grupo: str, clave: str, valor) -> None:
        if self.escribe and self.estado.id(grupo, clave) != valor:
            self.estado.registrar_id(grupo, clave, valor)

    # -- proveedores
    def _paso_proveedores(self, lector: Sesion) -> None:
        existentes = lector.get("/proveedores")["datos"]["proveedores"]
        for servicio, nombre, contacto in PROVEEDORES:
            iguales = [p for p in existentes if " ".join(p["nombre"].lower().split()) == " ".join(nombre.lower().split())]
            if len(iguales) > 1:
                raise Detener(REVISION, f"Hay varios proveedores con el nombre «{nombre}»: revise el catálogo.")
            if iguales:
                p = iguales[0]
                if p["nombre"] != nombre or list(p["servicios"]) != [servicio] or p["contacto"] != contacto or not p["activo"]:
                    raise Detener(REVISION, f"El proveedor «{nombre}» ya existe con otros datos (servicios, contacto o estado): no se modifica.")
                self.ids_prov[servicio] = p["proveedorId"]
                self.informe.encontrado("proveedor", nombre, p["proveedorId"])
                self.estado_registrar("proveedores", servicio, p["proveedorId"])
                continue
            if not self.escribe:
                self.informe.pendiente("proveedor", nombre)
                continue
            paso = f"proveedor.{servicio}"
            self.estado.marcar(paso, "intencion")
            r = self.coord.post("/proveedores", {"nombre": nombre, "servicios": [servicio], "contacto": contacto}, f"Registrar el proveedor «{nombre}»", (201,))
            pid = r["datos"]["proveedorId"]
            self.ids_prov[servicio] = pid
            self.estado.marcar(paso, "hecho", proveedor_id=pid)
            self.estado_registrar("proveedores", servicio, pid)
            self.informe.creado("proveedor", nombre, pid)

    # -- eventos
    def _paso_evento(self, ev: EventoDemo, lector: Sesion) -> Optional[dict]:
        lista = lector.get("/eventos", params={"desde": VENTANA_DESDE, "hasta": VENTANA_HASTA}).get("eventos", [])
        candidatos = [e for e in lista if e.get("clienteId") == ev.cliente_id]
        if len(candidatos) > 1:
            raise Detener(REVISION, f"Hay {len(candidatos)} eventos del cliente {ev.cliente_id}: es ambiguo. Revíselos antes de continuar.")
        paso = f"{ev.etq}.evento"
        if candidatos:
            c = candidatos[0]
            adm = lector.get(f"/eventos/{c['eventoId']}/administracion")
            if (c.get("tipoEvento") != ev.tipo or c.get("fechaHora") != ev.fecha_hora or c.get("lugar") != ev.lugar
                    or adm.get("invitadosAproximados") != ev.invitados or list(adm.get("serviciosSolicitados", [])) != list(ev.servicios)):
                raise Detener(REVISION, f"Ya existe un evento del cliente {ev.cliente_id} con datos distintos a los esperados: no se modifica.")
            previo = self.estado.id("eventos", ev.etq)
            origen = (previo or {}).get("origen") if isinstance(previo, dict) else None
            if origen is None:
                p = self.estado.paso(paso)
                origen = "creado" if p and p.get("estado") in ("intencion", "hecho") else "encontrado_sin_historial"
            if self.escribe and (not isinstance(previo, dict) or previo.get("id") != c["eventoId"] or previo.get("origen") != origen):
                self.estado.registrar_id("eventos", ev.etq, {"id": c["eventoId"], "origen": origen})
                if origen == "creado" and (self.estado.paso(paso) or {}).get("estado") != "hecho":
                    self.estado.marcar(paso, "hecho", evento_id=c["eventoId"])
            self.informe.encontrado("evento", f"{ev.cliente_id} · {ev.tipo[:40]}", c["eventoId"])
            return {"id": c["eventoId"], "origen": origen}
        p = self.estado.paso(paso)
        if p and p.get("estado") == "hecho":
            raise Detener(REVISION, f"El progreso indica que el evento {ev.cliente_id} ya se creó, pero la API no lo muestra en la ventana de fechas: revise.")
        if not self.escribe:
            self.informe.pendiente("evento", f"{ev.cliente_id} · {ev.tipo[:40]}")
            return None
        self.estado.marcar(paso, "intencion")
        r = self.coord.post("/eventos", {"cliente_id": ev.cliente_id, "servicios": list(ev.servicios),
                                         "datos": {"tipo": ev.tipo, "fecha_hora": ev.fecha_hora, "lugar": ev.lugar, "invitados_aproximados": ev.invitados}},
                            f"Registrar el evento {ev.cliente_id}", (201,))
        eid = r.get("evento_id") or r.get("datos", {}).get("evento_id")
        if not eid:
            raise Detener(RED, "La API no devolvió el identificador del evento.")
        self.estado.registrar_id("eventos", ev.etq, {"id": eid, "origen": "creado"})
        self.estado.marcar(paso, "hecho", evento_id=eid)
        self.informe.creado("evento", f"{ev.cliente_id} · {ev.tipo[:40]}", eid)
        return {"id": eid, "origen": "creado"}

    def _paso_propuesta(self, ev: EventoDemo, eid: str, lector: Sesion) -> Optional[dict]:
        props = lector.get(f"/eventos/{eid}/propuestas").get("propuestas", [])
        esperados = [self.ids_prov.get(s) for s in ev.servicios]
        if len(props) > 1:
            raise Detener(REVISION, f"El evento {ev.cliente_id} tiene {len(props)} propuestas: es ambiguo.")
        if props:
            p = props[0]
            if (list(p.get("servicios", [])) != list(ev.servicios) or _dec(p.get("costoTotal")) != _dec(ev.costo) or p.get("condiciones") != CONDICIONES
                    or (None not in esperados and sorted(p.get("proveedoresConsiderados", [])) != sorted(esperados))):
                raise Detener(REVISION, f"La propuesta del evento {ev.cliente_id} difiere de la esperada: no se modifica.")
            self.informe.encontrado("propuesta", ev.cliente_id, p["propuestaId"])
            self.estado_registrar("propuestas", ev.etq, p["propuestaId"])
            return p
        adm = lector.get(f"/eventos/{eid}/administracion")
        if adm.get("estadoEvento") != "En gestión":
            raise Detener(REVISION, f"El evento {ev.cliente_id} no tiene propuesta y ya no está «En gestión»: es ambiguo.")
        if not self.escribe or None in esperados:
            self.informe.pendiente("propuesta", ev.cliente_id)
            return None
        paso = f"{ev.etq}.propuesta"
        self.estado.marcar(paso, "intencion")
        r = self.coord.post(f"/eventos/{eid}/propuestas", {"servicios": list(ev.servicios), "proveedores_considerados": esperados,
                                                          "costo_total": ev.costo, "condiciones": CONDICIONES},
                            f"Crear la propuesta del evento {ev.cliente_id}", (201,))
        pid = r.get("propuesta_id") or r.get("datos", {}).get("propuesta_id")
        self.estado.marcar(paso, "hecho", propuesta_id=pid)
        self.estado_registrar("propuestas", ev.etq, pid)
        self.informe.creado("propuesta", ev.cliente_id, pid or "")
        props = self.coord.get(f"/eventos/{eid}/propuestas").get("propuestas", [])
        return props[0] if len(props) == 1 else None

    def _paso_aceptacion(self, ev: EventoDemo, eid: str, prop: dict, lector: Sesion) -> Optional[dict]:
        if prop.get("estado") == "Aceptada":
            self.informe.omitido("aceptación", ev.cliente_id, prop["propuestaId"])
            return prop
        if prop.get("estado") not in ("En revisión del Cliente", "En elaboración"):
            raise Detener(REVISION, f"La propuesta del evento {ev.cliente_id} está «{prop.get('estado')}»: no se acepta automáticamente.")
        if not self.escribe:
            self.informe.pendiente("aceptación", ev.cliente_id)
            return None
        paso = f"{ev.etq}.aceptacion"
        self.estado.marcar(paso, "intencion")
        self.coord.post(f"/propuestas/{prop['propuestaId']}/aceptacion", {"version_id": prop["versionVigenteId"]},
                        f"Aceptar la propuesta del evento {ev.cliente_id}", (200,))
        nueva = self.coord.get(f"/eventos/{eid}/propuestas").get("propuestas", [])
        if len(nueva) != 1 or nueva[0].get("estado") != "Aceptada":
            raise Detener(REVISION, f"No se pudo comprobar la aceptación de la propuesta del evento {ev.cliente_id}.")
        self.estado.marcar(paso, "hecho")
        self.informe.creado("aceptación", ev.cliente_id, nueva[0]["propuestaId"])
        return nueva[0]

    def _contrato(self, adm: dict, ev: EventoDemo) -> Optional[dict]:
        contratos = adm.get("contratos", [])
        if len(contratos) > 1:
            raise Detener(REVISION, f"El evento {ev.cliente_id} tiene {len(contratos)} contratos: es ambiguo.")
        if contratos and _dec(contratos[0].get("costoTotal")) != _dec(ev.costo):
            raise Detener(REVISION, f"El contrato del evento {ev.cliente_id} tiene un costo distinto del esperado.")
        return contratos[0] if contratos else None

    def _paso_contrato(self, ev: EventoDemo, eid: str, prop: dict, lector: Sesion) -> Optional[dict]:
        c = self._contrato(lector.get(f"/eventos/{eid}/administracion"), ev)
        if c:
            self.informe.encontrado("contrato", ev.cliente_id, c["contratoId"])
            self.estado_registrar("contratos", ev.etq, c["contratoId"])
            return c
        if not self.escribe:
            self.informe.pendiente("contrato", ev.cliente_id)
            return None
        paso = f"{ev.etq}.contrato"
        self.estado.marcar(paso, "intencion")
        self.coord.post(f"/propuestas/{prop['propuestaId']}/contrato", {"politica_incluida": True}, f"Preparar el contrato del evento {ev.cliente_id}", (201,))
        c = self._contrato(self.coord.get(f"/eventos/{eid}/administracion"), ev)
        if not c:
            raise Detener(REVISION, f"No se pudo comprobar la creación del contrato del evento {ev.cliente_id}.")
        self.estado.marcar(paso, "hecho", contrato_id=c["contratoId"])
        self.estado_registrar("contratos", ev.etq, c["contratoId"])
        self.informe.creado("contrato", ev.cliente_id, c["contratoId"])
        return c

    # -- política (no repetible, no verificable) y firma
    def _confirmar(self, frase: str) -> None:
        if not pedir_confirmacion(self.io, frase):
            raise Detener(REVISION, "Confirmación incorrecta o ausente: no se ejecuta la recuperación.")

    def _paso_politica_y_firma(self, ev: EventoDemo, eid: str, origen: str, lector: Sesion) -> bool:
        """Devuelve True si el contrato queda firmado (o confirmado)."""
        c = self._contrato(lector.get(f"/eventos/{eid}/administracion"), ev)
        estado_c, kp, kf = c["estado"], f"{ev.etq}.politica", f"{ev.etq}.firma"
        p = self.estado.paso(kp)
        quiere = self.reanudar_politica == ev.cliente_id
        politica_ok = False
        if estado_c == "Contratación confirmada":
            politica_ok = True                                  # la confirmación exige la política comunicada
            if self.escribe and not (p and p.get("estado") == "hecho"):
                self.estado.marcar(kp, "hecho", inferido="contrato confirmado")
            self.informe.omitido("política de no reembolso", ev.cliente_id, "(contrato confirmado)")
        elif p and p.get("estado") == "hecho":
            politica_ok = True
            self.informe.omitido("política de no reembolso", ev.cliente_id, "(ya comunicada)")
            if quiere:
                raise Detener(ARGUMENTOS, f"La política del evento {ev.cliente_id} ya consta como comunicada: no hay nada que reanudar.")
        else:
            seguro = (p is None and estado_c == "En preparación" and origen == "creado")
            if not seguro and not quiere:
                raise Detener(REVISION, f"No puede comprobarse si la política de no reembolso del evento {ev.cliente_id} ya se comunicó (la API no la expone; "
                                        f"contrato «{estado_c}», progreso «{(p or {}).get('estado', 'sin registro')}»). NO se repite automáticamente. Revise y, si "
                                        f"decide repetirla (solo reescribe la fecha registrada), use --reanudar-politica {ev.cliente_id}.")
            if quiere and not self.escribe:
                raise Detener(ARGUMENTOS, "--reanudar-politica solo se admite con --aplicar.")
            if not self.escribe:
                self.informe.pendiente("política de no reembolso", ev.cliente_id)
            else:
                if quiere:
                    self.io.salida(f"RECUPERACIÓN EXPLÍCITA: se reenviará UNA vez la comunicación de la política del evento {ev.cliente_id}; la fecha registrada "
                                   "se reescribirá con la actual.")
                    self._confirmar(FRASE_POLITICA)
                self.estado.marcar(kp, "intencion")
                self.coord.post(f"/contratos/{c['contratoId']}/comunicacion-politica-no-reembolso", {"fecha": _iso(self.ahora())},
                                f"Comunicar la política del evento {ev.cliente_id}", (200,))
                self.estado.marcar(kp, "hecho", **({"repetida_con_autorizacion": True} if quiere else {}))
                self.informe.creado("política de no reembolso", ev.cliente_id)
                politica_ok = True
        # firma (verificable por el estado del contrato)
        if estado_c in ("Firmado", "Contratación confirmada"):
            self.informe.omitido("firma", ev.cliente_id, c["contratoId"])
            return True
        if estado_c != "En preparación":
            raise Detener(REVISION, f"El contrato del evento {ev.cliente_id} está «{estado_c}»: estado no esperado.")
        if not politica_ok or not self.escribe:
            self.informe.pendiente("firma", ev.cliente_id)
            return False
        self.estado.marcar(kf, "intencion")
        self.coord.post(f"/contratos/{c['contratoId']}/firma", {"fecha": _iso(self.ahora())}, f"Firmar el contrato del evento {ev.cliente_id}", (200,))
        c2 = self._contrato(self.coord.get(f"/eventos/{eid}/administracion"), ev)
        if c2["estado"] not in ("Firmado", "Contratación confirmada"):
            raise Detener(REVISION, f"No se pudo comprobar la firma del contrato del evento {ev.cliente_id}.")
        self.estado.marcar(kf, "hecho")
        self.informe.creado("firma", ev.cliente_id, c["contratoId"])
        return True

    # -- anticipo
    def _paso_anticipo(self, ev: EventoDemo, eid: str, lector: Sesion) -> bool:
        pagos = lector.get(f"/eventos/{eid}/pagos").get("estadosCuenta", [])
        if len(pagos) > 1:
            raise Detener(REVISION, f"El evento {ev.cliente_id} tiene {len(pagos)} estados de cuenta: es ambiguo.")
        if not pagos:
            self.informe.pendiente("anticipo", ev.cliente_id, "(requiere contrato firmado)")
            return False
        ec = pagos[0]
        ant = ec["anticipo"]
        if _dec(ant.get("importe")) != _dec(ev.anticipo):
            raise Detener(REVISION, f"El anticipo del evento {ev.cliente_id} no es de {ev.anticipo}.")
        if ant.get("estado") == "Liquidada" and _dec(ant.get("pagado")) == _dec(ev.anticipo):
            self.informe.omitido("anticipo", ev.cliente_id, "(liquidado)")
            return True
        if ant.get("estado") != "Pendiente" or _dec(ant.get("pagado")) != Decimal(0):
            raise Detener(REVISION, f"El anticipo del evento {ev.cliente_id} está en un estado no esperado («{ant.get('estado')}», pagado {ant.get('pagado')}).")
        if ant.get("plazoVencido"):
            raise Detener(REVISION, f"El plazo del anticipo del evento {ev.cliente_id} venció: no se registra automáticamente.")
        if not self.escribe:
            self.informe.pendiente("anticipo", ev.cliente_id)
            return False
        paso = f"{ev.etq}.anticipo"
        self.estado.marcar(paso, "intencion")
        r = self.admin.post(f"/estados-cuenta/{ec['estadoCuentaId']}/pagos",
                            {"obligacion_id": ant["obligacionId"], "importe": ev.anticipo, "fecha": _iso(self.ahora()), "comprobante": ev.comprobante,
                             "verificar_ahora": True}, f"Registrar el anticipo del evento {ev.cliente_id}", (201,))
        nuevo = self.admin.get(f"/eventos/{eid}/pagos")["estadosCuenta"][0]["anticipo"]
        if nuevo.get("estado") != "Liquidada" or _dec(nuevo.get("pagado")) != _dec(ev.anticipo):
            raise Detener(REVISION, f"No se pudo comprobar la liquidación del anticipo del evento {ev.cliente_id}.")
        self.estado.marcar(paso, "hecho", pago_id=str(r.get("datos", {}).get("pago_id", "")))
        self.informe.creado("anticipo", ev.cliente_id, f"{ev.anticipo} MXN (pago simulado)")
        return True

    def _esperar_organizacion(self, ev: EventoDemo, eid: str, lector: Sesion) -> dict:
        for intento in range(ESPERA_ORGANIZACION_S + 1):
            adm = lector.get(f"/eventos/{eid}/administracion")
            if adm.get("estadoEvento") in ("En organización", "Cancelado") or not self.escribe:
                return adm
            if intento < ESPERA_ORGANIZACION_S:
                self.io.esperar(1.0)
        raise Detener(REVISION, f"El evento {ev.cliente_id} no pasó a «En organización» en {ESPERA_ORGANIZACION_S} s tras el anticipo. Puede que la "
                                "reacción (Outbox) no se esté procesando: revise el trabajador. No se fuerza la confirmación.")

    # -- asignación del proveedor de Banquete (escenario 2)
    def _paso_asignacion(self, ev: EventoDemo, eid: str, adm: dict) -> None:
        pid = self.ids_prov.get(SERVICIO_BANQUETE)
        servicio = next((s for s in adm.get("proveedores", []) if s.get("servicio") == SERVICIO_BANQUETE), None)
        if servicio is None:
            self.informe.pendiente("asignación Banquete", ev.cliente_id, "(el contrato aún no está confirmado)")
            return
        if servicio.get("proveedorId"):
            if servicio["proveedorId"] != pid:
                raise Detener(REVISION, f"El servicio Banquete del evento {ev.cliente_id} está asignado a otro proveedor: no se modifica.")
            self.informe.omitido("asignación Banquete", ev.cliente_id, servicio.get("estado", ""))
            self.estado_registrar("servicios", ev.etq, servicio["servicioContratadoId"])
            return
        if not self.escribe or not pid:
            self.informe.pendiente("asignación Banquete", ev.cliente_id)
            return
        paso = f"{ev.etq}.asignacion"
        self.estado.marcar(paso, "intencion")
        self.coord.post(f"/eventos/{eid}/servicios/{servicio['servicioContratadoId']}/proveedor", {"proveedor_id": pid},
                        f"Asignar el proveedor de Banquete al evento {ev.cliente_id}", (200,))
        nuevo = next(s for s in self.coord.get(f"/eventos/{eid}/administracion")["proveedores"] if s["servicio"] == SERVICIO_BANQUETE)
        if nuevo.get("proveedorId") != pid:
            raise Detener(REVISION, "No se pudo comprobar la asignación del proveedor.")
        self.estado.marcar(paso, "hecho", servicio_id=nuevo["servicioContratadoId"])
        self.estado_registrar("servicios", ev.etq, nuevo["servicioContratadoId"])
        self.informe.creado("asignación Banquete", ev.cliente_id, nuevo.get("estado", ""))

    # -- cancelación y revisión administrativa (escenario 3)
    def _paso_cancelacion_y_revision(self, ev: EventoDemo, eid: str, adm: dict) -> None:
        kc, kr = f"{ev.etq}.cancelacion", f"{ev.etq}.revision"
        estado_ev = adm.get("estadoEvento")
        if estado_ev == "Cancelado":
            pc = self.estado.paso(kc)
            if self.escribe and pc and pc.get("estado") == "intencion":
                self.estado.marcar(kc, "hecho", comprobada="estado Cancelado")          # verificable: el efecto existe
            self.informe.omitido("cancelación", ev.cliente_id, "(ya cancelado)")
        elif estado_ev == "En organización":
            if not self.escribe:
                self.informe.pendiente("cancelación", ev.cliente_id)
                self.informe.pendiente("revisión administrativa", ev.cliente_id)
                return
            self.estado.marcar(kc, "intencion")
            self.coord.post(f"/eventos/{eid}/cancelacion", {"motivo": MOTIVO_CANCELACION}, f"Cancelar el evento {ev.cliente_id}", (200,))
            if self.coord.get(f"/eventos/{eid}/administracion").get("estadoEvento") != "Cancelado":
                raise Detener(REVISION, f"No se pudo comprobar la cancelación del evento {ev.cliente_id}.")
            self.estado.marcar(kc, "hecho")
            self.informe.creado("cancelación", ev.cliente_id)
        else:
            self.informe.pendiente("cancelación", ev.cliente_id, f"(evento «{estado_ev}»)")
            self.informe.pendiente("revisión administrativa", ev.cliente_id)
            return
        pr = self.estado.paso(kr)
        pc = self.estado.paso(kc)
        quiere = self.reanudar_revision
        if pr and pr.get("estado") == "hecho":
            self.informe.omitido("revisión administrativa", ev.cliente_id, "(ya registrada)")
            if quiere:
                raise Detener(ARGUMENTOS, "La revisión administrativa ya consta como registrada: no hay nada que reanudar.")
            return
        ambigua = (pr and pr.get("estado") == "intencion") or not (pc and pc.get("estado") == "hecho")
        if ambigua and not quiere:
            raise Detener(REVISION, f"No puede comprobarse si la revisión administrativa del evento {ev.cliente_id} ya se registró (la API no la expone; progreso "
                                    f"«{(pr or {}).get('estado', 'sin registro')}»). NO se repite automáticamente. Si decide repetirla (solo reescribe su fecha), "
                                    "use --reanudar-revision.")
        if quiere and not self.escribe:
            raise Detener(ARGUMENTOS, "--reanudar-revision solo se admite con --aplicar.")
        if not self.escribe:
            self.informe.pendiente("revisión administrativa", ev.cliente_id)
            return
        if quiere:
            self.io.salida(f"RECUPERACIÓN EXPLÍCITA: se reenviará UNA vez la revisión administrativa del evento {ev.cliente_id}; su fecha se reescribirá.")
            self._confirmar(FRASE_REVISION)
        self.estado.marcar(kr, "intencion")
        r = self.admin.post(f"/eventos/{eid}/revision-administrativa", {"fecha": _iso(self.ahora()), "resultado": RESULTADO_REVISION},
                            f"Registrar la revisión administrativa del evento {ev.cliente_id}", (200,))
        d = r.get("datos", {})
        self.estado.marcar(kr, "hecho", pagos_realizados=str(d.get("pagos_realizados", "")), saldo_pendiente=str(d.get("saldo_pendiente", "")),
                           **({"repetida_con_autorizacion": True} if quiere else {}))
        if _dec(d.get("pagos_realizados")) != _dec(ev.anticipo):
            self.io.salida(f"ADVERTENCIA: la revisión del evento {ev.cliente_id} informó pagos realizados {d.get('pagos_realizados')} (esperado {ev.anticipo}).")
        self.informe.creado("revisión administrativa", ev.cliente_id, f"pagos {d.get('pagos_realizados')} · saldo {d.get('saldo_pendiente')} · sin reembolso")

    # -- cuenta de proveedor: asignaciones
    def _paso_proveedor_sesion(self) -> None:
        e2 = next(e for e in EVENTOS if e.avanza == "organizacion")
        eid = (self.estado.id("eventos", e2.etq) or {}).get("id")
        if not (self.escribe or self.incluir_proveedor):
            return
        correo = CORREO_PROVEEDOR
        if self.prov is None:
            if CORREO_PROVEEDOR not in self._cuentas_existentes and "proveedor" not in self._claves_nuevas:
                self.informe.pendiente("sesión del proveedor", correo, "(la cuenta no existe)")
                return
            clave = self._claves_nuevas.pop("proveedor", None) or self._pedir_clave("proveedor", correo, False)
            s = self._sesion("proveedor")
            s.entrar(correo, clave)
            clave = None
            self.prov = s
        yo = self.prov.get("/auth/yo")["datos"]["usuario"]
        asign = self.prov.get("/mis-asignaciones").get("eventos", [])
        servicio = None
        for e in asign:
            if eid is None or e.get("eventoId") == eid:
                servicio = next((s for s in e.get("servicios", []) if s.get("servicio") == SERVICIO_BANQUETE), None) or servicio
                if servicio is not None:
                    eid = e["eventoId"]
        if servicio is None:
            if self.escribe:
                raise Detener(REVISION, "La asignación de Banquete no aparece en /mis-asignaciones de la cuenta del proveedor.")
            self.informe.pendiente("asignación visible al proveedor", correo)
            return
        estado_s = servicio.get("estado")
        self.informe.encontrado("asignación visible al proveedor", correo, f"{estado_s}")
        if not (self.responder_proveedor and self.escribe):
            if estado_s == "Pendiente de confirmación del proveedor":
                self.informe.omitido("respuesta del proveedor", correo, "(pendiente por diseño: se responde manualmente en la demostración)")
            return
        if estado_s == "Confirmado por el proveedor":
            self.informe.omitido("respuesta del proveedor", correo, "(ya confirmada)")
            return
        if estado_s != "Pendiente de confirmación del proveedor":
            raise Detener(REVISION, f"La asignación está «{estado_s}»: no se responde automáticamente.")
        paso = f"{e2.etq}.respuesta_proveedor"
        self.estado.marcar(paso, "intencion")
        self.prov.post(f"/eventos/{eid}/servicios/{servicio['servicioContratadoId']}/respuesta-proveedor",
                       {"proveedor_id": yo["proveedorId"], "disponible": True}, "Responder como proveedor", (200,))
        despues = next((s for e in self.prov.get("/mis-asignaciones").get("eventos", []) for s in e.get("servicios", [])
                        if s.get("servicioContratadoId") == servicio["servicioContratadoId"]), {})
        if despues.get("estado") != "Confirmado por el proveedor":
            raise Detener(REVISION, "La API no confirmó la respuesta del proveedor.")
        self.estado.marcar(paso, "hecho")
        self.informe.creado("respuesta del proveedor", correo, "Confirmado por el proveedor")

    # -- orquestación
    def ejecutar(self) -> None:
        self._login_admin()
        usuarios = {u["correo"]: u for u in self.admin.get("/usuarios")["datos"]["usuarios"]}
        self._cuentas_existentes = usuarios
        self._asegurar_cuenta(usuarios, CORREO_COORDINADOR, NOMBRE_COORDINADOR, "coordinador", None)
        if self.escribe:
            clave = self._claves_nuevas.pop("coordinador", None) or self._pedir_clave("coordinador", CORREO_COORDINADOR, False)
            self.coord = self._sesion("coordinador")
            self.coord.entrar(CORREO_COORDINADOR, clave)
            clave = None
        lector = self.coord or self.admin
        self._paso_proveedores(lector)
        pid_banquete = self.ids_prov.get(SERVICIO_BANQUETE)
        self._asegurar_cuenta(usuarios, CORREO_PROVEEDOR, NOMBRE_CUENTA_PROVEEDOR, "proveedor", pid_banquete)
        self._cuentas_existentes = {**usuarios}
        for ev in EVENTOS:
            self._flujo_evento(ev, lector)
        self._paso_proveedor_sesion()

    def _flujo_evento(self, ev: EventoDemo, lector: Sesion) -> None:
        ctx = self._paso_evento(ev, lector)
        if ctx is None:
            return
        eid = ctx["id"]
        prop = self._paso_propuesta(ev, eid, lector)
        if ev.avanza == "propuesta":
            return
        if prop is None:
            return
        prop = self._paso_aceptacion(ev, eid, prop, lector)
        if prop is None:
            return
        contrato = self._paso_contrato(ev, eid, prop, lector)
        if contrato is None:
            return
        if not self._paso_politica_y_firma(ev, eid, ctx["origen"], lector):
            return
        if not self._paso_anticipo(ev, eid, lector):
            return
        adm = self._esperar_organizacion(ev, eid, lector)
        if ev.avanza == "organizacion":
            self._paso_asignacion(ev, eid, adm)
        else:
            self._paso_cancelacion_y_revision(ev, eid, adm)


# ------------------------------------------------------------------------------------------------ presentación
def imprimir_plan(salida: Callable[[str], None], destino: Destino, modo: str, ahora: datetime, estado: EstadoLocal) -> None:
    salida(f"Entorno: {destino.entorno.upper()} · destino: {destino.host} (puerto {destino.puerto}) · modo: {modo.upper()}")
    salida(f"Hora de negocio: {_iso(ahora)} · validez de las fechas fijas: hasta {_iso(LIMITE_VALIDEZ)}")
    salida("PLAN (datos ficticios, marcados [DEMO]):")
    salida(f"  Cuentas (las crea el administrador existente): {CORREO_COORDINADOR} · {CORREO_PROVEEDOR} (vinculada al proveedor de Banquete)")
    for servicio, nombre, _ in PROVEEDORES:
        salida(f"  Proveedor ({servicio}): {nombre}")
    for ev in EVENTOS:
        extra = {"propuesta": "propuesta pendiente", "organizacion": "contrato confirmado, política comunicada, anticipo 3,000.00 de 10,000.00, Banquete asignado",
                 "cancelado": "anticipo 3,000.00, cancelación y revisión administrativa con constancia de no reembolso"}[ev.avanza]
        salida(f"  Evento {ev.etq} · {ev.cliente_id} · {ev.fecha_hora} · {ev.costo} MXN · {extra}")
    salida("  Orden: administrador → coordinador → proveedores → cuenta del proveedor → eventos → propuestas → contratos → política y firma → anticipo → "
           "asignación / cancelación → revisión → consulta del proveedor.")
    if estado.ruta.is_file():
        pasos = estado.datos.get("pasos", {})
        salida(f"  Progreso local previo: {len(pasos)} pasos registrados ({estado.ruta.name}).")
    else:
        salida("  Progreso local previo: ninguno.")


def _preflight(destino: Destino, fabrica, registro, estricto: bool, salida: Callable[[str], None]) -> None:
    """Solo GET públicos: confirma que el destino es Eventos Nova y que usa PostgreSQL (en memoria se perderían las cuentas)."""
    s = Sesion("publico", destino, fabrica(destino), registro)
    try:
        salud = s.get("/health")
        if salud.get("estado") != "ok" or salud.get("aplicacion") != "Eventos Nova":
            raise Detener(REVISION, "El destino no responde como Eventos Nova en /health.")
        listo = s.get("/ready")
    except Detener as e:
        if estricto:
            raise
        salida(f"  (no verificado) {e.mensaje}")
        return
    ok = listo.get("estado") == "ok" and listo.get("base_de_datos") == "ok" and listo.get("persistencia") == "postgresql"
    if not ok and estricto:
        raise Detener(REVISION, "El destino no está listo con PostgreSQL (/ready): no se siembra.")
    salida(f"  /health y /ready: {'correctos (PostgreSQL)' if ok else 'NO correctos'}.")


def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Siembra de datos de demostración de Eventos Nova por la API real.",
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--base-url", required=True, help="origen del destino, p. ej. https://eventosnova.onrender.com (sin ruta)")
    ap.add_argument("--entorno", required=True, choices=["local", "produccion"])
    ap.add_argument("--admin-correo", required=True, help="correo del administrador YA existente")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--simular", action="store_true", help="(por omisión) muestra el plan; no inicia sesión ni escribe")
    g.add_argument("--verificar-estado", action="store_true", help="inicia sesión y hace solo GET de negocio")
    g.add_argument("--aplicar", action="store_true", help="escribe lo que falte")
    ap.add_argument("--responder-como-proveedor", action="store_true", help="la cuenta de proveedor responde la asignación (por omisión queda pendiente)")
    ap.add_argument("--incluir-proveedor", action="store_true", help="con --verificar-estado, inicia también la sesión del proveedor")
    ap.add_argument("--reanudar-politica", metavar="CL-DEMO-0N", help="recuperación explícita: reenvía UNA vez la comunicación de la política")
    ap.add_argument("--reanudar-revision", action="store_true", help="recuperación explícita: reenvía UNA vez la revisión administrativa")
    return ap


def main(argv: Optional[List[str]] = None, *, fabrica_http=None, getpass_fn=None, input_fn=None, salida=None, error=None,
         directorio_estado: Optional[Path] = None, ahora_fn=None, esperar=None, registro_http: Optional[list] = None) -> int:
    salida = salida or print
    error = error or (lambda m: print(m, file=sys.stderr))
    ap = _parser()
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return int(e.code or 0) if e.code in (0, None) else ARGUMENTOS
    modo = "aplicar" if a.aplicar else "verificar" if a.verificar_estado else "simular"
    ahora_fn = ahora_fn or reloj_negocio
    registro = registro_http if registro_http is not None else []
    io = EntradaSalida(getpass_fn or getpass.getpass, input_fn or input, salida, esperar or time.sleep)
    fabrica = fabrica_http or fabrica_httpx
    estado = None
    try:
        destino = validar_destino(a.base_url, a.entorno)
        if (a.reanudar_politica or a.reanudar_revision) and modo != "aplicar":
            raise Detener(ARGUMENTOS, "Las opciones de recuperación solo se admiten con --aplicar.")
        if a.reanudar_politica and a.reanudar_politica not in {e.cliente_id for e in EVENTOS if e.anticipo}:
            raise Detener(ARGUMENTOS, "--reanudar-politica admite CL-DEMO-02 o CL-DEMO-03.")
        if a.responder_como_proveedor and modo != "aplicar":
            raise Detener(ARGUMENTOS, "--responder-como-proveedor solo se admite con --aplicar.")
        if modo != "simular" and getpass_fn is None and not sys.stdin.isatty():
            raise Detener(ARGUMENTOS, "Las contraseñas se piden con getpass: se necesita una terminal interactiva (con la entrada redirigida se mostrarían "
                                      "o se filtrarían).")
        ahora = ahora_fn()
        if ahora >= LIMITE_VALIDEZ:
            raise Detener(ARGUMENTOS, f"Las fechas fijas de los eventos (2027) ya no son válidas para sembrar (límite {_iso(LIMITE_VALIDEZ)}): se requiere "
                                      "una revisión de las constantes del script.")
        estado = EstadoLocal(directorio_estado or DIRECTORIO_ESTADO, destino, ahora_fn)
        estado.cargar()
        imprimir_plan(salida, destino, modo, ahora, estado)
        if modo == "simular":
            salida("SIMULACIÓN: no se inicia sesión ni se escribe nada. Comprobaciones públicas (solo GET):")
            _preflight(destino, fabrica, registro, False, salida)
            salida("Fin de la simulación.")
            return OK
        _preflight(destino, fabrica, registro, True, salida)
        if modo == "verificar" and destino.entorno == "produccion":
            salida(f"ADVERTENCIA: --verificar-estado inicia sesión (POST /auth/inicio-sesion) en {destino.host} (PRODUCCIÓN): el login CREA UNA SESIÓN y ACTUALIZA "
                   "EL ÚLTIMO ACCESO de la cuenta. Después solo se hacen consultas GET.")
            if not pedir_confirmacion(io, f"VERIFICAR ESTADO EN {destino.host}"):
                raise Detener(ARGUMENTOS, "Confirmación incorrecta o ausente: no se inicia sesión ni se consulta nada privado.")
        if modo == "aplicar":
            salida(f"ATENCIÓN: se va a ESCRIBIR datos de demostración en {destino.host} ({destino.entorno}).")
            if destino.entorno == "produccion" and not pedir_confirmacion(io, f"SEMBRAR DEMO EN {destino.host}"):
                raise Detener(ARGUMENTOS, "Confirmación incorrecta o ausente: no se escribe nada.")
            estado.adquirir_candado()
        s = Sembrador(destino, modo, estado, io, fabrica, ahora_fn, a.admin_correo, registro, a.responder_como_proveedor, a.incluir_proveedor,
                      a.reanudar_politica, a.reanudar_revision)
        try:
            s.ejecutar()
        finally:
            s.informe.imprimir(salida)
        if modo == "aplicar":
            estado.datos["ultimo_informe"] = {"t": _iso(ahora_fn()), "creados": s.informe.cuenta("CREADO"), "encontrados": s.informe.cuenta("ENCONTRADO"),
                                              "omitidos": s.informe.cuenta("OMITIDO"), "pendientes": s.informe.cuenta("PENDIENTE")}
            estado.guardar()
        salida("Fin: correcto." if modo == "aplicar" else "Fin de la verificación (no se escribió ningún dato de negocio).")
        return OK
    except Detener as e:
        error(f"DETENIDO (código {e.codigo}): {e.mensaje}")
        return e.codigo
    except Exception as e:                                           # noqa: BLE001  (sin traza: no se exponen datos de la sesión)
        error(f"DETENIDO (código {RED}): error inesperado ({type(e).__name__}). Revise el progreso con --verificar-estado antes de repetir; "
              "nada se reintenta automáticamente.")
        return RED
    finally:
        if estado is not None:
            estado.liberar_candado()


if __name__ == "__main__":
    raise SystemExit(main())
