"""
Teste de login (debug).
Uso: python teste_login.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.auth import autenticar

email = input("Email: ").strip().lower()
senha = input("Senha: ").strip()

print()
print("A autenticar...")

try:
    ok, dados = autenticar(email, senha)
    print(f"OK: {ok}")
    print(f"Dados: {dados}")
except Exception as e:
    import traceback
    traceback.print_exc()