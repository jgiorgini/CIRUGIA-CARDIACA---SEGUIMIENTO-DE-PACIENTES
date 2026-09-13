RCV-V1.0-LOCAL-004

PROTOTIPO LOCAL PARA PRUEBAS. NO USAR CON DATOS REALES DE PACIENTES EN PRODUCCION.

Inicio en Windows:
1. Descomprimir toda la carpeta.
2. Tener Python 3 instalado.
3. Doble clic en start_rcv.bat.
4. Se abre http://127.0.0.1:8767 en el navegador.
5. La consola muestra también la URL para celular/tablet si están en la misma red Wi-Fi.

Persistencia:
- Los datos se guardan en data\rcv.db (SQLite) en esta computadora.
- El sistema hace autoguardado.
- Desde la aplicación se puede exportar/importar un backup JSON.
- RESET_TEST_DATA.bat elimina todos los datos de prueba.

Esta versión inicia SIN pacientes ni casos precargados.

Cambios principales LOCAL-004:
- Corrección del motor de formularios PREOP: cambiar un campo numérico ya no redibuja la pantalla durante el clic siguiente.
- Verificación de persistencia/autoguardado prevista para todos los controles.
- Apellido y nombre en campos separados.
- DNI como identificador principal obligatorio.
- HC opcional, editable posteriormente desde PREOP.
- Mantiene todos los cambios clínicos y de drogas de LOCAL-003-HF1.
- Puerto exclusivo 8767 y caché HTTP desactivada durante desarrollo.
