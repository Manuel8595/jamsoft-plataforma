"""
Ver o estado da fila de sincronizacao.
Uso: python _ver_fila.py
"""

from database import conectar


def main():
    conn = conectar()
    cur = conn.cursor()
    
    # 1. Fila por estado
    print("=" * 50)
    print("FILA POR ESTADO")
    print("=" * 50)
    cur.execute("SELECT COUNT(*), estado FROM fila_sincronizacao GROUP BY estado")
    for estado, count in cur.fetchall():
        print(f"  {estado}: {count}")
    
    # 2. Total
    cur.execute("SELECT COUNT(*) FROM fila_sincronizacao")
    print(f"\nTotal: {cur.fetchone()[0]} registos")
    
    # 3. Exemplos ITEN_VENDA
    print()
    print("=" * 50)
    print("EXEMPLOS ITEN_VENDA (5)")
    print("=" * 50)
    cur.execute("""
        SELECT id, uuid, tipo, estado, tentativas
        FROM fila_sincronizacao
        WHERE tipo = 'ITEN_VENDA'
        LIMIT 5
    """)
    for r in cur.fetchall():
        uuid_curto = r[1][:15] + "..." if r[1] else "(sem uuid)"
        print(f"  id={r[0]} uuid={uuid_curto} tipo={r[2]} estado={r[3]} tent={r[4]}")
    
    # 4. Exemplos PRODUTO
    print()
    print("=" * 50)
    print("EXEMPLOS PRODUTO (5)")
    print("=" * 50)
    cur.execute("""
        SELECT id, uuid, tipo, estado, tentativas
        FROM fila_sincronizacao
        WHERE tipo = 'PRODUTO'
        LIMIT 5
    """)
    for r in cur.fetchall():
        uuid_curto = r[1][:15] + "..." if r[1] else "(sem uuid)"
        print(f"  id={r[0]} uuid={uuid_curto} tipo={r[2]} estado={r[3]} tent={r[4]}")
    
    conn.close()


if __name__ == "__main__":
    main()