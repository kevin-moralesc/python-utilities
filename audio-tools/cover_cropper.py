import os
import io
import shutil
import logging
from datetime import datetime

import music_tag
from PIL import Image, UnidentifiedImageError

# ============================================================
# CONFIGURACIÓN - AJUSTA ESTOS VALORES ANTES DE EJECUTAR
# ============================================================

RUTA_CARPETA = r"C:\ruta\a\tu\musica"
CARPETA_BACKUP = r"C:\ruta\a\tu\backup"

DRY_RUN = True           # <-- Se recomienda dejarlo en True para pruebas iniciales
HACER_BACKUP = True     
CALIDAD_JPEG = 95

FORMATOS_VALIDOS = ('.mp3', '.m4a', '.opus', '.flac', '.ogg')
# .wav se excluye por defecto: el soporte de portadas en WAV es muy inconsistente
# entre mutagen/music_tag y distintos reproductores. Si lo necesitas, agrégalo
# bajo tu propio riesgo y revisa los resultados manualmente después.

# ============================================================
# LOGGING (consola + archivo, para poder revisar los 4000 resultados después)
# ============================================================

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"reporte_portadas_{timestamp}.txt"

logger = logging.getLogger("portadas")
logger.setLevel(logging.INFO)
logger.handlers.clear()

_fh = logging.FileHandler(log_filename, encoding="utf-8")
_ch = logging.StreamHandler()
_formatter = logging.Formatter("%(message)s")
_fh.setFormatter(_formatter)
_ch.setFormatter(_formatter)
logger.addHandler(_fh)
logger.addHandler(_ch)


# ============================================================
# FUNCIÓN PRINCIPAL DE PROCESAMIENTO
# ============================================================

def recortar_portada_universal(ruta_archivo, ruta_raiz):
    """
    Procesa un solo archivo. Nunca deja escapar una excepción: siempre
    devuelve un estado para que el bucle principal pueda seguir con
    los demás archivos pase lo que pase.

    Devuelve: 'ok' | 'omitido_sin_portada' | 'omitido_ya_1_1' | 'error'
    """
    try:
        if not os.access(ruta_archivo, os.R_OK):
            logger.warning("  -> ERROR: sin permiso de lectura.")
            return 'error'

        audio = music_tag.load_file(ruta_archivo)
        artwork = audio['artwork']

        if not artwork or not artwork.values:
            logger.info("  -> Omitido: no tiene portada.")
            return 'omitido_sin_portada'

        datos_imagen = artwork.first.data

        try:
            imagen = Image.open(io.BytesIO(datos_imagen))
            imagen.load()  # fuerza decodificación completa: detecta imágenes corruptas aquí
        except UnidentifiedImageError:
            logger.warning("  -> ERROR: la portada incrustada está corrupta o no es una imagen válida.")
            return 'error'

        ancho, alto = imagen.size

        if ancho == alto:
            logger.info(f"  -> Omitido: ya es 1:1 ({ancho}x{alto}).")
            return 'omitido_ya_1_1'

        nuevo_tamano = min(ancho, alto)

        # --- Modo DRY-RUN: solo reportar, no tocar nada ---
        if DRY_RUN:
            logger.info(f"  -> [DRY-RUN] Se recortaría de {ancho}x{alto} a {nuevo_tamano}x{nuevo_tamano}.")
            return 'ok'

        # --- Backup del archivo original (solo si de verdad se va a modificar) ---
        if HACER_BACKUP:
            ruta_relativa = os.path.relpath(ruta_archivo, ruta_raiz)
            destino_backup = os.path.join(CARPETA_BACKUP, ruta_relativa)
            os.makedirs(os.path.dirname(destino_backup), exist_ok=True)
            if not os.path.exists(destino_backup):
                shutil.copy2(ruta_archivo, destino_backup)

        # --- Recorte 1:1 centrado ---
        izq = int((ancho - nuevo_tamano) / 2)
        arr = int((alto - nuevo_tamano) / 2)
        der = izq + nuevo_tamano
        aba = arr + nuevo_tamano

        imagen_recortada = imagen.crop((izq, arr, der, aba))

        if imagen_recortada.mode != "RGB":
            imagen_recortada = imagen_recortada.convert("RGB")

        buffer = io.BytesIO()
        imagen_recortada.save(buffer, format="JPEG", quality=CALIDAD_JPEG)

        audio['artwork'] = buffer.getvalue()
        audio.save()

        logger.info(f"  -> ÉXITO: portada recortada a {nuevo_tamano}x{nuevo_tamano}.")
        return 'ok'

    except PermissionError:
        logger.warning("  -> ERROR: archivo protegido contra escritura (PermissionError).")
        return 'error'
    except (OSError, IOError) as e:
        logger.warning(f"  -> ERROR de E/S: {e}")
        return 'error'
    except Exception as e:
        logger.warning(f"  -> ERROR inesperado ({type(e).__name__}): {e}")
        return 'error'


# ============================================================
# ESCANEO RECURSIVO Y EJECUCIÓN
# ============================================================

def main():
    if not os.path.isdir(RUTA_CARPETA):
        logger.error(f"La carpeta no existe: {RUTA_CARPETA}")
        return

    modo = "(DRY-RUN, sin modificar nada) " if DRY_RUN else ""
    logger.info(f"Iniciando escaneo {modo}en: {RUTA_CARPETA}")
    logger.info(f"Log completo se guardará en: {log_filename}\n")

    contadores = {'ok': 0, 'omitido_sin_portada': 0, 'omitido_ya_1_1': 0, 'error': 0}
    archivos_con_error = []
    total_archivos = 0

    carpeta_backup_normalizada = os.path.normpath(CARPETA_BACKUP)

    for carpeta_actual, subcarpetas, archivos in os.walk(RUTA_CARPETA):
        # Evita entrar a la propia carpeta de backup si quedó dentro de la carpeta de música
        try:
            if HACER_BACKUP and os.path.commonpath(
                [os.path.normpath(carpeta_actual), carpeta_backup_normalizada]
            ) == carpeta_backup_normalizada:
                subcarpetas[:] = []
                continue
        except ValueError:
            pass  # rutas en discos distintos en Windows, no hay conflicto posible

        for nombre_archivo in archivos:
            if nombre_archivo.lower().endswith(FORMATOS_VALIDOS):
                total_archivos += 1
                ruta_completa = os.path.join(carpeta_actual, nombre_archivo)
                ruta_mostrar = os.path.relpath(ruta_completa, RUTA_CARPETA)
                logger.info(f"[{total_archivos}] Analizando: {ruta_mostrar}")

                resultado = recortar_portada_universal(ruta_completa, RUTA_CARPETA)
                contadores[resultado] += 1
                if resultado == 'error':
                    archivos_con_error.append(ruta_mostrar)

    logger.info("\n" + "=" * 50)
    logger.info("RESUMEN FINAL")
    logger.info("=" * 50)
    logger.info(f"Total de archivos analizados: {total_archivos}")
    logger.info(f"  Recortados/OK:             {contadores['ok']}")
    logger.info(f"  Ya eran 1:1:               {contadores['omitido_ya_1_1']}")
    logger.info(f"  Sin portada:               {contadores['omitido_sin_portada']}")
    logger.info(f"  Errores:                   {contadores['error']}")

    if archivos_con_error:
        logger.info("\nArchivos con error (revísalos manualmente):")
        for a in archivos_con_error:
            logger.info(f"  - {a}")

    if DRY_RUN:
        logger.info("\n*** Esto fue un DRY-RUN. Ningún archivo fue modificado. ***")
        logger.info("*** Cambia DRY_RUN = False cuando estés conforme con el resultado. ***")


if __name__ == "__main__":
    main()