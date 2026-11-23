# NovaMarket Ecuador — Grupo 8 — Escenario 02

Prototipo académico funcional de **Plataforma de Gestión de Catálogo y Pedidos** (UNEMI, Modelamiento de Software, CP2). Proyecto desarrollado por **Briggitte Castro Pacheco y Aleyska Cabrera Bravo**. Implementa **Decorator, Factory Method y Observer** en Python 3.10+ (sin dependencias externas).

## Ejecución

En la carpeta del proyecto:

```bash
python novamarket.py
python novamarket.py --menu
python -m unittest -v
```

- Sin argumentos ejecuta la demostración y crea tres facturas HTML en `facturas/`.
- Con `--menu` permite consultar catálogo, agregar o eliminar productos, ver carrito, emitir facturas y consultar eventos.
- Abra `facturas/factura_nacional.html`, `factura_exportacion.html` o `factura_simplificada.html` en su navegador. Puede imprimirlas o guardarlas como PDF desde el navegador.
- `uml/novamarket_uml.png` es el diagrama integrado; `uml/novamarket.dot` es editable con Graphviz.

## Datos de la demostración

Empresa: NovaMarket Ecuador, Guayaquil. Cliente de ejemplo: Valeria Torres. Catálogo de seis productos con precio base inmutable. Se añaden dos audífonos de $45 y una camiseta de $24; se agrega y retira un termo para demostrar Observer. Subtotal $114, descuento ilustrativo 10% ($11.40), impuesto de simulación 15% ($15.39), envío $5, total $122.99.

La tasa del 15% es **un parámetro elegido para demostrar Decorator**, no una afirmación sobre el tratamiento tributario de cada operación. En particular, la factura de exportación NO implementa reglas aduaneras o tributarias reales.

## Patrones y SOLID

- **Decorator (estructural)**: `ComponentePrecio`, `PrecioBase`, `PrecioSubtotal`, `DecoradorPrecio`, `DescuentoDecorator`, `ImpuestoDecorator`, `EnvioDecorator`. **OCP**: extensiones mediante envoltorios sin modificar `Producto`.
- **Factory Method (creacional)**: `CreadorFactura` y sus tres subclases, `Factura` y sus tres subclases. **OCP / DIP**: `Pedido` recibe un creador abstracto; agregar otra factura implica nuevas subclases.
- **Observer (comportamiento)**: `CarritoCompras`, `Observador`, `ModuloStock`, `SistemaRecomendaciones`. **DIP**: el carrito notifica a la interfaz común, no a implementaciones específicas.

## Límites del prototipo

Las facturas **NO tienen validez tributaria**, ni RUC real, autorización SRI, firma electrónica o clave de acceso. Los números y datos de identificación son de referencia para la actividad académica. Las tres variantes usan el mismo cálculo ilustrativo para que el patrón Factory Method se pueda comparar; una implementación tributaria real requeriría reglas específicas por operación. No hay base de datos, pagos reales, autenticación ni servidor web. Las notificaciones Observer son síncronas y una excepción de un observador no tiene reversión transaccional completa. No se afirma que el sistema sea apto para producción.

## Rúbrica y entrega

Entregar diagrama UML, código funcional y presentación de **máximo 10 diapositivas**. Justificar para cada patrón el problema recurrente, intención, contexto, participantes y relación SOLID. Todos los integrantes deben exponer; el docente indica grupos de 4 a 5, por lo que conviene confirmar autorización para exponer siendo dos.
