#!/usr/bin/env bash
# hadolint sur les Dockerfile du DÉPÔT, jamais sur ceux des fixtures.
#
# POURQUOI CETTE DISTINCTION
#
# Un `fixtures/` peut livrer un Dockerfile volontairement fautif : ordre des
# couches à l'envers, image de base en tag flottant, root. C'est le sujet de
# l'exercice, et hadolint y rendrait un échec permanent dont la seule façon de
# sortir serait de retirer du lab ce qui fait le lab.
#
# Les `solution/` sont un cas intermédiaire, et c'est le point délicat : la
# solution du premier lab est VOLONTAIREMENT naïve, parce qu'elle fait ce que la
# leçon enseigne à ce stade et que les labs suivants en montreront le coût.
# hadolint lui reprocherait l'absence de `USER`, ce qui serait juste dans
# l'absolu et faux pédagogiquement.
#
# Les solutions sont donc contrôlées avec `--failure-threshold error` : les
# vraies fautes arrêtent, les conseils de style ne bloquent pas une progression
# délibérée.
set -euo pipefail
cd "$(dirname "$0")/../.."

mapfile -t solutions < <(find labs -type f -path '*/solution/*' -name 'Dockerfile*' 2>/dev/null | sort)

if [ ${#solutions[@]} -eq 0 ]; then
    echo "aucun Dockerfile de solution à contrôler"
    exit 0
fi

echo "hadolint sur ${#solutions[@]} Dockerfile de solution"
hadolint --failure-threshold error "${solutions[@]}"
