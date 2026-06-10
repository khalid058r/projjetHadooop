"""
Génère un dataset e-commerce synthétique (~2 Go).
Format CSV : order_id, customer_id, product_id, category,
             seller_region, customer_region, price, freight_value,
             review_score, order_date
"""
import random
import os
from datetime import datetime, timedelta

CATEGORIES = [
    'electronique', 'vetements', 'livres', 'sport', 'maison_jardin',
    'beaute', 'jouets', 'alimentation', 'automobile', 'sante'
]

REGIONS = [
    'Ile-de-France', 'Occitanie', 'Auvergne-Rhone-Alpes',
    'Nouvelle-Aquitaine', 'Hauts-de-France', 'Provence-Alpes-Cote-dAzur',
    'Grand-Est', 'Normandie', 'Pays-de-la-Loire', 'Bretagne'
]

PRICE_RANGES = {
    'electronique':   (50,   2000),
    'vetements':      (15,   300),
    'livres':         (8,    80),
    'sport':          (20,   500),
    'maison_jardin':  (10,   800),
    'beaute':         (5,    150),
    'jouets':         (10,   200),
    'alimentation':   (3,    100),
    'automobile':     (30,   1500),
    'sante':          (5,    200),
}

RATING_WEIGHTS = [5, 8, 15, 35, 37]   # distribution réaliste (surtout 4-5 étoiles)

TARGET_ROWS  = 20_000_000
BATCH_SIZE   = 200_000
OUTPUT_FILE  = 'ecommerce_data.csv'

# Précalcul des dates disponibles (2020-01 à 2023-12)
BASE_DATE = datetime(2020, 1, 1)
DATES = [
    (BASE_DATE + timedelta(days=i)).strftime('%Y-%m')
    for i in range(0, 365 * 4)
]

print(f"Génération de {TARGET_ROWS:,} lignes → {OUTPUT_FILE}")
print("(cela peut prendre quelques minutes)")

with open(OUTPUT_FILE, 'w', encoding='utf-8', buffering=4 * 1024 * 1024) as f:
    f.write("order_id,customer_id,product_id,category,"
            "seller_region,customer_region,price,freight_value,"
            "review_score,order_date\n")

    written = 0
    while written < TARGET_ROWS:
        batch = min(BATCH_SIZE, TARGET_ROWS - written)
        lines = []
        for j in range(batch):
            idx  = written + j
            cat  = random.choice(CATEGORIES)
            pmin, pmax = PRICE_RANGES[cat]
            price   = round(random.uniform(pmin, pmax), 2)
            freight = round(price * random.uniform(0.05, 0.20), 2)
            score   = random.choices([1, 2, 3, 4, 5], weights=RATING_WEIGHTS)[0]
            date    = random.choice(DATES)
            lines.append(
                f"ORD{idx:09d},"
                f"CUST{random.randint(1, 500_000):06d},"
                f"PROD{random.randint(1, 10_000):05d},"
                f"{cat},"
                f"{random.choice(REGIONS)},"
                f"{random.choice(REGIONS)},"
                f"{price:.2f},{freight:.2f},{score},{date}\n"
            )
        f.write(''.join(lines))
        written += batch

        if written % 2_000_000 == 0 or written == TARGET_ROWS:
            pct  = written / TARGET_ROWS * 100
            size = os.path.getsize(OUTPUT_FILE) / (1024 ** 3)
            print(f"  {written:>12,} / {TARGET_ROWS:,}  ({pct:5.1f}%)  —  {size:.2f} Go",
                  flush=True)

size_gb = os.path.getsize(OUTPUT_FILE) / (1024 ** 3)
print(f"\nDataset prêt : {OUTPUT_FILE}  ({size_gb:.2f} Go)")
