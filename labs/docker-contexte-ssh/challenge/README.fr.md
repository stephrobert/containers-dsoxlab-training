# Contrat fonctionnel : docker-contexte-ssh

Le client Docker sur `docker.lab` doit utiliser un contexte SSH nommé vers
le vrai moteur de `docker-client.lab`. Les tests comparent les identités des
moteurs, préservent le contexte sélectionné et exigent le refus d'une clé SSH
lisible mais non autorisée. L'état initial est refusé. Seuls les identités et
espaces dédiés au lab sont modifiés.
