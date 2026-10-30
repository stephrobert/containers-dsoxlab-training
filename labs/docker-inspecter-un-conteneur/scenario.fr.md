# Le conteneur tourne, et personne ne sait rien de lui

## La situation

Un prestataire a livré un service en conteneur, l'a lancé à la main sur cette
machine, puis son contrat s'est terminé. Il n'a laissé ni documentation, ni
fichier de configuration, ni script de démarrage.

Le conteneur `greffier` tourne. C'est à peu près tout ce qu'on sait.

Vous cherchez d'abord dans `/etc`, puis dans `/opt`, puis dans l'historique du
shell. Rien. Et c'est normal : **un conteneur en marche ne laisse presque rien
sur l'hôte**. Ce qu'il a dit en démarrant, l'adresse qu'on lui a donnée, le
port par lequel on l'atteint, ce qu'il a écrit depuis : tout cela est détenu
par le moteur, et le moteur ne le publie pas. Il faut le lui demander.

C'est la situation la plus banale du dépannage de conteneurs, et elle désarme
quiconque n'a que des réflexes de système classique.

## L'objectif

Obtenir du moteur quatre choses qui ne sont écrites nulle part sur cette
machine. Elles sont **tirées au hasard à chaque passage** : il n'y a rien à
retenir, et rien à recopier d'ailleurs.

Renseignez les trois lignes de `/opt/lab-inspection/reponses.txt` :

```text
jeton=<le jeton de session que `greffier` a annoncé au démarrage>
adresse=<l'adresse IP que le moteur a donnée à `greffier`>
port=<le port de L'HÔTE sur lequel le 80 du conteneur est publié>
```

Puis sortez du conteneur le fichier qu'il a écrit **après** son démarrage, et
déposez-le à l'identique :

```text
/var/log/greffier/trace.log   ->   /opt/lab-inspection/trace.log
```

Le conteneur doit **toujours tourner** à la fin. L'énoncé est aussi déposé dans
`/opt/MISSION.md`.

## Ce qui est noté

L'**état du système**, jamais les commandes tapées. Chaque réponse est
recalculée au moment de la notation, en interrogeant le moteur, puis confrontée
à ce que vous avez écrit.

Il y a donc plusieurs bons chemins, et ils comptent tous : le jeton se lit dans
la sortie du conteneur comme dans le fichier journal que le moteur tient sur
l'hôte, le port par la table des ports comme par l'inspection complète, et le
fichier se sort par une copie comme par une redirection.

Un seul geste est une faute, et il coûte deux contrôles : **arrêter le
conteneur pour le fouiller**. Un conteneur arrêté n'a plus d'adresse ni de
table des ports.
