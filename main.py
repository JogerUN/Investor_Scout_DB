"""
Investor Scout — ETL: Yahoo Finance -> MySQL

Script de EJECUCIÓN DIRECTA. 

Uso:
    python main.py                  # usa los tickers de config/tickers.txt
    python main.py AAPL MSFT NVDA   # usa estos tickers en vez del archivo
"""
import logging
import os
import sys
import time
import getpass
from app.services.auth_service import AuthService
from app.repositories.cliente_repository import ClienteRepository
from app.services.logger_service import sesion
from menu import mostrar_menu

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

from scripts.init_db import initialize_database
from app.services.yahoo_provider import YahooFinanceProvider
from app.services.sync_service import SyncService
from app.data_structures.stock_cache import StockCache

TICKERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "tickers.txt")


def load_tickers_from_file(path: str):
    if not os.path.exists(path):
        return []
    tickers = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            tickers.append(line.upper())
    return tickers


def get_tickers():
    # Si se pasan tickers como argumentos de línea de comandos, tienen prioridad.
    if len(sys.argv) > 1:
        return [t.strip().upper() for t in sys.argv[1:] if t.strip()]
    return load_tickers_from_file(TICKERS_FILE)


def run():
    while True:
        print(f"")
        print(f"")
        print(f"")
        print(f"==============================================")
        print(f"                INVESTOR SCOUT                ")
        print(f"==============================================")
        print(f"")
        print(f"1. Registrate si no tienes una cuenta todavia")
        print(f"")
        print(f"2. Inicia sesion si ya tienes una cuenta")
        print(f"")
        print(f"3. Salir")
        print(f"==============================================")
        print(f"")

        opcion = input(f"Escribe tu accion: ")

        while opcion not in ["1", "2", "3"]:
            print(f"")
            opcion = input(f"Por favor, escribe una opcion disponible: ")

        if opcion == "3":
            print("¡Hasta pronto!")
            sys.exit(0)
            
        if opcion == "1":
            print(f"")
            print(f"==============================================")
            print(f"           REGISTRO EN INVESTOR SCOUT         ")
            print(f"==============================================")
            print(f"")
            print(f"Estamos felices de que nos hayas elegido")
            print(f"")
            
            nombre = input(f"Por favor, digita tu nombre: ").strip()
            while not nombre:
                nombre = input("Nombre invalido, intenta nuevamente: ").strip()

            apellido = input(f"Digita tu apellido: ").strip()
            while not apellido:
                apellido = input("Apellido invalido, intenta nuevamente: ").strip()

            email = input("Digita tu dirección de correo: ").strip().lower()
            while "@" not in email or "." not in email.split("@")[-1]:
                email = input("Correo inválido, intenta nuevamente: ").strip().lower()

            telefono = input(f"Digita tu numero de telefono: ").strip()
            telefono = telefono if telefono else None
            
            print(f"")
            contrasena = getpass.getpass(prompt=f"Digita tu contraseña: ")
            while not contrasena:
                contrasena = input(f"Contraseña invalida, intenta nuevamente: ")
                
            confirmacion = getpass.getpass(prompt=f"Confirma tu contraseña: ")
            while not confirmacion:
                confirmacion = input(f"Contraseña invalida, intenta nuevamente: ")
                
            while contrasena != confirmacion:
                print(f"Las contraseñas no coinciden.")
                print(f"")
                contrasena = getpass.getpass(prompt=f"Digita tu contraseña: ")
                confirmacion = getpass.getpass(prompt=f"Confirma tu contraseña: ")

            auth_service = AuthService() 
            resultado = auth_service.registrar(nombre=nombre, apellido=apellido, email=email, telefono=telefono, contrasena=contrasena)

            if resultado.exito:
                print(f"\nRegistro exitoso. Bienvenido " + nombre)
            else:
                print(f"\nError al registrar: {resultado.mensaje}")

        if opcion == "2":
            print(f"")
            print(f"==============================================")
            print(f"       INICIO DE SESION EN INVESTOR SCOUT     ")
            print(f"==============================================")
            print(f"")
            print(f"Estamos felices de tenerte devuelta")
            print(f"")
            
            email = input("Digita tu dirección de correo: ").strip().lower()
            while "@" not in email or "." not in email.split("@")[-1]:
                email = input("Por favor, digita una direccion de correo valida: ").strip().lower()
                
            print(f"")
            contrasena = getpass.getpass(prompt=f"Digita tu contraseña: ")
            while not contrasena:
                contrasena = getpass.getpass(prompt=f"Por favor, digita una contraseña: ")

            auth_service = AuthService()
            resultado = auth_service.iniciar_sesion(email=email, contrasena=contrasena)

            if resultado.exito:
                # resultado.cliente contiene todos los datos del usuario que acaba de entrar
                sesion.iniciar(resultado.cliente)
                print(f"\nInicio de sesion correcto. Bienvenido de vuelta, {resultado.cliente.nombre}!")

                mostrar_menu(resultado.cliente)

            else:
                print(f"\nError: {resultado.mensaje}")


if __name__ == "__main__":
    run()