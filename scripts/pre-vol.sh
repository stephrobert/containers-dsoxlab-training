#!/usr/bin/env bash
# Rejoue localement ce que la CI vérifiera, y compris sur un EXPORT PROPRE.
#
# POURQUOI CE SCRIPT EXISTE
#
# Les contrôles locaux ne lisent pas le dépôt : ils lisent le disque de celui
# qui les lance. L'écart se paie au premier clone. Mesuré sur le catalogue
# DevSecOps le 2026-09-25 : cinq fixtures déclarées dans un `lab.yaml`
# existaient sur la machine de l'auteur mais n'étaient pas versionnées. Trois
# labs étaient cassés pour quiconque clone, et intacts chez lui. La différence
# n'était pas dans les contrôles, elle était dans ce qu'ils lisaient.
#
# Ce script comble l'écart : il exporte le dépôt tel que git le voit, puis y
# relance les contrôles. Un fichier oublié dans un `git add` s'y voit, et nulle
# part ailleurs avant la CI.
#
# L'INDEX, ET NON `HEAD`
#
# L'export part de `git write-tree`, donc de ce qu'on s'apprête à livrer, et
# non du dernier commit. Sans cela, un fichier ajouté mais pas encore commité
# manque à l'export, et le pré-vol accuse à tort un lab qu'on vient d'écrire.
#
# CE QU'IL NE FAIT PAS
#
# CodeQL, qui demande l'infrastructure de GitHub. Et le rejeu des labs, qui
# construit des images et lance des conteneurs : c'est `scripts/test-all.sh` et
# `scripts/valider-labs.py`, et cela se compte en minutes, pas en secondes.
#
#     scripts/pre-vol.sh            # tout
#     scripts/pre-vol.sh --rapide   # sans les hooks, qui sont les plus lents
set -uo pipefail

RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${RACINE}" || exit 1

RAPIDE=0
[[ "${1:-}" == "--rapide" ]] && RAPIDE=1

JOURNAUX="$(mktemp -d)"
echecs=0
titre() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()    { printf '   \033[0;32mOK\033[0m    %s\n' "$*"; }
ko()    { printf '   \033[0;31mÉCHEC\033[0m %s\n' "$*"; echecs=$((echecs + 1)); }
note()  { printf '   \033[0;33m-\033[0m     %s\n' "$*"; }

titre "1. Ce que git publierait : un export de l'index"
EXPORT="$(mktemp -d)"
trap 'rm -rf "${EXPORT}" "${JOURNAUX}"' EXIT

if ARBRE="$(git write-tree)" && git archive "${ARBRE}" | tar -x -C "${EXPORT}"; then
    ok "index exporté dans un répertoire neuf ($(find "${EXPORT}" -type f | wc -l) fichiers)"
else
    ko "git write-tree ou git archive a échoué : rien à vérifier sur l'export"
fi

# Le contrat, lu sur l'export et non sur le disque de travail. C'est CE contrôle
# qui voit un lab dont un fichier requis n'est pas versionné.
if (cd "${EXPORT}" && LAB_HOME="${EXPORT}" uvx 'dsoxlab>=0.5.0' validate-structure \
        > "${JOURNAUX}/structure.log" 2>&1); then
    ok "dsoxlab validate-structure sur l'export"
else
    ko "dsoxlab validate-structure sur l'export"
    grep -E '✘|ERROR|error' "${JOURNAUX}/structure.log" | head -10
fi

# Les méta-tests sur l'export. Deux d'entre eux changent de verdict ici plutôt
# que sur le disque de travail, et ce sont les plus utiles : les solutions
# chiffrées et les liens internes portent sur des fichiers, et un fichier non
# versionné manque à l'export. `test_aucun_jeton_versionne.py` s'y SKIPPE, par
# construction : son périmètre est `git ls-files`, qui ne répond pas hors d'un
# dépôt, et un contrôle qui n'a pas pu regarder ne conclut jamais au vert.
if (cd "${EXPORT}" && "${RACINE}/.venv/bin/python" -m pytest tests/ -q \
        > "${JOURNAUX}/tests-export.log" 2>&1); then
    ok "méta-tests sur l'export : $(tail -1 "${JOURNAUX}/tests-export.log")"
else
    ko "méta-tests sur l'export"
    grep -E '^(FAILED|ERROR)' "${JOURNAUX}/tests-export.log" | head -12
fi

titre "2. Les méta-tests et le catalogue, sur l'arbre de travail"
if uv run --no-sync pytest tests/ -q > "${JOURNAUX}/tests.log" 2>&1; then
    ok "$(tail -1 "${JOURNAUX}/tests.log")"
else
    ko "méta-tests"
    grep -E '^(FAILED|ERROR)' "${JOURNAUX}/tests.log" | head -12
fi

if uv run --no-sync python scripts/gen_catalog.py --check > /dev/null 2>&1; then
    ok "catalogue des README à jour"
else
    ko "catalogue périmé : lancez scripts/gen_catalog.py"
fi

titre "3. Le lint, avec les règles du dépôt"
# `--force-exclude` : sans lui, l'`exclude` du pyproject est ignoré pour tout
# fichier passé en argument, ce qui est exactement ce que font les hooks.
if uvx ruff check --force-exclude . > "${JOURNAUX}/ruff.log" 2>&1; then
    ok "ruff"
else
    ko "ruff"
    tail -8 "${JOURNAUX}/ruff.log"
fi

titre "4. Les workflows, les trois analyseurs de la CI"
# Un binaire absent est une mesure MANQUANTE, pas un succès : il se dit, et il
# ne compte pas pour un échec. C'est la règle de tout le dépôt, et c'est ce qui
# distingue « j'ai regardé et c'est bon » de « je n'ai pas regardé ».
if command -v actionlint > /dev/null 2>&1; then
    if actionlint > "${JOURNAUX}/actionlint.log" 2>&1; then
        ok "actionlint"
    else
        ko "actionlint"
        head -12 "${JOURNAUX}/actionlint.log"
    fi
else
    note "actionlint absent du PATH : non mesuré (mise use -g actionlint)"
fi

if command -v zizmor > /dev/null 2>&1; then
    if zizmor --no-online-audits .github/workflows > "${JOURNAUX}/zizmor.log" 2>&1; then
        ok "zizmor ($(zizmor --version))"
    else
        ko "zizmor"
        grep -vE '^ INFO' "${JOURNAUX}/zizmor.log" | head -14
    fi
else
    note "zizmor absent du PATH : non mesuré (mise use -g zizmor)"
fi

if command -v poutine > /dev/null 2>&1; then
    # poutine sort en 0 même avec des constats : c'est leur nombre qu'on lit,
    # pas son code de retour.
    poutine analyze_local . > "${JOURNAUX}/poutine.log" 2>&1
    if grep -qE '\| +[1-9][0-9]* +\| Failed' "${JOURNAUX}/poutine.log"; then
        ko "poutine"
        grep -E 'Failed' "${JOURNAUX}/poutine.log" | head -8
    else
        ok "poutine"
    fi
else
    note "poutine absent du PATH : non mesuré"
fi

if [[ "${RAPIDE}" -eq 0 ]]; then
    titre "5. Les hooks, dans les deux étapes que la CI rejoue"
    if uvx pre-commit@4.6.0 run --all-files > "${JOURNAUX}/hooks.log" 2>&1; then
        ok "hooks, étape commit"
    else
        ko "hooks, étape commit"
        grep -E 'Failed' "${JOURNAUX}/hooks.log" | head -8
    fi
    if uvx pre-commit@4.6.0 run --all-files --hook-stage pre-push \
            > "${JOURNAUX}/hooks-push.log" 2>&1; then
        ok "hooks, étape pre-push"
    else
        ko "hooks, étape pre-push"
        grep -E 'Failed' "${JOURNAUX}/hooks-push.log" | head -8
    fi
else
    note "hooks non joués (--rapide)"
fi

printf '\n'
if [[ "${echecs}" -eq 0 ]]; then
    printf '\033[0;32mPré-vol vert.\033[0m La CI ne devrait rien trouver de plus, hors CodeQL et le rejeu des labs.\n'
else
    printf '\033[0;31m%s contrôle(s) en échec.\033[0m Corrigez avant de pousser.\n' "${echecs}"
fi
exit "${echecs}"
