// Recorrido en Chrome real de los tres roles contra una API en marcha (por omisión, la del entorno manual). Verifica COR-02, COR-03, COR-05, COR-06,
// COR-07, COR-13, COR-16 y COR-17 con los datos que ya existen. NO ENVÍA NADA: los formularios se abren, se llenan y se cancelan (se retira el diálogo)
// antes de confirmar, de modo que no se crea ni modifica ningún registro.
// Las credenciales se leen de un archivo privado indicado por argumento (formato: «ROL: correo» y, en la línea siguiente, «contraseña: …») y no se imprimen.
// Uso: node scripts/probar_bloque_a_navegador.mjs <base> <archivo_credenciales> <carpeta_capturas> [puerto_cdp]
import { spawn } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const [BASE, CRED, SALIDA, P] = process.argv.slice(2);
if (!BASE || !CRED || !SALIDA) { console.error('Uso: node scripts/probar_bloque_a_navegador.mjs <base> <credenciales> <capturas> [puerto]'); process.exit(2); }
mkdirSync(SALIDA, { recursive: true });
const PUERTO = Number(P || 9461);
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const pausa = (ms) => new Promise((r) => setTimeout(r, ms));
const lineas = readFileSync(CRED, 'utf8').split(/\r?\n/);
const credencial = (rol) => {
  const i = lineas.findIndex((l) => new RegExp(`^${rol}\\s*:`, 'i').test(l));
  if (i < 0) throw new Error(`No hay credencial para ${rol}`);
  return [lineas[i].split(':').slice(1).join(':').trim().split(/\s+/)[0], lineas[i + 1].split(':').slice(1).join(':').trim()];
};

const perfil = mkdtempSync(join(tmpdir(), 'enova-bloque-a-'));
const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PUERTO}`, `--user-data-dir=${perfil}`, '--no-first-run', '--disable-gpu', '--window-size=1440,900', 'about:blank'], { stdio: 'ignore' });
let ws; let idMsg = 0; const pend = new Map(); const consola = [];
const enviar = (metodo, params = {}) => new Promise((res, rej) => { const id = ++idMsg; pend.set(id, { res, rej }); ws.send(JSON.stringify({ id, method: metodo, params })); });
const evaluar = async (expresion) => {
  const r = await enviar('Runtime.evaluate', { expression: expresion, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails.exception?.description || r.exceptionDetails.text));
  return r.result.value;
};
const resultados = []; let fallos = 0;
const comprobar = (desc, ok, det = '') => { resultados.push({ desc, ok, det }); if (!ok) fallos++; };
const cap = async (n) => { const r = await enviar('Page.captureScreenshot', { format: 'png' }); writeFileSync(join(SALIDA, n), Buffer.from(r.data, 'base64')); };
const ir = async (hash, ms = 1800) => { await evaluar(`location.hash=${JSON.stringify(hash)}; true`); await pausa(ms); };
const cerrarDialogos = () => evaluar(`document.querySelectorAll('dialog.modal').forEach((d) => d.remove()); true`);

async function entrar(rol) {
  const [correo, clave] = credencial(rol);
  await enviar('Network.clearBrowserCookies');
  await enviar('Page.navigate', { url: BASE + '/app/' }); await pausa(1500);
  await evaluar(`(()=>{try{localStorage.clear();sessionStorage.clear();}catch{} return true})()`);
  await enviar('Page.navigate', { url: BASE + '/app/' }); await pausa(1800);
  await evaluar(`(()=>{const c=document.getElementById('ing-clave'); const e=document.getElementById('ing-correo')||document.querySelector('input[name=correo]'); e.value=${JSON.stringify(correo)}; c.value=${JSON.stringify(clave)}; c.form.requestSubmit(); return true;})()`);
  await pausa(2500);
  return evaluar(`document.body.innerText.includes('Cerrar sesión')`);
}
const api = (ruta) => evaluar(`(async()=>{const r=await fetch(${JSON.stringify(ruta)},{headers:{Accept:'application/json'}}); let j=null; try{j=await r.json()}catch{} return {status:r.status, j}})()`);
const rellenar = (nombre, valor) => evaluar(`(async()=>{const c=document.querySelector('dialog.modal [name="${nombre}"]'); if(!c) return false; c.value=${JSON.stringify(valor)}; c.dispatchEvent(new Event('input',{bubbles:true})); c.dispatchEvent(new Event('change',{bubbles:true})); await new Promise(r=>setTimeout(r,80)); return true})()`);
const clicBoton = (texto) => evaluar(`(()=>{const b=[...document.querySelectorAll('button')].find((x)=>x.textContent.trim()===${JSON.stringify(texto)}); if(!b) return false; b.click(); return true})()`);

try {
  for (let i = 0; i < 60; i++) { try { if ((await fetch(`http://127.0.0.1:${PUERTO}/json/version`)).ok) break; } catch { /* aún */ } await pausa(500); }
  const lista = await (await fetch(`http://127.0.0.1:${PUERTO}/json/list`)).json();
  ws = new WebSocket(lista.find((t) => t.type === 'page').webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  ws.onmessage = (m) => {
    const d = JSON.parse(m.data);
    if (d.id && pend.has(d.id)) { const { res, rej } = pend.get(d.id); pend.delete(d.id); d.error ? rej(new Error(JSON.stringify(d.error))) : res(d.result); }
    else if (d.method === 'Runtime.exceptionThrown') consola.push('excepción: ' + (d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text));
    else if (d.method === 'Runtime.consoleAPICalled' && d.params.type === 'error') consola.push('console.error: ' + d.params.args.map((a) => a.value || a.description).join(' '));
  };
  await enviar('Page.enable'); await enviar('Runtime.enable'); await enviar('Network.enable');

  // ======================================================== ADMINISTRADOR
  comprobar('Administración: inicia sesión', await entrar('ADMINISTRADOR'));
  await ir('#/cuentas');
  const filtros = await evaluar(`(async()=>{const esp=(ms=90)=>new Promise(r=>setTimeout(r,ms)); const filas=()=>document.querySelectorAll('.tabla tbody tr').length;
    const total=filas(); const q=document.getElementById('cu-buscar'); const rol=document.getElementById('cu-rol'); const est=document.getElementById('cu-estado');
    rol.value='proveedor'; rol.dispatchEvent(new Event('change',{bubbles:true})); await esp(); const porRol=filas(); const soloProv=[...document.querySelectorAll('.tabla tbody tr')].every(r=>r.innerText.includes('Proveedor'));
    rol.value=''; rol.dispatchEvent(new Event('change',{bubbles:true})); est.value='desactivada'; est.dispatchEvent(new Event('change',{bubbles:true})); await esp(); const desact=filas();
    est.value=''; est.dispatchEvent(new Event('change',{bubbles:true})); q.value='zzz-no-existe'; q.dispatchEvent(new Event('input',{bubbles:true})); await esp(); const sin=filas(); q.value=''; q.dispatchEvent(new Event('input',{bubbles:true})); await esp();
    return {total,porRol,soloProv,desact,sin,vuelve:filas()}})()`);
  comprobar('Cuentas (COR-13): los filtros reducen la lista y limpiar la restaura', filtros.total > 0 && filtros.porRol <= filtros.total && filtros.soloProv && filtros.sin === 0 && filtros.vuelve === filtros.total, JSON.stringify(filtros));
  await cap('01_admin_cuentas_1440.png');

  // COR-02 + COR-03 en el formulario Crear cuenta (se cancela)
  await clicBoton('Crear cuenta'); await pausa(900);
  const f1 = await evaluar(`(async()=>{const esp=(ms=120)=>new Promise(r=>setTimeout(r,ms)); const d=document.querySelector('dialog.modal');
    const q=(n)=>d.querySelector('[name="'+n+'"]'); const fila=(n)=>q(n).closest('.campo'); const vis=(n)=>{const r=fila(n).getBoundingClientRect(); return r.width>0&&r.height>0};
    const out={};
    for (const rol of ['administrador','coordinador']) { q('rol').value=rol; q('rol').dispatchEvent(new Event('change',{bubbles:true})); await esp(); out['prov_'+rol]=vis('proveedor_id'); }
    q('rol').value='proveedor'; q('rol').dispatchEvent(new Event('change',{bubbles:true})); await esp(); out.prov_proveedor=vis('proveedor_id');
    const sel=q('proveedor_id'); const caja=fila('proveedor_id').querySelector('.busca-opciones'); out.opciones=sel.options.length; out.tieneBusqueda=!!caja;
    const objetivo=[...sel.options].filter(o=>o.value).map(o=>({v:o.value,t:o.textContent}))[3];
    caja.value=objetivo.t.slice(0,12).toLowerCase(); caja.dispatchEvent(new Event('input',{bubbles:true})); await esp();
    out.filtradas=sel.options.length; const elegida=[...sel.options].find(o=>o.value===objetivo.v); out.encuentra=!!elegida;
    sel.value=objetivo.v; sel.dispatchEvent(new Event('change',{bubbles:true})); await esp();
    out.valor_es_id=sel.value===objetivo.v && /^PV-/.test(sel.value); out.texto_legible=sel.options[sel.selectedIndex].textContent===objetivo.t && !/^PV-/.test(objetivo.t);
    caja.value=''; caja.dispatchEvent(new Event('input',{bubbles:true})); await esp(); out.conserva_seleccion=sel.value===objetivo.v; out.restauradas=sel.options.length;
    q('rol').value='coordinador'; q('rol').dispatchEvent(new Event('change',{bubbles:true})); await esp(); out.reinicia=q('proveedor_id').value===''&&!vis('proveedor_id');
    const clave=q('contrasena'); const ojo=clave.parentElement.querySelector('.btn-ojo'); out.ojo=!!ojo; if(ojo){ojo.click(); out.ojo_muestra=clave.type==='text'; ojo.click(); out.ojo_oculta=clave.type==='password';}
    return out})()`);
  comprobar('COR-03: el campo Proveedor solo aparece con el rol Proveedor y se reinicia al cambiar de rol', !f1.prov_administrador && !f1.prov_coordinador && f1.prov_proveedor && f1.reinicia, JSON.stringify(f1));
  comprobar('COR-02: la lista larga tiene búsqueda, localiza por nombre, conserva el identificador y muestra el nombre legible', f1.opciones > 6 && f1.tieneBusqueda && f1.filtradas < f1.opciones && f1.encuentra && f1.valor_es_id && f1.texto_legible && f1.conserva_seleccion && f1.restauradas === f1.opciones, JSON.stringify(f1));
  comprobar('Mostrar/Ocultar contraseña en Crear cuenta', f1.ojo && f1.ojo_muestra && f1.ojo_oculta, JSON.stringify(f1));
  await cap('02_admin_crear_cuenta_busqueda_1440.png');
  await cerrarDialogos();

  // COR-07: pago superior al saldo, solo hasta el resumen de confirmación (no se confirma)
  const pagosPend = await api('/pagos-pendientes');
  const anticipo = (pagosPend.j.pagos || []).find((x) => x.concepto === 'Anticipo' && Number(x.saldo) > 0);
  comprobar('Hay una obligación de anticipo con saldo para probar COR-07 sin tocar la boda', !!anticipo, anticipo ? 'ok' : 'sin datos');
  if (anticipo) {
    await ir(`#/evento/${anticipo.eventoId}`, 2500);
    await cap('03_admin_evento_pagos_1440.png');
    const etiquetas = await evaluar(`document.body.innerText`);
    comprobar('COR-06: la pantalla del evento no muestra nombres internos de conceptos', !/SaldoContratoOriginal|CargoCambioTardio|SustitucionProveedor|CargosMoratorios|ServicioAdicional/.test(etiquetas), 'texto revisado');
    await clicBoton('Registrar pago'); await pausa(900);
    const op = await evaluar(`(()=>{const s=document.querySelector('dialog.modal [name="obligacion_id"]'); return [...s.options].map(o=>({v:o.value,t:o.textContent}))})()`);
    const objetivoOb = op.find((o) => /^Anticipo/.test(o.t));
    comprobar('COR-06/04: el selector de obligación usa el concepto legible y el saldo', !!objetivoOb && /saldo [\d,]+\.\d{2}/.test(objetivoOb.t), JSON.stringify(op.map((o) => o.t)));
    await rellenar('obligacion_id', objetivoOb.v);
    await rellenar('importe', String(Number(anticipo.saldo) + 1000)); await rellenar('comprobante', 'PRUEBA-NO-ENVIAR');
    await evaluar(`document.querySelector('dialog.modal form').requestSubmit(); true`); await pausa(700);
    const resumen = await evaluar(`document.querySelector('dialog.modal').innerText`);
    comprobar('COR-07: el resumen muestra una advertencia visible cuando el importe supera el saldo y no bloquea (aparece el botón de confirmar)', /Atención: el importe supera el saldo pendiente/.test(resumen) && /no se devuelve automáticamente/.test(resumen) && await evaluar(`!!document.querySelector('dialog.modal .confirmacion .aviso-fuerte') && !!document.getElementById('btn-confirmar')`), resumen.slice(0, 200).replace(/\s+/g, ' '));
    await cap('04_admin_pago_advertencia_excedente_1440.png');
    await cerrarDialogos();
    // importe igual al saldo: sin advertencia
    await clicBoton('Registrar pago'); await pausa(800);
    await rellenar('obligacion_id', objetivoOb.v); await rellenar('importe', anticipo.saldo); await rellenar('comprobante', 'PRUEBA-NO-ENVIAR');
    await evaluar(`document.querySelector('dialog.modal form').requestSubmit(); true`); await pausa(700);
    comprobar('COR-07: con un importe que no supera el saldo no aparece la advertencia', !/Atención: el importe supera/.test(await evaluar(`document.querySelector('dialog.modal').innerText`)), '');
    await cerrarDialogos();
  }

  // COR-17 / COR-06 en la boda de la Ronda 2 (solo lectura)
  const boda = 'EV-d1dbdf71-10c7-4a85-b9eb-658ff020e1fb';
  await ir(`#/evento/${boda}`, 1500);
  for (let i = 0; i < 20 && !(await evaluar(`document.body.innerText.includes('Pagos registrados')`)); i++) await pausa(500);   // espera a que cargue el estado de cuenta
  const textoBoda = await evaluar(`document.body.innerText`);
  comprobar('COR-17: los pagos verificados se muestran como Verificado con su fecha y se explica que ya se suman', /Verificado/.test(textoBoda) && /ya se suma a lo pagado/.test(textoBoda), '');
  comprobar('COR-06: la boda muestra «Cargo por cambio tardío»/«Servicio adicional» y no los nombres internos', !/SaldoContratoOriginal|CargoCambioTardio|ServicioAdicional|\\bservicio adicional\\b(?=\\s*$)/m.test(textoBoda), '');
  await cap('05_admin_boda_1440.png');
  const pagosApi = await api(`/eventos/${boda}/pagos`);
  const pagosBoda = (pagosApi.j.estadosCuenta || []).flatMap((e) => e.pagosRegistrados || []);
  comprobar('La boda conserva sus 7 pagos verificados (sin cambios)', pagosBoda.length === 7 && pagosBoda.every((p) => p.estado === 'Verificado'), `pagos=${pagosBoda.length}`);

  // ======================================================== COORDINACIÓN
  comprobar('Coordinación: inicia sesión', await entrar('COORDINADOR'));
  await ir(`#/evento/${boda}`, 2800);
  const info = (await api(`/eventos/${boda}/administracion`)).j;
  const tieneBoton = await evaluar(`[...document.querySelectorAll('button')].some((b)=>b.textContent.trim()==='Solicitar cambio')`);
  comprobar('Coordinación: ve las acciones de solicitudes de la boda (cambio, servicio adicional, sustitución)', tieneBoton && await evaluar(`['Solicitar servicio adicional','Sustituir proveedor'].every((t)=>[...document.querySelectorAll('button')].some((b)=>b.textContent.trim()===t))`), '');
  comprobar('Coordinación: no ve el botón de registrar pagos (permiso solo de Administración)', !(await evaluar(`[...document.querySelectorAll('button')].some((b)=>b.textContent.trim()==='Registrar pago')`)), '');
  await clicBoton('Solicitar cambio'); await pausa(900);
  const pre = await evaluar(`(async()=>{const esp=(ms=120)=>new Promise(r=>setTimeout(r,ms)); const d=document.querySelector('dialog.modal'); const q=(n)=>d.querySelector('[name="'+n+'"]');
    const antes=['tipo','fecha_hora','lugar','invitados_aproximados'].map((n)=>{const r=q(n).closest('.campo').getBoundingClientRect(); return r.width>0&&r.height>0});
    const marca=q('cambiar_datos'); const marcadoInicial=marca.checked; marca.checked=true; marca.dispatchEvent(new Event('change',{bubbles:true})); await esp();
    return {antes, marcadoInicial, tipo:q('tipo').value, fecha:q('fecha_hora').value, lugar:q('lugar').value, invitados:q('invitados_aproximados').value}})()`);
  comprobar('COR-16: los campos de datos están ocultos y sin marcar por omisión (no se sobrescribe nada sin una acción explícita)', pre.antes.every((v) => v === false) && pre.marcadoInicial === false, JSON.stringify(pre.antes));
  comprobar('COR-16: al marcar «modifica los datos» aparecen los datos actuales del evento (tipo, fecha y hora, lugar, invitados)',
    pre.tipo === info.tipoEvento && pre.fecha.slice(0, 16) === info.fechaHora.slice(0, 16) && pre.lugar === info.lugar && String(pre.invitados) === String(info.invitadosAproximados), JSON.stringify({ pre, info: { t: info.tipoEvento, f: info.fechaHora, l: info.lugar, i: info.invitadosAproximados } }));
  await cap('06_coord_cambio_precarga_1440.png');
  await cerrarDialogos();
  const desdeApi = (await api(`/eventos/${boda}/administracion`)).j;
  comprobar('COR-16: abrir y cancelar el formulario no modifica el evento', desdeApi.fechaHora === info.fechaHora && desdeApi.lugar === info.lugar && desdeApi.invitadosAproximados === info.invitadosAproximados, '');
  await ir('#/solicitudes', 2200);
  const solicitudes = await evaluar(`document.body.innerText`);
  comprobar('Solicitudes: los tipos se muestran con etiqueta legible y los filtros conservan el valor interno', /Servicio adicional|Sustitución de proveedor|Cambio/.test(solicitudes) && await evaluar(`[...document.querySelectorAll('#f-tipo option')].map(o=>o.value).join('|')`) === '|cambio|servicio adicional|sustitución de proveedor', '');
  await ir('#/proveedores', 2200);
  comprobar('Coordinación: consulta el catálogo de proveedores', /Proveedores/.test(await evaluar(`document.body.innerText`)), '');
  comprobar('Coordinación: no ve la administración de cuentas', !(await evaluar(`[...document.querySelectorAll('#menu a')].some((a)=>{const r=a.getBoundingClientRect(); return !a.hidden && r.width>0 && r.height>0 && a.textContent.trim()==='Cuentas'})`)), '');

  // ======================================================== PROVEEDOR (el que tiene los servicios de la boda)
  comprobar('Proveedor: inicia sesión', await entrar('ALTERNO'));
  await ir('#/proveedor', 2500);
  const textoProv = await evaluar(`document.body.innerText`);
  const asign = await api('/mis-asignaciones');
  const servicios = (asign.j.eventos || []).flatMap((e) => e.servicios || []);
  comprobar('Proveedor (COR-05): la API devuelve solo claves operativas, sin condiciones comerciales', servicios.length > 0 && servicios.every((s) => JSON.stringify(Object.keys(s).sort()) === JSON.stringify(['estado', 'respuesta', 'servicio', 'servicioContratadoId'])), `servicios=${servicios.length}`);
  comprobar('Proveedor (COR-05): la pantalla no muestra «Condiciones» ni importes del contrato', !/Condiciones/.test(textoProv.split('Mis datos')[0]) && !/\$|10,?000|Anticipo|Saldo/.test(textoProv), '');
  comprobar('Proveedor: ve sus servicios asignados de la boda', (asign.j.eventos || []).some((e) => e.eventoId === boda), '');
  const ajeno = await api(`/eventos/${boda}/administracion`);
  comprobar('Proveedor: no accede a la información administrativa ni a los pagos (403)', ajeno.status === 403 && (await api(`/eventos/${boda}/pagos`)).status === 403 && (await api('/usuarios')).status === 403, `estados=${ajeno.status}`);
  comprobar('Proveedor: su menú solo muestra «Mi proveedor» y «Sistema y ayuda»', (await evaluar(`[...document.querySelectorAll('#menu a')].filter((a)=>{const r=a.getBoundingClientRect(); return !a.hidden && r.width>0 && r.height>0}).map((a)=>a.textContent.trim()).join('|')`)) === 'Mi proveedor|Sistema y ayuda', '');
  await cap('07_proveedor_1440.png');
  await enviar('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  await pausa(700); await cap('08_proveedor_390.png');
  comprobar('Móvil 390 px: la vista del proveedor no desborda horizontalmente', (await evaluar(`document.documentElement.scrollWidth - document.documentElement.clientWidth`)) <= 1, '');
  comprobar('Sin errores de consola ni excepciones durante todo el recorrido', consola.length === 0, consola.slice(0, 3).join(' | '));
} catch (e) {
  fallos++; resultados.push({ desc: 'El recorrido no pudo completarse', ok: false, det: String(e.message || e) });
} finally {
  try { ws && ws.close(); } catch { /* nada */ }
  chrome.kill(); await pausa(800);
  try { rmSync(perfil, { recursive: true, force: true, maxRetries: 5, retryDelay: 300 }); } catch { /* perfil temporal */ }
}
for (const r of resultados) console.log((r.ok ? 'OK    ' : 'FALLA ') + r.desc + (r.ok ? '' : '\n        → ' + String(r.det).slice(0, 400)));
console.log(`\n${resultados.length - fallos} de ${resultados.length} comprobaciones correctas`);
process.exit(fallos ? 1 : 0);
