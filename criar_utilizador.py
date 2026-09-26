"""
Cria um utilizador (CEO) com senha.
Uso: python criar_utilizador.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.auth import registar_utilizador, obter_utilizador_por_email


def main():
    print("=" * 60)
    print("  CRIAR UTILIZADOR (CEO)")
    print("=" * 60)
    print()
    
    email = input("Email: ").strip().lower()
    if not email:
        print("Cancelado.")
        return
    
    if obter_utilizador_por_email(email):
        print(f"X Ja existe utilizador com email '{email}'.")
        return
    
    nome = input("Nome completo: ").strip()
    if not nome:
        print("Cancelado.")
        return
    
    senha = input("Senha (min 6 caracteres): ").strip()
    if len(senha) < 6:
        print("X Senha muito curta.")
        return
    
    confirma = input("Confirma senha: ").strip()
    if senha != confirma:
        print("X Senhas nao coincidem.")
        return
    
    if registar_utilizador(email, senha, nome):
        print()
        print(f"OK Utilizador '{nome}' criado com sucesso!")
        print(f"   Email: {email}")
    else:
        print("X Erro ao criar utilizador.")


if __name__ == "__main__":
    main()