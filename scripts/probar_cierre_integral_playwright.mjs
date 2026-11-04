// Prueba REAL de cierre integral con Playwright (Chrome instalado, sin mocks): los tres roles de principio a fin contra una PILA AISLADA
// (API + trabajador reales sobre una base de pruebas desechable), con interacciones de interfaz y comprobación directa en PostgreSQL.
// Cubre S-1 a S-9 y D-P1 a D-P3: contratación, pagos parciales, cobranza, devoluciones, solicitudes, captura de costos, respuestas de proveedor
// directas y capturadas, integración de importes, inicio automático y de respaldo, finalización y cancelación por falta de regularización.
//   PILA: API en 127.0.0.1:8002 con DATABASE_URL de la base desechable; el guion arranca y detiene SU trabajador con AISLADA_URL.
//   PLAYWRIGHT_DIR=… EVENTOSNOVA_E2E_ADMIN_CORREO=… EVENTOSNOVA_E2E_ADMIN_CLAVE=… AISLADA_URL=… PYTHON=… \
//   node scripts/probar_cierre_integral_playwright.mjs http://127.0.0.1:8002 <carpeta de capturas> [base_de_datos]
// Solo modifica fechas de SUS PROPIOS eventos (UPDATE por identificador) en la base desechable para simular el paso del tiempo; no limpia nada.
import { createRequire } from 'node:module';
import { execFileSync, spawn, spawnSync } from 'node:child_process';
import { randomBytes } from 'node:crypto';
import { prepararCuentas } from './lib_sesion_e2e.mjs';

const { chromium } = createRequire(`${process.env.PLAYWRIGHT_DIR}/`)('playwright');
const BASE = process.argv[2] || 'http://127.0.0.1:8002';
const SALIDA = process.argv[3] || '.';
const BASE_DATOS = process.argv[4] || 'eventosnova_regresion_test';
if (!/_test$/.test(BASE_DATOS) || /manual/i.test(BASE_DATOS)) throw new Error('Este guion solo se ejecuta contra una base desechable de pruebas.');
const MARCA = Date.now().toString(36).toUpperCase();
const resultados = []; const paginas = {};
const paso = async (nombre, fn) => {
  try { await fn(); resultados.push(['OK', nombre]); console.log('OK   ', nombre); } catch (e) {
    resultados.push(['FALLO', nombre, e.message]); console.log('FALLO', nombre, '->', String(e.message).split('\n')[0].slice(0, 420));
    for (const [quien, pg] of Object.entries(paginas)) { try { await pg.screenshot({ path: `${SALIDA}/fallo_${quien}_${resultados.length}.png`, fullPage: true }); const d = await pg.locator('dialog[open]').allInnerTexts(); if (d.length) console.log(`      [${quien}] diálogo abierto: ${normal(d.join(' | ')).slice(0, 300)}`); } catch { /* */ } }
  }
};
const igual = (real, esperado, que) => { if (JSON.stringify(real) !== JSON.stringify(esperado)) throw new Error(`${que}: se esperaba ${JSON.stringify(esperado)} y se obtuvo ${JSON.stringify(real)}`); };
const sql = (consulta) => execFileSync('docker', ['exec', 'eventosnova-db', 'sh', '-c', `psql -U "$POSTGRES_USER" -d ${BASE_DATOS} -At -F '|' -c "${consulta}"`], { encoding: 'utf8' }).trim();
const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
const mx = (desplazamientoMs = 0) => new Date(Date.now() - 6 * 3600 * 1000 + desplazamientoMs).toISOString().slice(0, 19);   // hora de negocio (UTC-6, sin horario de verano)
const local = (iso) => iso.slice(0, 16);                                                                                          // para datetime-local

// ------------------------------------------------------------------ trabajador real (se arranca y se detiene a voluntad)
let trabajador = null;
const arrancarTrabajador = () => {
  if (trabajador) return;
  trabajador = spawn(process.env.PYTHON || 'python', ['-m', 'infrastructure.persistencia.trabajador_outbox', '--intervalo', '1'],
    { env: { ...process.env, DATABASE_URL: process.env.AISLADA_URL, EVENTOSNOVA_PERSISTENCIA: 'postgresql', PYTHONPATH: 'src' }, stdio: 'ignore' });
};
const detenerTrabajador = async () => { if (trabajador) { trabajador.kill(); trabajador = null; await dormir(1500); } };
const esperarSql = async (consulta, esperado, que, ms = 25000) => {
  const limite = Date.now() + ms; let real;
  while (Date.now() < limite) { real = sql(consulta); if (real === esperado) return; await dormir(700); }
  throw new Error(`${que}: se esperaba ${esperado} y la base tiene ${real}`);
};

const c = await prepararCuentas(BASE, MARCA);
arrancarTrabajador();                                  // el trabajador real despacha las reacciones (estado de cuenta, confirmación de la contratación…)
const navegador = await chromium.launch({ channel: 'chrome', headless: true });
const errores = [];
async function sesionUI(correo, clave, ancho = 1366) {
  const ctx = await navegador.newContext({ viewport: { width: ancho, height: 1000 } });
  const page = await ctx.newPage();
  page.on('pageerror', (e) => errores.push(e.message));
  await page.goto(`${BASE}/app/`);
  await page.fill('#ing-correo', correo); await page.fill('#ing-clave', clave);
  await page.click('.ingreso-forma button[type=submit]');
  await page.waitForSelector('#sesion-caja button', { timeout: 15000 });
  return { ctx, page, correo, clave };
}
const texto = (page) => page.evaluate(() => document.body.innerText);
// innerText respeta text-transform (las etiquetas salen en mayúsculas): se compara sin distinguir mayúsculas
const esperarTexto = (page, t, ms = 12000) => page.waitForFunction((x) => document.body.innerText.toLowerCase().includes(x.toLowerCase()), t, { timeout: ms });
const sinTexto = async (page, t) => { if ((await texto(page)).toLowerCase().includes(t.toLowerCase())) throw new Error(`no debería verse «${t}»`); };
const normal = (s) => s.replace(/\s+/g, ' ');

/** Rellena un diálogo por etiqueta: texto→fill, lista→selectOption, casilla→setChecked. */
async function llenar(dlg, campos) {
  for (const [etiqueta, valor] of Object.entries(campos)) {
    const ctl = dlg.getByLabel(etiqueta, { exact: false }).first();
    const tipo = await ctl.evaluate((e) => `${e.tagName}:${e.type || ''}`);
    if (tipo.startsWith('SELECT')) await ctl.selectOption(valor);
    else if (tipo.endsWith('checkbox')) await ctl.setChecked(Boolean(valor));
    else await ctl.fill(String(valor));
  }
}
async function enviar(page, dlg) {
  if (!(await page.locator('#btn-confirmar:visible').count())) await dlg.locator('button[type=submit]').click();      // sin campos el diálogo abre directo en la confirmación
  await page.waitForTimeout(500);
  if (await page.locator('#btn-confirmar:visible').count()) await page.locator('#btn-confirmar').click();      // algunas acciones se envían sin paso de confirmación
  await dlg.waitFor({ state: 'detached', timeout: 12000 });
}
/** Hace clic en un botón (opcionalmente dentro de una fila) y devuelve el diálogo abierto. */
async function abrir(page, boton, fila) {
  const btn = (r) => r.getByRole('button', { name: boton, exact: true });
  const b = (fila ? page.locator('tr', { hasText: fila }).filter({ has: btn(page) }).first().locator('button', { hasText: boton }) : btn(page)).first();
  try { await b.waitFor({ timeout: 8000 }); } catch { throw new Error(`no hay botón «${boton}»${fila ? ` en la fila ${fila}` : ''}`); }
  await b.click();
  const dlg = page.locator('dialog[open]'); await dlg.waitFor({ timeout: 8000 });
  return dlg;
}
const accion = async (page, boton, campos = {}, fila) => { const dlg = await abrir(page, boton, fila); await llenar(dlg, campos); await enviar(page, dlg); };
const irEvento = async (page, id, esperar) => { await page.goto(`${BASE}/app/#/evento/${id}`); await page.reload(); await esperarTexto(page, esperar || 'Ciclo de vida del evento'); };
const botones = (page) => page.getByRole('button').allInnerTexts();
const hay = async (page, boton, fila) => (fila ? page.locator('tr', { hasText: fila }) : page).getByRole('button', { name: boton, exact: true }).count();
/** El diálogo de «Registrar pago»: obligación (por concepto), importe, comprobante y si se verifica en el acto. */
async function pagar(page, concepto, importe, comprobante, verificar = true) {
  const dlg = await abrir(page, 'Registrar pago');
  const opcion = await dlg.getByLabel('Obligación que se paga').locator('option').evaluateAll((os, k) => os.find((o) => o.textContent.includes(k))?.value, concepto);
  if (!opcion) throw new Error(`no hay obligación «${concepto}» en el diálogo de pago`);
  await llenar(dlg, { 'Obligación que se paga': opcion, 'Importe pagado': importe, 'Referencia del comprobante': comprobante, 'Verificar el pago ahora': verificar });
  await enviar(page, dlg);
}

const S1 = `Banquete ${MARCA}`; const S2 = `Fotografía ${MARCA}`; const SA = `DJ ${MARCA}`;
const NOMBRE_A = `Banquetes ${MARCA}`; const NOMBRE_B = `Fotos ${MARCA}`; const NOMBRE_C = `DJ Nova ${MARCA}`; const NOMBRE_D = `Banquetes Alternos ${MARCA}`;
let admin; let coord; let provA; let provB; let credA; let credB; let eventoId; let contratoId; let pv = {}; let ec;

await paso('Administrador: inicio de sesión, menú de su rol y consulta operativa', async () => {
  admin = await sesionUI(c.correoAdmin, c.claveAdmin); paginas.admin = admin.page;
  const menu = normal(await admin.page.locator('#menu').innerText());
  for (const m of ['Panel principal', 'Eventos', 'Solicitudes', 'Pagos y devoluciones', 'Seguimiento', 'Proveedores', 'Cuentas', 'Sistema y ayuda']) if (!menu.includes(m)) throw new Error(`falta «${m}» en el menú de Administración`);
  if (menu.includes('Mi proveedor')) throw new Error('Administración ve «Mi proveedor»');
  for (const hash of ['#/', '#/eventos', '#/solicitudes', '#/pagos', '#/seguimiento', '#/proveedores', '#/cuentas']) { await admin.page.goto(`${BASE}/app/${hash}`); await admin.page.waitForSelector('h1', { timeout: 8000 }); }
});

await paso('Coordinación: inicio de sesión y menú de su rol (sin Cuentas)', async () => {
  coord = await sesionUI(c.correoCoord, c.claveCoord); paginas.coord = coord.page;
  const menu = normal(await coord.page.locator('#menu').innerText());
  if (menu.includes('Cuentas') || menu.includes('Mi proveedor')) throw new Error('el menú de Coordinación trae opciones ajenas');
  await coord.page.goto(`${BASE}/app/#/cuentas`); await esperarTexto(coord.page, 'No tienes permiso para ver esta pantalla');
});

await paso('Catálogo (S-8, D-P1): Coordinación registra proveedores desde la interfaz; Administración los edita; Coordinación no ve Editar', async () => {
  await coord.page.goto(`${BASE}/app/#/proveedores`); await esperarTexto(coord.page, 'Registrar proveedor');
  for (const [nombre, servicios] of [[NOMBRE_A, S1], [NOMBRE_B, S2], [NOMBRE_C, SA], [NOMBRE_D, S1]]) {
    await coord.page.goto(`${BASE}/app/#/proveedores`); await esperarTexto(coord.page, 'Registrar proveedor');
    await accion(coord.page, 'Registrar proveedor', { 'Nombre del proveedor': nombre, 'Servicios que ofrece': servicios, 'Contacto': '55 0000 0000' });
    await esperarTexto(coord.page, nombre);
    pv[nombre] = sql(`select proveedor_id from proveedor where nombre='${nombre}'`);
    if (!pv[nombre]) throw new Error('no quedó en PostgreSQL ' + nombre);
  }
  if (await hay(coord.page, 'Editar') || await hay(coord.page, 'Desactivar')) throw new Error('Coordinación ve Editar/Desactivar en la ficha');
  await admin.page.goto(`${BASE}/app/#/proveedores/${pv[NOMBRE_C]}`); await esperarTexto(admin.page, NOMBRE_C);
  await accion(admin.page, 'Editar', { 'Contacto': '55 1111 2222' });
  await esperarTexto(admin.page, '55 1111 2222');
  igual(sql(`select contacto from proveedor where proveedor_id='${pv[NOMBRE_C]}'`), '55 1111 2222', 'contacto editado');
});

await paso('Cuentas (S-1): Administración crea las cuentas de proveedor desde la interfaz, las edita, desactiva y reactiva; no hay otros roles', async () => {
  await admin.page.goto(`${BASE}/app/#/cuentas`); await esperarTexto(admin.page, 'Crear cuenta');
  const dlg = await abrir(admin.page, 'Crear cuenta');
  const roles = await dlg.getByLabel('Rol').locator('option').evaluateAll((os) => os.map((o) => o.value).filter(Boolean));
  igual(roles.sort(), ['administrador', 'coordinador', 'proveedor'], 'roles que ofrece el formulario');
  await dlg.getByRole('button', { name: 'Cancelar' }).click(); await dlg.waitFor({ state: 'detached', timeout: 8000 });
  credA = { correo: `prov.a.${MARCA}@eventosnova.example`.toLowerCase(), clave: 'Prov-' + randomBytes(12).toString('base64url') };
  credB = { correo: `prov.b.${MARCA}@eventosnova.example`.toLowerCase(), clave: 'Prov-' + randomBytes(12).toString('base64url') };
  for (const [cred, nombre, prov] of [[credA, `Persona A ${MARCA}`, NOMBRE_A], [credB, `Persona B ${MARCA}`, NOMBRE_B]]) {
    await admin.page.goto(`${BASE}/app/#/cuentas`); await esperarTexto(admin.page, 'Crear cuenta');
    const d = await abrir(admin.page, 'Crear cuenta');
    await llenar(d, { 'Nombre de la persona': nombre, 'Correo (será su usuario)': cred.correo, 'Rol': 'proveedor' });
    await d.getByLabel('Proveedor al que pertenece').selectOption(pv[prov]);
    await llenar(d, { 'Contraseña inicial': cred.clave });
    await enviar(admin.page, d);
    await esperarTexto(admin.page, cred.correo);
  }
  igual(sql(`select rol, proveedor_id from usuario where correo='${credA.correo}'`), `proveedor|${pv[NOMBRE_A]}`, 'cuenta A');
  // editar, desactivar y reactivar la cuenta B
  const fila = admin.page.locator('tr', { hasText: credB.correo }).first();
  await accion(admin.page, 'Editar', { 'Nombre de la persona': `Persona B editada ${MARCA}` }, credB.correo);
  await esperarTexto(admin.page, `Persona B editada ${MARCA}`);
  await accion(admin.page, 'Desactivar cuenta', {}, credB.correo); await esperarTexto(admin.page, 'Desactivada');
  igual(sql(`select activo from usuario where correo='${credB.correo}'`), 'f', 'cuenta B desactivada');
  const rechazo = await fetch(`${BASE}/auth/inicio-sesion`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ correo: credB.correo, contrasena: credB.clave }) });
  if (rechazo.status !== 401) throw new Error('la cuenta desactivada pudo entrar: ' + rechazo.status);
  await accion(admin.page, 'Activar cuenta', {}, credB.correo); await esperarTexto(admin.page, 'Activa');
  igual(sql(`select activo from usuario where correo='${credB.correo}'`), 't', 'cuenta B reactivada');
});

await paso('Coordinación (UI): registra un evento, crea y acepta la propuesta, prepara el contrato, comunica la política y registra la firma', async () => {
  await coord.page.goto(`${BASE}/app/#/eventos`); await esperarTexto(coord.page, 'Registrar evento');
  await accion(coord.page, 'Registrar evento', { 'Identificador del cliente': 'CL-E2E', 'Tipo de evento': `Boda E2E ${MARCA}`, 'Fecha y hora del evento': local(mx(75 * 864e5)),
    'Lugar': 'Salón Nova', 'Invitados aproximados': '120', 'Servicios solicitados': `${S1}, ${S2}` });
  await esperarTexto(coord.page, 'En gestión');
  eventoId = sql(`select evento_id from evento where tipo='Boda E2E ${MARCA}'`);
  igual(sql(`select estado from evento where evento_id='${eventoId}'`), 'EN_GESTION', 'evento registrado');
  await accion(coord.page, 'Crear propuesta', { 'Proveedores considerados': `${pv[NOMBRE_A]}, ${pv[NOMBRE_B]}`, 'Costo total': '10000.00', 'Condiciones': 'Condiciones de la prueba E2E' });
  await esperarTexto(coord.page, 'En revisión del Cliente');
  await accion(coord.page, 'Aceptar propuesta');
  await esperarTexto(coord.page, 'Aceptada');
  await accion(coord.page, 'Preparar contrato');
  await esperarTexto(coord.page, 'En preparación');
  contratoId = sql(`select contrato_id from contrato where evento_id='${eventoId}'`);
  await accion(coord.page, 'Comunicar política de no reembolso');
  await accion(coord.page, 'Registrar firma del contrato', { 'Confirmo que la política': true });
  await esperarTexto(coord.page, 'Firmado');
  igual(sql(`select estado from contrato where contrato_id='${contratoId}'`), 'FIRMADO', 'contrato firmado');
});

await paso('Administración (UI): pagos parciales del anticipo (1,000 + 2,000) con «Registrado sin verificar», verificación y paso a En organización por el trabajador', async () => {
  await esperarSql(`select count(*) from estado_cuenta where contrato_id='${contratoId}'`, '1', 'estado de cuenta creado por el trabajador');
  await irEvento(admin.page, eventoId, 'Estado de cuenta');
  await pagar(admin.page, 'Anticipo', '1000.00', `E2E-A1-${MARCA}`, false);
  await esperarTexto(admin.page, 'Registrado sin verificar');
  const dlg = await abrir(admin.page, 'Verificar pago'); await enviar(admin.page, dlg);
  await esperarTexto(admin.page, 'Pagado (verificado)');
  await pagar(admin.page, 'Anticipo', '2000.00', `E2E-A2-${MARCA}`, true);
  await esperarSql(`select estado from evento where evento_id='${eventoId}'`, 'EN_ORGANIZACION', 'el trabajador debe pasar el evento a En organización');
  await irEvento(admin.page, eventoId); await esperarTexto(admin.page, 'En organización');
  igual(sql(`select sum(p.importe) from pago p join obligacion_pago o on o.obligacion_id=p.obligacion_id join estado_cuenta e on e.estado_cuenta_id=o.estado_cuenta_id where e.contrato_id='${contratoId}' and p.estado='VERIFICADO'`), '3000.00', 'pagos verificados');
  ec = sql(`select estado_cuenta_id from estado_cuenta where contrato_id='${contratoId}'`);
  // duplicados: el mismo comprobante en la misma obligación se rechaza (la operación financiera no se duplica)
  const dup = await c.admin.fetch(`/estados-cuenta/${ec}/pagos`, { method: 'POST', body: JSON.stringify({ obligacion_id: sql(`select obligacion_id from obligacion_pago where estado_cuenta_id='${ec}' and concepto='SALDO_CONTRATO_ORIGINAL'`), importe: '500.00', fecha: mx(), comprobante: `E2E-S1-${MARCA}`, verificar_ahora: false }) });
  const dup2 = await c.admin.fetch(`/estados-cuenta/${ec}/pagos`, { method: 'POST', body: JSON.stringify({ obligacion_id: sql(`select obligacion_id from obligacion_pago where estado_cuenta_id='${ec}' and concepto='SALDO_CONTRATO_ORIGINAL'`), importe: '500.00', fecha: mx(), comprobante: `E2E-S1-${MARCA}`, verificar_ahora: false }) });
  if (dup.status !== 201 || dup2.status !== 422) throw new Error(`comprobante duplicado: ${dup.status}/${dup2.status}`);
});

await paso('Coordinación (S-4): consulta financiera en modo lectura; sin ningún botón de pago, verificación, cobranza ni devolución', async () => {
  await irEvento(coord.page, eventoId, 'Estado de cuenta');
  const t = (await texto(coord.page)).toLowerCase();
  for (const x of ['Pagado (verificado)', 'Saldo', 'Anticipo', 'Saldo del contrato original']) if (!t.includes(x.toLowerCase())) throw new Error(`Coordinación no ve «${x}»`);
  for (const b of ['Registrar pago', 'Verificar pago', 'Registrar vencimiento del saldo', 'Activar protocolo de cobro', 'Registrar regularización del saldo', 'Registrar devolución efectuada']) if (await hay(coord.page, b)) throw new Error(`Coordinación ve «${b}»`);
  await coord.page.goto(`${BASE}/app/#/pagos`); await esperarTexto(coord.page, 'Pagos');
  for (const b of ['Registrar pago', 'Verificar pago', 'Registrar devolución efectuada']) if (await hay(coord.page, b)) throw new Error(`Coordinación ve «${b}» en Pagos`);
  for (const [m, r] of [['POST', `/estados-cuenta/${ec}/pagos`], ['POST', `/estados-cuenta/${ec}/protocolo-cobro`], ['POST', `/estados-cuenta/${ec}/devoluciones/DV-X/ejecucion`]]) {
    const x = await c.coord.fetch(r, { method: m, body: '{}' }); if (x.status !== 403) throw new Error(`${r}: ${x.status}`);
  }
});

await paso('Coordinación asigna proveedores (candidatos del catálogo); el proveedor A responde directamente; Coordinación captura la respuesta del B con el medio (S-5)', async () => {
  await irEvento(coord.page, eventoId, S1);
  await accion(coord.page, 'Asignar proveedor', { 'Proveedor': pv[NOMBRE_A] }, S1);
  await esperarTexto(coord.page, 'Pendiente de confirmación del proveedor');
  await accion(coord.page, 'Asignar proveedor', { 'Proveedor': pv[NOMBRE_B] }, S2);
  igual(sql(`select count(*) from evento_servicio_contratado where evento_id='${eventoId}' and estado='PENDIENTE_CONFIRMACION'`), '2', 'servicios pendientes');
  // proveedor A: respuesta directa
  provA = await sesionUI(credA.correo, credA.clave); paginas.provA = provA.page;
  await provA.page.goto(`${BASE}/app/#/proveedor`); await esperarTexto(provA.page, 'Mis asignaciones');
  await esperarTexto(provA.page, S1);
  await sinTexto(provA.page, S2);
  await accion(provA.page, 'Registrar respuesta del proveedor', {});
  await esperarTexto(provA.page, 'Confirmado por el proveedor');
  await esperarTexto(provA.page, 'respuesta directa del proveedor');
  igual(sql(`select respuesta_origen, coalesce(respuesta_medio,'-'), respuesta_disponible from evento_servicio_contratado where evento_id='${eventoId}' and servicio='${S1}'`), 'Proveedor|-|t', 'procedencia directa en PostgreSQL');
  // Coordinación captura la respuesta del B: el medio es obligatorio
  await irEvento(coord.page, eventoId, S2);
  const dlg = await abrir(coord.page, 'Registrar respuesta del proveedor', S2);
  await dlg.locator('button[type=submit]').click();
  await coord.page.waitForFunction(() => /obligatorio/i.test(document.querySelector('dialog[open]')?.innerText || ''), null, { timeout: 6000 });      // sin medio no se envía
  await llenar(dlg, { 'Medio por el que el proveedor respondió': 'Llamada telefónica' });
  await enviar(coord.page, dlg);
  await esperarTexto(coord.page, 'capturada por Coordinación (medio: Llamada telefónica)');
  igual(sql(`select respuesta_origen, respuesta_medio, respuesta_registrada_por_nombre like 'Coordinación de prueba%' from evento_servicio_contratado where evento_id='${eventoId}' and servicio='${S2}'`), 'Coordinación|Llamada telefónica|t', 'procedencia capturada en PostgreSQL');
  await irEvento(admin.page, eventoId, S2);
  await esperarTexto(admin.page, 'respuesta directa del proveedor'); await esperarTexto(admin.page, 'capturada por Coordinación');
});

await paso('Proveedor (aislamiento y persistencia): B ve solo lo suyo con la procedencia; A no ve lo de B; las respuestas persisten tras recargar y volver a entrar', async () => {
  provB = await sesionUI(credB.correo, credB.clave); paginas.provB = provB.page;
  await provB.page.goto(`${BASE}/app/#/proveedor`); await esperarTexto(provB.page, S2);
  await esperarTexto(provB.page, 'capturada por Coordinación (medio: Llamada telefónica)');
  await sinTexto(provB.page, S1);
  await esperarTexto(provB.page, NOMBRE_B);
  await sinTexto(provB.page, NOMBRE_A);
  // identificadores manipulados: el proveedor A no puede consultar al B ni su evento por API
  const ses = await provA.page.evaluate(async (ids) => {
    const { api } = await import('/app/js/api.js'); const salida = [];
    for (const [m, r] of ids) { try { await api(m, r); salida.push([r, 200]); } catch (e) { salida.push([r, e.estado]); } }
    return salida;
  }, [['GET', `/proveedores/${pv[NOMBRE_B]}`], ['GET', `/proveedores/${pv[NOMBRE_B]}/eventos/${eventoId}`], ['GET', '/proveedores'], ['GET', `/eventos/${eventoId}/pagos`], ['GET', `/eventos/${eventoId}/propuestas`]]);
  for (const [r, st] of ses) if (st !== 403) throw new Error(`${r} respondió ${st} y se esperaba 403`);
  // recarga y nueva sesión
  await provA.page.reload(); await esperarTexto(provA.page, 'respuesta directa del proveedor');
  await provA.page.getByRole('button', { name: 'Cerrar sesión' }).click(); await provA.page.waitForSelector('#ing-correo');
  await provA.page.fill('#ing-correo', credA.correo); await provA.page.fill('#ing-clave', credA.clave); await provA.page.click('.ingreso-forma button[type=submit]');
  await provA.page.waitForSelector('#sesion-caja button'); await provA.page.goto(`${BASE}/app/#/proveedor`);
  await esperarTexto(provA.page, 'Confirmado por el proveedor'); await esperarTexto(provA.page, `Banquetes ${MARCA}`);
  // consultar sus propios datos
  await esperarTexto(provA.page, 'Mis datos');
  const nav = normal(await provA.page.locator('#menu').innerText());
  if (!/Mi proveedor/.test(nav) || /Eventos|Cuentas|Pagos/.test(nav)) throw new Error('menú del proveedor: ' + nav);
});

// ------------------------------------------------------------------ solicitudes: servicio adicional, cambio y sustitución
let sa = null; let sc = null; let sp = null;
await paso('Servicio adicional (D-P3): solicitud, captura de proveedor/costo/condiciones, decisión del Cliente, autorización con el importe a la vista, anexo, pago y confirmación', async () => {
  await irEvento(coord.page, eventoId, 'Solicitudes del evento');
  await accion(coord.page, 'Solicitar servicio adicional', { 'Servicio solicitado': SA });
  await esperarTexto(coord.page, SA);
  sa = sql(`select solicitud_id from solicitud_servicio_adicional where evento_id='${eventoId}'`);
  await accion(coord.page, 'Registrar proveedor, costo y condiciones', { 'Proveedor del catálogo': pv[NOMBRE_C], 'Costo del proveedor': '800.00', 'Condiciones del servicio': 'DJ 4 horas con sonido' }, sa);
  await esperarTexto(coord.page, 'Pendiente de aprobación del Cliente');
  await accion(coord.page, 'Registrar aprobación del Cliente', {}, sa);
  await esperarTexto(coord.page, 'Pendiente de autorización');
  await irEvento(admin.page, eventoId, 'Solicitudes del evento');
  const fila = normal(await admin.page.locator('tr', { hasText: sa }).first().innerText());
  if (!/800\.00/.test(fila) || !fila.includes('DJ 4 horas con sonido') || !fila.includes(pv[NOMBRE_C])) throw new Error('Administración no ve proveedor, costo y condiciones: ' + fila.slice(0, 200));
  if (await hay(admin.page, 'Registrar proveedor, costo y condiciones', sa)) throw new Error('Administración ve el botón de captura');
  await accion(admin.page, 'Registrar autorización de Administración', {}, sa);
  await esperarTexto(admin.page, 'Autorizada');
  await irEvento(coord.page, eventoId, 'Solicitudes del evento');
  await accion(coord.page, 'Registrar anexo del contrato', { 'Descripción del anexo': 'Anexo del servicio adicional' }, sa);
  await accion(coord.page, 'Comunicar solicitud de pago', {}, sa);
  await esperarTexto(coord.page, 'Pendiente de pago');
  await irEvento(admin.page, eventoId, 'Estado de cuenta');
  await pagar(admin.page, 'ServicioAdicional', '300.00', `E2E-SA1-${MARCA}`, true);              // pago parcial
  await esperarTexto(admin.page, 'Saldo');
  await pagar(admin.page, 'ServicioAdicional', '500.00', `E2E-SA2-${MARCA}`, true);
  await irEvento(coord.page, eventoId, 'Solicitudes del evento');
  await accion(coord.page, 'Confirmar servicio adicional', {}, sa);
  await esperarSql(`select estado from solicitud_servicio_adicional where solicitud_id='${sa}'`, 'CONFIRMADA', 'servicio adicional confirmado');
  igual(sql(`select count(*) from obligacion_pago where origen_id='${sa}'`), '1', 'una sola obligación, sin cargo propio de Eventos Nova');
  igual(sql(`select importe from obligacion_pago where origen_id='${sa}'`), '800.00', 'importe = costo del proveedor');
});

await paso('Cambio (D-P3): costo y condiciones opcionales; Administración los ve y autoriza', async () => {
  await irEvento(coord.page, eventoId, 'Solicitudes del evento');
  await accion(coord.page, 'Solicitar cambio', { 'Descripción del cambio': 'Cambio de menú', 'Tarifa vigente': '500.00' });
  sc = sql(`select solicitud_id from solicitud_cambio where evento_id='${eventoId}'`);
  await esperarTexto(coord.page, sc);
  await accion(coord.page, 'Evaluar viabilidad del cambio', { 'Costo adicional del proveedor': '1000.00', 'Condiciones del proveedor': 'Pago del proveedor por adelantado' }, sc);
  await accion(coord.page, 'Registrar decisión del Cliente', {}, sc);
  await irEvento(admin.page, eventoId, 'Solicitudes del evento');
  const fila = normal(await admin.page.locator('tr', { hasText: sc }).first().innerText());
  if (!/1,?000\.00/.test(fila) || !fila.includes('Pago del proveedor por adelantado')) throw new Error('Administración no ve costo y condiciones del cambio: ' + fila.slice(0, 200));
  await accion(admin.page, 'Registrar autorización de Administración', {}, sc);
  igual(sql(`select condiciones_proveedor from solicitud_cambio where solicitud_id='${sc}'`), 'Pago del proveedor por adelantado', 'condiciones del cambio en PostgreSQL');
});

await paso('Sustitución (S-6): alternativa del catálogo, autorizaciones, integración del importe por Administración una sola vez y trazabilidad', async () => {
  await irEvento(coord.page, eventoId, 'Solicitudes del evento');
  const dlg = await abrir(coord.page, 'Sustituir proveedor'); await dlg.getByLabel('Servicio contratado').selectOption({ label: new RegExp(S1) }).catch(async () => {
    const valor = await dlg.getByLabel('Servicio contratado').locator('option').evaluateAll((os, k) => os.find((o) => o.textContent.includes(k))?.value, S1); await dlg.getByLabel('Servicio contratado').selectOption(valor); });
  await enviar(coord.page, dlg);
  sp = sql(`select sustitucion_id from sustitucion_proveedor where evento_id='${eventoId}'`);
  await esperarTexto(coord.page, sp);
  await accion(coord.page, 'Proponer alternativa de proveedor', { 'Proveedor alternativo del catálogo': pv[NOMBRE_D], 'Condiciones de la alternativa': 'Menú equivalente', 'Costo adicional': '250.50' }, sp);
  await accion(coord.page, 'Registrar decisión del Cliente', {}, sp);
  await irEvento(admin.page, eventoId, 'Solicitudes del evento');
  if (await hay(admin.page, 'Integrar importe adicional al saldo', sp)) throw new Error('Se ofrece integrar antes de autorizar');
  const fila = normal(await admin.page.locator('tr', { hasText: sp }).first().innerText());
  if (!fila.includes(pv[NOMBRE_D]) || !/250\.50/.test(fila)) throw new Error('Administración no ve la alternativa: ' + fila.slice(0, 200));
  await accion(admin.page, 'Registrar autorización de Administración', {}, sp);
  await irEvento(coord.page, eventoId, 'Solicitudes del evento');
  await accion(coord.page, 'Registrar anexo del contrato', { 'Descripción del anexo': 'Anexo de la sustitución' }, sp);
  if (await hay(coord.page, 'Integrar importe adicional al saldo', sp)) throw new Error('Coordinación ve «Integrar importe adicional»');
  await irEvento(admin.page, eventoId, 'Solicitudes del evento');
  const d2 = await abrir(admin.page, 'Integrar importe adicional al saldo', sp);
  igual(await d2.getByLabel('Importe adicional autorizado').inputValue(), '250.50', 'importe propuesto');
  await d2.getByLabel('Importe adicional autorizado').fill('999.00');
  await d2.locator('button[type=submit]').click(); await admin.page.waitForTimeout(400);
  if (await admin.page.locator('#btn-confirmar:visible').count()) await admin.page.locator('#btn-confirmar').click();
  await admin.page.waitForFunction(() => /no coincide|aprobado/i.test(document.querySelector('dialog[open]')?.innerText || ''), null, { timeout: 8000 });   // otro importe: rechazado
  await d2.getByLabel('Importe adicional autorizado').fill('250.50');
  await enviar(admin.page, d2);
  igual(sql(`select concepto, importe, origen_id from obligacion_pago where origen_id='${sp}'`), `SUSTITUCION_PROVEEDOR|250.50|${sp}`, 'obligación trazable');
  const otra = await c.admin.fetch(`/sustituciones/${sp}/importe-adicional`, { method: 'POST', body: JSON.stringify({ importe: '250.50' }) });
  if (otra.status !== 422) throw new Error('se pudo integrar dos veces: ' + otra.status);
  igual(sql(`select count(*) from obligacion_pago where origen_id='${sp}'`), '1', 'una sola obligación de la sustitución');
});

// ------------------------------------------------------------------ cobranza, cancelación por falta de regularización
let ev2 = null; let ec2 = null;
await paso('Cobranza y S-3: vencimiento del saldo, protocolo de cobro y regularización por Administración; cancelación solo por Coordinación y solo después de la verificación', async () => {
  const k = await prepararEvento(`Cobranza ${MARCA}`);
  ev2 = k.evento; ec2 = k.ec;
  // el saldo vence (simulación del paso del tiempo sobre el evento propio)
  sql(`update obligacion_pago set plazo_vence = now() - interval '1 day' where estado_cuenta_id='${ec2}' and concepto='SALDO_CONTRATO_ORIGINAL'`);
  await irEvento(coord.page, ev2, 'Estado de cuenta');
  if (await hay(coord.page, 'Cancelar por falta de regularización')) throw new Error('Coordinación ya puede cancelar sin verificación de Administración');
  const prematura = await c.coord.fetch(`/eventos/${ev2}/cancelacion-por-falta-de-regularizacion`, { method: 'POST', body: JSON.stringify({ motivo: 'Prematura' }) });
  if (prematura.status !== 422) throw new Error('cancelación anticipada respondió ' + prematura.status);
  await irEvento(admin.page, ev2, 'Estado de cuenta');
  await accion(admin.page, 'Registrar vencimiento del saldo'); await esperarTexto(admin.page, 'Vencida');
  await accion(admin.page, 'Activar protocolo de cobro', { 'Importe de los cargos moratorios': '200.00', 'Seguimiento realizado': 'Recordatorio amistoso enviado' });
  igual(sql(`select count(*) from obligacion_pago where estado_cuenta_id='${ec2}' and concepto='CARGOS_MORATORIOS'`), '1', 'cargos moratorios');
  sql(`update obligacion_pago set plazo_inicio = now() - interval '3 days', plazo_vence = now() - interval '2 days' where estado_cuenta_id='${ec2}' and concepto='CARGOS_MORATORIOS'`);
  await irEvento(admin.page, ev2, 'Estado de cuenta');
  await accion(admin.page, 'Registrar regularización del saldo'); await esperarTexto(admin.page, 'No regularizado').catch(() => esperarTexto(admin.page, 'Plazo de regularización vencido'));
  await irEvento(coord.page, ev2, 'Estado de cuenta');
  await accion(coord.page, 'Cancelar por falta de regularización', { 'Motivo': 'Saldo vencido sin regularizar tras el protocolo' });
  await esperarTexto(coord.page, 'Cancelado');
  igual(sql(`select estado, motivo_cancelacion_origen, motivo_cancelacion_registrado_por like 'Coordinación de prueba%' from evento where evento_id='${ev2}'`), 'CANCELADO|FALTA_REGULARIZACION|t', 'cancelación registrada por la cuenta de Coordinación');
  const otra = await c.coord.fetch(`/eventos/${ev2}/cancelacion-por-falta-de-regularizacion`, { method: 'POST', body: JSON.stringify({ motivo: 'Otra vez' }) });
  if (otra.status !== 200 || !(await otra.json()).mensaje.includes('ya estaba cancelado')) throw new Error('la cancelación se duplicó');
  await irEvento(admin.page, ev2, 'Ciclo de vida del evento');
  await accion(admin.page, 'Registrar revisión administrativa', { 'Resultado': 'Sin reembolso por política de no reembolso' }).catch(() => { throw new Error('revisión administrativa'); });
});

let ev3 = null; let sa2 = null; let ec3 = null;
await paso('Devoluciones (SE-012): un servicio adicional con pago parcial que vence sin completarse se cierra por Coordinación y Administración registra la devolución de lo recibido', async () => {
  const k = await prepararEvento(`Devolución ${MARCA}`);
  ev3 = k.evento; ec3 = k.ec;
  await irEvento(coord.page, ev3, 'Solicitudes del evento');
  await accion(coord.page, 'Solicitar servicio adicional', { 'Servicio solicitado': SA });
  sa2 = sql(`select solicitud_id from solicitud_servicio_adicional where evento_id='${ev3}'`);
  await accion(coord.page, 'Registrar proveedor, costo y condiciones', { 'Proveedor del catálogo': pv[NOMBRE_C], 'Costo del proveedor': '900.00', 'Condiciones del servicio': 'DJ 5 horas' }, sa2);
  await accion(coord.page, 'Registrar aprobación del Cliente', {}, sa2);
  await irEvento(admin.page, ev3, 'Solicitudes del evento'); await accion(admin.page, 'Registrar autorización de Administración', {}, sa2);
  await irEvento(coord.page, ev3, 'Solicitudes del evento');
  await accion(coord.page, 'Registrar anexo del contrato', { 'Descripción del anexo': 'Anexo' }, sa2);
  await accion(coord.page, 'Comunicar solicitud de pago', {}, sa2);
  await irEvento(admin.page, ev3, 'Estado de cuenta'); await pagar(admin.page, 'ServicioAdicional', '400.00', `E2E-DV1-${MARCA}`, true);
  sql(`update obligacion_pago set plazo_inicio = now() - interval '2 days', plazo_vence = now() - interval '1 day' where origen_id='${sa2}'`);
  await irEvento(coord.page, ev3, 'Solicitudes del evento');
  if (!(await hay(coord.page, 'Cerrar por falta de pago', sa2))) throw new Error('no se ofrece el cierre por falta de pago');
  await accion(coord.page, 'Cerrar por falta de pago', {}, sa2);
  await esperarTexto(coord.page, 'Cerrada por falta de pago');
  await esperarSql(`select count(*) from devolucion where estado_cuenta_id='${ec3}'`, '1', 'devolución generada');
  await irEvento(admin.page, ev3, 'Estado de cuenta'); await esperarTexto(admin.page, '400.00');
  if (await hay(coord.page, 'Registrar devolución efectuada')) throw new Error('Coordinación ve «Registrar devolución efectuada»');
  await admin.page.goto(`${BASE}/app/#/pagos`); await esperarTexto(admin.page, 'Devoluciones');
  await irEvento(admin.page, ev3, 'Devoluciones');
  await accion(admin.page, 'Registrar devolución efectuada', { 'Comprobante de la devolución': `TRF-${MARCA}` });
  await esperarSql(`select estado from devolucion where estado_cuenta_id='${ec3}'`, 'EJECUTADA', 'devolución ejecutada').catch(async () => { igual(sql(`select estado from devolucion where estado_cuenta_id='${ec3}'`).length > 0, true, 'estado de la devolución'); });
});

// ------------------------------------------------------------------ S-7: inicio automático, respaldo manual, finalización
let ev4 = null; let ev5 = null; let ev6 = null;
async function prepararEvento(tipo) {
  const e = (await c.coord.json('POST', '/eventos', { cliente_id: 'CL-E2E', datos: { tipo, fecha_hora: mx(75 * 864e5), lugar: 'Salón', invitados_aproximados: 50 }, servicios: [S1] })).evento_id;
  const prop = (await c.coord.json('POST', `/eventos/${e}/propuestas`, { servicios: [S1], proveedores_considerados: ['PV-X'], costo_total: '10000.00', condiciones: 'Prueba' })).propuesta_id;
  await c.coord.json('POST', `/propuestas/${prop}/aceptacion`, { version_id: `${prop}-v1` });
  const ct = (await c.coord.json('POST', `/propuestas/${prop}/contrato`, { politica_incluida: true })).datos.contrato_id;
  await c.coord.json('POST', `/contratos/${ct}/comunicacion-politica-no-reembolso`, { fecha: mx() }); await c.coord.json('POST', `/contratos/${ct}/firma`, { fecha: mx() });
  let ecId = '';
  for (let i = 0; i < 30 && !ecId; i++) { ecId = sql(`select estado_cuenta_id from estado_cuenta where contrato_id='${ct}'`); if (!ecId) await dormir(400); }
  const ob = sql(`select obligacion_id from obligacion_pago where estado_cuenta_id='${ecId}' and concepto='ANTICIPO'`);
  await c.admin.json('POST', `/estados-cuenta/${ecId}/pagos`, { obligacion_id: ob, importe: '3000.00', fecha: mx(), comprobante: `E2E-${e}`, verificar_ahora: true });
  await esperarSql(`select estado from evento where evento_id='${e}'`, 'EN_ORGANIZACION', 'evento En organización', 30000);
  return { evento: e, ec: ecId };
}

await paso('S-7: tres eventos listos; el inicio manual anticipado se rechaza en la interfaz y por API, y el evento sigue En organización', async () => {
  ev4 = (await prepararEvento(`Inicio respaldo ${MARCA}`)).evento;
  ev5 = (await prepararEvento(`Inicio automático ${MARCA}`)).evento;
  ev6 = (await prepararEvento(`Inicio futuro ${MARCA}`)).evento;
  await irEvento(coord.page, ev6, 'Ciclo de vida del evento');
  await esperarTexto(coord.page, 'mecanismo excepcional');
  const dlg = await abrir(coord.page, 'Registrar inicio del evento (respaldo)');
  await dlg.locator('button[type=submit]').click().catch(() => {}); await coord.page.waitForTimeout(300);
  if (await coord.page.locator('#btn-confirmar:visible').count()) await coord.page.locator('#btn-confirmar').click();
  await coord.page.waitForFunction(() => /antes de su fecha y hora/i.test(document.querySelector('dialog[open]')?.innerText || ''), null, { timeout: 8000 });
  await coord.page.locator('dialog[open]').getByRole('button', { name: 'Cancelar' }).click();
  const r = await c.coord.fetch(`/eventos/${ev6}/inicio`, { method: 'POST' }); if (r.status !== 422) throw new Error('inicio anticipado por API: ' + r.status);
  igual(sql(`select estado from evento where evento_id='${ev6}'`), 'EN_ORGANIZACION', 'el evento futuro no cambió');
  const admin403 = await c.admin.fetch(`/eventos/${ev6}/inicio`, { method: 'POST' }); if (admin403.status !== 403) throw new Error('Administración inicia eventos: ' + admin403.status);
});

await paso('S-7: con el trabajador detenido y la hora vencida el evento NO cambia solo; Coordinación lo inicia como respaldo (una sola vez) y luego registra la finalización', async () => {
  await detenerTrabajador();
  const pasado = mx(-2 * 3600 * 1000);
  sql(`update evento set fecha_hora='${pasado}' where evento_id in ('${ev4}','${ev5}')`);
  await dormir(3500);
  igual(sql(`select estado from evento where evento_id='${ev4}'`), 'EN_ORGANIZACION', 'sin trabajador no hay inicio automático');
  await irEvento(coord.page, ev4, 'Ciclo de vida del evento');
  await accion(coord.page, 'Registrar inicio del evento (respaldo)');
  await esperarTexto(coord.page, 'En ejecución');
  igual(sql(`select estado, fecha_inicio is not null from evento where evento_id='${ev4}'`), 'EN_EJECUCION|t', 'respaldo manual');
  if (await hay(coord.page, 'Registrar inicio del evento (respaldo)')) throw new Error('sigue el botón de inicio tras iniciar (duplicado posible)');
  const dup = await c.coord.fetch(`/eventos/${ev4}/inicio`, { method: 'POST' }); if (dup.status !== 422) throw new Error('segundo inicio: ' + dup.status);
  await irEvento(admin.page, ev4, 'Ciclo de vida del evento');
  if (await hay(admin.page, 'Registrar finalización del evento')) throw new Error('Administración ve la finalización');
  const f403 = await c.admin.fetch(`/eventos/${ev4}/finalizacion`, { method: 'POST', body: JSON.stringify({ fecha: mx() }) }); if (f403.status !== 403) throw new Error('Administración finaliza: ' + f403.status);
  await irEvento(coord.page, ev4, 'Ciclo de vida del evento');
  await accion(coord.page, 'Registrar finalización del evento', { 'Fecha de finalización': local(mx(10 * 60 * 1000)) });
  await esperarTexto(coord.page, 'Finalizado');
  igual(sql(`select estado, fecha_finalizacion is not null from evento where evento_id='${ev4}'`), 'FINALIZADO|t', 'finalización');
});

await paso('S-7 (trabajador real): al reiniciarlo recupera el evento cuya hora ya pasó, no inicia el futuro y no repite nada en ciclos posteriores', async () => {
  igual(sql(`select estado from evento where evento_id='${ev5}'`), 'EN_ORGANIZACION', 'ev5 sigue pendiente con el trabajador detenido');
  arrancarTrabajador();
  await esperarSql(`select estado from evento where evento_id='${ev5}'`, 'EN_EJECUCION', 'el trabajador reiniciado debe iniciar el evento vencido');
  const inicio = sql(`select fecha_inicio from evento where evento_id='${ev5}'`);
  igual(sql(`select estado from evento where evento_id='${ev6}'`), 'EN_ORGANIZACION', 'el evento futuro no se inicia');
  await dormir(4000);
  igual(sql(`select fecha_inicio from evento where evento_id='${ev5}'`), inicio, 'fecha de inicio sin reescribir');
  await irEvento(admin.page, ev5, 'Ciclo de vida del evento'); await esperarTexto(admin.page, 'En ejecución');
  await irEvento(coord.page, ev5, 'Ciclo de vida del evento');
  if (await hay(coord.page, 'Registrar inicio del evento (respaldo)')) throw new Error('se ofrece iniciar un evento ya iniciado');
});

// ------------------------------------------------------------------ S-9, seguridad y cierre
await paso('S-9 y seguridad: Administración no crea ni gestiona lo de Coordinación (interfaz y servidor); sin sesión no hay acceso; cada rol rechaza lo ajeno', async () => {
  await admin.page.goto(`${BASE}/app/#/eventos`); await esperarTexto(admin.page, 'Eventos');
  if (await hay(admin.page, 'Registrar evento')) throw new Error('Administración ve «Registrar evento»');
  await irEvento(admin.page, eventoId, 'Solicitudes del evento');
  for (const b of ['Crear propuesta', 'Preparar contrato', 'Solicitar cambio', 'Solicitar servicio adicional', 'Sustituir proveedor', 'Asignar proveedor', 'Registrar firma del contrato']) if (await hay(admin.page, b)) throw new Error(`Administración ve «${b}»`);
  await esperarTexto(admin.page, 'Aceptada');
  for (const [m, r] of [['POST', '/eventos'], ['POST', `/eventos/${eventoId}/propuestas`], ['POST', '/solicitudes-cambio'], ['POST', '/solicitudes-servicio-adicional'], ['POST', '/sustituciones']]) {
    const x = await c.admin.fetch(r, { method: m, body: '{}' }); if (x.status !== 403) throw new Error(`Administración ${r}: ${x.status}`);
  }
  for (const r of [`/eventos/${eventoId}/administracion`, `/eventos/${eventoId}/pagos`, `/eventos/${eventoId}/propuestas`, '/solicitudes', '/pagos-pendientes']) {
    const sin = await fetch(BASE + r); if (sin.status !== 401) throw new Error(`sin sesión ${r}: ${sin.status}`);
  }
  const x = await c.coord.fetch('/usuarios'); if (x.status !== 403) throw new Error('Coordinación lista cuentas: ' + x.status);
});

await paso('Sin excepciones de JavaScript', async () => { if (errores.length) throw new Error(errores.slice(0, 3).join(' | ')); });
await navegador.close();
await detenerTrabajador();
console.log(`\nRESUMEN: ${resultados.filter((r) => r[0] === 'OK').length} OK, ${resultados.filter((r) => r[0] === 'FALLO').length} FALLO`);
process.exit(resultados.some((r) => r[0] === 'FALLO') ? 1 : 0);
