"""Servidor web NovaMarket Ecuador. Ejecutar: python web_app.py"""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
from threading import RLock
from datetime import datetime
import json
from decimal import Decimal
from novamarket import (crear_tienda, Pedido, Cliente, CreadorNacional, CreadorExportacion,
                        CreadorSimplificada, D)
import os


ROOT=Path(__file__).resolve().parent
CATALOGO,CARRITO,STOCK,RECOMENDACIONES=crear_tienda()
LOCK=RLock()
FACTURAS={'nacional':CreadorNacional,'exportacion':CreadorExportacion,'simplificada':CreadorSimplificada}


def estado():
    return {'productos':[{'codigo':p.codigo,'nombre':p.nombre,'categoria':p.categoria,
             'precio':str(p.precio_base),'stock':STOCK.existencias[p.codigo]} for p in CATALOGO.listar()],
            'carrito':[{'codigo':p.codigo,'nombre':p.nombre,'precio':str(p.precio_base),'cantidad':q,
                       'total':str(D(p.precio_base*q))} for p,q in CARRITO.items],
            'subtotal':str(CARRITO.subtotal()),
            'eventos_stock':STOCK.historial[-12:], 'eventos_recomendaciones':RECOMENDACIONES.historial[-12:]}

class Handler(BaseHTTPRequestHandler):
    def log_message(self,fmt,*args): pass
    def enviar(self, data, status=200, tipo='application/json; charset=utf-8'):
        body=json.dumps(data,ensure_ascii=False).encode() if isinstance(data,(dict,list)) else data.encode()
        self.send_response(status);self.send_header('Content-Type',tipo);self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/':return self.enviar((ROOT/'web'/'index.html').read_text(encoding='utf-8'),tipo='text/html; charset=utf-8')
        if path=='/api/estado':
            with LOCK:return self.enviar(estado())
        self.enviar({'error':'Ruta inexistente'},404)
    def do_POST(self):
        path=urlparse(self.path).path
        if path not in ('/api/agregar','/api/eliminar','/api/facturar'):
            return self.enviar({'error':'Ruta inexistente'},404)
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<1 or n>16000:raise ValueError('Solicitud vacía o demasiado grande')
            data=json.loads(self.rfile.read(n))
            with LOCK:
                if path in ('/api/agregar','/api/eliminar'):
                    codigo=str(data['codigo']).upper()
                    cantidad=data['cantidad']
                    if type(cantidad) is not int or not 1<=cantidad<=100:raise ValueError('Cantidad inválida')
                    if path=='/api/agregar': CARRITO.agregar(CATALOGO.buscar(codigo),cantidad)
                    else: CARRITO.eliminar(codigo,cantidad)
                    return self.enviar(estado())
                tipo=str(data.get('tipo',''))
                if tipo not in FACTURAS:raise ValueError('Tipo de factura inválido')
                cliente_data=data.get('cliente',{})
                campos=['nombre','identificacion','direccion','ciudad','correo']
                if any(not isinstance(cliente_data.get(k),str) or not cliente_data[k].strip() or len(cliente_data[k])>120 for k in campos):
                    raise ValueError('Completa los datos del cliente')
                cliente=Cliente(*(cliente_data[k].strip() for k in campos))
                descuento=Decimal(str(data.get('descuento',0)))
                impuesto=Decimal(str(data.get('impuesto',0)))
                envio=Decimal(str(data.get('envio',0)))
                if not all(x.is_finite() for x in (descuento,impuesto,envio)):raise ValueError('Importes inválidos')
                pedido=Pedido(CARRITO,cliente,FACTURAS[tipo](),descuento,impuesto,envio)
                numero='NM-G8-'+datetime.now().strftime('%Y%m%d-%H%M%S')
                datos=pedido.preparar_factura(numero,datetime.now().strftime('%d/%m/%Y %H:%M'))
                html=FACTURAS[tipo]().crear_factura().html(datos)
                return self.enviar({'html':html,'total':str(datos.total),'numero':numero})
        except (ValueError,KeyError,TypeError,ArithmeticError,OverflowError,json.JSONDecodeError) as e:
            self.enviar({'error':str(e)},400)

if __name__=='__main__':
    print('NovaMarket Ecuador | http://localhost:8000')
    print('Presiona Ctrl+C para detener el servidor.')
    ThreadingHTTPServer(
    ('0.0.0.0', int(os.environ.get('PORT', '8000'))),
    Handler
).serve_forever()
