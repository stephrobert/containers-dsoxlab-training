#!/usr/bin/env bash
# Rejoue les tests de TOUS les labs contre leur solution de référence.
#
# C'est le contrôle formateur « mes solutions passent mes propres tests ».
# Mécanisme : la fixture autouse `_apply_lab_state` de `conftest.py` joue
# `solution/<lab>/solution.yaml` sur la machine du lab AVANT ses tests. Les
# solutions étant chiffrées, elle a besoin de `.vault-pass`.
#
# POURQUOI IL NE REMPLACE PAS `valider-labs.py`, ET RÉCIPROQUEMENT
#
# Ce script ne joue qu'un sens : « avec la solution, tout passe ». Il ne prouve
# donc pas qu'un test MESURE quelque chose : un test vrai avant le travail
# passerait ici sans broncher. `scripts/valider-labs.py` est celui qui exige
# **0 avant, 100 après**, puis photographie le moteur pour refuser un lab qui
# laisse une trace. Il est beaucoup plus lent, et c'est lui qui écrit
# `validation-labs.json`.
#
# Ce script sert donc à une chose : voir vite si une montée de version d'une
# image de base, de Docker ou de l'outillage a cassé des solutions, sans
# relancer une campagne complète.
#
# POUR UN SEUL LAB, PRÉFÉRER LA CLI
#
#     dsoxlab check <id-du-lab>
#
# Elle pose l'état de départ et désactive le rejeu de la solution
# (`LAB_NO_REPLAY=1`), donc elle note comme pour un apprenant.
#
# PRÉREQUIS
#
#   - les outils aux versions de `mise.toml` (`mise install`) ;
#   - `.vault-pass` présent : les solutions sont chiffrées ;
#   - les machines des labs provisionnées : tous les labs sont en
#     `runtime: vm`, et leurs tests se connectent en SSH. Sans elles, chaque
#     lab échoue sur la connexion, et ce n'est pas un défaut du catalogue.

set -euo pipefail

RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${RACINE}"

log()  { printf '\033[0;34m[test-all]\033[0m %s\n' "$*"; }
ok()   { printf '\033[0;32m[OK]\033[0m %s\n' "$*"; }
ko()   { printf '\033[0;31m[ÉCHEC]\033[0m %s\n' "$*" >&2; }

if [[ ! -d labs ]]; then
    ko "labs/ introuvable : à lancer depuis la racine du dépôt."
    exit 1
fi

# Un catalogue vide doit ÉCHOUER, pas passer en silence : sinon la suite sort
# verte dès qu'elle ne trouve aucun lab, et c'est la forme la plus discrète de
# faux vert.
labs="$(find labs -name lab.yaml | wc -l)"
if [[ "${labs}" -eq 0 ]]; then
    ko "aucun lab trouvé sous labs/ : catalogue vide ?"
    exit 1
fi

# Les squelettes LÈVENT, par construction (`def test_a_ecrire`). Les compter
# ici évite la seule mauvaise lecture possible de la sortie : un rouge attendu
# pris pour une régression. Le marqueur est celui que `tests/` emploie, et
# `tests/test_maturite_des_labs.py` le tient en place.
squelettes="$(grep -rl 'def test_a_ecrire' labs --include='test_functional.py' | wc -l)"
log "${labs} labs, dont ${squelettes} squelettes qui échoueront volontairement"
log "les $((labs - squelettes)) autres sont joués avec leur solution de référence"

if [[ ! -f .vault-pass ]]; then
    ko ".vault-pass absent : les solutions chiffrées ne peuvent pas être rejouées."
    ko "Sans lui, chaque lab serait joué SANS sa solution, donc rouge pour une"
    ko "raison qui n'a rien à voir avec son contenu."
    exit 1
fi

# `-k` et les autres arguments sont transmis tels quels : jouer une section du
# catalogue est le cas courant, parce que la totalité demande que toutes les
# machines soient debout en même temps.
if "${RACINE}/.venv/bin/python" -m pytest labs/ "$@"; then
    ok "tous les labs joués passent"
else
    ko "au moins un lab échoue (voir ci-dessus)"
    ko "Un squelette dans le lot est un échec ATTENDU : comparez aux ${squelettes} annoncés."
    exit 1
fi
