// Complemento de los recorridos de navegador por rol (Chrome real, API con PostgreSQL, autenticación activa): lo que los otros guiones no cubren.
//   EVENTOSNOVA_E2E_ADMIN_CORREO=… EVENTOSNOVA_E2E_ADMIN_CLAVE=… node scripts/probar_roles_completo_navegador.mjs http://127.0.0.1:8001 <carpeta de capturas>
// Administración: registrar un pago SIN verificarlo y verificarlo después (el evento pasa a En organización), autorizar un cambio, devoluciones.
// Coordinación: seguimiento del anticipo y que no ve la autorización. Proveedor: respuesta, recarga de la página y persistencia tras cerrar e iniciar sesión de nuevo.
// Usa SUS PROPIOS datos de prueba («Verificación de roles …»): no toca el conjunto controlado que se deja para las pruebas manuales. No imprime contraseñas.
import { spawn } from 'node:child_process';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { randomBytes } from 'node:crypto';
import { prepararCuentas } from './lib_sesion_e2e.mjs';

const BASE = process.argv[2] || 'http://127.0.0.1:8001';
const SALIDA = process.argv[3] || '.';
const MARCA = Date.now().toString(36).toUpperCase();
const PUERTO = 9340;
const perfil = mkdtempSync(join(tmpdir(), 'enova-roles-'));
const chrome = spawn('C:/Program Files/Google/Chrome/Application/chrome.exe', ['--headless=new', '--disable-gpu', '--no-sandbox', `--remote-debugging-port=${PUERTO}`, `--user-data-dir=${perfil}`, '--window-size=1280,900', 'about:blank'], { stdio: 'ignore' });
const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
let ws; let id = 0; const pend = new Map(); const errores = [];
for (let i = 0; i < 40; i++) { try { const l = await (await fetch(`http://127.0.0.1:${PUERTO}/json`)).json(); const p = l.find((x) => x.type === 'page'); if (p) { ws = new WebSocket(p.webSocketDebuggerUrl); await new Promise((a, b) => { ws.onopen = a; ws.onerror = b; }); break; } } catch { /* espera */ } await dormir(250); }
ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); } if (d.method === 'Runtime.exceptionThrown') errores.push(d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text); };
const cdp = (method, params = {}) => new Promise((res) => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
async function ev(expr) { const r = await cdp('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true }); if (r.result.exceptionDetails) throw new Error('evaluate: ' + JSON.stringify(r.result.exceptionDetails.exception?.description || r.result.exceptionDetails.text)); return r.result.result.value; }
async function esperar(expr, texto, ms = 9000) { const t0 = Date.now(); while (Date.now() - t0 < ms) { try { if (await ev(expr)) return true; } catch { /* reintenta */ } await dormir(120); } throw new Error('Tiempo agotado esperando: ' + texto); }
const NL = String.fromCharCode(10);
const seccion = (titulo) => ev(`(() => { const s = [...document.querySelectorAll('section')].find(x => x.innerText.includes(${JSON.stringify(titulo)})); return s ? s.innerText.split(String.fromCharCode(10)).join(' | ').slice(0, 700) : 'sin sección'; })()`);
const resultados = [];
const paso = async (nombre, fn) => { try { await fn(); resultados.push(['OK', nombre]); console.log('OK   ', nombre); } catch (e) { let dom = ''; try { dom = (await ev("(document.querySelector('dialog[open]') || document.querySelector('#contenido')).innerText.slice(0, 300)")).split(NL).join(' | '); } catch { /* */ } resultados.push(['FALLO', nombre, e.message]); console.log('FALLO', nombre, '->', e.message); if (dom) console.log('   DOM:', dom); } };
const helpers = `(() => {
  window.$t = (txt, sel='button,a') => [...document.querySelectorAll(sel)].find(e => e.textContent.trim() === txt && e.offsetParent !== null);
  window.$ti = (txt, sel='button,a') => [...document.querySelectorAll(sel)].find(e => e.textContent.trim().includes(txt) && e.offsetParent !== null);
  window.$campo = (txt) => { const l = [...document.querySelectorAll('dialog[open] label')].find(x => x.textContent.includes(txt)); return l && document.getElementById(l.getAttribute('for')); };
  window.$poner = (txt, v) => { const c = $campo(txt); if (!c) throw new Error('campo no encontrado: ' + txt); if (c.type === 'checkbox') c.checked = v; else c.value = v; c.dispatchEvent(new Event('input', {bubbles:true})); c.dispatchEvent(new Event('change', {bubbles:true})); };
  window.$dlg = () => document.querySelector('dialog[open]');
})()`;
const ir = async (hash) => {
  const destino = `${BASE}/app/${hash}`;
  if ((await ev('location.href')) === destino) await cdp('Page.reload');                // la misma URL no se vuelve a cargar sola: se recarga para ver el estado actual del servidor
  else await cdp('Page.navigate', { url: destino });
  await dormir(500); await esperar(`document.readyState === 'complete' && !document.querySelector('.cargando')`, 'carga ' + hash, 12000); await ev(helpers); };
const recargar = async () => { await cdp('Page.reload'); await dormir(800); await esperar(`document.readyState === 'complete' && !document.querySelector('.cargando')`, 'recarga', 12000); await ev(helpers); };
async function entrar(correo, clave) {
  await cdp('Network.clearBrowserCookies'); await cdp('Page.navigate', { url: `${BASE}/app/` }); await dormir(500);
  await esperar(`!!document.getElementById('ing-correo')`, 'formulario de ingreso');
  await ev(`(() => { document.getElementById('ing-correo').value = ${JSON.stringify(correo)}; document.getElementById('ing-clave').value = ${JSON.stringify(clave)}; document.querySelector('.ingreso-forma button[type=submit]').click(); })()`);
  await esperar(`!document.getElementById('ing-correo') && !!document.querySelector('#sesion-caja button')`, 'sesión iniciada'); await ev(helpers);
}
const confirmar = async () => { await esperar(`!!document.getElementById('btn-confirmar')`, 'confirmación'); await ev(`document.getElementById('btn-confirmar').click()`); };
const texto = () => ev('document.body.innerText');
const ahora = () => new Date(Date.now() - 6 * 3600 * 1000).toISOString().slice(0, 19);
const CODIGO = /\b(?:BN|CA|GL|SE|US|CU|RN|AR|TP|ADR|[ACDEHR])-\d{1,3}[A-Za-z]?\b(?!-)/;
const VACIO = /(^|[\s(«"'])(null|undefined|NaN)([\s.,;:)»"']|$)|\[object /;

const c = await prepararCuentas(BASE, MARCA);
await cdp('Runtime.enable'); await cdp('Page.enable'); await cdp('Network.enable');
const j = (quien, m, r, b) => quien.json(m, r, b);
async function eventoHastaFirma(servicios, etiqueta) {
  const ev_ = (await j(c.coord, 'POST', '/eventos', { cliente_id: 'CL-VERIF', datos: { tipo: `Verificación de roles ${etiqueta} ${MARCA}`, fecha_hora: new Date(Date.now() + 75 * 864e5).toISOString().slice(0, 19), lugar: 'Salón de verificación', invitados_aproximados: 30 }, servicios })).evento_id;
  const prop = (await j(c.coord, 'POST', `/eventos/${ev_}/propuestas`, { servicios, proveedores_considerados: ['PV-X'], costo_total: '10000.00', condiciones: 'Verificación' })).propuesta_id;
  await j(c.coord, 'POST', `/propuestas/${prop}/aceptacion`, { version_id: `${prop}-v1` });
  const ct = (await j(c.coord, 'POST', `/propuestas/${prop}/contrato`, { politica_incluida: true })).datos.contrato_id;
  await j(c.coord, 'POST', `/contratos/${ct}/comunicacion-politica-no-reembolso`, { fecha: ahora() }); await j(c.coord, 'POST', `/contratos/${ct}/firma`, { fecha: ahora() });
  return { evento: ev_, contrato: ct };
}
async function enOrganizacion(evento) { for (let i = 0; i < 25; i++) { if ((await j(c.coord, 'GET', `/eventos/${evento}/administracion`)).estadoEvento === 'En organización') return; await dormir(300); } throw new Error('no llegó a En organización'); }
const SERVICIO_PROV = `Servicio de verificación ${MARCA}`;
let T1; let T2; let T3; let provX; let cuentaProv; let servicioId;

await paso('Datos propios de la verificación (por la API): eventos con contrato firmado y un proveedor con su cuenta', async () => {
  T1 = await eventoHastaFirma(['Banquete', 'Fotografía'], 'pagos y autorización'); T2 = await eventoHastaFirma(['Banquete'], 'seguimiento del anticipo'); T3 = await eventoHastaFirma([SERVICIO_PROV], 'proveedor');
  provX = (await j(c.coord, 'POST', '/proveedores', { nombre: `Prueba verificación proveedor ${MARCA}`, servicios: [SERVICIO_PROV], contacto: '' })).datos.proveedorId;
  const clave = 'Prueba-' + randomBytes(12).toString('base64url'); const correo = `proveedor.verif.${MARCA}@eventosnova.example`.toLowerCase();
  await j(c.admin, 'POST', '/usuarios', { correo, nombre: `Proveedor verificación ${MARCA}`, rol: 'proveedor', contrasena: clave, proveedor_id: provX }); cuentaProv = { correo, clave };
  const ec = (await j(c.admin, 'GET', `/eventos/${T3.evento}/pagos`)).estadosCuenta[0].estadoCuentaId; const ob = (await j(c.admin, 'GET', `/pagos-pendientes?evento_id=${T3.evento}`)).pagos.find((p) => p.concepto === 'Anticipo');
  await j(c.admin, 'POST', `/estados-cuenta/${ec}/pagos`, { obligacion_id: ob.obligacionId, importe: '3000.00', fecha: ahora(), comprobante: `CMP-VERIF-${MARCA}`, verificar_ahora: true });
  await enOrganizacion(T3.evento);
  servicioId = (await j(c.coord, 'GET', `/eventos/${T3.evento}/administracion`)).proveedores[0].servicioContratadoId;
  await j(c.coord, 'POST', `/eventos/${T3.evento}/servicios/${servicioId}/proveedor`, { proveedor_id: provX });
});

await paso('Administración: «Pagos y devoluciones» lista el anticipo pendiente y las devoluciones (vacías) sin errores', async () => {
  await entrar(c.correoAdmin, c.claveAdmin); await ir('#/pagos');
  await esperar(`document.body.innerText.includes('Pagos pendientes o vencidos') && document.body.innerText.includes('Devoluciones pendientes')`, 'secciones');
  await esperar(`[...document.querySelectorAll('tbody tr')].some(r => r.textContent.includes(${JSON.stringify(T1.evento)}))`, 'el anticipo del evento de prueba');
  if (await ev(`!!document.querySelector('.caja-error')`)) throw new Error('caja de error');
});

await paso('Administración: registra un pago SIN verificarlo (queda Registrado) y lo verifica después: el anticipo queda Liquidada y el evento pasa a En organización', async () => {
  await ev(`[...document.querySelectorAll('tbody tr')].find(r => r.textContent.includes(${JSON.stringify(T1.evento)})).querySelector('button').click()`); await esperar(`!!$dlg() && !!$campo('Importe pagado')`, 'formulario de pago');
  await ev(`$poner('Importe pagado', '3000'); $poner('Referencia del comprobante', 'CMP-VERIF-${MARCA}-1'); $poner('Verificar el pago ahora', false)`);
  await ev(`$dlg().querySelector('button[type=submit]').click()`); await confirmar(); await esperar(`!$dlg()`, 'cierre del formulario');
  await ir(`#/evento/${T1.evento}`); await esperar(`document.body.innerText.includes('Registrado')`, 'pago Registrado');
  if ((await j(c.admin, 'GET', `/eventos/${T1.evento}/administracion`)).estadoEvento === 'En organización') throw new Error('el evento no debía pasar a En organización con el pago solo Registrado');
  await esperar(`!!$ti('Verificar pago')`, 'botón Verificar pago'); await ev(`$ti('Verificar pago').click()`); await esperar(`!!$dlg() && !!$campo('Identificador del pago')`, 'formulario');
  if (!(await ev(`$campo('Identificador del pago').value`)).startsWith('PG-')) throw new Error('no propone el identificador del pago registrado');
  await ev(`$dlg().querySelector('button[type=submit]').click()`); await dormir(400); if (await ev(`!!document.getElementById('btn-confirmar')`)) await confirmar();
  await esperar(`!$dlg()`, 'verificación'); await enOrganizacion(T1.evento);
  await ir(`#/evento/${T1.evento}`); await esperar(`document.querySelector('h1 .insignia')?.textContent === 'En organización' && document.body.innerText.includes('Liquidada')`, 'estado visible');
});

await paso('Administración autoriza un cambio (y Coordinación no ve la autorización): flujo viabilidad → decisión del Cliente → autorización', async () => {
  const sc = (await j(c.coord, 'POST', '/solicitudes-cambio', { evento_id: T1.evento, contrato_id: T1.contrato, descripcion: 'Cambio de verificación', tarifa_vigente: '500.00' })).datos.solicitud_id;
  await j(c.coord, 'POST', `/solicitudes-cambio/${sc}/viabilidad`, { viable: true, motivo: '', costo_adicional_proveedor: '1000.00' });
  const estadoDe = async () => (await j(c.admin, 'GET', `/solicitudes?evento_id=${T1.evento}`)).solicitudes.find((x) => x.solicitudId === sc).estadoActual;
  let estado = await estadoDe(); if (estado !== 'Pendiente de aprobación del Cliente') throw new Error('estado tras la viabilidad: ' + estado);
  await j(c.coord, 'POST', `/solicitudes-cambio/${sc}/decision-cliente`, { actor: 'Cliente', aprobada: true, fecha: ahora(), motivo: '' });
  estado = await estadoDe(); if (estado !== 'Pendiente de autorización') throw new Error('estado tras la decisión del Cliente: ' + estado);
  await ir(`#/evento/${T1.evento}`);
  await esperar(`!!$ti('autorización de Administración')`, 'acción de autorización para Administración').catch(async (e) => { console.log('      sección de solicitudes:', await seccion('Solicitudes del evento')); throw e; });
  await ev(`$ti('autorización de Administración').click()`); await esperar(`!!$dlg() && !!$campo('Quién decide')`, 'formulario');
  await ev(`$dlg().querySelector('button[type=submit]').click()`); await dormir(400); if (await ev(`!!document.getElementById('btn-confirmar')`)) await confirmar(); await esperar(`!$dlg()`, 'autorización registrada');
  estado = await estadoDe(); console.log('      estado tras la autorización:', estado);
  if (estado === 'Pendiente de autorización') throw new Error('la autorización no cambió el estado');
  await entrar(c.correoCoord, c.claveCoord); await ir(`#/evento/${T1.evento}`); await esperar(`!!document.querySelector('h1')`, 'evento');
  if (await ev(`!!$ti('autorización de Administración')`)) throw new Error('Coordinación ve la acción de autorizar');
});

await paso('Coordinación: seguimiento del anticipo pendiente (acción real con respuesta del sistema y sin acciones de pago)', async () => {
  await ir(`#/evento/${T2.evento}`);
  await esperar(`!!$ti('seguimiento al anticipo')`, 'acción de seguimiento').catch(async (e) => { console.log('      sección de contratación:', await seccion('Contratación')); throw e; });
  if (await ev(`!!$t('Registrar pago') || !!$ti('Verificar pago')`)) throw new Error('Coordinación ve acciones de pago');
  await ev(`$ti('seguimiento al anticipo').click()`); await esperar(`!!$dlg() && !!$campo('Resultado del contacto')`, 'formulario');
  await ev(`$poner('Resultado del contacto', 'Se contactó al Cliente (verificación)')`);
  await ev(`$dlg().querySelector('button[type=submit]').click()`); await dormir(400); if (await ev(`!!document.getElementById('btn-confirmar')`)) await confirmar();
  await esperar(`!$dlg() || !$dlg().querySelector('.modal-alerta').hidden`, 'respuesta del sistema');
  const salida = await ev(`$dlg() ? $dlg().querySelector('.modal-alerta').innerText : [...document.querySelectorAll('.aviso')].map(a => a.innerText).join(' / ')`);
  console.log('      respuesta del sistema:', String(salida).split(NL).join(' ').slice(0, 160)); if (!salida) throw new Error('sin respuesta visible');
  if (await ev(`!!$dlg()`)) await ev(`[...document.querySelectorAll('dialog[open] button')].find(b => b.textContent.trim() === 'Cancelar').click()`);
});

await paso('Proveedor: ve sus asignaciones sin escribir ningún identificador, responde desde la interfaz; tras recargar y volver a entrar sigue Confirmado', async () => {
  await entrar(cuentaProv.correo, cuentaProv.clave); await ir('#/proveedor');
  if (await ev(`!!document.getElementById('p-ev')`)) throw new Error('la cuenta de proveedor todavía debe escribir el identificador del evento');
  await esperar(`document.body.innerText.includes('Mis datos') && document.body.innerText.includes(${JSON.stringify('Prueba verificación proveedor ' + MARCA)})`, 'sus datos');
  const lista = async () => { await esperar(`document.body.innerText.includes('Mis asignaciones') && document.body.innerText.includes(${JSON.stringify(SERVICIO_PROV)}) && !!document.querySelector('.tabla')`, 'su asignación'); };
  await lista(); await esperar(`document.body.innerText.includes('Pendiente de confirmación del proveedor')`, 'estado pendiente');
  if (!(await ev('document.body.innerText')).includes(T3.evento)) throw new Error('la asignación no muestra su evento');
  await ev(`$ti('Registrar respuesta').click()`); await esperar(`!!$dlg()`, 'formulario'); await ev(`$dlg().querySelector('button[type=submit]').click()`); await confirmar();
  await esperar(`!$dlg()`, 'respuesta registrada'); await esperar(`document.body.innerText.includes('Confirmado por el proveedor')`, 'confirmado en pantalla');
  await recargar(); await lista();
  await esperar(`document.body.innerText.includes('Confirmado por el proveedor')`, 'sigue Confirmado tras recargar');
  await ev(`[...document.querySelectorAll('#sesion-caja button')].find(b => b.textContent.trim() === 'Cerrar sesión').click()`); await esperar(`!!document.getElementById('ing-correo')`, 'cierre');
  await entrar(cuentaProv.correo, cuentaProv.clave); await ir('#/proveedor'); await lista(); await esperar(`document.body.innerText.includes('Confirmado por el proveedor')`, 'sigue Confirmado tras volver a entrar');
  if ((await j(c.coord, 'GET', `/eventos/${T3.evento}/administracion`)).proveedores[0].estado !== 'Confirmado por el proveedor') throw new Error('el servidor no lo tiene confirmado');
  const cap = await cdp('Page.captureScreenshot', { format: 'png' }); writeFileSync(SALIDA + '/proveedor_persistencia.png', Buffer.from(cap.result.data, 'base64'));
});

await paso('Sin null, undefined ni códigos internos en las pantallas recorridas por cada rol', async () => {
  for (const [correo, clave, hashes] of [[c.correoAdmin, c.claveAdmin, ['#/', '#/pagos', `#/evento/${T1.evento}`, '#/cuentas', '#/proveedores']], [c.correoCoord, c.claveCoord, ['#/', `#/evento/${T2.evento}`, '#/seguimiento', '#/proveedores']]]) {
    await entrar(correo, clave);
    for (const h of hashes) { await ir(h); await dormir(500); const malos = (await texto()).split(NL).filter((l) => VACIO.test(l) || CODIGO.test(l)); if (malos.length) throw new Error(`${h}: ${malos[0]}`); }
  }
});

await paso('Sin excepciones de JavaScript', async () => { if (errores.length) throw new Error(errores.slice(0, 3).join(' | ')); });
console.log(`${NL}RESUMEN: ${resultados.filter((r) => r[0] === 'OK').length} OK, ${resultados.filter((r) => r[0] === 'FALLO').length} FALLO`);
try { ws.close(); } catch { /* */ }
chrome.kill();
process.exit(resultados.some((r) => r[0] === 'FALLO') ? 1 : 0);
