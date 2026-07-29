"""
Reinicio COMPLETO de la base de datos (DROP DATABASE + recreación desde cero).

"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.init_db import reset_database

if __name__ == "__main__":
    print("¡ATENCIÓN! Esto borrará TODA la base de datos InvestorScout y la recreará vacía.")
    confirm = input("Escribe 'CONFIRMAR' para continuar: ").strip()
    if confirm == "CONFIRMAR":
        reset_database()
    else:
        print("Operación cancelada.")
