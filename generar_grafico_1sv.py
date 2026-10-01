import os
import time
import matplotlib.pyplot as plt
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Cargar variables
load_dotenv()
URL_OBJETIVO = os.getenv("URL_QUIC")
PRUEBAS_TOTALES = int(os.getenv("PRUEBAS_TOTALES", 10))

if not URL_OBJETIVO:
    raise ValueError("Error: Define URL_QUIC en tu archivo .env")

def test_load_time(browser, url, protocolo):
    # Crear un contexto limpio (sin caché)
    context = browser.new_context()
    page = context.new_page()
    start_time = time.time()
    try:
        # "load" detiene el reloj en cuanto la interfaz principal está lista
        page.goto(url, wait_until="load", timeout=60000)
    except Exception as e:
        print(f"  [!] Error en {protocolo}: {e}")
    end_time = time.time()
    context.close()
    return end_time - start_time

def ejecutar_experimento():
    print(f"Iniciando {PRUEBAS_TOTALES} pruebas sobre el mismo servidor ({URL_OBJETIVO})...")
    
    # Configurar el gráfico
    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.canvas.manager.set_window_title('QUIC vs TCP (En un mismo Servidor)')
    
    intentos, tiempos_tcp, tiempos_quic = [], [], []

    line_tcp, = ax.plot([], [], 'r-o', linewidth=2, label='TCP (HTTP/2)')
    line_quic, = ax.plot([], [], 'b-o', linewidth=2, label='QUIC (HTTP/3)')
    
    ax.set_xlim(1, PRUEBAS_TOTALES)
    ax.set_ylim(0, 2)
    ax.set_xlabel('n')
    ax.set_ylabel('Tiempo de Carga (s)')
    ax.set_title('Comparación TCP VS QUIC')
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend()

    with sync_playwright() as p:
        # Inicializamos DOS navegadores usando tu Chrome local
        # Navegador 1: TCP puro (Bloquea QUIC explícitamente)
        browser_tcp = p.chromium.launch(channel="chrome", headless=True, args=['--disable-quic'])
        # Navegador 2: QUIC activo
        browser_quic = p.chromium.launch(channel="chrome", headless=True, args=['--enable-quic'])
        
        for i in range(1, PRUEBAS_TOTALES + 1):
            print(f"\n--- Ejecutando Prueba {i}/{PRUEBAS_TOTALES} ---")
            intentos.append(i)
            
            # Ejecutar prueba en H2
            t_tcp = test_load_time(browser_tcp, URL_OBJETIVO, "TCP")
            tiempos_tcp.append(t_tcp)
            print(f"  TCP (h2) cargó en: {t_tcp:.2f} s")
            
            # Ejecutar prueba en H3
            t_quic = test_load_time(browser_quic, URL_OBJETIVO, "QUIC")
            tiempos_quic.append(t_quic)
            print(f"  QUIC (h3) cargó en: {t_quic:.2f} s")
            
            # Actualizar gráfico
            line_tcp.set_data(intentos, tiempos_tcp)
            line_quic.set_data(intentos, tiempos_quic)
            
            max_time = max(max(tiempos_tcp), max(tiempos_quic))
            if max_time > ax.get_ylim()[1]:
                ax.set_ylim(0, max_time + 0.5)
            
            plt.pause(0.1)

        # Limpieza
        browser_tcp.close()
        browser_quic.close()

    print("\nExperimento finalizado. Cierra la ventana del gráfico para salir.")
    plt.ioff()
    plt.show()

if __name__ == "__main__":
    ejecutar_experimento()