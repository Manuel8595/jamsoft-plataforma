"""
Verifica o que esta sincronizado no Supabase.
Uso: python verificar_supabase.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from services.supabase_client import _get
TABELAS = [
    "farmacias", "vendas", "itens_venda", "produtos", "perdas",
    "compras", "clientes", "facturas", "devolucoes", "turnos_caixa",
    "dias_operação", "lotes", "metas_farmacia", "depositos",
    "saldo_farmacia", "utilizadores", "categorias", "fornecedores",
    "plataforma_utilizadores", "plataforma_convites",
]
print("=" * 60)
print("VERIFICACAO DO SUPABASE")
print("=" * 60)
print()
existem = []
nao_existem = []
for t in TABELAS:
    try:
        r = _get(t, {"select": "id", "limit": "1"})
        if r is not None:
            # tentar contar
            r2 = _get(t, {"select": "id"})
            n = len(r2) if r2 else 0
            print(f"OK  {t}: {n} registos")
            existem.append((t, n))
        else:
            print(f"--  {t}: vazio ou nao existe")
            nao_existem.append(t)
    except Exception as e:
        print(f"XX  {t}: erro - {e}")
        nao_existem.append(t)
print()
print("=" * 60)
print(f"RESUMO: {len(existem)} tabelas com dados / {len(nao_existem)} em falta")
print("=" * 60)
