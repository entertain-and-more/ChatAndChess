# -*- coding: utf-8 -*-
"""Verhaltenstests Bugsweep 2026-06-28 – Spezialzüge.

Scope: Rochade, En-Passant, Bauernumwandlung, Matt/Patt-Erkennung.
Keine früheren Bugsweep-Läufe haben konkrete Stellungstests für diese
Regelkombinationen abgedeckt; diese Datei schließt die Lücke.

Getestete Konstellationen:
  BS28-1  En passant mit aufdeckendem horizontalem Schach → illegal
  BS28-2  En passant ohne aufdeckenden Schach → legal
  BS28-3  Rochade aus dem Schach → illegal
  BS28-4  Rochade durch bedrohtes Transitfeld → illegal
  BS28-5  Rochade, wenn König auf Zielfeld im Schach landet → illegal
  BS28-6  Rochade bei freier Bahn → legal (positiver Basisfall)
  BS28-7  Rochaderecht verloren nach Turm-Zug; Rückkehr stellt es NICHT wieder her
  BS28-8  Unterumwandlung zum Springer (weiß) → N, nicht Q
  BS28-9  Unterumwandlung zum Turm (schwarz) → r, nicht q
  BS28-10 Standardumwandlung ohne promo-Argument → Dame (Q)
  BS28-11 Patt wird korrekt als 1/2-1/2 erkannt (nicht als Matt)
  BS28-12 Rückreihenmatt wird korrekt als 0-1 erkannt
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import chess as c


def _leeres_brett():
    return [["." for _ in range(8)] for _ in range(8)]


# ---------------------------------------------------------------------------
# BS28-1 / BS28-2: En passant mit / ohne aufdeckenden Schach
# ---------------------------------------------------------------------------

def test_en_passant_aufdeckender_schach_illegal():
    """BS28-1: En-Passant-Schlag von f5 nach g6 deckt weißen König auf schwarzen Turm auf.

    Aufstellung Zeile 3 (Rang 5):
      a5 = schwarzer Turm (r), e5 = weißer König (K),
      f5 = weißer Bauer (P), g5 = schwarzer Bauer (p, soeben g7→g5 gezogen).
    En-Passant-Ziel: g6 = (2, 6).

    Nach f5xg6: schwarzer Bauer g5 fällt weg, weißer Bauer verlässt f5 →
    schwarzer Turm a5 greift weißen König auf e5 direkt an → Zug muss illegal sein.
    """
    board = _leeres_brett()
    board[3][0] = 'r'   # schwarzer Turm a5
    board[3][4] = 'K'   # weißer König e5
    board[3][5] = 'P'   # weißer Bauer f5
    board[3][6] = 'p'   # schwarzer Bauer g5 (für En-Passant)
    board[0][7] = 'k'   # schwarzer König h8

    ep = (2, 6)  # g6
    legal = c.get_legal_moves(board, True, ep, None)
    assert (3, 5, 2, 6) not in legal, (
        "En-Passant f5xg6 darf nicht legal sein: deckt König e5 auf schwarzen Turm a5 auf"
    )


def test_en_passant_kein_aufdeckender_schach_legal():
    """BS28-2: Gleicher En-Passant-Zug ist legal, wenn kein Turm den König bedroht.

    Identische Aufstellung wie BS28-1, aber ohne schwarzen Turm auf a5.
    Der Schlag f5xg6 darf dann in den legalen Zügen stehen.
    """
    board = _leeres_brett()
    board[3][4] = 'K'   # weißer König e5
    board[3][5] = 'P'   # weißer Bauer f5
    board[3][6] = 'p'   # schwarzer Bauer g5
    board[0][7] = 'k'   # schwarzer König h8

    ep = (2, 6)  # g6
    legal = c.get_legal_moves(board, True, ep, None)
    assert (3, 5, 2, 6) in legal, (
        "En-Passant f5xg6 muss legal sein, wenn kein aufdeckender Schach entsteht"
    )


# ---------------------------------------------------------------------------
# BS28-3: Rochade aus dem Schach verboten
# ---------------------------------------------------------------------------

def test_rochade_verboten_koenig_im_schach():
    """BS28-3: König steht im Schach → keine Rochade (weder Königs- noch Damenseite).

    Schwarzer Läufer auf b4 (4,1) greift e1 (7,4) diagonal an: b4-c3-d2-e1.
    Wege c3 und d2 sind frei.
    """
    board = _leeres_brett()
    board[7][4] = 'K'   # weißer König e1
    board[7][7] = 'R'   # weißer Turm h1
    board[4][1] = 'b'   # schwarzer Läufer b4 (greift e1 diagonal an)
    board[0][7] = 'k'   # schwarzer König h8

    cr = {"K", "Q"}
    legal = c.get_legal_moves(board, True, None, cr)

    assert c.in_check(board, True), (
        "Voraussetzung: weißer König muss im Schach stehen (Läufer b4→e1)"
    )
    assert (7, 4, 7, 6) not in legal, "Königsseiten-Rochade darf nicht aus dem Schach möglich sein"


# ---------------------------------------------------------------------------
# BS28-4: Rochade durch bedrohtes Transitfeld verboten
# ---------------------------------------------------------------------------

def test_rochade_verboten_transitfeld_bedroht():
    """BS28-4: Königsseiten-Rochade verboten, wenn f1 von schwarzem Turm bedroht wird.

    Schwarzer Turm f8 (0,5) greift f1 (7,5) an – das Transitfeld des Königs.
    König e1 steht selbst NICHT im Schach.
    """
    board = _leeres_brett()
    board[7][4] = 'K'   # weißer König e1
    board[7][7] = 'R'   # weißer Turm h1
    board[0][5] = 'r'   # schwarzer Turm f8 (bedroht f1 = Transitfeld)
    board[0][0] = 'k'   # schwarzer König a8

    cr = {"K"}
    legal = c.get_legal_moves(board, True, None, cr)

    assert not c.in_check(board, True), "König sollte NICHT im Schach stehen"
    assert (7, 4, 7, 6) not in legal, (
        "Rochade darf nicht möglich sein, wenn Transitfeld f1 bedroht ist"
    )


# ---------------------------------------------------------------------------
# BS28-5: Rochade, wenn König auf g1 im Schach landen würde
# ---------------------------------------------------------------------------

def test_rochade_verboten_zielfeld_bedroht():
    """BS28-5: Königsseiten-Rochade verboten, wenn König auf g1 im Schach stünde.

    Schwarzer Turm g8 (0,6) greift g1 (7,6) an – das Zielfeld des Königs.
    Abgefangen im castling-Check von get_raw_moves (is_square_attacked col 6).
    """
    board = _leeres_brett()
    board[7][4] = 'K'   # weißer König e1
    board[7][7] = 'R'   # weißer Turm h1
    board[0][6] = 'r'   # schwarzer Turm g8 (bedroht g1)
    board[0][0] = 'k'   # schwarzer König a8

    cr = {"K"}
    legal = c.get_legal_moves(board, True, None, cr)

    assert not c.in_check(board, True), "König sollte NICHT im Schach stehen"
    assert (7, 4, 7, 6) not in legal, (
        "Rochade darf nicht möglich sein, wenn König auf g1 im Schach stünde"
    )


# ---------------------------------------------------------------------------
# BS28-6: Rochade bei freier Bahn – positiver Basisfall
# ---------------------------------------------------------------------------

def test_rochade_erlaubt_bei_freier_bahn():
    """BS28-6: Königsseiten-Rochade muss erlaubt sein, wenn alle Bedingungen erfüllt sind."""
    board = _leeres_brett()
    board[7][4] = 'K'   # weißer König e1
    board[7][7] = 'R'   # weißer Turm h1
    board[0][7] = 'k'   # schwarzer König h8

    cr = {"K"}
    legal = c.get_legal_moves(board, True, None, cr)

    assert (7, 4, 7, 6) in legal, (
        "Königsseiten-Rochade muss bei freier, unbedrohter Bahn und vorhandenem Recht erlaubt sein"
    )


# ---------------------------------------------------------------------------
# BS28-7: Rochaderecht verloren nach Turm-Zug – auch nach Rückkehr
# ---------------------------------------------------------------------------

def test_rochaderecht_verloren_nach_turm_zug_und_rueckkehr():
    """BS28-7: Damenseiten-Rochaderecht bleibt verloren, wenn a1-Turm zieht und zurückkehrt.

    Laut Schachregeln geht das Rochaderecht dauerhaft verloren,
    sobald der entsprechende Turm gezogen hat – unabhängig davon,
    ob er anschließend auf sein Ausgangsfeld zurückkehrt.
    """
    cr = {"K", "Q"}

    # Weißer a1-Turm zieht nach a2
    c.update_castling_rights(cr, "R", 7, 0, 6, 0)
    assert "Q" not in cr, "Damenseiten-Rochaderecht muss nach Turm-Zug weg sein"
    assert "K" in cr, "Königsseiten-Rochaderecht darf durch a1-Turm-Zug nicht beeinflusst werden"

    # Turm kehrt von a2 nach a1 zurück → Recht bleibt verloren
    c.update_castling_rights(cr, "R", 6, 0, 7, 0)
    assert "Q" not in cr, (
        "Damenseiten-Rochaderecht darf nach Turm-Rückkehr NICHT wiederhergestellt werden"
    )


# ---------------------------------------------------------------------------
# BS28-8 / BS28-9 / BS28-10: Bauernumwandlung
# ---------------------------------------------------------------------------

def test_unterumwandlung_springer_weiss():
    """BS28-8: Weißer Bauer auf e7 → e8 mit promo='n' erzeugt weißen Springer (N)."""
    board = _leeres_brett()
    board[1][4] = 'P'   # weißer Bauer e7
    board[7][7] = 'K'   # weißer König h1
    board[0][0] = 'k'   # schwarzer König a8

    result = c.make_move(board, 1, 4, 0, 4, None, 'n')
    assert result[0][4] == 'N', (
        f"Unterumwandlung mit 'n' soll weißen Springer 'N' erzeugen, bekam '{result[0][4]}'"
    )


def test_unterumwandlung_turm_schwarz():
    """BS28-9: Schwarzer Bauer auf d2 → d1 mit promo='r' erzeugt schwarzen Turm (r)."""
    board = _leeres_brett()
    board[6][3] = 'p'   # schwarzer Bauer d2
    board[7][7] = 'K'   # weißer König h1
    board[0][0] = 'k'   # schwarzer König a8

    result = c.make_move(board, 6, 3, 7, 3, None, 'r')
    assert result[7][3] == 'r', (
        f"Unterumwandlung mit 'r' soll schwarzen Turm 'r' erzeugen, bekam '{result[7][3]}'"
    )


def test_standardumwandlung_ohne_promo_ergibt_dame():
    """BS28-10: make_move ohne promo-Argument wandelt Bauer standardmäßig in Dame um."""
    board = _leeres_brett()
    board[1][0] = 'P'   # weißer Bauer a7
    board[7][7] = 'K'   # weißer König h1
    board[0][7] = 'k'   # schwarzer König h8

    result = c.make_move(board, 1, 0, 0, 0, None, None)
    assert result[0][0] == 'Q', (
        f"Standardumwandlung (promo=None) soll 'Q' erzeugen, bekam '{result[0][0]}'"
    )


# ---------------------------------------------------------------------------
# BS28-11 / BS28-12: Patt vs. Matt
# ---------------------------------------------------------------------------

def test_patt_als_remis_erkannt():
    """BS28-11: Klassische Patt-Stellung → detect_game_result gibt 1/2-1/2.

    Aufstellung:
      Weißer König a1 (7,0), schwarze Dame c2 (6,2), schwarzer König e5 (3,4).

    Angriffsanalyse schwarze Dame c2 (6,2):
      - a2 (6,0): gleiche Zeile → bedroht
      - b2 (6,1): gleiche Zeile → bedroht
      - b1 (7,1): Diagonale SW (+1,−1) von c2 → bedroht
      - a1 (7,0): NICHT bedroht (kein gerades oder diagonales Linienverhältnis zu c2)
    König hat keine legalen Züge, steht aber NICHT im Schach → Patt.
    """
    board = _leeres_brett()
    board[7][0] = 'K'   # weißer König a1
    board[6][2] = 'q'   # schwarze Dame c2
    board[3][4] = 'k'   # schwarzer König e5

    assert not c.in_check(board, True), (
        "Voraussetzung: König darf für Patt-Test nicht im Schach stehen"
    )
    result = c.detect_game_result(board, True, set(), None)
    assert result == "1/2-1/2", f"Patt erwartet '1/2-1/2', got '{result}'"


def test_matt_als_niederlage_erkannt():
    """BS28-12: Rückreihenmatt → detect_game_result gibt 0-1 (Schwarz gewinnt).

    Aufstellung:
      Weißer König a1 (7,0).
      Schwarzer Turm a8 (0,0): bietet Schach (gleiche Spalte).
      Schwarzer Turm b8 (0,1): deckt b-Spalte ab und schützt a8-Turm.

    Fluchtfelder des Königs:
      - a2 (6,0): von Turm a8 (Spalte 0) bedroht
      - b1 (7,1): von Turm b8 (Spalte 1) bedroht
      - b2 (6,1): von Turm b8 (Spalte 1) bedroht
    König kann a8 nicht schlagen (7 Felder entfernt).
    → Kein Ausweg: Matt.
    """
    board = _leeres_brett()
    board[7][0] = 'K'   # weißer König a1
    board[0][0] = 'r'   # schwarzer Turm a8 (Schachgebot)
    board[0][1] = 'r'   # schwarzer Turm b8 (deckt b-Spalte + schützt a8)
    board[3][4] = 'k'   # schwarzer König e5

    assert c.in_check(board, True), (
        "Voraussetzung: König muss im Schach stehen (Matt-Test)"
    )
    result = c.detect_game_result(board, True, set(), None)
    assert result == "0-1", f"Matt erwartet '0-1', got '{result}'"
