#!/usr/bin/env bash
set -e

echo "======================================================"
echo "  Mini-projet Hadoop — Analyse E-commerce"
echo "======================================================"

INPUT_HDFS="/user/root/ecommerce/input"
OUTPUT_HDFS="/user/root/ecommerce/output"

# ---------- 1. Générer le dataset ----------
if [ ! -f ecommerce_data.csv ]; then
    echo ""
    echo "[1/6] Génération du dataset (~2 Go, quelques minutes)..."
    python3 generate_dataset.py
else
    echo ""
    echo "[1/6] Dataset existant : $(du -sh ecommerce_data.csv | cut -f1)"
fi

# ---------- 2. Copier dans le namenode ----------
echo ""
echo "[2/6] Copie vers le conteneur namenode..."
docker cp ecommerce_data.csv namenode:/tmp/ecommerce_data.csv
echo "  OK"

# ---------- 3. Charger dans HDFS ----------
echo ""
echo "[3/6] Chargement dans HDFS..."
docker exec namenode bash -c "
    hdfs dfs -mkdir -p ${INPUT_HDFS}
    hdfs dfs -test -e ${INPUT_HDFS}/ecommerce_data.csv && \
        hdfs dfs -rm ${INPUT_HDFS}/ecommerce_data.csv || true
    hdfs dfs -put /tmp/ecommerce_data.csv ${INPUT_HDFS}/
    echo '  Vérification :'
    hdfs dfs -ls -h ${INPUT_HDFS}
    echo ''
    echo '  Découpage en blocs HDFS :'
    hdfs fsck ${INPUT_HDFS}/ecommerce_data.csv -files -blocks 2>/dev/null | grep -E 'Under|blocks|repl'
"

# ---------- 4. Compiler le programme Java ----------
echo ""
echo "[4/6] Compilation de EcommerceAnalysis.java..."
docker cp EcommerceAnalysis.java namenode:/tmp/EcommerceAnalysis.java
docker exec namenode bash -c "
    cd /tmp
    rm -f EcommerceAnalysis*.class ecommerce.jar
    javac -encoding UTF-8 -classpath \$(hadoop classpath) EcommerceAnalysis.java || exit 1
    jar cf ecommerce.jar EcommerceAnalysis*.class || exit 1
    echo '  ecommerce.jar créé avec succès.'
" || { echo "ERREUR : compilation Java échouée"; exit 1; }

# ---------- 5. Exécuter les 4 jobs MapReduce ----------
echo ""
echo "[5/6] Exécution des 4 jobs MapReduce sur YARN..."
echo "      → Suivez la progression sur http://localhost:8088"
echo ""

docker exec namenode bash -c "
    # Nettoyer les sorties précédentes
    for job in revenue_category orders_region ratings monthly_trend; do
        hdfs dfs -rm -r -f ${OUTPUT_HDFS}/\${job} 2>/dev/null || true
    done

    echo '  ── Job 1/4 : Chiffre d affaires par catégorie ──'
    hadoop jar /tmp/ecommerce.jar EcommerceAnalysis revenue_category \
        ${INPUT_HDFS} ${OUTPUT_HDFS}/revenue_category
    echo ''

    echo '  ── Job 2/4 : Commandes par région ──'
    hadoop jar /tmp/ecommerce.jar EcommerceAnalysis orders_region \
        ${INPUT_HDFS} ${OUTPUT_HDFS}/orders_region
    echo ''

    echo '  ── Job 3/4 : Distribution des notes ──'
    hadoop jar /tmp/ecommerce.jar EcommerceAnalysis ratings \
        ${INPUT_HDFS} ${OUTPUT_HDFS}/ratings
    echo ''

    echo '  ── Job 4/4 : Tendance mensuelle ──'
    hadoop jar /tmp/ecommerce.jar EcommerceAnalysis monthly_trend \
        ${INPUT_HDFS} ${OUTPUT_HDFS}/monthly_trend
    echo ''
    echo '  Tous les jobs terminés avec succès.'
"

# ---------- 6. Récupérer les résultats ----------
echo ""
echo "[6/6] Récupération des résultats..."
docker exec namenode bash -c "
    for job in revenue_category orders_region ratings monthly_trend; do
        rm -rf /tmp/\${job}
        hdfs dfs -get ${OUTPUT_HDFS}/\${job} /tmp/\${job}
    done
"
rm -rf ./results
mkdir -p ./results
for job in revenue_category orders_region ratings monthly_trend; do
    docker cp namenode:/tmp/${job} ./results/
done

# ---------- Aperçu rapide ----------
echo ""
echo "======================================================"
echo "  RÉSULTATS"
echo "======================================================"
echo ""
echo "  Chiffre d'affaires par catégorie (€) :"
sort -k2 -nr results/revenue_category/part-r-00000 | \
    awk -F'\t' '{printf "    %-22s %15.2f €\n", $1, $2}'

echo ""
echo "  Commandes par région :"
sort -k2 -nr results/orders_region/part-r-00000 | \
    awk -F'\t' '{printf "    %-35s %10d commandes\n", $1, $2}'

echo ""
echo "  Distribution des notes :"
cat results/ratings/part-r-00000 | \
    awk -F'\t' '{printf "    %d étoile(s) : %d\n", $1, $2}'

echo ""
echo "  Total commandes : $(awk -F'\t' '{s+=$2} END{print s}' results/orders_region/part-r-00000)"
echo ""
echo "  Lancez maintenant : python3 visualisation_ecommerce.py"
echo "======================================================"
