# Solution de reference du premier lab.
#
# Elle est VOLONTAIREMENT naive : elle fait ce que la lecon enseigne a ce
# stade, et rien de plus. Les labs suivants la reprendront pour en montrer le
# cout, couche par couche. Y mettre deja le multi-etapes et l'utilisateur
# non-root priverait la serie de sa progression.

FROM debian:12

# Python n'est pas dans l'image de base : c'est le premier constat du lab.
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app/ /app/

# `--break-system-packages` : Debian 12 protege son Python systeme (PEP 668).
# Dans un conteneur dedie a une seule application, il n'y a pas d'autre
# environnement a proteger, et la lecon l'explique.
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt

# EXPOSE ne publie rien et n'ouvre aucun port : il DECLARE celui que l'image
# ecoute. C'est de la documentation lue par les outils, et par le lecteur.
EXPOSE 8000

# `--host 0.0.0.0` et non 127.0.0.1 : dans le conteneur, la boucle locale
# n'est joignable que depuis le conteneur. Une application qui n'ecoute que
# sur elle-meme est injoignable depuis l'hote, meme avec -p.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
