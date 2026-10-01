# Page_response_time_graph

Creado para comprobar la diferencia entre TCP y QUIC en sitios web.
Dependencias a instalar:
pip install python-dotenv
pip install playwright matplotlib
playwright install chrome (si no esta instalado)

.env:
URL_TCP=https://tusitio1.com
URL_QUIC=https://tusitio2.com
PRUEBAS_TOTALES=15