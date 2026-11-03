"""Le fichier d'identifiant sejourne-t-il dans le repertoire de contexte ?

POURQUOI CE CONTROLE EXISTE

Le scenario exige que le secret reste « hors du contexte de build », et le
rappelle une seconde fois : « il ne doit pas etre copie dans le contexte ».
Aucun test ne le mesurait. Un apprenant qui copiait `depot.token` dans
`appli/` puis le passait par `--secret id=depot,src=./depot.token` passait donc
les trois controles, parce qu'ils inspectent l'IMAGE : configuration,
historique et couches. Or un fichier present dans le contexte mais jamais
`COPY` n'entre dans aucune couche. L'exigence etait invisible, et l'apprenant
la croyait notee.

CE QU'IL REFUSE, ET POURQUOI SANS EXCEPTION POUR `.dockerignore`

Un secret exclu par `.dockerignore` ne part effectivement pas au demon. Mais il
reste sur le disque, dans le repertoire que l'on versionne, et une exclusion
s'oublie : le jour ou quelqu'un retire la ligne, ou ajoute un `COPY . .` avant
elle, le secret suit l'arborescence. C'est pourquoi l'exigence porte sur le
REPERTOIRE et non sur ce que Docker en transmet, et c'est ce que le message
explique a l'apprenant plutot que de le laisser deviner.

CE QU'IL CHERCHE

Le jeton en clair, mais aussi sa forme base64 et l'en-tete `Bearer` construit,
sous les deux formes : un secret recopie dans un fichier de configuration ou un
script d'aide ne se presente pas toujours brut. Les noms de fichiers sont
inspectes autant que leur contenu, un `depot.token` recopie etant deja une
faute meme vide.

ET IL NE CONCLUT JAMAIS AU VERT SUR UNE SURFACE QU'IL N'A PAS SU LIRE : les
chemins illisibles sont rendus a l'appelant, qui leve. Un controle qui avale
son echec de lecture note l'apprenant sur ce qu'il n'a pas regarde.
"""

from __future__ import annotations

import base64
import json
import os
import sys


def aiguilles(jeton: bytes) -> list[bytes]:
    """Les formes sous lesquelles le secret peut se presenter."""
    formes = [jeton, base64.b64encode(jeton)]
    porteur = b"Bearer " + jeton
    formes += [porteur, base64.b64encode(porteur)]
    return [f for f in formes if f]


def main() -> int:
    racine, chemin_jeton = sys.argv[1], sys.argv[2]
    jeton = open(chemin_jeton, "rb").read().strip()
    if not jeton:
        print(json.dumps({"erreur": f"jeton vide dans {chemin_jeton}"}))
        return 2
    cherchees = aiguilles(jeton)
    # Le nom EXACT du fichier d'identifiant, et non tout nom qui evoque un
    # jeton : refuser un `tokenizer.py` innocent serait un faux rouge, et un
    # controle qui crie a tort s'apprend a ignorer.
    nom_du_jeton = os.path.basename(chemin_jeton)

    fuites: list[dict[str, str]] = []
    illisibles: list[str] = []
    for dossier, _, fichiers in os.walk(racine):
        for nom in fichiers:
            complet = os.path.join(dossier, nom)
            relatif = os.path.relpath(complet, racine)
            # Le fichier d'identifiant RECOPIE est deja la faute visee, meme
            # vide : c'est le geste « j'ai copie le secret dans le contexte »
            # que le scenario interdit, et son contenu n'y change rien.
            if nom == nom_du_jeton:
                fuites.append({"chemin": relatif, "ou": "le nom du fichier"})
                continue
            try:
                with open(complet, "rb") as fichier:
                    contenu = fichier.read()
            except OSError as erreur:
                illisibles.append(f"{relatif} ({erreur.strerror})")
                continue
            if any(aiguille in contenu for aiguille in cherchees):
                fuites.append({"chemin": relatif, "ou": "le contenu du fichier"})

    print(json.dumps({
        "propre": not fuites,
        "fuites": fuites,
        "illisibles": illisibles,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
