/* Administración de cuentas (solo el rol administrador; el servidor lo vuelve a comprobar). */
import { GET } from '../api.js';
import { ACCIONES } from '../acciones.js';
import { ETIQUETA_ROL, estado as sesion } from '../sesion.js';
import { fmtFechaHora } from '../negocio.js';
import { aviso, botonAccion, cargarEn, ejecutarAccion, h, insignia, tabla, tarjeta } from '../ui.js';

export function cuentas(contenedor) {
  const salida = h('div');
  const filtro = { texto: '', rol: '', estado: '' };            // solo afecta lo que se muestra; la lista completa viene del servidor
  let cargado = null;
  const coincide = (x, nombreProveedor) => {
    const q = filtro.texto.trim().toLowerCase();
    if (filtro.rol && x.rol !== filtro.rol) return false;
    if (filtro.estado && (x.activo ? 'activa' : 'desactivada') !== filtro.estado) return false;
    return !q || [x.nombre, x.correo, nombreProveedor[x.proveedorId] || ''].some((t) => String(t).toLowerCase().includes(q));
  };
  const pintarTabla = (pintar) => {
    const { u, p } = cargado;
    const nombreProveedor = Object.fromEntries(p.map((x) => [x.proveedorId, x.nombre]));
    const visibles = u.filter((x) => coincide(x, nombreProveedor));
    const hay = visibles.length !== u.length;
    return tarjeta(hay ? `${visibles.length} de ${u.length} cuenta(s)` : `${u.length} cuenta(s)`, tabla([
      { titulo: 'Persona', celda: (x) => h('div', null, x.nombre, h('div', { class: 'peq' }, x.correo)) },
      { titulo: 'Rol', celda: (x) => ETIQUETA_ROL[x.rol] || x.rol },
      { titulo: 'Proveedor', celda: (x) => (x.proveedorId ? (nombreProveedor[x.proveedorId] || x.proveedorId) : '—') },
      { titulo: 'Estado', celda: (x) => insignia(x.activo ? 'Activa' : 'Desactivada') },
      { titulo: 'Último acceso', celda: (x) => (x.ultimoAcceso ? fmtFechaHora(x.ultimoAcceso) : 'Nunca') },
      { titulo: 'Acciones', celda: (x) => h('div', { class: 'acciones' },
        x.usuarioId === (sesion.usuario && sesion.usuario.usuarioId) ? h('span', { class: 'peq' }, 'Tu cuenta')
          : botonAccion(x.activo ? ACCIONES.desactivarCuenta : ACCIONES.activarCuenta, { usuario: x }, pintar, { clase: 'btn btn-peq' }),
        botonAccion(ACCIONES.editarCuenta, { usuario: x }, pintar, { clase: 'btn btn-peq', texto: 'Editar' }),
        botonAccion(ACCIONES.restablecerContrasena, { usuario: x }, pintar, { clase: 'btn btn-peq' })) },
    ], visibles, { vacioTitulo: u.length ? 'Ninguna cuenta coincide con la búsqueda' : 'No hay cuentas', vacioDetalle: u.length ? 'Cambia o limpia los filtros para ver las demás cuentas.' : undefined }));
  };
  const tablaEn = h('div');
  const repintarTabla = () => { if (cargado) tablaEn.replaceChildren(pintarTabla(pintar)); };
  const pintar = () => cargarEn(salida, async () => ({ u: (await GET('/usuarios')).datos.usuarios, p: (await GET('/proveedores')).datos.proveedores }), (datos) => {
    cargado = datos;
    tablaEn.replaceChildren(pintarTabla(pintar));
    return tablaEn;
  });
  const opciones = (lista) => lista.map(([v, t]) => h('option', { value: v }, t));
  const barra = h('form', { class: 'barra-filtros', role: 'search', onsubmit: (ev) => ev.preventDefault() },
    h('div', { class: 'campo' }, h('label', { for: 'cu-buscar' }, 'Buscar'),
      h('input', { id: 'cu-buscar', type: 'search', placeholder: 'Nombre, correo o proveedor', autocomplete: 'off', oninput: (ev) => { filtro.texto = ev.target.value; repintarTabla(); } })),
    h('div', { class: 'campo' }, h('label', { for: 'cu-rol' }, 'Rol'),
      h('select', { id: 'cu-rol', onchange: (ev) => { filtro.rol = ev.target.value; repintarTabla(); } }, opciones([['', 'Todos los roles'], ...Object.entries(ETIQUETA_ROL)]))),
    h('div', { class: 'campo' }, h('label', { for: 'cu-estado' }, 'Estado'),
      h('select', { id: 'cu-estado', onchange: (ev) => { filtro.estado = ev.target.value; repintarTabla(); } }, opciones([['', 'Todas'], ['activa', 'Activas'], ['desactivada', 'Desactivadas']]))));
  contenedor.replaceChildren(
    h('header', { class: 'pagina-cab' }, h('h1', null, 'Cuentas'),
      h('p', null, 'Quién puede entrar a la aplicación y con qué rol. Una cuenta nueva solo recibe los permisos de su rol; las de proveedor se vinculan a un proveedor del catálogo.'),
      h('div', { class: 'acciones' }, h('button', { type: 'button', class: 'btn btn-primario', onclick: async () => {
        let proveedores = [];
        try { proveedores = (await GET('/proveedores')).datos.proveedores; } catch (e) { aviso('error', e.message); return; }
        await ejecutarAccion(ACCIONES.crearCuenta, { proveedores }, pintar);
      } }, 'Crear cuenta'))),
    barra, salida);
  pintar();
}
