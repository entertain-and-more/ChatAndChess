# Exportformat ChatAndChess

Stand: 2026-05-27

Dieses Dokument beschreibt den geplanten dateibasierten Austausch für Desktop-Plattformen und andere Schachtools. Es ist bewusst ein Planungsdokument; die aktuelle App implementiert dieses Exportformat noch nicht vollständig.

## Ziele

- Partien zwischen Windows, macOS und Linux über Dateien austauschbar machen.
- Keine direkte Synchronisierung und kein Cloud-Zwang.
- Schachstandardformate nutzen, wo sie passen.
- Claude-Code-Worker-Daten nicht unredigiert als öffentliches Austauschformat behandeln.

## Formate

### `chatandchess-game-v1.json`

Empfohlenes App-eigenes Format für vollständige lokale Partien.

```json
{
  "schema": "chatandchess-game-v1",
  "app": "ChatAndChess",
  "created_at": "2026-05-27T00:00:00Z",
  "position": {
    "fen": "startpos",
    "side_to_move": "white",
    "castling_rights": "KQkq",
    "en_passant": null
  },
  "moves": [
    {"uci": "e2e4", "san": null, "by": "white"}
  ],
  "mode": {
    "kind": "local|bot|claude_api|claude_code",
    "bot_depth": 3,
    "hints_enabled": false
  },
  "notes": []
}
```

Regeln:

- `schema` ist Pflicht und bleibt stabil versioniert.
- `moves[].uci` ist Pflicht, weil die aktuelle App UCI-Notation nutzt.
- `fen` sollte gesetzt werden, sobald FEN-Export implementiert ist.
- API-Schlüssel, lokale Pfade, Prompts und vollständige Claude-Antworten gehören nicht in dieses Format.

### FEN

Für einzelne Stellungen ist FEN das bevorzugte Minimalformat. Es eignet sich für Web-Viewer, mobile Analyse und Austausch mit anderen Schachtools.

### PGN

PGN ist das bevorzugte Standardformat für abgeschlossene Partien. Sobald ChatAndChess PGN schreibt, sollte PGN für allgemeine Schachsoftware und `chatandchess-game-v1.json` für App-spezifische Metadaten parallel angeboten werden.

## Plattformbezug

- Desktop-Vollversion: liest und schreibt langfristig `chatandchess-game-v1.json`, FEN und PGN.
- Web/PWA: kein Ziel für ChatAndChess; ein grafisches Browser-Schachspiel wäre ein eigenes Produkt.
- Android/iOS: kein Ziel, weil ein mobiles Terminal kein sinnvoller Endnutzer-Usecase ist.
- Keine direkte Synchronisierung zwischen Plattformen.
