// Verifica en Chrome real el formulario «Crear cuenta» (visibilidad, obligatoriedad, valor y carga útil según el rol).
// La API corre EN MEMORIA, sin autenticación y sin ninguna base de datos; `enviar` se sustituye por un espía: no se crea ninguna cuenta.
// Requisitos: Node 22+ y Google Chrome (variable CHROME_PATH si no está en la ruta habitual). No usa PostgreSQL ni la base de ningún entorno.
// Uso:  node scripts/probar_formulario_cuentas_navegador.mjs <carpeta del proyecto> <python> [puerto_api] [puerto_cdp]
//       python -m unittest tests.test_interfaz_formulario_cuentas   (con EVENTOSNOVA_PRUEBAS_NAVEGADOR=1)
import { spawn } from 'node:child_process';
import { existsSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const REPO = process.argv[2];
const PY = process.argv[3];
const PUERTO_API = Number(process.argv[4] || 18961);
const PUERTO_CDP = Number(process.argv[5] || 9444);
const CHROME = [process.env.CHROME_PATH, 'C:/Program Files/Google/Chrome/Application/chrome.exe', '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser']
  .find((p) => p && existsSync(p));
if (!CHROME) { console.error('No se encontró Google Chrome (defina CHROME_PATH).'); process.exit(2); }
const BASE = `http://127.0.0.1:${PUERTO_API}`;
const pausa = (ms) => new Promise((r) => setTimeout(r, ms));

const env = { ...process.env, EVENTOSNOVA_AUTENTICACION: 'desactivada', EVENTOSNOVA_ENTORNO: 'local', PYTHONDONTWRITEBYTECODE: '1' };
for (const k of Object.keys(env)) if (k === 'DATABASE_URL' || k === 'TEST_DATABASE_URL' || k === 'EVENTOSNOVA_PERSISTENCIA') delete env[k];
const api = spawn(PY, ['-B', '-m', 'uvicorn', 'api.main:app', '--app-dir', 'src', '--port', String(PUERTO_API)], { cwd: REPO, env, stdio: 'ignore' });
const perfil = mkdtempSync(join(tmpdir(), 'enova-cuentas-'));
const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PUERTO_CDP}`, `--user-data-dir=${perfil}`, '--no-first-run', '--disable-gpu', '--window-size=1000,900', 'about:blank'], { stdio: 'ignore' });

async function esperar(url, intentos = 60) {
  for (let i = 0; i < intentos; i++) { try { const r = await fetch(url); if (r.ok) return r; } catch { /* aún no */ } await pausa(500); }
  throw new Error('No respondió: ' + url);
}

let ws; let idMsg = 0; const pend = new Map();
function enviar(metodo, params = {}) { return new Promise((res, rej) => { const id = ++idMsg; pend.set(id, { res, rej }); ws.send(JSON.stringify({ id, method: metodo, params })); }); }
async function evaluar(expresion) {
  const r = await enviar('Runtime.evaluate', { expression: expresion, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error('Error en la página: ' + JSON.stringify(r.exceptionDetails.exception?.description || r.exceptionDetails.text));
  return r.result.value;
}

const PAGINA = `(async () => {
  const ui = await import('/app/js/ui.js'); const ac = await import('/app/js/acciones.js');
  const def = ac.ACCIONES.crearCuenta;
  const provs = [{ proveedorId: 'PV-1', nombre: 'Proveedor Uno' }, { proveedorId: 'PV-2', nombre: 'Proveedor Dos' }];
  const espera = (ms = 40) => new Promise((r) => setTimeout(r, ms));
  window.__envios = [];
  const abrir = () => { document.querySelectorAll('dialog.modal').forEach((d) => d.remove());
    ui.abrirFormulario({ ...def, campos: def.campos({ proveedores: provs }), enviar: async (v) => { window.__envios.push(v); return { ok: true }; } }); };
  const q = (n) => document.querySelector('dialog.modal [name="' + n + '"]');
  const fila = (n) => q(n).closest('.campo');
  const est = (n) => { if (!q(n)) return { cerrado: true, atributoHidden: false, display: '', visible: false, valor: '', error: '' };
    const f = fila(n), c = q(n), r = f.getBoundingClientRect();
    return { atributoHidden: f.hidden, display: getComputedStyle(f).display, visible: r.width > 0 && r.height > 0, valor: c.value, error: f.querySelector('.error-campo').textContent.trim() }; };
  const poner = async (n, v) => { const c = q(n); if (!c) return; c.value = v; c.dispatchEvent(new Event('input', { bubbles: true })); c.dispatchEvent(new Event('change', { bubbles: true })); await espera(); };
  const llenar = async (rol) => { await poner('nombre', 'Persona de Prueba'); await poner('correo', 'prueba@ejemplo.mx'); await poner('contrasena', 'una-contrasena-larga-1'); await poner('rol', rol); };
  const mandar = async () => { const fm = document.querySelector('dialog.modal form'); if (!fm) return; fm.requestSubmit(); await espera(80);
    const b = document.getElementById('btn-confirmar'); if (b) { b.click(); await espera(80); } };
  const out = {};
  // 1. estado inicial al abrir
  abrir(); await espera();
  out.inicial = { rol: q('rol').value, proveedor: est('proveedor_id'), opcionesProveedor: [...q('proveedor_id').options].map((o) => o.value + '|' + o.textContent) };
  // 2. visibilidad por rol
  out.porRol = {};
  for (const rol of ['administrador', 'coordinador', 'proveedor']) { await poner('rol', rol); out.porRol[rol] = est('proveedor_id'); }
  // 3. cargas útiles
  out.envios = {};
  for (const rol of ['administrador', 'coordinador']) { abrir(); await espera(); await llenar(rol); window.__envios.length = 0; await mandar(); out.envios[rol] = window.__envios.slice(); }
  // proveedor sin elegir proveedor: debe bloquearse
  abrir(); await espera(); await llenar('proveedor'); window.__envios.length = 0; await mandar();
  out.proveedorSinElegir = { enviado: window.__envios.slice(), campo: est('proveedor_id') };
  // proveedor con selección explícita
  await poner('proveedor_id', 'PV-2'); window.__envios.length = 0; await mandar(); out.envios.proveedor = window.__envios.slice();
  // 4. cambio dinámico: proveedor+PV-2 -> coordinador -> proveedor -> administrador
  abrir(); await espera(); await llenar('proveedor'); await poner('proveedor_id', 'PV-2');
  out.cambio = { conPV2: est('proveedor_id') };
  await poner('rol', 'coordinador'); out.cambio.alPasarACoordinador = est('proveedor_id');
  await poner('rol', 'proveedor'); out.cambio.alVolverAProveedor = est('proveedor_id');
  await poner('rol', 'administrador'); out.cambio.alPasarAAdministrador = est('proveedor_id');
  window.__envios.length = 0; await mandar(); out.cambio.envioComoAdministrador = window.__envios.slice();
  document.querySelectorAll('dialog.modal').forEach((d) => d.remove());
  return out;
})()`;

let fallos = 0; const resultados = [];
const comprobar = (desc, ok, detalle = '') => { resultados.push({ desc, ok, detalle }); if (!ok) fallos++; };

try {
  await esperar(BASE + '/health');
  await esperar(`http://127.0.0.1:${PUERTO_CDP}/json/version`);
  const lista = await (await fetch(`http://127.0.0.1:${PUERTO_CDP}/json/list`)).json();
  const objetivo = lista.find((t) => t.type === 'page');
  ws = new WebSocket(objetivo.webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pend.has(d.id)) { const { res, rej } = pend.get(d.id); pend.delete(d.id); d.error ? rej(new Error(JSON.stringify(d.error))) : res(d.result); } };
  await enviar('Page.enable');
  await enviar('Page.navigate', { url: BASE + '/app/' });
  await pausa(2500);
  const o = await evaluar(PAGINA);

  const ocultoReal = (e) => e.visible === false && e.display === 'none';
  const visibleReal = (e) => e.visible === true && e.display !== 'none';
  comprobar('Al abrir, el rol preseleccionado es el primero de la lista (Coordinación)', o.inicial.rol === 'coordinador', o.inicial.rol);
  comprobar('Al abrir con Coordinación el campo «Proveedor» está OCULTO (display none, sin tamaño)', ocultoReal(o.inicial.proveedor), JSON.stringify(o.inicial.proveedor));
  comprobar('Administración: el campo Proveedor está oculto', ocultoReal(o.porRol.administrador), JSON.stringify(o.porRol.administrador));
  comprobar('Coordinación: el campo Proveedor está oculto', ocultoReal(o.porRol.coordinador), JSON.stringify(o.porRol.coordinador));
  comprobar('Proveedor: el campo Proveedor está visible', visibleReal(o.porRol.proveedor), JSON.stringify(o.porRol.proveedor));
  comprobar('Proveedor: al aparecer NO trae un proveedor preseleccionado (exige elegir)', o.porRol.proveedor.valor === '', 'valor=' + o.porRol.proveedor.valor);
  comprobar('Administración: la carga útil no incluye proveedor_id', o.envios.administrador.length === 1 && !('proveedor_id' in o.envios.administrador[0]), JSON.stringify(o.envios.administrador));
  comprobar('Coordinación: la carga útil no incluye proveedor_id', o.envios.coordinador.length === 1 && !('proveedor_id' in o.envios.coordinador[0]), JSON.stringify(o.envios.coordinador));
  comprobar('Proveedor sin elegir proveedor: se bloquea (no se envía) y marca el campo', o.proveedorSinElegir.enviado.length === 0 && o.proveedorSinElegir.campo.error !== '', JSON.stringify(o.proveedorSinElegir));
  comprobar('Proveedor con selección explícita: se envía rol y proveedor_id', o.envios.proveedor.length === 1 && o.envios.proveedor[0].rol === 'proveedor' && o.envios.proveedor[0].proveedor_id === 'PV-2', JSON.stringify(o.envios.proveedor));
  comprobar('Cambio Proveedor→Coordinación: el campo se oculta y su valor se reinicia', ocultoReal(o.cambio.alPasarACoordinador) && o.cambio.alPasarACoordinador.valor === '', JSON.stringify(o.cambio.alPasarACoordinador));
  comprobar('Cambio de vuelta a Proveedor: reaparece SIN el valor anterior', visibleReal(o.cambio.alVolverAProveedor) && o.cambio.alVolverAProveedor.valor === '', JSON.stringify(o.cambio.alVolverAProveedor));
  comprobar('Cambio a Administración: oculto y sin proveedor_id al enviar', ocultoReal(o.cambio.alPasarAAdministrador) && o.cambio.envioComoAdministrador.length === 1 && !('proveedor_id' in o.cambio.envioComoAdministrador[0]), JSON.stringify(o.cambio.envioComoAdministrador));
} catch (e) {
  fallos++; resultados.push({ desc: 'La verificación no pudo completarse', ok: false, detalle: String(e.message || e) });
} finally {
  try { ws && ws.close(); } catch { /* nada */ }
  chrome.kill(); api.kill();
  await pausa(800);
  try { rmSync(perfil, { recursive: true, force: true, maxRetries: 5, retryDelay: 300 }); } catch { /* el perfil temporal puede tardar en liberarse */ }
}
for (const r of resultados) console.log((r.ok ? 'OK    ' : 'FALLA ') + r.desc + (r.ok ? '' : '\n        → ' + r.detalle));
console.log(`\n${resultados.length - fallos} de ${resultados.length} comprobaciones correctas`);
process.exit(fallos ? 1 : 0);
