# Chaîne de livraison complète

Capstone c4, 120 minutes. Lire [l'épreuve](scenario.fr.md).
Source → BuildKit multi-étapes → inventaire SPDX réel → registre local →
pull par digest → Compose API/PostgreSQL durci → données durables → huit pannes.

Dépendances et épingles : [provenance](fixtures/PROVENANCE.md). VM Debian 13
amd64, Docker/BuildKit, Compose v2 `up --wait`, Python 3, ports 15088/18088 libres.
Seul le setup exige apt/réseau images ; wheel locale vérifiée pour les builds.
Nettoyage uniquement des conteneurs, images, réseaux, volumes du lab et de
`/opt/lab-delivery` ; bases partagées préservées. Référence chiffrée :
`solution/capstone-chaine-complete/solution.yaml`.
Le relevé avant pull distingue les bases introduites des bases préexistantes ;
retrait seulement si non utilisées et non partagées, sans force ni prune des parents.
