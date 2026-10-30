# Le conteneur a redémarré, mais ce n'est plus le même

## La situation

Une astreinte, la nuit. Un conteneur s'est arrêté, et la consigne du runbook
dit : « relancer le conteneur `dormeur` ». Vous le relancez, tout repart, vous
retournez dormir.

Le lendemain, l'équipe constate que les fichiers de travail du conteneur ont
disparu. Vous aviez pourtant fait exactement ce qui était écrit.

Ce qui s'est passé n'a rien d'une panne. « Relancer » peut désigner deux gestes
qui ne se ressemblent pas : **redémarrer** le conteneur qui existait, ou en
**créer un nouveau** portant le même nom. Les deux donnent un conteneur qui
tourne, et c'est bien ce qui rend la confusion durable. Un seul garde
l'identité du conteneur, ses journaux et ce qui avait été écrit dedans.

## L'objectif

Vous déplacer dans le cycle de vie sans jamais repartir de zéro. L'image est
déjà sur la machine : rien à tirer, rien à construire.

```text
dormeur   ARRÊTÉ, et il porte un fichier /empreinte.txt
actif     il TOURNE
```

1. `dormeur` **tourne à nouveau**, et c'est le **même** conteneur : son
   identifiant ne doit pas avoir changé.
2. Son fichier `/empreinte.txt` est toujours là.
3. `actif` est **en pause**, ni arrêté ni supprimé.
4. Un conteneur nommé `sortie` est **terminé**, avec le code de sortie **42**.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## Ce qui est noté

L'**état du moteur**, jamais les commandes tapées. Mais ici l'identité compte
autant que l'état : l'identifiant d'origine de `dormeur` a été relevé **avant**
que vous ne touchiez à quoi que ce soit, et il est comparé. Vous pouvez le lire
vous-même dans `/opt/lab-cycle/id-dormeur.txt`.

Ce n'est pas de la méfiance, c'est le seul moyen de distinguer les deux gestes :
leur résultat visible est identique, et seule l'empreinte les sépare.
