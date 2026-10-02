import uuid
import os
from database import conectar

conn = conectar()
cur = conn.cursor()
terminal = os.environ.get("COMPUTERNAME", "TERM-01")

# Corrigir itens_venda
print("A processar itens_venda...")
cur.execute("SELECT id FROM itens_venda WHERE uuid IS NULL")
ids = [r[0] for r in cur.fetchall()]

for rid in ids:
    u = str(uuid.uuid4())
    cur.execute("""
        UPDATE itens_venda 
        SET uuid = ?, terminal_id = ?, sincronizado = 0
        WHERE id = ?
    """, (u, terminal, rid))

print(f"itens_venda: {len(ids)} registos actualizados")

conn.commit()
conn.close()
print("OK")