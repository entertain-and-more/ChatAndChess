# Portierungsplan ChatAndChess

Stand: 2026-05-27

## Ergebnis

Es gab bisher keinen eigenständigen Portierungsplan. Dieser Plan ordnet ChatAndChess nach Nutzer-Usecases, Plattform-Settings und der bestehenden `.SOFTWARE`-Release-Pipeline ein.

Kurzentscheidung: Die bestehende Vollversion bleibt eine Desktop-/CLI-App für Windows, macOS und Linux. Mobile Versionen werden gestrichen. Zwar gibt es auf Android und iOS technisch Terminal-Apps, aber das ist kein normaler Endnutzer-Usecase und würde das Produkt als mobile App sinnlos machen. Eine Companion-App zur Desktop-Version ist ebenfalls nicht der richtige Zuschnitt, weil die mobile Nutzung kein Datenbeschaffungs-Usecase für die Terminal-App ist.

## Bestehende Fähigkeiten

- Terminal-Schach mit lokalem Hotseat-Spiel für zwei Personen.
- Minimax-Bot mit einstellbarer Suchtiefe.
- Vollständige Schachregeln inklusive Rochade, En passant, Umwandlung, Schach, Matt und Patt.
- Trainings- und Hinweis-Modi mit Engine-Kandidaten.
- Eigenständiger Taktik-Analyzer über `chess_analyze.py`.
- Optionaler Claude-API-Modus über `ANTHROPIC_API_KEY`.
- Datei-basierte Claude-Code-Kommunikation über `chess_comm/*.json`.
- Windows-Starter und optionaler PyInstaller-Build.

## Usecases der ausgebauten Version

### Usecase-Setting 1: Lokales Desktop-/CLI-Schach

Nutzer: Entwickler, Power-User, LLM-Nutzer, Terminal-affine Spieler.

Usecases:

- Eine schnelle lokale Schachpartie ohne Konto, Server oder Browser starten.
- Gegen einen eingebauten Bot trainieren.
- Stellungen und Zugfolgen im Terminal analysieren.
- Claude Code oder Claude API als experimentellen Gegner einbinden.
- Schachlogik und KI-Zugwahl in Tests oder Agenten-Workflows reproduzierbar prüfen.

Plattformentscheidung: Windows, macOS und Linux erfüllen dasselbe Usecase-Setting. Daher sollte dieselbe Python-Codebasis als eigenständige Desktop-/CLI-App auf allen drei Desktop-Plattformen laufen. Windows bekommt weiter die stärkste Paketierung; macOS und Linux werden zunächst als Source-Smoke-Ziele geführt.

### Usecase-Setting 2: Schachdatei-Austausch

Nutzer: Desktop-Spieler, Entwickler, Nutzer anderer Schachtools.

Usecases:

- Eine Desktop-Partie exportieren und archivieren.
- Eine Stellung mit anderen Schachtools austauschen.
- Zuglisten für Analyse, Tests oder Dokumentation weitergeben.
- Eine Partie zwischen Windows, macOS und Linux über Dateiimport fortsetzen.

Plattformentscheidung: Dieses Setting bleibt desktopnah. Es rechtfertigt ein Exportformat, aber keine mobile App. Die Verbindung zu anderen Tools bleibt dateibasiert über `chatandchess-game-v1.json`, FEN oder PGN; direkte Synchronisierung ist kein Ziel.

### Usecase-Setting 3: Agenten-/LLM-Experiment

Nutzer: LLM-Agenten, Entwickler, Prompt-/Worker-Tests.

Usecases:

- Claude Code über Request-/Response-Dateien in eine Partie einbinden.
- Zugvorschläge, Engine-Hinweise und Worker-Zustände maschinenlesbar testen.
- Regressionsfälle für Rochade, En passant und legale Zuglisten reproduzieren.

Plattformentscheidung: Dieses Setting ist Desktop-/Automations-nah und braucht lokalen Dateizugriff. Mobile Plattformen sind dafür nicht geeignet.

## Plattformplan

| Plattform | Zielbild | Begründung | Status |
|---|---|---|---|
| Windows | Primäre Desktop-/CLI-App mit EXE, `START_CHESS.bat` und GitHub-Release | Bestehender Starter und Build sind vorhanden; Terminal-Usecase passt | Aktiv |
| macOS | Source-Smoke, später optional ZIP/DMG | Python-CLI sollte grundsätzlich laufen, Claude-Code-Dateipfad prüfen | Geplant |
| Linux | Source-Smoke, später optional Tarball/AppImage | Terminal-/CLI-Usecase passt gut; keine GUI-Abhängigkeiten | Geplant |
| Web/PWA | Kein Portierungsziel | Wäre ein neues grafisches Schachprodukt, nicht die Terminal-App | Gestrichen |
| Android | Kein Portierungsziel | Mobiles Terminal ist kein sinnvoller Endnutzer-Usecase | Gestrichen |
| iOS | Kein Portierungsziel | Mobiles Terminal ist kein sinnvoller Endnutzer-Usecase | Gestrichen |

## Nicht-Ziele

- Kein Microsoft-Store-Fokus ohne grafische Oberfläche. Die bestehende Einstufung als GitHub-only bleibt richtig.
- Keine mobilen Versionen der Terminal-App.
- Kein nativer Smartphone-Klon und keine PWA-Hülle für die Terminal-App.
- Keine direkte Cloud-Synchronisierung zwischen Desktop und Mobile.
- Kein Online-Multiplayer als Portierungsbedingung; der bestehende Aufgabenstand hat diesen Punkt bereits gestrichen.
- Keine öffentliche Speicherung von Partien, API-Schlüsseln oder Worker-Daten.

## Austauschformat

Für spätere Plattformwechsel reicht ein dateibasierter Austausch. Details stehen in `EXPORTFORMAT.md`.

Mindestlinie:

- `chatandchess-game-v1.json` für Partie, Zugliste, Stellung, Modus-Metadaten und optionale Analyzer-Hinweise.
- FEN für einzelne Stellungen.
- PGN für Standard-Schachpartien, sobald eine Exportfunktion ergänzt wird.

## Umsetzungsschritte

### P0: Desktop-Portabilität absichern

- Windows-Smoke dokumentieren: `python chess.py`, `python chess.py --worker`, `python chess_analyze.py`.
- macOS-Smoke auf Mac Studio oder macOS-Runner prüfen.
- Linux-Smoke in sauberer Umgebung prüfen.
- Pfad- und Encoding-Checks für `chess_comm/`, `chess_settings.json` und `CLAUDE_PROMPT.txt` auf allen Desktop-Plattformen durchführen.

### P1: Dateiaustausch vorbereiten

- Exportfunktion für `chatandchess-game-v1.json` planen und später testbar implementieren.
- FEN-Export für aktuelle Stellung ergänzen.
- PGN-Export für abgeschlossene Partien prüfen.

### P2: Mobile/Web bewusst nicht verfolgen

- Android, iOS und Web/PWA bleiben Nicht-Ziele für ChatAndChess.
- Falls später ein grafisches Browser-Schachspiel gewünscht wird, als eigenes Produkt neu entscheiden.
- Desktop-Worker- und Claude-Code-Integration nicht in Mobile-/Web-Hüllen ziehen.

### P3: Release-Paketierung

- GitHub-Release bleibt kanonischer Anker.
- Windows-EXE als Komfortartefakt führen.
- macOS/Linux erst nach erfolgreichen Smokes paketieren.
- Store-Kanäle nur neu bewerten, wenn eine grafische App-Linie entsteht.
