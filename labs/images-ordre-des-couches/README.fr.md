# images-ordre-des-couches : un Dockerfile juste, et coûteux

## Ce que ce lab éprouve

Que l'ordre des instructions d'un Dockerfile décide de ce que le cache peut
servir, et que **le défaut ne se voit pas** : l'image produite est juste dans
les deux cas. Seul son coût de reconstruction change.

C'est ce qui rend ce défaut si répandu. Rien n'a l'air cassé, donc rien ne
semble à corriger, et une intégration continue met six minutes à refaire un
travail que personne n'a modifié.

## Mesuré avant d'être écrit

Sur `docker.lab`, le 2026-10-30, sur le même contexte et deux ordres :

| Ordre | code changé | manifeste changé |
| --- | --- | --- |
| copie du contexte puis installation | travail **refait** (3 s) | refait |
| manifeste, installation, puis code | **servi par le cache** (1 s) | refait |

Et la réponse naïve a été **éprouvée** : le Dockerfile de départ, construit tel
quel sous le nom attendu, rend **2/4**. Les deux contrôles verts sont ceux qui
ne portent pas sur l'ordre, et les deux rouges nomment la cause. Un lab dont la
réponse naïve donnerait 4/4 ne mesurerait rien.

## L'empreinte, et pourquoi pas l'identifiant de couche

L'outil d'installation tire seize octets au hasard et les écrit dans l'image.
Deux images qui portent la **même** empreinte n'ont pas rejoué l'instruction :
la couche vient du cache.

Le premier jet de ces tests comparait les identifiants de couche de `docker
history`. Mesuré le même jour : sous buildkit, ils valent tous `<missing>` pour
les couches intermédiaires, et la comparaison concluait « réutilisée » sur un
travail refait. **Un indicateur qui rend la même valeur partout ne mesure
rien**, et il concluait au vert.

## Pourquoi le travail coûteux ne dépend pas du réseau

`installer` est un outil déposé dans l'image de base : il lit le manifeste et
dort une seconde par ligne.

Un lab qui ferait un vrai `apt-get` ou `pip install` mesurerait la bande
passante du jour, et échouerait sur une machine sans accès sortant **en
accusant l'apprenant**. Le coût est simulé, et il est réel : trois secondes
suffisent à rendre le gain visible.

## Pourquoi les deux moitiés sont notées

Le cache doit servir quand le code change, et il doit **cesser** de servir
quand le manifeste change.

Copier le manifeste après l'installation rendrait le troisième contrôle vert et
ferait servir le cache même quand les dépendances changent : l'image resterait
figée sur les anciennes, et personne ne le verrait avant la production. Un
contrôle qui ne regarderait que la première moitié récompenserait donc la faute
la plus coûteuse des deux.

Le quatrième vérifie aussi que la nouvelle dépendance est **réellement
installée** : refaire un travail sans effet passerait sinon pour une réussite.

## Pourquoi le brouillon est dans le contexte

Une copie du contexte entier ne copie pas « le code », elle copie **tout**, le
Dockerfile compris. Ces fichiers grossissent l'image, et surtout chacun d'eux
invalide le cache en changeant : éditer le Dockerfile suffirait à refaire
l'installation.

Le contrôle ne dit pas comment les exclure. Un fichier d'exclusion et une copie
ciblée donnent le même état, et c'est l'état qui est noté.

## Pourquoi les contrôles reconstruisent dans une copie

Modifier le répertoire de l'apprenant pour le noter serait doublement fautif :
cela détruirait son travail, et le verdict porterait sur un état que le test a
produit lui-même.

La modification est un **ajout en fin de fichier** : le code reste exécutable,
le manifeste reste lisible, et l'image reste construisible.

## L'état de départ est cassé, et c'est la règle du dépôt

Le setup **ne construit pas** l'image : les quatre contrôles sont donc faux
avant tout travail, y compris ceux qui ne portent pas sur l'ordre. Construire
fait partie de la mission.

Une tâche du setup vérifie que le socle existe, que l'image de l'apprenant
n'existe pas, et que le Dockerfile de départ porte bien la copie en bloc : sans
elle, un passage mal nettoyé rendrait le lab déjà résolu.

## Un piège du cleanup, payé d'avance

**Le cache de construction doit partir avec le reste.** Les couches
intermédiaires d'une construction ne sont pas des images : elles vivent dans le
cache du constructeur, et un `docker image prune` ne les touche pas. Sans un
`builder prune`, la construction du passage suivant serait servie par un cache
dont l'apprenant n'a pas écrit une ligne, et le lab mesurerait un travail qui
n'a pas eu lieu.

C'est la purge la plus lente du catalogue, et c'est le prix de la
reproductibilité.

## Ce que le lab n'exige pas

Un chemin. Le jeton est tiré par le setup et relu dans le code source au moment
de la notation ; les dépendances sont relues dans le manifeste. Rien n'est écrit
en dur dans les contrôles, et rien ne se note sur un formulaire.
