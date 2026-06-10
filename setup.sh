#!/usr/bin/env bash
set -e

echo "======================================================"
echo "  Mini-projet Hadoop — Setup automatique"
echo "======================================================"

# ---------- 1. Télécharger le corpus ----------
echo ""
echo "[1/5] Téléchargement des livres Gutenberg..."
for id in 1342 11 1661 2701 84 98 2600 1080; do
    if [ ! -f "book_${id}.txt" ]; then
        wget -q -O "book_${id}.txt" "https://www.gutenberg.org/files/${id}/${id}-0.txt" \
            || wget -q -O "book_${id}.txt" "https://www.gutenberg.org/cache/epub/${id}/pg${id}.txt" \
            || echo "  Avertissement : livre ${id} non téléchargé, on continue."
    fi
done
cat book_*.txt > corpus.txt
CORPUS_SIZE=$(wc -c < corpus.txt)
echo "  corpus.txt : $(du -sh corpus.txt | cut -f1)"

# ---------- 2. Gonfler le fichier ----------
echo ""
echo "[2/5] Création de bigfile.txt (~2-3 Go)..."
> bigfile.txt
# Calcul dynamique du nombre de répétitions pour viser ~2 Go
TARGET_BYTES=$((2 * 1024 * 1024 * 1024))
REPEATS=$(( TARGET_BYTES / CORPUS_SIZE + 1 ))
echo "  Corpus : ${CORPUS_SIZE} octets → répétitions : ${REPEATS}"
for i in $(seq 1 ${REPEATS}); do
    cat corpus.txt >> bigfile.txt
done
echo "  bigfile.txt : $(du -sh bigfile.txt | cut -f1)"

# ---------- 3. Copier dans le namenode ----------
echo ""
echo "[3/5] Copie du fichier dans le conteneur namenode..."
docker cp bigfile.txt namenode:/tmp/bigfile.txt
echo "  Copie terminée."

# ---------- 4. Charger dans HDFS ----------
echo ""
echo "[4/5] Chargement dans HDFS..."
docker exec namenode bash -c "
    hdfs dfs -mkdir -p /user/root/input
    hdfs dfs -test -e /user/root/input/bigfile.txt && hdfs dfs -rm /user/root/input/bigfile.txt || true
    hdfs dfs -put /tmp/bigfile.txt /user/root/input/
    echo '  Vérification :'
    hdfs dfs -ls -h /user/root/input
"

# ---------- 5. Compiler et lancer le job MapReduce ----------
echo ""
echo "[5/5] Compilation et exécution du job MapReduce..."
docker cp WordCount.java namenode:/tmp/WordCount.java
docker exec namenode bash -c "
    cd /tmp
    hadoop com.sun.tools.javac.Main WordCount.java
    jar cf wc.jar WordCount*.class
    hdfs dfs -rm -r -f /user/root/output
    hadoop jar wc.jar WordCount /user/root/input /user/root/output
"

# ---------- Récupérer les résultats ----------
echo ""
echo "Récupération des résultats..."
docker exec namenode bash -c "hdfs dfs -get /user/root/output /tmp/output 2>/dev/null || true"
rm -rf ./output
docker cp namenode:/tmp/output ./output

echo ""
echo "======================================================"
echo "  Terminé ! Résultats dans ./output/"
echo ""
echo "  Top 10 mots :"
sort -k2 -nr output/part-r-00000 | head -10
echo ""
echo "  Mots distincts : $(wc -l < output/part-r-00000)"
echo ""
echo "  Lancez maintenant : python3 visualisation.py"
echo "======================================================"
