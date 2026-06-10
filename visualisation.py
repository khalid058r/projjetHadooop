import os
import matplotlib.pyplot as plt

result_file = "output/part-r-00000"

if not os.path.exists(result_file):
    print(f"Fichier introuvable : {result_file}")
    print("Assurez-vous d'avoir exécuté : docker cp namenode:/tmp/output ./output")
    exit(1)

data = []
with open(result_file, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if "\t" in line:
            w, c = line.rsplit("\t", 1)
            try:
                data.append((w, int(c)))
            except ValueError:
                pass

data.sort(key=lambda x: x[1], reverse=True)

total_occurrences = sum(c for _, c in data)
mots_distincts = len(data)

print("=" * 45)
print(f"  Mots distincts      : {mots_distincts:>12,}")
print(f"  Occurrences totales : {total_occurrences:>12,}")
print("=" * 45)
print("\nTop 20 mots les plus fréquents :")
for i, (w, c) in enumerate(data[:20], 1):
    print(f"  {i:2}. {w:<20} {c:>10,}")

top = data[:20]
mots = [w for w, _ in top]
counts = [c for _, c in top]

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh(mots[::-1], counts[::-1], color="steelblue", edgecolor="white")

for bar, val in zip(bars, counts[::-1]):
    ax.text(bar.get_width() + max(counts) * 0.005, bar.get_y() + bar.get_height() / 2,
            f"{val:,}", va="center", fontsize=9)

ax.set_title("Top 20 des mots les plus fréquents\n(Corpus Gutenberg — MapReduce Hadoop)",
             fontsize=13, fontweight="bold")
ax.set_xlabel("Nombre d'occurrences", fontsize=11)
ax.set_ylabel("Mot", fontsize=11)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
plt.tight_layout()
plt.savefig("top_words.png", dpi=150)
print("\nGraphique enregistré : top_words.png")
