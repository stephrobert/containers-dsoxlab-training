# Offline vulnerability fixture provenance / Provenance des fixtures

Retrieved unchanged on 2026-11-01 at 11:37:02 UTC / téléchargés sans modification.

* Database: https://security-tracker.debian.org/tracker/debsecan/release/1/bookworm
  SHA-256 `177c30ea1177be8a77c1ee8705099919ce0906a29e68173e49244f863c4604ab`.
* Legacy: https://archive.debian.org/debian/pool/main/o/openssl/libssl1.1_1.1.1n-0+deb10u3_amd64.deb
  SHA-256 `92247c2c011ec4c01f5832a38de0ec1a9c2cfac5c6c5dc229e5a1ac81148854c`.
* Fixed: https://deb.debian.org/debian/pool/main/o/openssl/libssl3_3.0.17-1~deb12u2_amd64.deb
  SHA-256 `d97c29db9d9d1d125580be5d7b2e1170adb47e5a8b4481841718be95fa652e68`.
* Advisory: https://security-tracker.debian.org/tracker/CVE-2023-0286

Packages retain their upstream/Debian copyright notices under
`usr/share/doc/*/copyright`. The original compressed database is not filtered
or edited. debsecan 0.4.20.2 was actually executed against both genuine package
inventories during authoring: CVE-2023-0286 is reported for the legacy library,
not the fixed one. It is not a claim of zero vulnerabilities in the fixed image.

Les paquets conservent leurs licences dans `usr/share/doc/*/copyright`.
La base compressée originale n'est ni filtrée ni modifiée. debsecan 0.4.20.2
a réellement identifié CVE-2023-0286 dans l'ancien paquet et pas dans le
nouveau. Cela ne prétend pas que l'image corrigée n'a aucune vulnérabilité.
