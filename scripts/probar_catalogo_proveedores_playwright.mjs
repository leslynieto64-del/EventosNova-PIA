// Prueba REAL con Playwright (Chrome instalado, sin mocks) de edición, desactivación y reactivación de proveedores desde la interfaz,
// contra la API con PostgreSQL del entorno manual. Cada cambio se comprueba en la pantalla Y directamente en la base (psql dentro del contenedor).
//   PLAYWRIGHT_DIR=<carpeta donde está instalado playwright> EVENTOSNOVA_E2E_ADMIN_CORREO=… EVENTOSNOVA_E2E_ADMIN_CLAVE=… \
//   node scripts/probar_catalogo_proveedores_playwright.mjs http://127.0.0.1:8001 <carpeta de capturas>
// Crea sus propios datos (un evento, dos servicios, un proveedor y una cuenta de proveedor); no borra ni limpia nada y no imprime contraseñas.
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import { randomBytes } from 'node:crypto';
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
    for (const [quien, pg] of Object.entries(paginas)) { try { await pg.screenshot({ path: `${SALIDA}/fallo_${quien}_${resultados.length}.png` }); console.log(`      [${quien}] ${pg.url().slice(-60)} | diálogos abiertos: ${await pg.locator('dialog[open]').count()} | botones: ${JSON.stringify((await pg.locator('button:visible').allInnerTexts()).slice(0, 8))}`); } catch { /* */ } }
  }
};
const igual = (real, esperado, que) => { if (JSON.stringify(real) !== JSON.stringify(esperado)) throw new Error(`${que}: se esperaba ${JSON.stringify(esperado)} y la base tiene ${JSON.stringify(real)}`); };

/** Consulta de solo lectura directa a PostgreSQL (la misma base que usa la API). */
const sql = (consulta) => execFileSync('docker', ['exec', 'eventosnova-db', 'sh', '-c', `psql -U "$POSTGRES_USER" -d ${BASE_DATOS} -At -F '|' -c "${consulta}"`], { encoding: 'utf8' }).trim();

const c = await prepararCuentas(BASE, MARCA);
const SA = `Catalogo A ${MARCA}`; const SB = `Catalogo B ${MARCA}`;
const NOMBRE0 = `Proveedor catálogo ${MARCA}`; const NOMBRE1 = `Proveedor catálogo editado ${MARCA}`;
let eventoId; let provId; let cuentaProv;
const ahora = () => new Date(Date.now() - 6 * 3600 * 1000).toISOString().slice(0, 19);

await paso('Datos de prueba por la API: evento En organización con dos servicios, proveedor del catálogo y su cuenta', async () => {
  eventoId = (await c.coord.json('POST', '/eventos', { cliente_id: 'CL-PW', datos: { tipo: `Prueba Playwright ${MARCA}`, fecha_hora: new Date(Date.now() + 75 * 864e5).toISOString().slice(0, 19), lugar: 'Salón', invitados_aproximados: 40 }, servicios: [SA, SB] })).evento_id;
  const prop = (await c.coord.json('POST', `/eventos/${eventoId}/propuestas`, { servicios: [SA, SB], proveedores_considerados: ['PV-X'], costo_total: '10000.00', condiciones: 'Prueba' })).propuesta_id;
  await c.coord.json('POST', `/propuestas/${prop}/aceptacion`, { version_id: `${prop}-v1` });
  const ct = (await c.coord.json('POST', `/propuestas/${prop}/contrato`, { politica_incluida: true })).datos.contrato_id;
  await c.coord.json('POST', `/contratos/${ct}/comunicacion-politica-no-reembolso`, { fecha: ahora() }); await c.coord.json('POST', `/contratos/${ct}/firma`, { fecha: ahora() });
  const ec = (await c.coord.json('GET', `/eventos/${eventoId}/pagos`)).estadosCuenta[0].estadoCuentaId;
  const ob = (await c.coord.json('GET', `/pagos-pendientes?evento_id=${eventoId}`)).pagos.find((p) => p.concepto === 'Anticipo');
  await c.admin.json('POST', `/estados-cuenta/${ec}/pagos`, { obligacion_id: ob.obligacionId, importe: '3000.00', fecha: ahora(), comprobante: `PW-${MARCA}`, verificar_ahora: true });
  for (let i = 0; i < 25; i++) { if ((await c.coord.json('GET', `/eventos/${eventoId}/administracion`)).estadoEvento === 'En organización') break; await new Promise((r) => setTimeout(r, 300)); }
  provId = (await c.coord.json('POST', '/proveedores', { nombre: NOMBRE0, servicios: [SA, SB], contacto: '55 0000 0000' })).datos.proveedorId;
  const clave = 'Prueba-' + randomBytes(12).toString('base64url'); const correo = `proveedor.pw.${MARCA}@eventosnova.example`.toLowerCase();
  await c.admin.json('POST', '/usuarios', { correo, nombre: `Proveedor PW ${MARCA}`, rol: 'proveedor', contrasena: clave, proveedor_id: provId }); cuentaProv = { correo, clave };
  igual(sql(`select activo from proveedor where proveedor_id='${provId}'`), 't', 'activo inicial');
});

const navegador = await chromium.launch({ channel: 'chrome', headless: true });
const errores = [];
async function sesionUI(correo, clave) {
  const ctx = await navegador.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  page.on('pageerror', (e) => errores.push(e.message));
  await page.goto(`${BASE}/app/`);
  await page.fill('#ing-correo', correo); await page.fill('#ing-clave', clave);
  await page.click('.ingreso-forma button[type=submit]');
  await page.waitForSelector('#sesion-caja button', { timeout: 15000 });
  return { ctx, page };
}
/** Abre un diálogo de acción, rellena campos por su etiqueta, envía y confirma en el paso de resumen. */
async function accion(page, boton, campos = {}) {
  await page.getByRole('button', { name: boton, exact: true }).first().click();
  const dlg = page.locator('dialog[open]'); await dlg.waitFor({ timeout: 8000 });
  for (const [etiqueta, valor] of Object.entries(campos)) await dlg.getByLabel(etiqueta, { exact: false }).fill(valor);
  if (await dlg.locator('#btn-confirmar:visible').count() === 0) await dlg.locator('button[type=submit]').click();     // sin campos, el diálogo abre directo en la confirmación
  await page.locator('#btn-confirmar').click();
  await dlg.waitFor({ state: 'detached', timeout: 10000 });
}
const textoPagina = (page) => page.evaluate(() => document.body.innerText);
const esperarTexto = (page, t, ms = 10000) => page.waitForFunction((x) => document.body.innerText.includes(x), t, { timeout: ms });

const admin = await sesionUI(c.correoAdmin, c.claveAdmin);
const coord = await sesionUI(c.correoCoord, c.claveCoord);
paginas.admin = admin.page; paginas.coord = coord.page;

await paso('EDITAR: Administración corrige nombre, servicios y contacto desde la ficha; la pantalla y PostgreSQL lo reflejan', async () => {
  await admin.page.goto(`${BASE}/app/#/proveedores/${provId}`); await esperarTexto(admin.page, NOMBRE0);
  await accion(admin.page, 'Editar', { 'Nombre del proveedor': NOMBRE1, 'Servicios que ofrece': `${SA}, ${SB}, Extra`, 'Contacto': '55 7777 0000' });
  await esperarTexto(admin.page, NOMBRE1);
  const fila = sql(`select nombre, contacto, array_to_string(servicios, ';'), activo from proveedor where proveedor_id='${provId}'`);
  igual(fila, `${NOMBRE1}|55 7777 0000|${SA};${SB};Extra|t`, 'fila del proveedor tras editar');
  await admin.page.screenshot({ path: `${SALIDA}/pw_1_editado.png` });
});

await paso('EDITAR persiste: tras recargar la página y desde el listado sigue el nombre nuevo (y el viejo ya no existe)', async () => {
  await admin.page.reload(); await esperarTexto(admin.page, NOMBRE1);
  await admin.page.goto(`${BASE}/app/#/proveedores?q=${encodeURIComponent(MARCA)}`); await esperarTexto(admin.page, NOMBRE1);
  if ((await textoPagina(admin.page)).includes(NOMBRE0)) throw new Error('el nombre anterior sigue en el listado');
  igual(sql(`select count(*) from proveedor where nombre='${NOMBRE0}'`), '0', 'proveedores con el nombre anterior');
});

await paso('EDITAR rechaza un nombre repetido con un mensaje claro y no cambia nada', async () => {
  const otro = (await c.coord.json('POST', '/proveedores', { nombre: `Otro proveedor ${MARCA}`, servicios: ['X'], contacto: '' })).datos.proveedorId;
  await admin.page.goto(`${BASE}/app/#/proveedores/${provId}`); await esperarTexto(admin.page, NOMBRE1);
  await admin.page.getByRole('button', { name: 'Editar', exact: true }).first().click();
  const dlg = admin.page.locator('dialog[open]'); await dlg.waitFor();
  await dlg.getByLabel('Nombre del proveedor').fill(`otro PROVEEDOR ${MARCA}`);
  await dlg.locator('button[type=submit]').click(); await admin.page.locator('#btn-confirmar').click();
  await admin.page.waitForFunction(() => /Ya existe otro proveedor/.test(document.querySelector('dialog[open]')?.innerText || document.body.innerText), null, { timeout: 8000 });
  await dlg.getByRole('button', { name: 'Cancelar' }).click(); await dlg.waitFor({ state: 'detached', timeout: 8000 });
  igual(sql(`select nombre from proveedor where proveedor_id='${provId}'`), NOMBRE1, 'nombre tras el rechazo');
  void otro;
});

await paso('Coordinación asigna el servicio A al proveedor activo desde la interfaz (queda pendiente de confirmación)', async () => {
  await coord.page.goto(`${BASE}/app/#/evento/${eventoId}`); await esperarTexto(coord.page, SA);
  const filaA = coord.page.locator('tr', { hasText: SA, has: coord.page.getByRole('button', { name: 'Ver candidatos', exact: true }) }).first();
  await filaA.getByRole('button', { name: 'Asignar proveedor' }).click();
  const dlg = coord.page.locator('dialog[open]'); await dlg.waitFor();
  const opciones = await dlg.locator('select option').allInnerTexts(); if (!opciones.some((o) => o.includes(NOMBRE1))) throw new Error('el proveedor activo no se ofrece: ' + JSON.stringify(opciones));
  await dlg.locator('select').selectOption({ index: opciones.findIndex((o) => o.includes(NOMBRE1)) });
  await dlg.locator('button[type=submit]').click(); await coord.page.locator('#btn-confirmar').click(); await dlg.waitFor({ state: 'detached' });
  await esperarTexto(coord.page, 'Pendiente de confirmación del proveedor');
  if (sql(`select proveedor_id from evento_servicio_contratado where evento_id='${eventoId}' and servicio='${SA}'`) !== provId) throw new Error('el servicio A no quedó asignado en PostgreSQL');
});

await paso('DESACTIVAR: Administración desactiva al proveedor; pantalla, listado y PostgreSQL lo reflejan y persiste al recargar', async () => {
  await admin.page.goto(`${BASE}/app/#/proveedores/${provId}`); await esperarTexto(admin.page, NOMBRE1);
  await accion(admin.page, 'Desactivar');
  await esperarTexto(admin.page, 'Desactivado'); igual(sql(`select activo from proveedor where proveedor_id='${provId}'`), 'f', 'activo tras desactivar');
  await admin.page.reload(); await esperarTexto(admin.page, 'Desactivado (no se propone para asignaciones nuevas)');
  await admin.page.goto(`${BASE}/app/#/proveedores?q=${encodeURIComponent(MARCA)}`); await esperarTexto(admin.page, 'Desactivado');
  await admin.page.screenshot({ path: `${SALIDA}/pw_2_desactivado.png` });
});

await paso('Un proveedor desactivado NO recibe asignaciones nuevas: la interfaz no lo ofrece, la API lo rechaza y la base no cambia', async () => {
  await coord.page.goto(`${BASE}/app/#/evento/${eventoId}`); await esperarTexto(coord.page, SB);
  const filaB = coord.page.locator('tr', { hasText: SB, has: coord.page.getByRole('button', { name: 'Ver candidatos', exact: true }) }).first();
  await filaB.getByRole('button', { name: 'Asignar proveedor' }).click();
  await esperarTexto(coord.page, 'No hay proveedores candidatos');
  await coord.page.screenshot({ path: `${SALIDA}/pw_3_sin_candidatos.png` });
  await coord.page.locator('dialog[open]').getByRole('button').first().click(); await coord.page.locator('dialog[open]').waitFor({ state: 'detached', timeout: 8000 });
  const sid = sql(`select servicio_contratado_id from evento_servicio_contratado where evento_id='${eventoId}' and servicio='${SB}'`);
  const r = await c.coord.fetch(`/eventos/${eventoId}/servicios/${sid}/proveedor`, { method: 'POST', body: JSON.stringify({ proveedor_id: provId }) });
  const cuerpo = await r.json(); if (r.status !== 422 || !String(cuerpo.detalle).includes('desactivado')) throw new Error(`la API debía rechazar con 422 «desactivado»: ${r.status} ${JSON.stringify(cuerpo)}`);
  igual(sql(`select coalesce(proveedor_id,'(sin proveedor)') from evento_servicio_contratado where evento_id='${eventoId}' and servicio='${SB}'`), '(sin proveedor)', 'servicio B en la base');
});

await paso('El HISTORIAL se conserva: el servicio A sigue asignado a ese proveedor, visible para Coordinación y para su cuenta, que aún puede responder', async () => {
  igual(sql(`select proveedor_id from evento_servicio_contratado where evento_id='${eventoId}' and servicio='${SA}'`), provId, 'servicio A sigue asignado');
  await coord.page.goto(`${BASE}/app/#/evento/${eventoId}`); await esperarTexto(coord.page, NOMBRE1);
  const prov = await sesionUI(cuentaProv.correo, cuentaProv.clave);
  await prov.page.goto(`${BASE}/app/#/proveedor`); await esperarTexto(prov.page, 'Mis asignaciones'); await esperarTexto(prov.page, SA);
  await accion(prov.page, 'Registrar respuesta del proveedor');
  await esperarTexto(prov.page, 'Confirmado por el proveedor');
  igual(sql(`select estado from evento_servicio_contratado where evento_id='${eventoId}' and servicio='${SA}'`).length > 0, true, 'estado registrado');
  await prov.page.reload(); await esperarTexto(prov.page, 'Confirmado por el proveedor');
  await prov.page.screenshot({ path: `${SALIDA}/pw_4_historial_proveedor.png` });
  await prov.ctx.close();
});

await paso('REACTIVAR: Administración lo reactiva; vuelve a ofrecerse y Coordinación asigna el servicio B; todo queda en PostgreSQL', async () => {
  await admin.page.goto(`${BASE}/app/#/proveedores/${provId}`); await esperarTexto(admin.page, 'Desactivado (no se propone');
  await accion(admin.page, 'Activar');
  await esperarTexto(admin.page, 'Activo'); igual(sql(`select activo from proveedor where proveedor_id='${provId}'`), 't', 'activo tras reactivar');
  await admin.page.reload(); await admin.page.waitForFunction(() => document.body.innerText.includes('Activo') && !document.body.innerText.includes('Desactivado (no se propone'), null, { timeout: 8000 });
  await coord.page.goto(`${BASE}/app/#/evento/${eventoId}`); await esperarTexto(coord.page, SB);
  const filaB = coord.page.locator('tr', { hasText: SB, has: coord.page.getByRole('button', { name: 'Ver candidatos', exact: true }) }).first();
  await filaB.getByRole('button', { name: 'Asignar proveedor' }).click();
  const dlg = coord.page.locator('dialog[open]'); await dlg.waitFor();
  const opciones = await dlg.locator('select option').allInnerTexts(); if (!opciones.some((o) => o.includes(NOMBRE1))) throw new Error('el proveedor reactivado no se ofrece: ' + JSON.stringify(opciones));
  await dlg.locator('select').selectOption({ index: opciones.findIndex((o) => o.includes(NOMBRE1)) });
  await dlg.locator('button[type=submit]').click(); await coord.page.locator('#btn-confirmar').click(); await dlg.waitFor({ state: 'detached' });
  await coord.page.waitForFunction((n) => document.body.innerText.includes(n), NOMBRE1);
  igual(sql(`select proveedor_id from evento_servicio_contratado where evento_id='${eventoId}' and servicio='${SB}'`), provId, 'servicio B asignado tras reactivar');
  await admin.page.screenshot({ path: `${SALIDA}/pw_5_reactivado.png` });
});

await paso('S-8: Coordinación ve la ficha pero sin Editar/Desactivar/Activar, y el servidor rechaza (403) editar, desactivar y activar por la API; PostgreSQL no cambia', async () => {
  const antes = sql(`select nombre, contacto, activo from proveedor where proveedor_id='${provId}'`);
  await coord.page.goto(`${BASE}/app/#/proveedores/${provId}`); await esperarTexto(coord.page, NOMBRE1);
  for (const boton of ['Editar', 'Desactivar', 'Activar']) {
    if (await coord.page.getByRole('button', { name: boton, exact: true }).count()) throw new Error(`Coordinación ve el botón «${boton}»`);
  }
  await coord.page.screenshot({ path: `${SALIDA}/pw_6_coordinacion_sin_edicion.png` });
  const cuerpos = { edicion: { nombre: `Intento ${MARCA}`, servicios: ['X'], contacto: '' }, desactivacion: {}, activacion: {} };
  for (const [ruta, cuerpo] of Object.entries(cuerpos)) {
    const r = await c.coord.fetch(`/proveedores/${provId}/${ruta}`, { method: 'POST', body: JSON.stringify(cuerpo) });
    if (r.status !== 403) throw new Error(`/${ruta} respondió ${r.status} y se esperaba 403`);
  }
  igual(sql(`select nombre, contacto, activo from proveedor where proveedor_id='${provId}'`), antes, 'proveedor tras los intentos de Coordinación');
  // Coordinación sí registra y consulta el catálogo
  if (!(await coord.page.goto(`${BASE}/app/#/proveedores`), await coord.page.getByRole('button', { name: 'Registrar proveedor', exact: true }).count())) throw new Error('Coordinación no ve «Registrar proveedor»');
});

await paso('D-P2 y S-7 en la interfaz: «Ver candidatos» aclara que la disponibilidad por fecha no se verifica, el inicio manual se presenta como respaldo y «Sistema y ayuda» ya no niega la autenticación', async () => {
  await coord.page.goto(`${BASE}/app/#/evento/${eventoId}`); await esperarTexto(coord.page, SA);
  const texto = await textoPagina(coord.page);
  if (/Ver disponibilidad/.test(texto)) throw new Error('sigue el botón «Ver disponibilidad»');
  await coord.page.locator('tr', { hasText: SB, has: coord.page.getByRole('button', { name: 'Ver candidatos', exact: true }) }).first().getByRole('button', { name: 'Ver candidatos', exact: true }).click();
  await esperarTexto(coord.page, 'no comprueba si está libre en la fecha del evento');
  await coord.page.screenshot({ path: `${SALIDA}/pw_7_candidatos.png` });
  await coord.page.locator('dialog[open]').getByRole('button').first().click(); await coord.page.locator('dialog[open]').waitFor({ state: 'detached', timeout: 8000 });
  if (!(await coord.page.getByRole('button', { name: 'Registrar inicio del evento (respaldo)', exact: true }).count())) throw new Error('falta el botón de inicio como respaldo');
  await esperarTexto(coord.page, 'mecanismo excepcional');
  await coord.page.goto(`${BASE}/app/#/sistema`); await esperarTexto(coord.page, 'Límites conocidos');
  if (/no tiene autenticación ni roles/.test(await textoPagina(coord.page))) throw new Error('«Sistema y ayuda» sigue negando la autenticación');
  await esperarTexto(coord.page, 'Cada persona entra con su cuenta y su rol');
});

await paso('Sin excepciones de JavaScript en el navegador', async () => { if (errores.length) throw new Error(errores.slice(0, 3).join(' | ')); });
await navegador.close();
console.log(`\nRESUMEN: ${resultados.filter((r) => r[0] === 'OK').length} OK, ${resultados.filter((r) => r[0] === 'FALLO').length} FALLO`);
process.exit(resultados.some((r) => r[0] === 'FALLO') ? 1 : 0);
