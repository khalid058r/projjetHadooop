"""
Dashboard de visualisation — Analyse E-commerce Hadoop MapReduce
Génère : ecommerce_dashboard.png
"""
import os
import sys
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

RESULTS = {
    'revenue_category': 'results/revenue_category/part-r-00000',
    'orders_region':    'results/orders_region/part-r-00000',
    'ratings':          'results/ratings/part-r-00000',
    'monthly_trend':    'results/monthly_trend/part-r-00000',
}

for name, path in RESULTS.items():
    if not os.path.exists(path):
        print(f"Fichier manquant : {path}")
        print("Lancez d'abord : bash run_ecommerce.sh")
        sys.exit(1)


def read_tab(path, key_type=str, val_type=float):
    data = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if '\t' in line:
                k, v = line.split('\t', 1)
                try:
                    data[key_type(k.strip())] = val_type(v.strip())
                except ValueError:
                    pass
    return data


revenue = read_tab(RESULTS['revenue_category'])
orders  = read_tab(RESULTS['orders_region'],   val_type=int)
ratings = read_tab(RESULTS['ratings'],         key_type=int, val_type=int)
monthly = read_tab(RESULTS['monthly_trend'])

# ── Statistiques globales ──────────────────────────────────────────
total_ca      = sum(revenue.values())
total_orders  = sum(orders.values())
total_ratings = sum(ratings.values())
avg_score     = sum(k * v for k, v in ratings.items()) / total_ratings
best_cat      = max(revenue, key=revenue.get)
best_region   = max(orders,  key=orders.get)

print("=" * 52)
print(f"  Chiffre d'affaires total : {total_ca:>16,.2f} €")
print(f"  Commandes totales        : {total_orders:>16,}")
print(f"  Note moyenne             : {avg_score:>16.2f} / 5")
print(f"  Meilleure catégorie      : {best_cat}")
print(f"  Région la plus active    : {best_region}")
print("=" * 52)

# ── Graphiques ────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(18, 12))
fig.suptitle(
    "Dashboard E-commerce — Cluster Hadoop MapReduce\n"
    f"({total_orders:,} commandes  •  CA total : {total_ca/1e6:.1f} M€)",
    fontsize=14, fontweight='bold', y=0.98
)

# 1. CA par catégorie
ax1 = axes[0, 0]
rev_sorted = sorted(revenue.items(), key=lambda x: x[1], reverse=True)
cats  = [k for k, _ in rev_sorted]
revs  = [v / 1e6 for _, v in rev_sorted]
bars1 = ax1.barh(cats[::-1], revs[::-1], color='steelblue', edgecolor='white')
ax1.set_title("Chiffre d'affaires par catégorie", fontsize=12, fontweight='bold')
ax1.set_xlabel("CA (millions €)")
for bar, val in zip(bars1, revs[::-1]):
    ax1.text(bar.get_width() + max(revs) * 0.01,
             bar.get_y() + bar.get_height() / 2,
             f"{val:.1f}M€", va='center', fontsize=8)
ax1.set_xlim(0, max(revs) * 1.18)
ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}M"))

# 2. Commandes par région
ax2 = axes[0, 1]
ord_sorted = sorted(orders.items(), key=lambda x: x[1], reverse=True)
regions = [k for k, _ in ord_sorted]
counts  = [v for _, v in ord_sorted]
bars2   = ax2.barh(regions[::-1], counts[::-1], color='coral', edgecolor='white')
ax2.set_title("Commandes par région client", fontsize=12, fontweight='bold')
ax2.set_xlabel("Nombre de commandes")
for bar, val in zip(bars2, counts[::-1]):
    ax2.text(bar.get_width() + max(counts) * 0.01,
             bar.get_y() + bar.get_height() / 2,
             f"{val:,}", va='center', fontsize=8)
ax2.set_xlim(0, max(counts) * 1.15)
ax2.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

# 3. Distribution des notes
ax3 = axes[1, 0]
score_labels  = [f"★ {s}" for s in sorted(ratings)]
score_values  = [ratings[s] for s in sorted(ratings)]
colors_rating = ['#d32f2f', '#f57c00', '#fbc02d', '#7cb342', '#2e7d32']
bars3 = ax3.bar(score_labels, score_values, color=colors_rating, edgecolor='white', width=0.6)
ax3.set_title("Distribution des avis clients", fontsize=12, fontweight='bold')
ax3.set_ylabel("Nombre d'avis")
for bar, val in zip(bars3, score_values):
    pct = val / total_ratings * 100
    ax3.text(bar.get_x() + bar.get_width() / 2,
             bar.get_height() + total_ratings * 0.003,
             f"{pct:.1f}%", ha='center', fontsize=9, fontweight='bold')
ax3.set_ylim(0, max(score_values) * 1.12)
ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax3.text(0.98, 0.96, f"Note moy. : {avg_score:.2f}/5",
         transform=ax3.transAxes, ha='right', va='top',
         fontsize=10, color='#2e7d32', fontweight='bold')

# 4. Tendance mensuelle
ax4 = axes[1, 1]
months_sorted = sorted(monthly.items())
months = [m for m, _ in months_sorted]
sales  = [v / 1e6 for _, v in months_sorted]
ax4.fill_between(range(len(months)), sales, alpha=0.15, color='green')
ax4.plot(range(len(months)), sales, 'o-', color='green', linewidth=2, markersize=3)
ax4.set_title("Tendance mensuelle du CA", fontsize=12, fontweight='bold')
ax4.set_ylabel("CA (millions €)")
step = max(1, len(months) // 12)
ax4.set_xticks(range(0, len(months), step))
ax4.set_xticklabels([months[i] for i in range(0, len(months), step)],
                    rotation=45, ha='right', fontsize=8)
ax4.grid(axis='y', linestyle='--', alpha=0.4)
ax4.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}M"))

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig("ecommerce_dashboard.png", dpi=150, bbox_inches='tight')
print("\nDashboard enregistré : ecommerce_dashboard.png")
