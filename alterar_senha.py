"""
Altera a senha de um utilizador.
Uso: python alterar_senha.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import requests
from services.auth import gerar_hash, obter_utilizador_por_email
from services.supabase_client import SUPABASE_URL, SUPABASE_KEY
from config_cloud import CLOUD_ACCESS_ENABLED

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def main():
    if not CLOUD_ACCESS_ENABLED:
        print("A plataforma online está temporariamente desligada por segurança.")
        return
    email = input("Email: ").strip().lower()
    user = obter_utilizador_por_email(email)
    if not user:
        print(f"X Utilizador '{email}' nao encontrado.")
        return
    
    print(f"OK Utilizador encontrado: {user['nome']}")
    
    senha = input("Nova senha: ").strip()
    confirma = input("Confirma: ").strip()
    if senha != confirma:
        print("X Senhas nao coincidem.")
        return
    
    novo_hash = gerar_hash(senha)
    url = f"{SUPABASE_URL}/rest/v1/plataforma_utilizadores?id=eq.{user['id']}"
    r = requests.patch(url, headers=HEADERS, json={"senha_hash": novo_hash})
    
    if r.status_code in (200, 204):
        print(f"OK Senha actualizada para {email}")
        print()
        print("Agora podes fazer login na plataforma com esta senha.")
    else:
        print(f"X Erro: {r.status_code} - {r.text}")


if __name__ == "__main__":
    main()
