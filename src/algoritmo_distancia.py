from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable

def calcular_distancia(endereco_origem, endereco_destino):
    geolocator = Nominatim(user_agent="localizador")
    try:
        coordenadas_origem = geolocator.geocode(endereco_origem)
        coordenadas_destino = geolocator.geocode(endereco_destino)
        distancia = geodesic(
                (coordenadas_origem.latitude, coordenadas_origem.longitude), 
                (coordenadas_destino.latitude, coordenadas_destino.longitude)
            ).kilometers

        return round(distancia + 1, 2)
    
    except AttributeError, GeocoderUnavailable:
        return None
    

def ordenar_distancias(empresa_compradora, produtos:list):
    produto_distancia = {}

    endereco_origem = str(empresa_compradora.localizacao)
    for p in produtos:
        endereco_destino = str(p.empresa.localizacao)
        distancia = calcular_distancia(endereco_origem, endereco_destino)
        produto_distancia[p] = distancia

    dict_ordernado = dict(sorted(produto_distancia.items(), key=lambda item: (item[1] is None, item[1])))

    return dict_ordernado

