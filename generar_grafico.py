import os
import time
import matplotlib.pyplot as plt
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Asignar las URLs desde las variables de entorno
URL_TCP = os.getenv("URL_TCP")
URL_QUIC = os.getenv("URL_QUIC")

# Validar que las variables existan para evitar errores de ejecución
if not URL_TCP or not URL_QUIC:
    raise ValueError("Error: Asegúrate de definir URL_TCP y URL_QUIC en tu archivo .env")

PRUEBAS_TOTALES = 10 # Define cuántas pruebas de carga seguidas quieres hacer

def test_load_time(context, url, protocolo):
    page = context.new_page()
    start_time = time.time()
    try:
        # wait_until="networkidle" asegura que espere hasta que todas las imágenes terminen de cargar
        page.goto(url, wait_until="networkidle", timeout=60000)
    except Exception as e:
        print(f"  [!] Error o timeout en {protocolo}: {e}")
    end_time = time.time()
    page.close()
    return end_time - start_time

def ejecutar_experimento():
    print(f"Iniciando {PRUEBAS_TOTALES} pruebas de carga automatizadas...")
    
    # Configurar el gráfico interactivo
    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.canvas.manager.set_window_title('Test en Tiempo Real: QUIC vs TCP')
    
    intentos = []
    tiempos_tcp = []
    tiempos_quic = []

    line_tcp, = ax.plot([], [], 'r-o', linewidth=2, label='TCP (Vercel - HTTP/2)')
    line_quic, = ax.plot([], [], 'b-o', linewidth=2, label='QUIC (Cloudflare - HTTP/3)')
    
    ax.set_xlim(1, PRUEBAS_TOTALES)
    ax.set_ylim(0, 2)
    ax.set_xlabel('Número de Prueba')
    ax.set_ylabel('Tiempo Total de Carga (Segundos)')
    ax.set_title('Impacto del Head-of-Line Blocking en Redes Inestables')
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend()

    # Iniciar el navegador de pruebas
    with sync_playwright() as p:
        # Lanzamos Chromium obligándolo a aceptar conexiones QUIC
        browser = p.chromium.launch(headless=True, args=['--enable-quic'])
        
        for i in range(1, PRUEBAS_TOTALES + 1):
            print(f"\n--- Ejecutando Prueba {i}/{PRUEBAS_TOTALES} ---")
            intentos.append(i)
            
            # Creamos un contexto nuevo en cada iteración para asegurar que no haya caché (Disable Cache)
            context = browser.new_context()
            
            # 1. Probar TCP
            t_tcp = test_load_time(context, URL_TCP, "TCP")
            tiempos_tcp.append(t_tcp)
            print(f"  TCP  cargó en: {t_tcp:.2f} segundos")
            
            # 2. Probar QUIC
            t_quic = test_load_time(context, URL_QUIC, "QUIC")
            tiempos_quic.append(t_quic)
            print(f"  QUIC cargó en: {t_quic:.2f} segundos")
            
            context.close()

            # Actualizar el gráfico en tiempo real
            line_tcp.set_data(intentos, tiempos_tcp)
            line_quic.set_data(intentos, tiempos_quic)
            
            # Ajustar el eje Y dinámicamente si los tiempos son muy altos
            max_time = max(max(tiempos_tcp), max(tiempos_quic))
            if max_time > ax.get_ylim()[1]:
                ax.set_ylim(0, max_time + 1)
            
            plt.pause(0.1) # Dibuja los nuevos puntos y pausa brevemente

        browser.close()

    print("\nExperimento finalizado. Cierra la ventana del gráfico para salir.")
    plt.ioff()
    plt.show()

if __name__ == "__main__":
    ejecutar_experimento()