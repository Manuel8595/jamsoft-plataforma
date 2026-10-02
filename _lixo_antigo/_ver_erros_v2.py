with open('pages_secundarias.py', encoding='utf-8') as f:
    linhas = f.readlines()

print("=" * 70)
print(f"FICHEIRO TEM {len(linhas)} LINHAS")
print("=" * 70)
print()

print("LINHAS 1035 a 1045:")
print("-" * 70)
for i in range(1034, min(1045, len(linhas))):
    print(f"{i+1:5}: {repr(linhas[i])}")

print()
print("LINHAS 1155 a 1170:")
print("-" * 70)
for i in range(1154, min(1170, len(linhas))):
    print(f"{i+1:5}: {repr(linhas[i])}")