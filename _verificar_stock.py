from database import conectar

conn = conectar()
cur = conn.cursor()

cur.execute("""
    SELECT 
        p.id, 
        p.nome, 
        p.estoque_atual, 
        COALESCE(SUM(l.quantidade), 0) AS total_lotes
    FROM produtos p 
    LEFT JOIN lotes l ON l.produto_id = p.id 
    GROUP BY p.id, p.nome, p.estoque_atual
    ORDER BY p.id
""")

print("=" * 80)
print(f"{'ID':<5} {'Produto':<40} {'Estoque':<10} {'Lotes':<10} {'Estado'}")
print("=" * 80)

problemas = 0
for r in cur.fetchall():
    pid, nome, estoque, lotes = r
    estado = "OK" if estoque == lotes else "DIVERGENTE"
    if estado == "DIVERGENTE":
        problemas += 1
    print(f"{pid:<5} {nome[:40]:<40} {estoque:<10} {lotes:<10} {estado}")

print("=" * 80)
print(f"Total: {problemas} produto(s) com divergencia")

conn.close()