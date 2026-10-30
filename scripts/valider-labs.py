#!/usr/bin/env python3
"""Joue chaque lab dans les deux sens et vérifie qu'il ne laisse aucune trace.

Repris de `github-actions-training/scripts/valider-labs.py`, en remplaçant act
par Docker. Un test qui passe ne prouve rien tant qu'on n'a pas vu échouer ce
qui doit échouer. Pour chaque lab, dans l'ordre :

    0. photographie : images, conteneurs et volumes présents
    1. dsoxlab run            l'état initial est posé (fixtures)
    2. dsoxlab check          DOIT rendre 0 : le travail n'est pas fait
    3. la solution du formateur, `solution/`, posée dans le répertoire de
       travail, sous-répertoires compris
    4. dsoxlab check          DOIT rendre 100
    5. dsoxlab clean, run, check   DOIT rendre 0 : le point de départ se rejoue
    6. dsoxlab clean
    7. photographie à nouveau, comparée à la première : aucun écart admis

Le validateur exige **0 puis 100**, pas « moins » puis « plus » : un lab à cinq
tests dont deux passent avant le travail mesure 40 points de rien.

## Pourquoi la photographie porte sur trois choses

Un lab de ce catalogue construit des images, lance des conteneurs et crée des
volumes sur la machine de l'apprenant, à côté de son travail à lui. Sur la
machine qui a servi à l'écrire, le moteur portait déjà **340 images, 16
conteneurs et 9,5 Go de volumes** : un objet laissé derrière s'y noie, et c'est
le lab suivant qui en paie le prix — il trouve un état qu'il n'a pas posé.

`conftest.py` tient la discipline du préfixe `dsoxlab-` et du retrait en
`finally`. Ce script vérifie qu'elle a été tenue.

## Ce qu'il ne fait pas

Il ne réimplémente aucune commande de dsoxlab : il les enchaîne. Un défaut du
moteur se corrige dans `~/Projets/dsoxlab`, jamais ici.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

# Le module partagé, IDENTIQUE dans les douze catalogues : il lit
# `dsoxlab check --json` et en tire un verdict à trois issues. `scripts/` est
# sur `sys.path` parce que c'est le répertoire de ce fichier.
import verdict_check
import yaml
from lecture_solution import est_chiffree, lire_solution
from lecture_yaml import lire_yaml

RACINE = Path(__file__).resolve().parent.parent
LABS = RACINE / "labs"
RESULTATS = RACINE / "validation-labs.json"
CACHE = Path.home() / ".cache" / "dsoxlab" / RACINE.name


class Echec(Exception):
    """Une étape du cycle a échoué : le lab est ROUGE, et on dit pourquoi."""


def commande(
    args: list[str], journal, timeout: int, cwd: Path | None = None, entree: str | None = None
) -> subprocess.CompletedProcess[str]:
    journal.write(f"\n$ {' '.join(args)}\n")
    journal.flush()
    env = dict(os.environ, LAB_HOME=str(RACINE))
    try:
        # check=False : c'est l'appelant qui juge le code de retour, et une
        # exception ici perdrait la sortie déjà journalisée.
        res = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            stdin=subprocess.DEVNULL if entree is None else None,
            input=entree,
            cwd=cwd or RACINE,
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        journal.write(f"DÉLAI DÉPASSÉ après {timeout}s\n")
        raise Echec(f"délai de {timeout}s dépassé : {' '.join(args[:3])}") from e
    except FileNotFoundError as e:
        # Une trace Python de quinze lignes pour dire qu'un binaire manque
        # n'apprend rien. Mesuré sur le catalogue GitHub Actions.
        journal.write(f"OUTIL ABSENT : {args[0]}\n")
        raise Echec(
            f"`{args[0]}` n'est pas sur le PATH. dsoxlab est un OUTIL, pas une "
            "dépendance de ce dépôt : `uv tool install dsoxlab`."
        ) from e
    journal.write(res.stdout)
    journal.write(res.stderr)
    return res


def dsoxlab(sous_commande: list[str], journal, timeout: int) -> subprocess.CompletedProcess[str]:
    return commande(["dsoxlab", *sous_commande], journal, timeout)


def docker(args: list[str], timeout: int = 60) -> list[str]:
    """Une liste de noms rendue par Docker, ou une liste vide s'il se tait."""
    res = subprocess.run(
        ["docker", *args], capture_output=True, text=True, timeout=timeout, check=False
    )
    if res.returncode != 0:
        return []
    return [ligne.strip() for ligne in res.stdout.splitlines() if ligne.strip()]


def photographier(lab: Path, journal) -> dict:
    """L'état du moteur et du répertoire de travail, avant et après.

    Les images sont relevées par leur `repository:tag` et non par leur
    identifiant : une image reconstruite à l'identique change d'identifiant si
    une couche change, ce qui ferait croire à un écart là où il n'y en a pas.
    """
    etat = {
        "images": sorted(docker(["image", "ls", "--format", "{{.Repository}}:{{.Tag}}"])),
        "conteneurs": sorted(docker(["ps", "-a", "--format", "{{.Names}}"])),
        "volumes": sorted(docker(["volume", "ls", "--format", "{{.Name}}"])),
        "reseaux": sorted(docker(["network", "ls", "--format", "{{.Name}}"])),
        "workdir_present": workdir(lab).is_dir(),
    }
    journal.write(
        f"\n# photographie : {len(etat['images'])} image(s), "
        f"{len(etat['conteneurs'])} conteneur(s), {len(etat['volumes'])} volume(s), "
        f"{len(etat['reseaux'])} réseau(x)\n"
    )
    journal.flush()
    return etat


def ecarts(avant: dict, apres: dict) -> list[str]:
    """Ce que le lab a laissé derrière lui, nommé objet par objet."""
    trouves = []
    for categorie in ("images", "conteneurs", "volumes", "reseaux"):
        restes = sorted(set(apres[categorie]) - set(avant[categorie]))
        trouves += [f"{categorie[:-1]} laissé : {nom}" for nom in restes]
    if apres["workdir_present"]:
        trouves.append("le répertoire de travail existe encore après `clean`")
    return trouves


def workdir(lab: Path) -> Path:
    d = yaml.safe_load((lab / "lab.yaml").read_text(encoding="utf-8")) or {}
    rel = ((d.get("runtime") or {}).get("workdir")) or "challenge/work"
    return lab / rel


def check(lab_id: str, journal) -> dict:
    """Le `check` du lab, lu dans le CONTRAT et non dans l'encadré du terminal.

    `verdict_check.lire` rend `status`, qui est le seul champ à pouvoir servir
    de verdict : `ok` dit « aucun test n'a échoué », ce qui est vrai d'une suite
    entièrement skippée, et `score` vaut alors 0 sans que rien ait tourné.
    """
    res = dsoxlab(["check", lab_id, "--json"], journal, 1800)
    try:
        return verdict_check.lire(res.stdout)
    except verdict_check.JsonIllisible as erreur:
        raise Echec(str(erreur)) from erreur


def python_dsoxlab() -> str:
    """Le Python qui porte pytest et testinfra : celui livré avec `dsoxlab`.

    NI `sys.executable`, NI le python de `mise` : aucun des deux ne porte
    pytest. L'erreur est silencieuse et coûteuse, parce qu'elle ressemble à un
    échec du lab. Mesurée deux fois le 2026-10-28, sur ce catalogue et sur
    `proxmox-dsoxlab-training` : « No module named pytest », puis un verdict
    qui accuse la solution.

    C'est le calcul que font les validateurs des dépôts qui gèrent déjà des VM.
    """
    binaire = shutil.which("dsoxlab")
    if binaire:
        candidat = Path(binaire).resolve().parent / "python"
        if candidat.is_file():
            return str(candidat)
    return sys.executable


def poser_solution(lab: Path, journal) -> None:
    """Pose `solution/` par-dessus le répertoire de travail, fichier par fichier.

    La copie descend dans les SOUS-RÉPERTOIRES, et c'est le piège : un
    `Dockerfile` est à la racine, mais un `compose.yaml` et ses secrets ne le
    sont pas. Le catalogue Terraform a perdu une campagne entière sur ce défaut
    exact, quinze labs rendant 0 puis 0 parce que la pose était à plat.
    """
    # UN LAB VM NE SE RÉSOUT PAS EN COPIANT DES FICHIERS EN LOCAL.
    #
    # La suite de cette fonction pose `solution/` dans le workdir du lab :
    # c'est le geste d'un atelier `shell`, où l'apprenant travaille sur la
    # machine qui lance les tests. Un lab `vm` travaille sur une MACHINE
    # DISTANTE, et sa solution est un playbook à y jouer.
    #
    # Ce cas est déjà traité, et une seule fois : la fixture autouse
    # `_apply_lab_state` du conftest joue `solution/<lab>/solution.yaml` par
    # ansible-runner, déchiffre le vault au passage, et ne fait rien quand
    # `LAB_NO_REPLAY=1` est posé. On lui délègue donc, au lieu d'écrire ici un
    # second mécanisme qui dériverait du premier.
    #
    # C'est ce que fait `valider-labs.py` des dépôts qui gèrent déjà des VM :
    # ils lancent la suite SANS `LAB_NO_REPLAY`, et le `check` qui suit fait
    # foi. Ajouté le 2026-10-28, quand le premier lab VM de ce catalogue a
    # rendu 0/100 après sa solution alors que le lab était bon.
    rel = lab.relative_to(RACINE / "labs")
    if (lire_yaml(lab / "lab.yaml") or {}).get("runtime", {}).get("type") == "vm":
        playbook = RACINE / "solution" / rel / "solution.yaml"
        if not playbook.is_file():
            raise Echec(f"lab vm sans solution/{rel}/solution.yaml : rien à jouer sur la machine")
        journal.write(f"\n# solution vm déléguée au conftest : {playbook.relative_to(RACINE)}\n")
        journal.flush()
        env = {k: v for k, v in os.environ.items() if k not in ("LAB_NO_REPLAY", "VIRTUAL_ENV")}
        proc = subprocess.run(
            [python_dsoxlab(), "-m", "pytest", str(lab / "challenge" / "tests"),
             "-q", "-p", "no:cacheprovider", "--no-header"],
            cwd=RACINE, env=env, capture_output=True, text=True, timeout=1800, check=False,
        )
        sortie = proc.stdout + proc.stderr
        journal.write(sortie)
        journal.flush()
        # ON LIT LE CODE DE RETOUR, PAS SEULEMENT UN MOTIF.
        #
        # Une première version ne cherchait que « solution.yaml a échoué » dans
        # la sortie. Le pytest avait alors rendu « No module named pytest » et
        # ce motif était absent : la pose n'avait pas eu lieu, et la fonction
        # rendait la main sans rien dire. Le cycle concluait « la solution
        # laisse 4 tests en échec », ce qui accusait le lab au lieu du harnais.
        #
        # Un code de retour non nul couvre les deux cas : la solution qui
        # échoue, et le harnais qui n'a pas démarré.
        if proc.returncode != 0:
            raise Echec(f"la solution n'a pas pu être posée (rc={proc.returncode}) : {sortie[-400:]}")
        return

    source = lab / "solution"
    if not source.is_dir():
        raise Echec(
            "le lab n'a pas de répertoire `solution/` : rien à poser, et le "
            "cycle ne peut pas prouver que les tests passent le travail fait"
        )
    fichiers = [f for f in sorted(source.rglob("*")) if f.is_file()]
    if not fichiers:
        raise Echec("le répertoire `solution/` est vide")

    cible = workdir(lab)
    for fichier in fichiers:
        destination = cible / fichier.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if est_chiffree(fichier):
            # Un fichier chiffré se pose DÉCHIFFRÉ : `docker build` lirait
            # sinon « $ANSIBLE_VAULT;1.1;AES256 » comme une instruction, et
            # l'erreur parlerait de syntaxe Dockerfile, pas de chiffrement.
            destination.write_text(lire_solution(fichier), encoding="utf-8")
            shutil.copystat(fichier, destination)
        else:
            shutil.copy2(fichier, destination)

    journal.write(f"\n# solution posée : {len(fichiers)} fichier(s)\n")
    for fichier in fichiers:
        journal.write(f"  {fichier.relative_to(source)}\n")
    journal.flush()


def valider(lab: Path, rejeu: bool = True) -> dict:
    ident = lab.name
    debut = time.time()
    etapes: list[str] = []
    resultat: dict = {
        "id": ident,
        "date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "docker": (docker(["version", "--format", "{{.Server.Version}}"]) or ["inconnue"])[0],
        "store": "containerd" if any(
            "containerd.snapshotter" in s for s in docker(["info", "--format", "{{.DriverStatus}}"])
        ) else "classic",
    }

    def dire(message: str) -> None:
        etapes.append(message)
        print(f"    {message}", flush=True)

    CACHE.mkdir(parents=True, exist_ok=True)
    journal_path = CACHE / f"validation-{ident}.log"
    # Le chemin est enregistré RELATIF au cache de l'utilisateur :
    # `validation-labs.json` est versionné et lu par d'autres.
    resultat["journal"] = str(journal_path.relative_to(Path.home()))

    with journal_path.open("w", encoding="utf-8") as journal:
        try:
            avant = photographier(lab, journal)
            if avant["workdir_present"]:
                raise Echec(
                    "le répertoire de travail existe déjà : lancez "
                    f"`dsoxlab clean {ident}` avant de valider"
                )
            dire(
                f"état photographié : {len(avant['images'])} image(s), "
                f"{len(avant['conteneurs'])} conteneur(s), {len(avant['volumes'])} volume(s)"
            )

            res = dsoxlab(["run", ident], journal, 300)
            if res.returncode != 0:
                raise Echec(
                    f"dsoxlab run a échoué (rc={res.returncode}) : "
                    f"{(res.stdout + res.stderr).strip()[-400:]}"
                )
            resultat["avant"] = check(ident, journal)
            dire(f"avant le travail : {resultat['avant']['passed']}/{resultat['avant']['total']}")

            poser_solution(lab, journal)
            resultat["apres"] = check(ident, journal)
            dire(f"après la solution : {resultat['apres']['passed']}/{resultat['apres']['total']}")

            if rejeu:
                dsoxlab(["clean", ident, "--yes"], journal, 300)
                res = dsoxlab(["run", ident], journal, 300)
                if res.returncode != 0:
                    raise Echec(
                        f"le second `run` a échoué (rc={res.returncode}) : le point de "
                        f"départ ne se rejoue pas. {(res.stdout + res.stderr).strip()[-300:]}"
                    )
                resultat["rejeu"] = check(ident, journal)
                dire(f"après clean et run : {resultat['rejeu']['passed']}/{resultat['rejeu']['total']}")

            res = dsoxlab(["clean", ident, "--yes"], journal, 300)
            if res.returncode != 0:
                raise Echec(f"dsoxlab clean a échoué (rc={res.returncode})")

            resultat["ecarts"] = ecarts(avant, photographier(lab, journal))
            dire(
                "moteur rendu intact"
                if not resultat["ecarts"]
                else f"{len(resultat['ecarts'])} écart(s) après clean"
            )
        except Echec as e:
            resultat["erreur"] = str(e)
            dire(f"ÉCHEC : {e}")
            # On tente quand même de rendre la machine.
            with contextlib.suppress(Echec):
                dsoxlab(["clean", ident, "--yes"], journal, 300)

    resultat["duree_s"] = round(time.time() - debut)
    resultat["verdict"] = verdict(resultat, rejeu)
    resultat["etapes"] = etapes
    return resultat


def verdict(r: dict, rejeu: bool) -> str:
    if "erreur" in r:
        return "ROUGE"
    # Trois issues, pas deux. Une exécution qui n'a RIEN mesuré n'accuse pas le
    # lab : elle dit que le poste n'était pas prêt (répertoire de travail non
    # préparé, service arrêté, machine injoignable). La peindre en rouge
    # enverrait corriger un lab qui n'a jamais tourné ; la peindre en vert
    # serait pire. Elle reste donc à mesurer.
    etapes = [("avant le travail", r["avant"]), ("après la solution", r["apres"])]
    if "rejeu" in r:
        # Le rejeu entrait dans le jugement par `passed != 0`, qui est FAUX
        # quand rien n'a tourné : un second `run` dont la suite skippe passait
        # donc pour un point de départ sain.
        etapes.append(("après clean et run", r["rejeu"]))
    for quand, c in etapes:
        if not verdict_check.a_mesure(c):
            r["raisons"] = [f"{quand}, {verdict_check.pourquoi_rien_mesure(c)}"]
            return verdict_check.SKIP
    raisons = []
    if r["avant"]["passed"] != 0:
        raisons.append(
            f"{r['avant']['passed']} test(s) passent avant le travail : "
            f"{', '.join(set(r['avant'].get('echecs', [])) ^ set()) or 'voir le journal'}"
        )
    if r["apres"]["passed"] != r["apres"]["total"]:
        restes = r["apres"]["echecs"]
        detail = f" : {', '.join(restes)}" if restes else ""
        raisons.append(
            f"la solution laisse {r['apres']['total'] - r['apres']['passed']} "
            f"test(s) en échec{detail}"
        )
    if rejeu and r.get("rejeu", {}).get("passed"):
        raisons.append(f"{r['rejeu']['passed']} test(s) passent après clean et run")
    if r.get("ecarts"):
        raisons.append("le moteur n'est pas rendu intact")
    r["raisons"] = raisons
    return "VALIDE" if not raisons else "ROUGE"


def relire() -> int:
    """Le verdict versionné couvre-t-il le catalogue, et est-il vert ?

    Vérifie DEUX choses, et la première est la moins évidente : qu'aucun lab
    n'a été ajouté sans être validé. Un fichier de verdicts tous verts qui
    ignore la moitié du catalogue passerait sans elle.
    """
    if not RESULTATS.is_file():
        print(f"{RESULTATS.name} est absent : aucun lab n'a jamais été validé.", file=sys.stderr)
        return 1

    verdicts = json.loads(RESULTATS.read_text(encoding="utf-8"))
    labs = sorted(p.parent.name for p in LABS.rglob("lab.yaml"))

    manquants = [nom for nom in labs if nom not in verdicts]
    if manquants:
        print(
            f"{len(manquants)} lab(s) sans verdict : {', '.join(manquants)}.\n"
            "Un lab livré sans validation ne prouve rien.",
            file=sys.stderr,
        )
        return 1

    # Trois issues, et deux conclusions bien distinctes : un ROUGE est un
    # défaut DU LAB, un SKIP est une mesure qui n'a pas eu lieu sur CE POSTE.
    # Les confondre enverrait corriger un lab qui n'a jamais tourné, et dire
    # « aucun ROUGE » d'un catalogue dont la moitié n'a pas été mesurée.
    rouges = [n for n in labs if verdicts[n].get("verdict") == verdict_check.ROUGE]
    skips = [n for n in labs if verdicts[n].get("verdict") == verdict_check.SKIP]
    inconnus = [n for n in labs
                if verdicts[n].get("verdict") not in
                (verdict_check.VALIDE, verdict_check.ROUGE, verdict_check.SKIP)]

    def _dire(noms: list[str], entete: str) -> None:
        if not noms:
            return
        print(entete, file=sys.stderr)
        for nom in noms:
            raisons = (verdicts[nom].get("raisons")
                       or [verdicts[nom].get("erreur", "raison non enregistrée")])
            print(f"  {nom} : {'; '.join(raisons)}", file=sys.stderr)

    _dire(rouges, f"{len(rouges)} lab(s) ROUGE :")
    _dire(inconnus, f"{len(inconnus)} lab(s) au verdict illisible :")
    _dire(skips, f"{len(skips)} lab(s) SKIP, à remesurer (le poste, pas le lab) :")
    if rouges or inconnus:
        return verdict_check.RC_UN_ROUGE
    if skips:
        # Un catalogue sans rouge n'est pas pour autant prouvé : ce code est
        # distinct pour qu'une construction automatisée ne confonde pas
        # « rien à réparer » avec « tout est mesuré ».
        return verdict_check.RC_UN_SKIP

    fantomes = sorted(set(verdicts) - set(labs))
    if fantomes:
        print(
            f"{RESULTATS.name} porte le verdict de lab(s) qui n'existent plus : "
            f"{', '.join(fantomes)}.",
            file=sys.stderr,
        )
        return 1

    print(f"{len(labs)} lab(s), tous VALIDE")
    return verdict_check.RC_TOUT_VALIDE


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--lab", action="append", help="ne jouer que ce lab (répétable)")
    ap.add_argument("--sans-rejeu", action="store_true", help="sauter l'étape clean, run, check")
    ap.add_argument(
        "--check",
        action="store_true",
        help="relire validation-labs.json sans rien rejouer : exit 0 si tout est VALIDE",
    )
    args = ap.parse_args()

    if args.check:
        return relire()

    labs = sorted(p.parent for p in LABS.rglob("lab.yaml"))
    if args.lab:
        inconnus = set(args.lab) - {p.name for p in labs}
        if inconnus:
            print(f"lab(s) inconnu(s) : {', '.join(sorted(inconnus))}", file=sys.stderr)
            return 2
        labs = [p for p in labs if p.name in args.lab]

    if not labs:
        print("aucun lab à valider", file=sys.stderr)
        return 2

    print(f"{len(labs)} lab(s) à éprouver dans les deux sens")
    anciens = json.loads(RESULTATS.read_text(encoding="utf-8")) if RESULTATS.is_file() else {}
    rouges = 0
    skips = 0
    for lab in labs:
        print(f"\n{lab.name}", flush=True)
        r = valider(lab, rejeu=not args.sans_rejeu)
        anciens[lab.name] = r
        RESULTATS.write_text(
            json.dumps(anciens, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if r["verdict"] != verdict_check.VALIDE:
            # Le SKIP est compté à part : il ne se répare pas, il se remesure.
            if r["verdict"] == verdict_check.SKIP:
                skips += 1
            else:
                rouges += 1
            for raison in r.get("raisons", []):
                print(f"    - {raison}")
            for e in r.get("ecarts", [])[:15]:
                print(f"    - {e}")
        print(f"    {r['verdict']} en {r['duree_s']} s")

    valides = len(labs) - rouges - skips
    print(f"\n{valides} valide(s), {rouges} rouge(s), {skips} à remesurer "
          f"sur {len(labs)} lab(s).")
    print(f"Détail : {RESULTATS}")
    if rouges:
        return verdict_check.RC_UN_ROUGE
    # Un catalogue sans rouge n'est pas prouvé pour autant : le code est
    # distinct pour qu'une construction automatisée ne confonde pas « rien à
    # réparer » avec « tout est mesuré ».
    return verdict_check.RC_UN_SKIP if skips else verdict_check.RC_TOUT_VALIDE


if __name__ == "__main__":
    sys.exit(main())
