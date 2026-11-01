# Quatre labs cassent le jour où la VM passe en Docker 29

Mesuré le 2026-11-01, sur un poste en **Docker Engine 29.1.3** (store containerd).

## Le fait

Le champ `IPAddress` **n'existe plus** dans `NetworkSettings`. Il n'est pas vide :
il est absent, et le gabarit Go échoue.

```console
$ docker inspect -f '{{.NetworkSettings.IPAddress}}' <conteneur>
template parsing error: template: :1:18: executing "" at
<.NetworkSettings.IPAddress>: map has no entry for key "IPAddress"
```

Les seules clés restantes : `Networks`, `Ports`, `SandboxID`, `SandboxKey`.
L'adresse, la passerelle et l'adresse MAC ont migré sous `Networks.<réseau>`.

La forme **portable**, qui rend la même valeur sur 26 et sur 29 :

```console
$ docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' <conteneur>
172.17.0.6
```

## Pourquoi les labs sont verts quand même

`docker.lab` tourne **Docker 26.1.5** (paquet `docker.io` de Debian 13), avec le
store `classic`, où le champ plat existe encore. C'est écrit dans chaque entrée
de `validation-labs.json` : `"docker": "26.1.5+dfsg1"`, `"store": "classic"`.

Le verdict VALIDE de ces labs ne mesure donc que ce moteur-là. Le jour où la VM
prend un moteur 29.x, par une mise à jour du dépôt Debian ou un changement de
distribution de base, **quatre labs cassent d'un coup**, et deux d'entre eux
cassent dans leur `setup.yaml`, c'est-à-dire **avant que l'apprenant commence**.

## Les cinq emplacements à reprendre

| Lab | Fichier |
| --- | --- |
| `docker-inspecter-un-conteneur` | `challenge/tests/test_functional.py` |
| `reseau-publication-de-ports` | `challenge/tests/test_functional.py` |
| `reseau-bridge-par-defaut` | `setup.yaml` **et** `challenge/tests/test_functional.py` |
| `reseau-bridge-dedie` | `setup.yaml` |

Un indice de `docker-inspecter-un-conteneur` cite aussi la forme plate.

## Ce qui reste à faire

Remplacer les cinq occurrences par la forme portable, puis **réattester les
quatre labs** : un commit postérieur au relevé les fait repasser en
`a-reattester`, et le catalogue du site les retire alors de l'affichage.

Attention au quoting dans un `setup.yaml` Ansible : les deux occurrences de
`setup.yaml` passent déjà par `{{ '{{' }}` pour échapper les accolades de Jinja,
et la forme portable en comporte davantage.

**Non fait le 2026-11-01** parce qu'une campagne de réattestation tournait sur
ces labs. À reprendre dans la branche qui aligne les `doc_url`.
