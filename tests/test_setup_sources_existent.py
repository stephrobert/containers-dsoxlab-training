"""Chaque fichier qu'un setup copie sur la machine existe dans le lab.

Pourquoi ce test existe : la PR #101 (2026-11-23) a fondu les scenario.md dans
challenge/README.md, comme l'exige dsoxlab 0.9.9. Quarante-deux setups
copiaient encore scenario.md vers /opt/MISSION.md : `dsoxlab run` échouait sur
« Could not find or access 'scenario.md' ». Aucun contrôle ne l'a vu, parce que
la CI ne joue pas les setups et que `ansible-playbook --syntax-check` ne
cherche pas les fichiers. C'est un `dsoxlab run` réel qui l'a trouvé.

Ce test lit chaque `src:` des tâches `copy` et `template` d'un setup, et vérifie
que le fichier existe à côté du setup ou sous `files/`, là où Ansible le
cherche. La seule expression Jinja reconnue est celle du choix de langue
(`{{ '.fr' if ... else '' }}`) : le test vérifie ses deux issues. Un `src:`
portant une autre expression est ignoré, parce qu'il ne se résout pas sans
exécuter le playbook ; le test le dit au lieu de conclure.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parent.parent
LABS = RACINE / "labs"
LANGUE = re.compile(r"\{\{\s*'\.fr'\s+if\s+[^}]*else\s+''\s*\}\}")


def _sources(setup: Path) -> list[str]:
    """Les `src:` des tâches copy et template, au premier niveau de chaque play."""
    sources = []
    for play in yaml.safe_load(setup.read_text(encoding="utf-8")) or []:
        for tache in (play.get("tasks") or []) + (play.get("pre_tasks") or []):
            for module in ("ansible.builtin.copy", "copy", "ansible.builtin.template", "template"):
                params = tache.get(module)
                if (isinstance(params, dict) and isinstance(params.get("src"), str)
                        and not params.get("remote_src")):
                    sources.append(params["src"])
    return sources


SETUPS = sorted(LABS.glob("*/setup.yaml"))


def test_il_y_a_des_setups() -> None:
    """Garde-fou : un glob cassé rendrait la suite verte sans rien mesurer."""
    assert len(SETUPS) >= 50, f"{len(SETUPS)} setup(s) trouvés, le glob ne regarde plus au bon endroit"


@pytest.mark.parametrize("setup", SETUPS, ids=lambda p: p.parent.name)
def test_chaque_source_copiee_existe(setup: Path) -> None:
    lab = setup.parent
    manquants, ignores = [], []
    for src in _sources(setup):
        variantes = [LANGUE.sub(".fr", src), LANGUE.sub("", src)] if LANGUE.search(src) else [src]
        for chemin in variantes:
            if "{{" in chemin:
                ignores.append(chemin)
                continue
            if not ((lab / chemin).exists() or (lab / "files" / chemin).exists()):
                manquants.append(chemin)
    assert not manquants, (
        f"{lab.name}/setup.yaml copie des fichiers absents du lab : {manquants}.\n\n"
        "`dsoxlab run` échouerait sur « Could not find or access ». Si le fichier "
        "a été renommé ou fondu ailleurs (scenario.md dans challenge/README.md "
        "depuis dsoxlab 0.9.9), mettez à jour le src."
    )
