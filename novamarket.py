"""NovaMarket Ecuador — prototipo educativo del Grupo 8.
Patrones GoF: Decorator, Factory Method y Observer. Solo Python estándar.
Facturas de muestra SIN VALIDEZ TRIBUTARIA.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from html import escape
from datetime import datetime

CENT = Decimal('0.01')
def D(v):
    return Decimal(str(v)).quantize(CENT, rounding=ROUND_HALF_UP)
def usd(v):
    return f'${D(v):,.2f}'

# Catálogo: Producto conserva su precio base, inmutable.
@dataclass(frozen=True)
class Producto:
    codigo: str
    nombre: str
    categoria: str
    precio_base: Decimal
    def __post_init__(self):
        object.__setattr__(self, 'precio_base', D(self.precio_base))
        if self.precio_base < 0: raise ValueError('Precio base negativo')

class Catalogo:
    def __init__(self, productos: list[Producto]):
        self._productos = {p.codigo: p for p in productos}
    def listar(self): return tuple(self._productos.values())
    def buscar(self, codigo: str):
        if codigo not in self._productos: raise ValueError('Código inexistente')
        return self._productos[codigo]

# OBSERVER
class Observador(ABC):
    @abstractmethod
    def actualizar(self, evento: str, producto: Producto, cantidad: int): ...

class ModuloStock(Observador):
    def __init__(self, existencias: dict[str,int]):
        self.existencias = dict(existencias)
        self.historial = []
    def validar(self, producto: Producto, cantidad: int):
        if self.existencias.get(producto.codigo, 0) < cantidad:
            raise ValueError(f'Stock insuficiente para {producto.nombre}')
    def actualizar(self, evento, producto, cantidad):
        if evento == 'agregado':
            self.validar(producto, cantidad)
            self.existencias[producto.codigo] -= cantidad
        elif evento == 'eliminado':
            self.existencias[producto.codigo] = self.existencias.get(producto.codigo, 0) + cantidad
        else: raise ValueError('Evento desconocido')
        self.historial.append(f'{evento}: {cantidad} × {producto.nombre}')

class SistemaRecomendaciones(Observador):
    def __init__(self): self.historial = []
    def actualizar(self, evento, producto, cantidad):
        self.historial.append(f'{evento}: {producto.categoria} / {producto.nombre} ({cantidad})')

class CarritoCompras:
    def __init__(self):
        self._items: dict[str, tuple[Producto,int]] = {}
        self._observadores: list[Observador] = []
    def suscribir(self, observador: Observador):
        if observador not in self._observadores: self._observadores.append(observador)
    def desuscribir(self, observador: Observador):
        if observador in self._observadores: self._observadores.remove(observador)
    @property
    def items(self): return tuple(self._items.values())
    def notificar(self, evento, producto, cantidad):
        for obs in tuple(self._observadores): obs.actualizar(evento, producto, cantidad)
    def agregar(self, producto: Producto, cantidad: int = 1):
        if cantidad <= 0: raise ValueError('Cantidad inválida')
        # Prevalidar stock antes de emitir el evento.
        for obs in self._observadores:
            if isinstance(obs, ModuloStock): obs.validar(producto, cantidad)
        actual = self._items.get(producto.codigo, (producto,0))[1]
        self._items[producto.codigo] = (producto, actual+cantidad)
        self.notificar('agregado', producto, cantidad)
    def eliminar(self, codigo: str, cantidad: int = 1):
        if cantidad <= 0: raise ValueError('Cantidad inválida')
        if codigo not in self._items or self._items[codigo][1] < cantidad:
            raise ValueError('Cantidad no disponible en el carrito')
        producto, actual = self._items[codigo]
        if actual == cantidad: del self._items[codigo]
        else: self._items[codigo] = (producto, actual-cantidad)
        self.notificar('eliminado', producto, cantidad)
    def subtotal(self):
        return D(sum((p.precio_base*q for p,q in self.items), Decimal('0')))

# DECORATOR: se envuelven componentes sin modificar Producto.
class ComponentePrecio(ABC):
    @abstractmethod
    def calcular_precio(self) -> Decimal: ...

class PrecioBase(ComponentePrecio):
    def __init__(self, producto: Producto, cantidad: int):
        self.producto, self.cantidad = producto, cantidad
    def calcular_precio(self): return D(self.producto.precio_base * self.cantidad)

class PrecioSubtotal(ComponentePrecio):
    def __init__(self, monto: Decimal): self.monto = D(monto)
    def calcular_precio(self): return self.monto

class DecoradorPrecio(ComponentePrecio, ABC):
    def __init__(self, componente: ComponentePrecio): self._componente = componente

class DescuentoDecorator(DecoradorPrecio):
    def __init__(self, componente, porcentaje):
        super().__init__(componente)
        self.porcentaje = Decimal(str(porcentaje))
        if not 0 <= self.porcentaje <= 100: raise ValueError('Descuento inválido')
    def calcular_precio(self):
        return D(self._componente.calcular_precio()*(1-self.porcentaje/100))

class ImpuestoDecorator(DecoradorPrecio):
    def __init__(self, componente, porcentaje):
        super().__init__(componente)
        self.porcentaje = Decimal(str(porcentaje))
        if self.porcentaje < 0: raise ValueError('Impuesto inválido')
    def calcular_precio(self):
        return D(self._componente.calcular_precio()*(1+self.porcentaje/100))

class EnvioDecorator(DecoradorPrecio):
    def __init__(self, componente, costo):
        super().__init__(componente)
        self.costo = D(costo)
        if self.costo < 0: raise ValueError('Envío inválido')
    def calcular_precio(self): return D(self._componente.calcular_precio()+self.costo)

@dataclass(frozen=True)
class Cliente:
    nombre: str
    identificacion: str
    direccion: str
    ciudad: str
    correo: str

@dataclass(frozen=True)
class LineaFactura:
    codigo: str
    descripcion: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal
    descuento: Decimal
    impuesto: Decimal
    total: Decimal

@dataclass(frozen=True)
class DatosFactura:
    numero: str
    fecha: str
    cliente: Cliente
    lineas: tuple[LineaFactura,...]
    subtotal: Decimal
    descuento: Decimal
    base_imponible: Decimal
    impuesto: Decimal
    envio: Decimal
    total: Decimal

# FACTORY METHOD: las subclases deciden qué factura instanciar.
class Factura(ABC):
    titulo = ''
    leyenda = ''
    @abstractmethod
    def tipo(self) -> str: ...
    def html(self, datos: DatosFactura) -> str:
        h = escape
        filas = ''.join(
            f'<tr><td>{h(l.codigo)}</td><td>{h(l.descripcion)}</td><td>{l.cantidad}</td>'
            f'<td>{usd(l.precio_unitario)}</td><td>{usd(l.subtotal)}</td>'
            f'<td>{usd(l.descuento)}</td><td>{usd(l.impuesto)}</td><td><b>{usd(l.total)}</b></td></tr>'
            for l in datos.lineas)
        resumen = [('Subtotal',datos.subtotal),('Descuento',-datos.descuento),
                   ('Base luego de descuento',datos.base_imponible),('Impuesto de simulación',datos.impuesto),
                   ('Envío',datos.envio),('TOTAL USD',datos.total)]
        totales = ''.join(f'<tr><td>{h(k)}</td><td>{usd(v)}</td></tr>' for k,v in resumen)
        return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><title>{h(self.titulo)}</title>
<style>body{{font:14px Arial,sans-serif;color:#1e293b;background:#eef2f7;padding:30px}}main{{max-width:980px;margin:auto;background:white;padding:36px;box-shadow:0 8px 30px #cbd5e1}}header{{display:flex;justify-content:space-between;border-bottom:4px solid #0d9488;padding-bottom:20px}}h1{{color:#0f172a;margin:0}}.muted{{color:#64748b}}.stamp{{color:#b91c1c;border:2px solid #b91c1c;padding:8px;font-weight:bold;text-align:center;margin:20px 0}}table{{border-collapse:collapse;width:100%;margin:22px 0}}th{{background:#15344b;color:white}}th,td{{padding:9px;border-bottom:1px solid #cbd5e1;text-align:left}}.summary{{width:390px;margin-left:auto}}.summary tr:last-child{{background:#ccfbf1;font-size:17px;font-weight:bold}}footer{{border-top:1px solid #cbd5e1;margin-top:28px;padding-top:14px;font-size:12px;color:#64748b}}@media print{{body{{background:white;padding:0}}main{{box-shadow:none;padding:12px}}}}</style></head><body><main>
<header><div><h1>NOVAMARKET ECUADOR</h1><p>Tienda de tecnología, moda y accesorios</p><p class="muted">Guayaquil, Ecuador · contacto@novamarket.example<br>Identificación tributaria: DEMO-NO-VALIDA</p></div><div><h2>{h(self.titulo)}</h2><p><b>N.º:</b> {h(datos.numero)}<br><b>Fecha:</b> {h(datos.fecha)}<br><b>Moneda:</b> USD</p></div></header>
<div class="stamp">DOCUMENTO ACADÉMICO · SIN VALIDEZ TRIBUTARIA · NO AUTORIZADO POR EL SRI</div>
<h3>Datos del cliente</h3><p><b>{h(datos.cliente.nombre)}</b><br>Identificación de referencia: {h(datos.cliente.identificacion)}<br>{h(datos.cliente.direccion)}, {h(datos.cliente.ciudad)}<br>{h(datos.cliente.correo)}</p>
<p><b>Modalidad:</b> {h(self.tipo())} · {h(self.leyenda)}</p>
<table><thead><tr><th>Código</th><th>Descripción</th><th>Cant.</th><th>P. unit.</th><th>Subtotal</th><th>Desc.</th><th>Imp.</th><th>Total</th></tr></thead><tbody>{filas}</tbody></table>
<table class="summary">{totales}</table>
<footer>Proyecto NovaMarket Ecuador · Grupo 8 · Responsables: Briggitte Castro Pacheco y Aleyska Cabrera Bravo. Las tasas, identificaciones y numeraciones son ilustrativas; no constituye comprobante fiscal ni demuestra cumplimiento de requisitos del SRI.</footer></main></body></html>'''

class FacturaNacional(Factura):
    titulo = 'FACTURA NACIONAL · ECUADOR'
    leyenda = 'Venta nacional'
    def tipo(self): return 'Nacional'
class FacturaExportacion(Factura):
    titulo = 'FACTURA DE EXPORTACIÓN'
    leyenda = 'Venta internacional · modelo académico sin gestión aduanera'
    def tipo(self): return 'Exportación'
class FacturaSimplificada(Factura):
    titulo = 'FACTURA SIMPLIFICADA'
    leyenda = 'Formato académico resumido; no equivale a comprobante autorizado'
    def tipo(self): return 'Simplificada'

class CreadorFactura(ABC):
    @abstractmethod
    def crear_factura(self) -> Factura: ...
    def emitir(self, datos: DatosFactura, destino: Path) -> Path:
        factura = self.crear_factura()
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(factura.html(datos), encoding='utf-8')
        return destino
class CreadorNacional(CreadorFactura):
    def crear_factura(self): return FacturaNacional()
class CreadorExportacion(CreadorFactura):
    def crear_factura(self): return FacturaExportacion()
class CreadorSimplificada(CreadorFactura):
    def crear_factura(self): return FacturaSimplificada()

class Pedido:
    def __init__(self, carrito: CarritoCompras, cliente: Cliente, creador: CreadorFactura,
                 descuento: Decimal | int = 0, impuesto: Decimal | int = 0,
                 envio: Decimal | int = 0):
        self.carrito, self.cliente, self.creador = carrito, cliente, creador
        self.descuento = Decimal(str(descuento))
        self.impuesto = Decimal(str(impuesto))
        self.envio = D(envio)
        if not 0 <= self.descuento <= 100 or self.impuesto < 0 or self.envio < 0:
            raise ValueError('Parámetros de precio inválidos')
    def preparar_factura(self, numero='DEMO-0001', fecha='23/11/2026') -> DatosFactura:
        if not self.carrito.items: raise ValueError('Carrito vacío')
        lineas = []
        for producto, cantidad in self.carrito.items:
            base = PrecioBase(producto, cantidad)
            desc = DescuentoDecorator(base, self.descuento)
            imp = ImpuestoDecorator(desc, self.impuesto)
            subtotal = base.calcular_precio()
            despues_desc = desc.calcular_precio()
            total = imp.calcular_precio()
            lineas.append(LineaFactura(producto.codigo, producto.nombre, cantidad,
                producto.precio_base, subtotal, D(subtotal-despues_desc),
                D(total-despues_desc), total))
        sub = D(sum((x.subtotal for x in lineas),Decimal('0')))
        descuento = D(sum((x.descuento for x in lineas),Decimal('0')))
        impuesto = D(sum((x.impuesto for x in lineas),Decimal('0')))
        base = D(sub-descuento)
        total_items = D(sum((x.total for x in lineas),Decimal('0')))
        total = EnvioDecorator(PrecioSubtotal(total_items),self.envio).calcular_precio()
        return DatosFactura(numero, fecha, self.cliente, tuple(lineas), sub,
                            descuento, base, impuesto, self.envio, total)
    def finalizar(self, destino: Path, numero='DEMO-0001', fecha='23/11/2026'):
        return self.creador.emitir(self.preparar_factura(numero,fecha),destino)

PRODUCTOS_DEMO = [
    Producto('TEC-001','Audífonos inalámbricos','Tecnología','45.00'),
    Producto('TEC-002','Teclado mecánico','Tecnología','68.50'),
    Producto('MOD-001','Camiseta algodón premium','Moda','24.00'),
    Producto('MOD-002','Mochila urbana','Moda','39.90'),
    Producto('ACC-001','Termo de acero 750 ml','Accesorios','18.75'),
    Producto('ACC-002','Soporte para laptop','Accesorios','27.30'),
]
CLIENTE_DEMO = Cliente('Valeria Torres','ID-DEMO-4582',
    'Av. Comercial 123','Guayaquil, Ecuador','valeria@example.com')

def crear_tienda():
    catalogo = Catalogo(PRODUCTOS_DEMO)
    stock = ModuloStock({'TEC-001':8,'TEC-002':5,'MOD-001':12,'MOD-002':7,'ACC-001':10,'ACC-002':9})
    recomendaciones = SistemaRecomendaciones()
    carrito = CarritoCompras()
    carrito.suscribir(stock)
    carrito.suscribir(recomendaciones)
    return catalogo, carrito, stock, recomendaciones

def demo(destino: Path = Path('facturas')):
    catalogo, carrito, stock, recomendaciones = crear_tienda()
    carrito.agregar(catalogo.buscar('TEC-001'),2)
    carrito.agregar(catalogo.buscar('MOD-001'),1)
    carrito.agregar(catalogo.buscar('ACC-001'),1)
    carrito.eliminar('ACC-001',1)
    print('=== NOVAMARKET ECUADOR | DEMOSTRACIÓN GRUPO 8 ===')
    print('CATÁLOGO:')
    for p in catalogo.listar(): print(f'  {p.codigo} | {p.nombre} | {usd(p.precio_base)} | stock {stock.existencias[p.codigo]}')
    print('\nCARRITO Y OBSERVER:')
    for p,q in carrito.items: print(f'  {q} × {p.nombre} = {usd(p.precio_base*q)}')
    print('  Stock:',stock.historial)
    print('  Recomendaciones:',recomendaciones.historial)
    print('\nDECORATOR + FACTORY METHOD:')
    for tipo,creador in [('nacional',CreadorNacional()),('exportacion',CreadorExportacion()),('simplificada',CreadorSimplificada())]:
        pedido = Pedido(carrito, CLIENTE_DEMO, creador, descuento=10, impuesto=15, envio=5)
        datos = pedido.preparar_factura('DEMO-G8-2026-001')
        archivo = pedido.finalizar(destino/f'factura_{tipo}.html','DEMO-G8-2026-001')
        print(f'  {tipo}: subtotal {usd(datos.subtotal)}, descuento {usd(datos.descuento)}, impuesto {usd(datos.impuesto)}, envío {usd(datos.envio)}, TOTAL {usd(datos.total)} -> {archivo}')
    print('\nDocumentos académicos SIN VALIDEZ TRIBUTARIA. Abrir archivos HTML en navegador para imprimir.')

def menu():
    catalogo, carrito, stock, rec = crear_tienda()
    creadores = {'1':('nacional',CreadorNacional()),'2':('exportacion',CreadorExportacion()),'3':('simplificada',CreadorSimplificada())}
    while True:
        print('\n=== NOVAMARKET ECUADOR ===\n1 Catálogo | 2 Agregar | 3 Eliminar | 4 Carrito | 5 Facturar | 6 Notificaciones | 0 Salir')
        op = input('Opción: ').strip()
        try:
            if op == '0': break
            if op == '1':
                for p in catalogo.listar(): print(p.codigo,p.nombre,p.categoria,usd(p.precio_base),'stock',stock.existencias[p.codigo])
            elif op == '2': carrito.agregar(catalogo.buscar(input('Código: ').strip().upper()),int(input('Cantidad: ')))
            elif op == '3': carrito.eliminar(input('Código: ').strip().upper(),int(input('Cantidad: ')))
            elif op == '4':
                for p,q in carrito.items: print(p.nombre,'x',q,'=',usd(p.precio_base*q))
                print('Subtotal:',usd(carrito.subtotal()))
            elif op == '5':
                tipo = input('Factura 1 Nacional, 2 Exportación, 3 Simplificada: ').strip()
                nombre,creador = creadores[tipo]
                desc = input('Descuento % (ej. 10): ')
                tasa = input('Impuesto % de simulación (ej. 15): ')
                envio = input('Costo envío USD (ej. 5): ')
                pedido = Pedido(carrito, CLIENTE_DEMO, creador,desc,tasa,envio)
                ruta = pedido.finalizar(Path('facturas')/f'factura_{nombre}_interactiva.html')
                print('TOTAL:',usd(pedido.preparar_factura().total),'| Archivo:',ruta)
            elif op == '6': print('Stock:',stock.historial,'\nRecomendaciones:',rec.historial)
            else: print('Opción desconocida')
        except (ValueError,KeyError) as e: print('Error:',e)

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--menu',action='store_true',help='Abrir menú interactivo')
    ap.add_argument('--salida',default='facturas',help='Carpeta de facturas para la demo')
    args = ap.parse_args()
    if args.menu: menu()
    else: demo(Path(args.salida))
