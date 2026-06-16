# Tetris in Python

Ein Vollbild-Tetris-Spiel mit `pygame`.

## Start

```bash
python -m pip install -r requirements.txt
python tetris.py
```

## Regeln

- Das Spielfeld wird im Vollbild angezeigt.
- Es gibt fünf Blockfarben.
- Eine vollständig gefüllte Zeile bringt 1 Punkt.
- Eine vollständig gefüllte Zeile mit nur einer Farbe bringt zusätzlich 5 Punkte.
- Verschwinden mehrere Zeilen gleichzeitig, gibt es zusätzlich `2^n` Punkte.
- Während des Spiels läuft eine generierte Hintergrundmelodie.
- Beim Verschwinden von Zeilen wird ein kurzes "Zack"-Geräusch abgespielt.
- Nach Spielende wird der Endstand angezeigt.

## Steuerung

- Pfeil links/rechts: Block bewegen
- Pfeil hoch: Block drehen
- Pfeil runter: schneller fallen
- Leertaste: sofort fallen lassen
- ESC: beenden
