---
status: resolved
trigger: "deploy-harp.yml Store install 3: occ integrity:check-app findling -> InvalidSignatureException: Certificate is not valid. (run 34057433444, commit e5760b6, leg stable35/8.3/true)"
created: 2026-09-06
updated: 2026-09-06
---

## Current Focus

hypothesis: root.crt der Serverzweige endet ohne Zeilenumbruch, der angehaengte CI-Root verschmilzt mit der letzten END-Zeile, Checker::splitCerts liefert ihn nicht zurueck, damit fehlt der Vertrauensanker und validateSignature() ist false
test: lokale Reproduktion mit phpseclib 3.0.55 und der splitCerts-Regex gegen beide Varianten
expecting: broken -> validateSignature false, fixed -> true
next_action: erledigt, Fix committet

## Symptoms

expected: occ integrity:check-app findling antwortet 0 mit leerer Ausgabe
actual: antwortet 1, OC\IntegrityCheck\Exceptions\InvalidSignatureException: Certificate is not valid.
errors: InvalidSignatureException: Certificate is not valid.
reproduction: CI-Legs (stable33, 8.2, false), (stable34, 8.2, false), (stable35, 8.3, true), Schritt "Store install 3"
started: erster Livelauf des zweiten Installationswegs (Plan 06.1-12), Staging-Fehler davor in e5760b6 gefixt

## Eliminated

- hypothesis: der CA oder dem Blatt fehlen basicConstraints CA:TRUE oder keyUsage keyCertSign, die phpseclib verlangt
  evidence: phpseclib 3.0.55 X509::loadCA Zeilen 993-1013, beide Pruefbloecke sind auskommentiert; ausserdem setzt openssl req -x509 seit 3.0 basicConstraints critical CA:TRUE, nachgemessen an der mit denselben Befehlen erzeugten CA
  timestamp: 2026-09-06

- hypothesis: Checker::verify prueft zusaetzlich gegen resources/codesigning/intermediate.crl.pem und stolpert ueber Revocation
  evidence: Checker.php stable35 enthaelt keine einzige crl-Referenz, verify() geht von loadCA direkt auf validateSignature
  timestamp: 2026-09-06

- hypothesis: CN-Abgleich schlaegt fehl (Gross- und Kleinschreibung, CN ungleich App-ID)
  evidence: der CN-Vergleich steht in Checker.php Zeile 307, also NACH dem Wurf in Zeile 304, und wuerde eine andere Meldung erzeugen ("Certificate is not valid for required scope"); in der Reproduktion liefert getDN exakt "findling"
  timestamp: 2026-09-06

- hypothesis: es wird an die root.crt der falschen Instanz angehaengt
  evidence: das Blatt und die Signatur werden von derselben Instanz erzeugt und geprueft, die Reproduktion mit der echten root.crt reicht aus, um den Fehler zu erzeugen
  timestamp: 2026-09-06

## Evidence

- timestamp: 2026-09-06
  checked: Checker.php stable35 Zeile 295-304
  found: verify() laedt root.crt, splittet mit splitCerts und wirft "Certificate is not valid." genau dann, wenn loadX509 false ist ODER validateSignature() false ist
  implication: die Meldung sagt nichts ueber das Zertifikat selbst, sie sagt "keine passende CA gefunden"

- timestamp: 2026-09-06
  checked: resources/codesigning/root.crt auf stable33, stable34, stable35
  found: alle drei enden mit dem Byte 0x2d, also mit "-----END CERTIFICATE-----" ohne abschliessenden Zeilenumbruch
  implication: cat ci-root >> root.crt klebt END und BEGIN auf eine Zeile

- timestamp: 2026-09-06
  checked: CI-Log des Jobs 101551773881, Schritt Store install 1
  found: "root.crt carried 2 certificate(s) and now carries 3", Blatt subject=CN=findling issuer=CN=Findling CI Code Signing Root, "Successfully signed"
  implication: der bestehende Guard war blind, weil grep -c zeilenweise zaehlt und die verschmolzene Zeile den Treffer enthaelt

- timestamp: 2026-09-06
  checked: lokale Reproduktion, PKI mit den Workflow-Befehlen erzeugt, splitCerts-Regex in PHP
  found: broken.crt liefert 2 Teile (Nextcloud-Intermediate plus ein durch die zehn Bindestriche verstuemmeltes Stueck), fixed.crt liefert 3 Teile inklusive CN=Findling CI Code Signing Root
  implication: der CI-Root wird nie als CA geladen

- timestamp: 2026-09-06
  checked: voller Checker-Pfad mit phpseclib 3.0.55 (die in nextcloud/3rdparty stable35 gepinnte Version)
  found: broken.crt -> validateSignature() false -> "Certificate is not valid.", fixed.crt -> true, CN findling, RSA-PSS true
  implication: exakte Reproduktion der CI-Meldung, und der Fix macht die Kette gruen

- timestamp: 2026-09-06
  checked: phpseclib X509::validateSignatureCountable Zeile 1345-1370 und testForIntermediate Zeile 1230-1279
  found: ohne CA mit passendem Subject faellt der Pfad auf testForIntermediate, das ohne authorityInfoAccess sofort false liefert
  implication: false ohne jede Aussage ueber Gueltigkeit oder Datum, genau das Beobachtete

- timestamp: 2026-09-06
  checked: gepatchter Block gegen die echten root.crt von stable33, stable34, stable35
  found: dreimal "carried 2 ... now carries 3", danach splitCerts=3 und validateSignature=true auf allen drei
  implication: der Fix traegt auf allen drei Legs

- timestamp: 2026-09-06
  checked: Gegenprobe, geschaerfter Guard ohne den Newline-Schritt
  found: verankert 2 -> 2, unverankert 3, Guard schlaegt an mit exit 1
  implication: dieser Fehlermodus meldet sich kuenftig an der Quelle statt zwei Schritte spaeter

## Resolution

root_cause: resources/codesigning/root.crt endet in nextcloud/server auf allen drei geprueften Zweigen ohne abschliessenden Zeilenumbruch. Der Workflow haengt den Wegwerf-CA mit cat an, dadurch stehen "-----END CERTIFICATE-----" des zweiten Nextcloud-Zertifikats und "-----BEGIN CERTIFICATE-----" des CI-Roots auf einer Zeile. Checker::splitCerts (Checker.php Zeile 258-262) schluckt mit dem gierigen abschliessenden [\-]{3,} beide Bindestrichgruppen und findet danach kein drittes Zertifikat mehr, weil [\S\ ]+? keinen Zeilenumbruch ueberspringt. Der CI-Root wird also nie per loadCA geladen, das Blatt findet keine CA mit passendem Subject, validateSignature() liefert false und Checker.php Zeile 304 wirft "Certificate is not valid.".
fix: vor dem Anhaengen einen Zeilenumbruch setzen, falls das letzte Byte keiner ist; zusaetzlich den Zaehl-Guard auf '^-----BEGIN CERTIFICATE-----$' verankern, damit er die verschmolzene Zeile nicht mehr als drittes Zertifikat zaehlt
verification: lokal mit PHP 8.2 und phpseclib 3.0.55 gegen die echten root.crt von stable33, stable34, stable35 nachgestellt; vorher false, nachher true samt CN-Abgleich und RSA-PSS-Pruefung. Der CI-Lauf selbst steht aus.
files_changed: [".github/workflows/deploy-harp.yml"]
