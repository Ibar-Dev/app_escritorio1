"""
GUÍA DE PRUEBA - Sistema de Manejo Robusto de Errores en Hilos
===============================================================

Este archivo documenta cómo verificar que el sistema de manejo de errores
en hilos (ejecutar_en_hilo_seguro) funciona correctamente en la aplicación.

REQUISITOS PREVIOS
------------------
✓ Todos los imports de `ejecutar_en_hilo_seguro` están en lugar correcto
✓ El archivo `ui/thread_utils.py` existe y contiene la función wrapper
✓ La aplicación puede iniciarse sin errores de sintaxis

PRUEBAS AUTOMÁTICAS
-------------------

1. PRUEBA DE ERROR VISUAL (Recomendado)
   ────────────────────────────────────
   
   Pasos:
   1. Ejecuta: uv run main.py
   2. Espera a que cargue la interfaz
   3. Navega a la pestaña "Facturas"
   4. Busca el botón "🧪 PRUEBA: Lanzar Error" (parte inferior derecha)
   5. Haz clic en el botón
   
   Resultado esperado:
   ✓ Un SnackBar ROJO debe aparecer en la parte inferior de la pantalla
   ✓ El mensaje dice: "Error en la operación: Esta es una prueba intencionada..."
   ✓ El botón "Aceptar" en el SnackBar es clickeable
   ✓ La interfaz NO se congela
   ✓ Puedes continuar interactuando con la aplicación
   
   En la CONSOLA debe aparecer:
   ✓ "Error crítico en el hilo: _prueba_error"
   ✓ Un traceback completo mostrando la excepción


2. PRUEBA DE OPERACIONES REALES
   ────────────────────────────
   
   Ahora puedes probar que las operaciones reales también funcionan:
   
   a) GENERAR FACTURA (Prueba _guardar)
      - Llena algunos datos de factura
      - Haz clic en "GENERAR FACTURA"
      - Si algo falla, aparecerá el SnackBar rojo
      - La interfaz no se congela
   
   b) EMAIL DE PRUEBA (Prueba _enviar)
      - Ve a la pestaña "Configuración"
      - Haz clic en "PROBAR CONEXIÓN"
      - Si hay error de conectividad, verás el SnackBar rojo
   
   c) EXPORTAR VENTAS (Prueba _exportar)
      - Ve a la pestaña "Ventas"
      - Haz clic en "EXPORTAR MES" o "EXPORTAR HISTORIAL"
      - Si hay error, aparecerá el SnackBar rojo


VERIFICACIÓN DE CÓDIGO
---------------------

1. Confirmación de Imports
   grep "from ui.thread_utils import" ui/*.py
   # Debe mostrar 3 resultados (email_view.py, facturas_view.py, ventas_view.py)

2. Confirmación de Reemplazos
   grep "ejecutar_en_hilo_seguro" ui/*.py | wc -l
   # Debe mostrar >= 8 líneas

3. Verificar que NO hay más threading.Thread en las vistas
   grep "threading.Thread.*target.*daemon" ui/*.py
   # Debe estar VACÍO

4. Verificación de thread_utils.py
   ls -la ui/thread_utils.py
   # Debe existir


CHECKLIST DE VALIDACIÓN
-----------------------

□ thread_utils.py existe en ui/
□ Función ejecutar_en_hilo_seguro existe y tiene docstring
□ Email_view, FacturasView, VentasView importan ejecutar_en_hilo_seguro
□ Botón "🧪 PRUEBA: Lanzar Error" aparece en la vista de Facturas
□ Al hacer clic en el botón, aparece el SnackBar rojo
□ El mensaje de error es legible
□ La interfaz NO se congela
□ Se puede hacer clic en "Aceptar" para cerrar el SnackBar
□ El traceback completo aparece en la consola
□ Las operaciones reales siguen funcionando (facturas, emails, reportes)


TROUBLESHOOTING
---------------

P: No veo el botón de prueba
R: Verifica que estés en la pestaña "Facturas" y que la aplicación se inició correctamente

P: El SnackBar no aparece
R: Revisa la consola para ver si hay errores de importación en thread_utils.py

P: La interfaz se congela al hacer clic
R: Significa que la función NO está usando el wrapper. Verifica que la llamada 
   sea: ejecutar_en_hilo_seguro(self.page, _prueba_error)

P: No veo traceback en consola
R: Verifica que los logs están configurados correctamente en src/settings.py


NOTAS TÉCNICAS
--------------

- El wrapper usa threading.Thread con daemon=True (igual que antes)
- La función objetivo se ejecuta en un hilo separado
- Los errores se capturan sin que el hilo muera silenciosamente
- La actualización de la UI (SnackBar) ocurre en el hilo principal de Flet
- page.update() fuerza la redibujación inmediata


RESULTADO ESPERADO FINAL
------------------------

Después de estas pruebas, tu aplicación tendrá:

✓ Interfaz siempre responsiva incluso si hay errores en hilos
✓ Usuarios informados de qué salió mal mediante SnackBar rojo
✓ Posibilidad de reintentar operaciones sin reiniciar la app
✓ Logs completos en consola para debugging
✓ Arquitectura mantenible y escalable
✓ Código en producción listo

¡Confirmame cuando hayas completado las pruebas!
"""
