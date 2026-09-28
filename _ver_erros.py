from database import conectar


def main():
    conn = conectar()
    cur = conn.cursor()
    print("=" * 70)
    print("ERROS NA FILA")
    print("=" * 70)
    sql = "SELECT id, tipo, tabela_origem, registo_id, estado, tentativas, ultimo_erro FROM fila_sincronizacao WHERE estado = 'ERRO' LIMIT 10"
    cur.execute(sql)
    rows = cur.fetchall()
    print(f"Total de erros: {len(rows)}")
    print()
    for r in rows:
        print(f"ID={r[0]} | tipo={r[1]} | tabela={r[2]} | registo_id={r[3]}")
        print(f"  estado={r[4]} | tentativas={r[5]}")
        print(f"  ERRO: {r[6]}")
        print()
    conn.close()


if __name__ == "__main__":
    main()