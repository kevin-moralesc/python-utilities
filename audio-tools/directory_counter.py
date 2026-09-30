from pathlib import Path

def analizar_directorio(directorio):
    """
    Cuenta el número total de archivos de música y la cantidad de carpetas 
    presentes en un directorio de manera recursiva.
    """
    extensiones_audio = {'.mp3', '.flac', '.wav', '.m4a', '.aac', '.ogg', '.wma', '.opus'}
    ruta = Path(directorio)
    
    if not ruta.exists() or not ruta.is_dir():
        print(f"Error: La ruta '{directorio}' no corresponde a un directorio válido.")
        return 0, 0
    
    total_canciones = 0
    total_carpetas = 0
    
    for elemento in ruta.rglob('*'):
        if elemento.is_dir():
            total_carpetas += 1
        elif elemento.is_file():
            if elemento.suffix.lower() in extensiones_audio:
                total_canciones += 1
                
    return total_canciones, total_carpetas

if __name__ == "__main__":
    directorio_usuario = input("Ingresa la ruta del directorio a analizar: ").strip('"')
    canciones, carpetas = analizar_directorio(directorio_usuario)
    
    if canciones or carpetas:
        print(f"\nResumen para '{directorio_usuario}':")
        print(f" - Cantidad de carpetas: {carpetas}")
        print(f" - Número total de canciones: {canciones}")