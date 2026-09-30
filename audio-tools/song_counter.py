from pathlib import Path

def contar_canciones(directorio):
    """
    Cuenta archivos de audio en un directorio considerando formatos comunes de audio y video.
    """
    extensiones_audio = {
        '.mp3', '.mp4', '.m4a', '.flac', '.wav', 
        '.aac', '.ogg', '.opus', '.wma', '.alac', '.mkv'
    }
    
    ruta = Path(directorio)
    
    if not ruta.exists() or not ruta.is_dir():
        print(f"Error: La ruta '{directorio}' no existe o no es accesible.")
        return 0

    total_canciones = 0

    for elemento in ruta.rglob('*'):
        if elemento.is_file():
            ext = elemento.suffix.lower()
            # Excluir explícitamente archivos de letras (.lrc)
            if ext != '.lrc' and ext in extensiones_audio:
                total_canciones += 1

    return total_canciones

if __name__ == "__main__":
    directorio_usuario = input("Ingresa la ruta de la carpeta de música: ").strip('"')
    cantidad = contar_canciones(directorio_usuario)
    
    if cantidad > 0:
        print(f"\nTotal de archivos de audio encontrados: {cantidad}")