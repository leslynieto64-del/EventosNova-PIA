// Prueba REAL con Playwright (Chrome instalado, sin mocks) de la decisión D-P3: costos y condiciones de proveedores capturados a mano por
// operación (servicio adicional, cambio y sustitución), contra la API con PostgreSQL del entorno manual. Cada paso se comprueba en la pantalla y en la base.
//   PLAYWRIGHT_DIR=<carpeta con playwright> EVENTOSNOVA_E2E_ADMIN_CORREO=… EVENTOSNOVA_E2E_ADMIN_CLAVE=… \
//   node scripts/probar_costos_condiciones_playwright.mjs http://127.0.0.1:8001 <carpeta de capturas>
// Crea sus propios datos (evento, proveedores y solicitudes); no borra ni limpia nada y no imprime contraseñas.
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import { prepararCuentas } from './lib_sesion_e2e.mjs';

const { chromium } = createRequire(`${process.env.PLAYWRIGHT_DIR}/`)('playwright');
const BASE = process.argv[2] || 'http://127.0.0.1:8001';
const SALIDA = process.argv[3] || '.';
const MARCA = Date.now().toString(36).toUpperCase();
const BASE_DATOS = 'eventosnova_manual_test';
const resultados = [];
const paginas = {};
const paso = async (nombre, fn) => {
  try { await fn(); resultados.push(['OK', nombre]); console.log('OK   ', nombre); } catch (e) {
    resultados.push(['FALLO', nombre, e.message]); console.log('FALLO', nombre, '->', String(e.message).split('\n')[0].slice(0, 300));
    for (const [quien, pg] of Object.entries(paginas)) { try { await pg.screenshot({ path: `${SALIDA}/fallo_${quien}_${resultados.length}.png` }); } catch { /* */ } }
  }
};
const igual = (real, esperado, que) => { if (JSON.stringify(real) !== JSON.stringify(esperado)) throw new Error(`${que}: se esperaba ${JSON.stringify(esperado)} y la base tiene ${JSON.stringify(real)}`); };
const sql = (consulta) => execFileSync('docker', ['exec', 'eventosnova-db', 'sh', '-c', `psql -U "$POSTGRES_USER" -d ${BASE_DATOS} -At -F '|' -c "${consulta}"`], { encoding: 'utf8' }).trim();

const c = await prepararCuentas(BASE, MARCA);
const SERV = `DJ ${MARCA}`; const BANQ = `Banquete ${MARCA}`;
let eventoId; let contratoId; let pvActivo; let pvInactivo; let pvOtro; let pvAlterno; let pvOriginal; let saId; let scId; let spId;
const ahora = () => new Date(Date.now() - 6 * 3600 * 1000).toISOString().slice(0, 19);
const decision = (actor) => ({ actor, aprobada: true, fecha: ahora(), motivo: '' });

await paso('Datos de prueba por la API: evento En organización, proveedores del catálogo (activo, inactivo, ajeno), servicio adicional, cambio y sustitución', async () => {
  eventoId = (await c.coord.json('POST', '/eventos', { cliente_id: 'CL-D3', datos: { tipo: `Prueba D-P3 ${MARCA}`, fecha_hora: new Date(Date.now() + 80 * 864e5).toISOString().slice(0, 19), lugar: 'Salón', invitados_aproximados: 40 }, servicios: [BANQ] })).evento_id;
  const prop = (await c.coord.json('POST', `/eventos/${eventoId}/propuestas`, { servicios: [BANQ], proveedores_considerados: ['PV-X'], costo_total: '10000.00', condiciones: 'Prueba' })).propuesta_id;
  await c.coord.json('POST', `/propuestas/${prop}/aceptacion`, { version_id: `${prop}-v1` });
  contratoId = (await c.coord.json('POST', `/propuestas/${prop}/contrato`, { politica_incluida: true })).datos.contrato_id;
  await c.coord.json('POST', `/contratos/${contratoId}/comunicacion-politica-no-reembolso`, { fecha: ahora() }); await c.coord.json('POST', `/contratos/${contratoId}/firma`, { fecha: ahora() });
  const ec = (await c.coord.json('GET', `/eventos/${eventoId}/pagos`)).estadosCuenta[0].estadoCuentaId;
  const ob = (await c.coord.json('GET', `/pagos-pendientes?evento_id=${eventoId}`)).pagos.find((p) => p.concepto === 'Anticipo');
  await c.admin.json('POST', `/estados-cuenta/${ec}/pagos`, { obligacion_id: ob.obligacionId, importe: '3000.00', fecha: ahora(), comprobante: `D3-${MARCA}`, verificar_ahora: true });
  for (let i = 0; i < 25; i++) { if ((await c.coord.json('GET', `/eventos/${eventoId}/administracion`)).estadoEvento === 'En organización') break; await new Promise((r) => setTimeout(r, 300)); }
  const alta = async (nombre, servicios) => (await c.coord.json('POST', '/proveedores', { nombre: `${nombre} ${MARCA}`, servicios, contacto: '' })).datos.proveedorId;
  pvActivo = await alta('DJ Activo', [SERV]); pvInactivo = await alta('DJ Inactivo', [SERV]); pvOtro = await alta('Fotos Ajenas', ['Fotografía']);
  pvOriginal = await alta('Banquetes Originales', [BANQ]); pvAlterno = await alta('Banquetes Alternos', [BANQ]);
  await c.admin.json('POST', `/proveedores/${pvInactivo}/desactivacion`);
  const servicioBanq = (await c.coord.json('GET', `/eventos/${eventoId}/administracion`)).proveedores[0].servicioContratadoId;
  await c.coord.json('POST', `/eventos/${eventoId}/servicios/${servicioBanq}/proveedor`, { proveedor_id: pvOriginal });
  saId = (await c.coord.json('POST', '/solicitudes-servicio-adicional', { evento_id: eventoId, contrato_id: contratoId, servicio: SERV })).datos.solicitud_id;
  scId = (await c.coord.json('POST', '/solicitudes-cambio', { evento_id: eventoId, contrato_id: contratoId, descripcion: 'Cambio de menú', tarifa_vigente: '500.00' })).datos.solicitud_id;
  spId = (await c.coord.json('POST', '/sustituciones', { evento_id: eventoId, servicio_contratado_id: servicioBanq, contrato_id: contratoId })).datos.sustitucion_id;
  igual(sql(`select estado from solicitud_servicio_adicional where solicitud_id='${saId}'`), 'REGISTRADA', 'estado inicial del servicio adicional');
});

const navegador = await chromium.launch({ channel: 'chrome', headless: true });
const errores = [];
async function sesionUI(correo, clave) {
  const ctx = await navegador.newContext({ viewport: { width: 1280, height: 1000 } });
  const page = await ctx.newPage();
  page.on('pageerror', (e) => errores.push(e.message));
  await page.goto(`${BASE}/app/`);
  await page.fill('#ing-correo', correo); await page.fill('#ing-clave', clave);
  await page.click('.ingreso-forma button[type=submit]');
  await page.waitForSelector('#sesion-caja button', { timeout: 15000 });
  return { ctx, page };
}
const esperarTexto = (page, t, ms = 10000) => page.waitForFunction((x) => document.body.innerText.includes(x), t, { timeout: ms });
const textoPagina = (page) => page.evaluate(() => document.body.innerText);
const fila = (page, id) => page.locator('tr', { hasText: id }).first();
/** Abre el diálogo de una acción de la fila de una solicitud y rellena campos: texto con fill, listas con selectOption y casillas con setChecked. */
async function abrir(page, id, boton) {
  const boton_ = fila(page, id).getByRole('button', { name: boton, exact: true });
  try { await boton_.waitFor({ timeout: 6000 }); } catch { throw new Error(`no hay botón «${boton}» en la fila de ${id}: ${(await fila(page, id).innerText().catch(() => '(sin fila)')).replace(/\s+/g, ' ').slice(0, 300)}`); }
  await boton_.click();
  const dlg = page.locator('dialog[open]'); await dlg.waitFor({ timeout: 8000 });
  return dlg;
}
async function enviar(page, dlg) {
  await dlg.locator('button[type=submit]').click();
  await page.waitForTimeout(500);
  if (await page.locator('#btn-confirmar:visible').count()) await page.locator('#btn-confirmar').click();      // algunas acciones se envían sin paso de confirmación
  await dlg.waitFor({ state: 'detached', timeout: 10000 });
}
const abrirEvento = async (page) => { await page.goto(`${BASE}/app/#/evento/${eventoId}`); await page.reload(); await esperarTexto(page, 'Solicitudes del evento'); await esperarTexto(page, saId); };

const admin = await sesionUI(c.correoAdmin, c.claveAdmin);
const coord = await sesionUI(c.correoCoord, c.claveCoord);
paginas.admin = admin.page; paginas.coord = coord.page;

await paso('Servicio adicional: el formulario solo ofrece proveedores del catálogo activos que ofrecen el servicio (ni el inactivo ni el ajeno)', async () => {
  await abrirEvento(coord.page);
  const dlg = await abrir(coord.page, saId, 'Registrar proveedor, costo y condiciones');
  const opciones = await dlg.getByLabel('Proveedor del catálogo').locator('option').evaluateAll((os) => os.map((o) => o.value));
  if (!opciones.includes(pvActivo)) throw new Error('falta el proveedor activo');
  if (opciones.includes(pvInactivo) || opciones.includes(pvOtro)) throw new Error('se ofrece un proveedor inactivo o ajeno al servicio');
  await coord.page.screenshot({ path: `${SALIDA}/d3_1_formulario_adicional.png` });
  await dlg.getByRole('button', { name: 'Cancelar' }).click(); await dlg.waitFor({ state: 'detached', timeout: 8000 });
});

await paso('Servicio adicional: la interfaz rechaza costo 0 y el servidor también (llamada directa por API) sin cambiar nada', async () => {
  const dlg = await abrir(coord.page, saId, 'Registrar proveedor, costo y condiciones');
  await dlg.getByLabel('Proveedor del catálogo').selectOption(pvActivo);
  await dlg.getByLabel('Costo del proveedor').fill('0'); await dlg.getByLabel('Condiciones del servicio').fill('DJ 4 horas');
  await dlg.locator('button[type=submit]').click();
  await coord.page.waitForFunction(() => /mayor que cero/.test(document.querySelector('dialog[open]')?.innerText || ''), null, { timeout: 8000 });
  await dlg.getByRole('button', { name: 'Cancelar' }).click(); await dlg.waitFor({ state: 'detached', timeout: 8000 });
  for (const costo of ['0', '0.00', '-10']) {
    const r = await c.coord.fetch(`/solicitudes-servicio-adicional/${saId}/disponibilidad`, { method: 'POST', body: JSON.stringify({ disponible: true, proveedor_id: pvActivo, costo, condiciones: 'x' }) });
    if (r.status !== 422) throw new Error(`costo ${costo}: respondió ${r.status} y se esperaba 422`);
  }
  const r2 = await c.coord.fetch(`/solicitudes-servicio-adicional/${saId}/disponibilidad`, { method: 'POST', body: JSON.stringify({ disponible: true, proveedor_id: pvInactivo, costo: '800.00', condiciones: 'x' }) });
  if (r2.status !== 422) throw new Error(`proveedor inactivo: respondió ${r2.status}`);
  igual(sql(`select estado, disponibilidad_costo from solicitud_servicio_adicional where solicitud_id='${saId}'`), 'REGISTRADA|', 'servicio adicional tras los rechazos');
});

await paso('Servicio adicional: Coordinación registra proveedor, costo y condiciones; PostgreSQL los conserva', async () => {
  const dlg = await abrir(coord.page, saId, 'Registrar proveedor, costo y condiciones');
  await dlg.getByLabel('Proveedor del catálogo').selectOption(pvActivo);
  await dlg.getByLabel('Costo del proveedor').fill('750.00'); await dlg.getByLabel('Condiciones del servicio').fill('DJ 4 horas con sonido');
  await enviar(coord.page, dlg);
  await esperarTexto(coord.page, 'Pendiente de aprobación del Cliente');
  igual(sql(`select estado, disponibilidad_proveedor_id, disponibilidad_costo, disponibilidad_condiciones from solicitud_servicio_adicional where solicitud_id='${saId}'`),
    `PENDIENTE_APROBACION_CLIENTE|${pvActivo}|750.00|DJ 4 horas con sonido`, 'fila del servicio adicional');
});

await paso('Servicio adicional: Administración ve proveedor, costo y condiciones en la tabla y en el diálogo de autorización, y autoriza', async () => {
  await c.coord.json('POST', `/solicitudes-servicio-adicional/${saId}/aprobacion-cliente`, decision('Cliente'));
  await abrirEvento(admin.page);
  const f = await fila(admin.page, saId).innerText();
  if (!/750\.00/.test(f) || !f.includes(pvActivo) || !f.includes('DJ 4 horas con sonido')) throw new Error('la tabla no muestra proveedor, costo y condiciones: ' + f.slice(0, 200));
  if (await fila(admin.page, saId).getByRole('button', { name: 'Registrar proveedor, costo y condiciones', exact: true }).count()) throw new Error('Administración ve el botón de captura');
  const dlg = await abrir(admin.page, saId, 'Registrar autorización de Administración');
  const intro = await dlg.innerText();
  if (!intro.includes('Registrado por Coordinación') || !/750\.00/.test(intro) || !intro.includes('DJ 4 horas con sonido')) throw new Error('el diálogo de autorización no muestra lo registrado: ' + intro.slice(0, 300));
  await admin.page.screenshot({ path: `${SALIDA}/d3_2_autorizacion.png` });
  await enviar(admin.page, dlg);
  await esperarTexto(admin.page, 'Autorizada');
});

await paso('Cambio: Coordinación registra costo y condiciones opcionales; Administración los ve; sin condiciones queda vacío', async () => {
  await abrirEvento(coord.page);
  const dlg = await abrir(coord.page, scId, 'Evaluar viabilidad del cambio');
  await dlg.getByLabel('Costo adicional del proveedor').fill('1000.00'); await dlg.getByLabel('Condiciones del proveedor').fill('Pago del proveedor por adelantado');
  await enviar(coord.page, dlg);
  igual(sql(`select costo_proveedor, condiciones_proveedor from solicitud_cambio where solicitud_id='${scId}'`), '1000.00|Pago del proveedor por adelantado', 'fila del cambio');
  await abrirEvento(admin.page);
  const f = await fila(admin.page, scId).innerText();
  if (!/1,?000\.00/.test(f) || !f.includes('Pago del proveedor por adelantado')) throw new Error('Administración no ve costo y condiciones del cambio: ' + f.slice(0, 200));
  // segundo cambio sin condiciones (opcionales)
  const sc2 = (await c.coord.json('POST', '/solicitudes-cambio', { evento_id: eventoId, contrato_id: contratoId, descripcion: 'Otro cambio', tarifa_vigente: '500.00' })).datos.solicitud_id;
  await abrirEvento(coord.page); await esperarTexto(coord.page, sc2);
  const dlg2 = await abrir(coord.page, sc2, 'Evaluar viabilidad del cambio');
  await dlg2.getByLabel('Costo adicional del proveedor').fill('300.00');
  await enviar(coord.page, dlg2);
  igual(sql(`select costo_proveedor, coalesce(condiciones_proveedor,'(vacío)') from solicitud_cambio where solicitud_id='${sc2}'`), '300.00|(vacío)', 'cambio sin condiciones');
});

await paso('Sustitución: la alternativa se elige del catálogo (activos que ofrecen el servicio, distintos del original) y Administración la revisa', async () => {
  await abrirEvento(coord.page); await esperarTexto(coord.page, spId);
  const dlg = await abrir(coord.page, spId, 'Proponer alternativa de proveedor');
  const opciones = await dlg.getByLabel('Proveedor alternativo del catálogo').locator('option').evaluateAll((os) => os.map((o) => o.value));
  if (!opciones.includes(pvAlterno)) throw new Error('falta el proveedor alterno');
  if (opciones.includes(pvOriginal) || opciones.includes(pvOtro) || opciones.includes(pvInactivo)) throw new Error('se ofrece el original, un ajeno o un inactivo');
  await dlg.getByLabel('Proveedor alternativo del catálogo').selectOption(pvAlterno);
  await dlg.getByLabel('Condiciones de la alternativa').fill('Menú equivalente'); await dlg.getByLabel('Costo adicional').fill('250.50');
  await enviar(coord.page, dlg);
  igual(sql(`select disponibilidad_proveedor_id, disponibilidad_costo, disponibilidad_condiciones from sustitucion_alternativa where sustitucion_id='${spId}'`),
    `${pvAlterno}|250.50|Menú equivalente`, 'alternativa de la sustitución');
  await abrirEvento(admin.page); await esperarTexto(admin.page, spId);
  const f = await fila(admin.page, spId).innerText();
  if (!f.includes(pvAlterno) || !/250\.50/.test(f) || !f.includes('Menú equivalente')) throw new Error('Administración no ve la alternativa: ' + f.slice(0, 200));
});

await paso('Permisos en el servidor: Administración no captura (403); y el proveedor desactivado conserva su historial', async () => {
  const r = await c.admin.fetch(`/solicitudes-servicio-adicional/${saId}/disponibilidad`, { method: 'POST', body: JSON.stringify({ disponible: false }) });
  if (r.status !== 403) throw new Error(`Administración captura: respondió ${r.status}`);
  const r2 = await c.admin.fetch(`/sustituciones/${spId}/alternativa`, { method: 'POST', body: JSON.stringify({ proveedor_id: pvAlterno, condiciones_alternativa: 'x' }) });
  if (r2.status !== 403) throw new Error(`Administración propone alternativa: respondió ${r2.status}`);
  igual(sql(`select activo from proveedor where proveedor_id='${pvInactivo}'`), 'f', 'proveedor inactivo sigue en el catálogo');
});

await paso('Sin excepciones de JavaScript en el navegador', async () => { if (errores.length) throw new Error(errores.slice(0, 3).join(' | ')); });
await navegador.close();
console.log(`\nRESUMEN: ${resultados.filter((r) => r[0] === 'OK').length} OK, ${resultados.filter((r) => r[0] === 'FALLO').length} FALLO`);
process.exit(resultados.some((r) => r[0] === 'FALLO') ? 1 : 0);
