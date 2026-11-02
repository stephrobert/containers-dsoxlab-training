# Le Dockerfile de l'epreuve, A COMPLETER.
#
# CE QU'IL FAUT OBTENIR. Une image qui porte `/app/empreinte.txt`, contenant
# l'empreinte SHA-256 du secret de construction, et dans laquelle le SECRET
# LUI-MEME ne survit dans AUCUNE couche.
#
# LE SECRET EST SUR LE DISQUE de l'hote de construction, en
# /opt/lab-livraison/build/jeton-de-build.txt. Il ne doit pas entrer dans
# l'image : ni par `COPY`, ni par `ARG`, ni par `ENV`. Un secret monte par
# BuildKit le temps d'une instruction n'entre dans aucune couche ; les trois
# autres voies y entrent, et se relisent dans l'historique.
#
# RIEN D'AUTRE N'EST IMPOSE. La façon de monter le secret, le nombre d'etapes,
# l'ordre des instructions : c'est votre travail. Le controle lit l'image
# produite, jamais ce fichier.
FROM python:3.14.10-slim-trixie@sha256:3cabfd7d7aaf394e6040e79fa1eec6ca1c52b74ed9188650472695d9a9326999
LABEL dsoxlab.lab="epreuve-livrer-une-image"
COPY service.py /service.py

# A COMPLETER : produire /app/empreinte.txt depuis le secret de construction,
# sans que le secret entre dans une couche.

CMD ["python", "/service.py"]
