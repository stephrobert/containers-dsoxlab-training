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
# LES SOLUTIONS SONT CHIFFRÉES
#
# hadolint lirait « $ANSIBLE_VAULT;1.1;AES256 » suivi d'un pavé hexadécimal,
# et n'y verrait aucune instruction : il rendrait du vert sans avoir rien
# contrôlé. Chaque fichier chiffré est donc déchiffré dans un temporaire avant
# l'analyse.
#
# En CI, `.vault-pass` n'existe pas, et c'est voulu : aucun catalogue de la
# collection ne confie son secret à la forge. Le contrôle s'y déclare alors
# NON JOUÉ, par un avertissement visible dans l'interface, plutôt que de
# passer pour un succès. Il se joue chez le formateur, qui a le secret.
set -euo pipefail
cd "$(dirname "$0")/../.."

# Surchargeable pour éprouver le chemin « sans secret » sans toucher au vrai.
VAULT_PASS="${VAULT_PASS:-.vault-pass}"

mapfile -t solutions < <(find labs -type f -path '*/solution/*' -name 'Dockerfile*' 2>/dev/null | sort)

if [ ${#solutions[@]} -eq 0 ]; then
    echo "aucun Dockerfile de solution à contrôler"
    exit 0
fi

temporaire="$(mktemp -d)"
trap 'rm -rf "$temporaire"' EXIT

analysables=()
chiffrees=0
for solution in "${solutions[@]}"; do
    if ! head -c 14 "$solution" | grep -q 'ANSIBLE_VAULT'; then
        analysables+=("$solution")
        continue
    fi
    chiffrees=$((chiffrees + 1))
    if [ ! -f "$VAULT_PASS" ]; then
        continue
    fi
    # Le nom du fichier est conservé : hadolint le cite dans ses messages, et
    # « /tmp/tmp.XYZ/1 » n'apprendrait rien à qui lit le journal.
    clair="$temporaire/$(echo "$solution" | tr '/' '_')"
    ansible-vault view --vault-password-file "$VAULT_PASS" "$solution" > "$clair"
    analysables+=("$clair")
done

if [ ${#analysables[@]} -eq 0 ]; then
    echo "::warning::contrôle NON JOUÉ : les ${chiffrees} Dockerfile de solution sont chiffrés et ${VAULT_PASS} est absent. Joue-le en local, où le secret existe."
    exit 0
fi

echo "hadolint sur ${#analysables[@]} Dockerfile de solution (dont ${chiffrees} déchiffré(s))"
hadolint --failure-threshold error "${analysables[@]}"
