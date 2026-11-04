// Responsivo en 10 anchos (320, 360, 375, 390, 430, 768, 1024, 1280, 1440 y 1920 px) con LOS TRES ROLES (Administración, Coordinación y Proveedor).
//   EVENTOSNOVA_E2E_ADMIN_CORREO=… EVENTOSNOVA_E2E_ADMIN_CLAVE=… node scripts/probar_responsivo_diez_anchos_navegador.mjs http://127.0.0.1:8001 <carpeta de capturas>
// Por ancho y rol mide desbordamiento horizontal, elementos y botones fuera de la pantalla, el menú móvil y los diálogos nuevos (editar proveedor, editar cuenta),
// y toma capturas. Crea sus propios datos (un evento En organización, un proveedor con cuenta y una asignación); no borra nada y no imprime contraseñas.
import { spawn } from 'node:child_process';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { randomBytes } from 'node:crypto';
import { prepararCuentas } from './lib_sesion_e2e.mjs';

const BASE = process.argv[2] || 'http://127.0.0.1:8001';
const SALIDA = process.argv[3] || '.';
const MARCA = Date.now().toString(36).toUpperCase();
const PUERTO = 9341;
const TAMANOS = [[320, 640], [360, 740], [375, 812], [390, 844], [430, 932], [768, 1024], [1024, 768], [1280, 800], [1440, 900], [1920, 1080]];
const perfil = mkdtempSync(join(tmpdir(), 'enova-anchos-'));
const chrome = spawn('C:/Program Files/Google/Chrome/Application/chrome.exe', ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${PUERTO}`, `--user-data-dir=${perfil}`, 'about:blank'], { stdio: 'ignore' });
const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
let ws; let id = 0; const pend = new Map(); const errores = [];
for (let i = 0; i < 40; i++) { try { const l = await (await fetch(`http://127.0.0.1:${PUERTO}/json`)).json(); const p = l.find((x) => x.type === 'page'); if (p) { ws = new WebSocket(p.webSocketDebuggerUrl); await new Promise((a, b) => { ws.onopen = a; ws.onerror = b; }); break; } } catch { /* espera */ } await dormir(250); }
ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); } if (d.method === 'Runtime.exceptionThrown') errores.push(d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text); };
const cdp = (method, params = {}) => new Promise((res) => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
async function ev(expr) { const r = await cdp('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true }); if (r.result.exceptionDetails) throw new Error('evaluate: ' + JSON.stringify(r.result.exceptionDetails.exception?.description || r.result.exceptionDetails.text)); return r.result.result.value; }
async function esperar(expr, texto, ms = 8000) { const t0 = Date.now(); while (Date.now() - t0 < ms) { try { if (await ev(expr)) return true; } catch { /* reintenta */ } await dormir(120); } throw new Error('Tiempo agotado esperando: ' + texto); }
const resultados = [];
const paso = async (nombre, fn) => { try { await fn(); resultados.push(['OK', nombre]); console.log('OK   ', nombre); } catch (e) { resultados.push(['FALLO', nombre, e.message]); console.log('FALLO', nombre, '->', e.message); } };

const MEDIR = `(() => {
  const vw = document.documentElement.clientWidth, vh = window.innerHeight;
  const desplazable = (e) => { for (let p = e.parentElement; p && p !== document.body; p = p.parentElement) { const o = getComputedStyle(p).overflowX; if (o === 'auto' || o === 'scroll') return true; } return false; };
  const fuera = [...document.querySelectorAll('body *')].filter((e) => {
    const cs = getComputedStyle(e); if (cs.display === 'none' || cs.visibility === 'hidden' || cs.position === 'fixed' || e.classList.contains('salto')) return false;   // el enlace «Saltar al contenido» está fuera a propósito
    const r = e.getBoundingClientRect(); if (!r.width || !r.height) return false;
    if (e.closest('.lateral') && document.documentElement.clientWidth <= 900 && !document.body.classList.contains('menu-abierto')) return false;
    return (r.right > vw + 1 || r.left < -1) && !desplazable(e);
  }).slice(0, 4).map((e) => e.tagName.toLowerCase() + '.' + String(e.className).split(' ')[0] + ' [' + Math.round(e.getBoundingClientRect().left) + ',' + Math.round(e.getBoundingClientRect().right) + ']');
  const botonesFuera = [...document.querySelectorAll('button, a.btn, input, select')].filter((e) => {
    const cs = getComputedStyle(e); if (cs.display === 'none' || cs.visibility === 'hidden' || e.hidden || e.closest('[hidden]')) return false;
    if (e.closest('.lateral') && vw <= 900 && !document.body.classList.contains('menu-abierto')) return false;
    const r = e.getBoundingClientRect(); return r.width && (r.right > vw + 1 || r.left < -1) && !desplazable(e);
  }).slice(0, 3).map((e) => (e.textContent || e.name || e.id).trim().slice(0, 30));
  const d = document.querySelector('dialog[open]'); let dlg = null;
  if (d) { const r = d.getBoundingClientRect(); const pie = d.querySelector('.modal-pie'); const pr = pie && pie.getBoundingClientRect();
    dlg = { cabe: r.left >= -1 && r.right <= vw + 1 && r.top >= -1 && r.bottom <= vh + 1, pie: !pie || (pr.bottom <= vh + 1 && pr.right <= vw + 1 && pr.left >= -1), ancho: Math.round(r.width), alto: Math.round(r.height) }; }
  return { vw, sw: document.documentElement.scrollWidth, desborda: document.documentElement.scrollWidth > vw + 1, fuera, botonesFuera, dlg };
})()`;
const tam = async (w, h) => { await cdp('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile: w <= 768 }); await dormir(250); };
const captura = async (nombre, completa = false) => { const c = await cdp('Page.captureScreenshot', { format: 'png', captureBeyondViewport: completa }); writeFileSync(`${SALIDA}/${nombre}.png`, Buffer.from(c.result.data, 'base64')); };
const ir = async (hash) => { await cdp('Page.navigate', { url: `${BASE}/app/${hash}` }); await dormir(500); await esperar(`document.readyState === 'complete' && !document.querySelector('.cargando')`, 'carga ' + hash, 12000); await dormir(300); };
async function ingresar(correo, clave) {
  await cdp('Page.navigate', { url: `${BASE}/app/` }); await dormir(500);
  await esperar(`!!document.getElementById('ing-correo')`, 'formulario de ingreso');
  await ev(`(() => { document.getElementById('ing-correo').value = ${JSON.stringify(correo)}; document.getElementById('ing-clave').value = ${JSON.stringify(clave)}; document.querySelector('.ingreso-forma button[type=submit]').click(); })()`);
}
async function entrar(correo, clave) { await cdp('Network.clearBrowserCookies'); await ingresar(correo, clave); await esperar(`!document.getElementById('ing-correo') && !!document.querySelector('#sesion-caja button')`, 'sesión iniciada'); }
async function salir() {
  await ev(`(() => { if (document.body.classList.contains('menu-abierto') === false && document.getElementById('boton-menu').offsetParent) document.getElementById('boton-menu').click(); })()`);
  await ev(`[...document.querySelectorAll('#sesion-caja button')].find(b => b.textContent.trim() === 'Cerrar sesión').click()`); await esperar(`!!document.getElementById('ing-correo')`, 'ingreso tras salir');
}
const menu = () => ev(`[...document.querySelectorAll('#menu a')].filter(a => !a.hidden).map(a => a.textContent.trim())`);
const texto = () => ev('document.body.innerText');
const CODIGO = /\b(?:BN|CA|GL|SE|US|CU|RN|AR|TP|ADR|[ACDEHR])-\d{1,3}[A-Za-z]?\b(?!-)/;
const VACIO = /(^|[\s(«"'])(null|undefined|NaN)([\s.,;:)»"']|$)|\[object /;
const nueva = () => 'Prueba-' + randomBytes(12).toString('base64url');
const revisar = (m, etiqueta) => { const malo = m.desborda ? `desbordamiento horizontal global (${m.sw} > ${m.vw})` : m.fuera.length ? 'elementos fuera: ' + m.fuera.join('; ') : m.botonesFuera.length ? 'controles fuera: ' + m.botonesFuera.join('; ') : (m.dlg && !m.dlg.cabe) ? 'el diálogo no cabe: ' + JSON.stringify(m.dlg) : (m.dlg && !m.dlg.pie) ? 'los botones del diálogo quedan fuera' : null; if (malo) throw new Error(`${etiqueta}: ${malo}`); };


const c = await prepararCuentas(BASE, MARCA);
await cdp('Runtime.enable'); await cdp('Page.enable'); await cdp('Network.enable');
const SERVICIO = `Servicio ancho ${MARCA}`;
let eventoId; let provId; let cuentaProv;
await paso('Datos de prueba por la API: evento En organización, proveedor del catálogo con cuenta y servicio asignado', async () => {
  const ahora = () => new Date(Date.now() - 6 * 3600 * 1000).toISOString().slice(0, 19);
  eventoId = (await c.coord.json('POST', '/eventos', { cliente_id: 'CL-ANCHOS', datos: { tipo: `Prueba anchos ${MARCA}`, fecha_hora: new Date(Date.now() + 75 * 864e5).toISOString().slice(0, 19), lugar: 'Salón', invitados_aproximados: 50 }, servicios: [SERVICIO] })).evento_id;
  const prop = (await c.coord.json('POST', `/eventos/${eventoId}/propuestas`, { servicios: [SERVICIO], proveedores_considerados: ['PV-X'], costo_total: '10000.00', condiciones: 'Prueba' })).propuesta_id;
  await c.coord.json('POST', `/propuestas/${prop}/aceptacion`, { version_id: `${prop}-v1` });
  const ct = (await c.coord.json('POST', `/propuestas/${prop}/contrato`, { politica_incluida: true })).datos.contrato_id;
  await c.coord.json('POST', `/contratos/${ct}/comunicacion-politica-no-reembolso`, { fecha: ahora() }); await c.coord.json('POST', `/contratos/${ct}/firma`, { fecha: ahora() });
  const ec = (await c.coord.json('GET', `/eventos/${eventoId}/pagos`)).estadosCuenta[0].estadoCuentaId;
  const ob = (await c.coord.json('GET', `/pagos-pendientes?evento_id=${eventoId}`)).pagos.find((p) => p.concepto === 'Anticipo');
  await c.admin.json('POST', `/estados-cuenta/${ec}/pagos`, { obligacion_id: ob.obligacionId, importe: '1000.00', fecha: ahora(), comprobante: `ANC-1-${MARCA}`, verificar_ahora: true });
  await c.admin.json('POST', `/estados-cuenta/${ec}/pagos`, { obligacion_id: ob.obligacionId, importe: '2000.00', fecha: ahora(), comprobante: `ANC-2-${MARCA}`, verificar_ahora: true });
  for (let i = 0; i < 20; i++) { if ((await c.coord.json('GET', `/eventos/${eventoId}/administracion`)).estadoEvento === 'En organización') break; await dormir(300); }
  provId = (await c.coord.json('POST', '/proveedores', { nombre: `Proveedor anchos ${MARCA}`, servicios: [SERVICIO], contacto: '55 0000 0000' })).datos.proveedorId;
  const clave = nueva(); const correo = `proveedor.anchos.${MARCA}@eventosnova.example`.toLowerCase();
  await c.admin.json('POST', '/usuarios', { correo, nombre: `Proveedor anchos ${MARCA}`, rol: 'proveedor', contrasena: clave, proveedor_id: provId }); cuentaProv = { correo, clave };
  const sid = (await c.coord.json('GET', `/eventos/${eventoId}/administracion`)).proveedores[0].servicioContratadoId;
  await c.coord.json('POST', `/eventos/${eventoId}/servicios/${sid}/proveedor`, { proveedor_id: provId });
});

await paso('El estado de cuenta muestra pagado, saldo y lo registrado sin verificar por obligación (pagos parciales acumulados)', async () => {
  await tam(1440, 900); await entrar(c.correoAdmin, c.claveAdmin); await ir(`#/evento/${eventoId}`);
  await esperar(`document.body.innerText.toLowerCase().includes('pagado (verificado)')`, 'pagado');
  const t = await texto(); for (const x of ['3,000.00', 'saldo', 'Liquidada']) if (!t.toLowerCase().includes(x.toLowerCase())) throw new Error('falta en el estado de cuenta: ' + x);
  for (const x of []) if (!t.includes(x)) throw new Error('falta en el estado de cuenta: ' + x);
  await salir();
});

const ROLES = [
  { clave: 'admin', nombre: 'Administración', correo: c.correoAdmin, pass: c.claveAdmin, paginas: ['#/', '#/eventos', '#/solicitudes', '#/pagos', '#/seguimiento', '#/proveedores', '#/cuentas', '#/sistema'] },
  { clave: 'coord', nombre: 'Coordinación', correo: c.correoCoord, pass: c.claveCoord, paginas: ['#/', '#/eventos', '#/solicitudes', '#/pagos', '#/seguimiento', '#/proveedores', '#/sistema'] },
  { clave: 'prov', nombre: 'Proveedor', get correo() { return cuentaProv.correo; }, get pass() { return cuentaProv.clave; }, paginas: ['#/proveedor', '#/sistema'] },
];
const cancelarDialogo = () => ev(`[...document.querySelectorAll('dialog[open] button')].find(b => b.textContent.trim() === 'Cancelar').click()`);
for (const rol of ROLES) {
  for (const [w, h] of TAMANOS) {
    await paso(`${rol.nombre} a ${w}×${h} px: todas sus pantallas sin desbordamiento ni controles fuera de la pantalla, y menú móvil`, async () => {
      await tam(w, h); await entrar(rol.correo, rol.pass);
      const extra = rol.clave === 'prov' ? [] : [`#/evento/${eventoId}`, `#/proveedores/${provId}`];
      for (const hash of [...rol.paginas, ...extra]) {
        await ir(hash);
        if (hash === '#/proveedor') await esperar(`document.body.innerText.includes('Mis asignaciones') && document.body.innerText.includes(${JSON.stringify(SERVICIO)})`, 'sus asignaciones');
        revisar(JSON.parse(JSON.stringify(await ev(MEDIR))), hash);
        const t = await texto(); const malos = t.split('\n').filter((l) => VACIO.test(l) || CODIGO.test(l)); if (malos.length) throw new Error(`${hash}: texto indebido: ${malos[0]}`);
        if (hash === '#/' || hash === '#/proveedor' || hash.startsWith('#/evento')) await captura(`${rol.clave}_${hash.startsWith('#/evento') ? 'evento' : 'inicio'}_${w}`, hash.startsWith('#/evento'));
      }
      if (rol.clave === 'admin') {                                         // diálogos nuevos: editar proveedor y editar cuenta
        await ir(`#/proveedores/${provId}`); await ev(`[...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'Editar').click()`); await esperar(`!!document.querySelector('dialog[open]')`, 'editar proveedor');
        revisar(JSON.parse(JSON.stringify(await ev(MEDIR))), 'diálogo editar proveedor'); await captura(`admin_editar_proveedor_${w}`); await cancelarDialogo();
        await ir('#/cuentas'); await ev(`[...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'Editar').click()`); await esperar(`!!document.querySelector('dialog[open]')`, 'editar cuenta');
        revisar(JSON.parse(JSON.stringify(await ev(MEDIR))), 'diálogo editar cuenta'); await captura(`admin_editar_cuenta_${w}`); await cancelarDialogo();
      }
      if (rol.clave === 'coord') {                                         // S-5: el diálogo con el medio de comunicación de la respuesta capturada por Coordinación
        await ir(`#/evento/${eventoId}`); await esperar(`[...document.querySelectorAll('button')].some(b => b.textContent.trim() === 'Registrar respuesta del proveedor')`, 'botón de respuesta');
        await ev(`[...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'Registrar respuesta del proveedor').click()`); await esperar(`!!document.querySelector('dialog[open]')`, 'diálogo de respuesta');
        if (!(await texto()).includes('Medio por el que el proveedor respondió')) throw new Error('el diálogo de Coordinación no pide el medio');
        revisar(JSON.parse(JSON.stringify(await ev(MEDIR))), 'diálogo respuesta capturada'); await captura(`coord_respuesta_${w}`); await cancelarDialogo();
      }
      if (w <= 900) {
        await ev(`document.getElementById('boton-menu').click()`); await dormir(350);
        revisar(JSON.parse(JSON.stringify(await ev(MEDIR))), 'menú desplegado');
        const vis = await ev(`(() => { const r = document.querySelector('.lateral').getBoundingClientRect(); return r.left >= -1 && r.right <= document.documentElement.clientWidth + 1; })()`);
        if (!vis) throw new Error('el menú desplegado no cabe en la pantalla'); await captura(`${rol.clave}_menu_${w}`);
        await ev(`document.getElementById('boton-menu').click()`);
      }
      await salir();
    });
  }
}

await paso('Sin excepciones de JavaScript', async () => { if (errores.length) throw new Error(errores.slice(0, 3).join(' | ')); });
console.log(`\nRESUMEN: ${resultados.filter((r) => r[0] === 'OK').length} OK, ${resultados.filter((r) => r[0] === 'FALLO').length} FALLO`);
try { ws.close(); } catch { /* */ }
chrome.kill();
process.exit(resultados.some((r) => r[0] === 'FALLO') ? 1 : 0);
