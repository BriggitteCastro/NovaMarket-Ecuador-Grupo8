import unittest
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from novamarket import *

class PruebasNovaMarket(unittest.TestCase):
    def setUp(self):
        self.catalogo,self.carrito,self.stock,self.rec = crear_tienda()
        self.p = self.catalogo.buscar('TEC-001')
    def test_catalogo_seis_productos(self): self.assertEqual(len(self.catalogo.listar()),6)
    def test_producto_inmutable(self):
        with self.assertRaises(Exception): self.p.precio_base = D(1)
    def test_decorator_precio_y_original(self):
        d = EnvioDecorator(ImpuestoDecorator(DescuentoDecorator(PrecioBase(self.p,2),10),15),5)
        self.assertEqual(d.calcular_precio(),D('98.15'))
        self.assertEqual(self.p.precio_base,D('45'))
    def test_decorator_valida_porcentajes(self):
        with self.assertRaises(ValueError): DescuentoDecorator(PrecioBase(self.p,1),101)
        with self.assertRaises(ValueError): ImpuestoDecorator(PrecioBase(self.p,1),-1)
    def test_stock_y_observer_agregar(self):
        self.carrito.agregar(self.p,2)
        self.assertEqual(self.stock.existencias[self.p.codigo],6)
        self.assertEqual(len(self.rec.historial),1)
    def test_observer_eliminar(self):
        self.carrito.agregar(self.p,2);self.carrito.eliminar(self.p.codigo,1)
        self.assertEqual(self.stock.existencias[self.p.codigo],7)
        self.assertEqual(len(self.rec.historial),2)
    def test_stock_insuficiente_no_muta_carrito(self):
        with self.assertRaises(ValueError): self.carrito.agregar(self.p,100)
        self.assertFalse(self.carrito.items)
    def test_desuscribir(self):
        self.carrito.desuscribir(self.rec);self.carrito.agregar(self.p)
        self.assertEqual(self.rec.historial,[])
    def test_pedido_total_integrado(self):
        self.carrito.agregar(self.p,2)
        self.carrito.agregar(self.catalogo.buscar('MOD-001'))
        d = Pedido(self.carrito,CLIENTE_DEMO,CreadorNacional(),10,15,5).preparar_factura()
        self.assertEqual((d.subtotal,d.descuento,d.impuesto,d.envio,d.total),(D(114),D('11.40'),D('15.39'),D(5),D('122.99')))
    def test_factory_tres_facturas(self):
        self.carrito.agregar(self.p)
        with TemporaryDirectory() as tmp:
            for creador,rotulo in [(CreadorNacional(),'NACIONAL'),(CreadorExportacion(),'EXPORTACIÓN'),(CreadorSimplificada(),'SIMPLIFICADA')]:
                ruta=Pedido(self.carrito,CLIENTE_DEMO,creador,10,15,5).finalizar(Path(tmp)/f'{rotulo}.html')
                contenido=ruta.read_text(encoding='utf-8')
                self.assertIn(rotulo,contenido)
                self.assertIn('SIN VALIDEZ TRIBUTARIA',contenido)
                self.assertIn('Audífonos inalámbricos',contenido)
    def test_factura_vacia(self):
        with self.assertRaises(ValueError): Pedido(self.carrito,CLIENTE_DEMO,CreadorNacional()).preparar_factura()
    def test_envio_una_vez(self):
        self.carrito.agregar(self.p,2)
        self.carrito.agregar(self.catalogo.buscar('MOD-001'))
        d = Pedido(self.carrito,CLIENTE_DEMO,CreadorNacional(),0,0,5).preparar_factura()
        self.assertEqual(d.total,D(119))
    def test_factura_suma_lineas(self):
        self.carrito.agregar(self.p,2)
        d=Pedido(self.carrito,CLIENTE_DEMO,CreadorNacional(),10,15,5).preparar_factura()
        self.assertEqual(D(sum((x.total for x in d.lineas),Decimal(0))+d.envio),d.total)
    def test_cantidades_invalidas(self):
        with self.assertRaises(ValueError): self.carrito.agregar(self.p,0)
        with self.assertRaises(ValueError): self.carrito.eliminar(self.p.codigo,1)
    def test_errores_parametros_pedido(self):
        for params in ({'descuento':101},{'impuesto':-2},{'envio':-5}):
            with self.assertRaises(ValueError): Pedido(self.carrito,CLIENTE_DEMO,CreadorNacional(),**params)

if __name__ == '__main__': unittest.main()
