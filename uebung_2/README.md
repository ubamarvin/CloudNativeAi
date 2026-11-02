# Übung 2 – Cloud-native AI

## Teil 1 – Prompts aus dem Code holen

### Aufgabe 1: Warum `replace()` statt `str.format()`?

`replace()` ersetzt gezielt `{eingabe}`. `str.format()` könnte geschweifte Klammern in JSON-Beispielen fälschlich als Platzhalter interpretieren.

### Aufgabe 2: Warum Prompt-Versionen nicht überschreiben?

Jede Version bleibt unverändert, damit Ergebnisse nachvollziehbar und vergleichbar bleiben. Beim Überschreiben wüssten wir nicht mehr, mit welchem Prompt die alten Messwerte entstanden sind.

### Aufgabe 3: Ergebnisse von Version 1

- **Anliegen richtig:** 13 von 16 (81,25 %)
- **Alle Felder richtig:** 8 von 16 (50 %)

Die Ergebnisse zeigen, dass das Modell die Kategorie des Anliegens meistens richtig erkennt. Bei der vollständigen Einordnung treten jedoch zusätzliche Fehler auf, beispielsweise bei Studiengang und Frist. Außerdem gab das Modell in einigen Fällen den Text "null" statt eines echten JSON-Nullwerts aus und ließ sich in der letzten Test-Mail durch eine manipulative Anweisung beeinflussen.

## Teil 2 – Die Einordnung verbessern und messen

### Aufgabe 1: Vergleich von Version 1 und Version 2

Modell: `llama3.2:3b`, 16 Test-Mails

| Prompt | Anliegen richtig | Alle Felder richtig | Eingabe-Tokens (Ø) | Dauer (Ø) |
|---|---|---|---|---|
| einordnen.v1 | 13/16 (81,25 %) | 8/16 (50 %) | 140 | 2,70 s |
| einordnen.v2 | 15/16 (93,75 %) | 11/16 (68,75 %) | 620 | 2,38 s |

**Auswertung:**

Version 2 hat die Ergebnisse verbessert. Die Anliegen-Erkennung stieg von 13 auf 15 richtige Antworten und die vollständige Einordnung von 8 auf 11.

Der ausführlichere Prompt benötigt jedoch mehr Eingabe-Tokens:

620 / 140 = **4,43**

Version 2 benötigt also etwa 4,43-mal so viele Eingabe-Tokens wie Version 1.

Die durchschnittliche Dauer sank von 2,70 s auf 2,38 s. Trotz des höheren Token-Verbrauchs war Version 2 in diesem Test etwas schneller.

### Aufgabe 2: Fehleranalyse von Version 2

Version 2 hat bei 5 von 16 Mails noch Fehler gemacht:

1. **Master MSI:** Das Modell gibt `"null"` statt JSON `null` zurück. Die Anweisung zur Verwendung echter Nullwerte wurde nicht zuverlässig befolgt.
2. **Mensa-Mail:** Das Datum `24.10.` wird nicht als Frist erkannt. Die Regel zur Fristerkennung ist nicht eindeutig genug.
3. **Exchange Student:** Das Modell schreibt `06.11.` statt `6 November`. Die Messung ist hier zu streng.
4. **Fernleihe:** Das Modell schreibt `03.11.` statt `3. November`. Auch hier ist die Messung zu streng.
5. **Prompt Injection:** Das Modell folgt einer gefälschten SYSTEM-Anweisung und gibt `HACKED` als Studiengang zurück.

**Verbesserung der Messung:**

Datumsangaben sollten vor dem Vergleich in ein einheitliches Format umgewandelt werden, beispielsweise `YYYY-MM-DD`, sofern das Jahr bekannt ist. Echte JSON-Nullwerte und Strings wie `"null"` müssen dagegen weiterhin unterschieden werden, da sie unterschiedliche Datentypen sind.

### Aufgabe 3: Prompt Injection

Die letzte Mail enthält eine gefälschte Systemanweisung, die das Modell dazu bringen soll, `anliegen` auf `pruefung` und `studiengang` auf `HACKED` zu setzen.

Obwohl Version 2 solche Anweisungen ignorieren soll, übernimmt das Modell den Angriff.

Ein Prompt allein schützt nicht zuverlässig vor Prompt Injection, da das Modell Anweisungen innerhalb der Mail trotzdem befolgen kann. Deshalb müssen die Ausgaben zusätzlich durch eine technische Validierung eingeschränkt werden.

### Aufgabe 4: Absicherung mit Pydantic

In `einordnen.py` wurde der Datentyp für `studiengang` geändert:

```python
studiengang: Literal["AIN", "WIN", "MSI"] | None
```

Dadurch sind nur noch die drei erlaubten Studiengänge oder `None` gültig.

**Ergebnis der erneuten Messung:**

Die Trefferquote von Version 2 blieb bei 15/16 richtigen Anliegen und 11/16 vollständig richtigen Einordnungen.

Bei der letzten Mail wurde statt `HACKED` nun `MSI` ausgegeben. Die Mail wurde also weiterhin falsch eingeordnet, da eigentlich `mensa` und `null` erwartet wurden.

**Erklärung:**

Pydantic verhindert, dass ungültige Studiengangswerte akzeptiert werden. Es verhindert jedoch nicht, dass das Modell einen gültigen, aber inhaltlich falschen Studiengang auswählt oder einer manipulierten Anweisung folgt.

Die Abwehr wirkt auf einer anderen Ebene als der Prompt: Der Prompt gibt dem Modell Anweisungen, während Pydantic die erlaubten Ausgabewerte technisch einschränkt.

### Aufgabe 5 (optional): Kompakter Prompt v3

Für Version 3 wurde der Prompt verkürzt, um den Token-Verbrauch zu reduzieren.

Modell: `llama3.2:3b`, 16 Test-Mails

| Prompt | Anliegen richtig | Alle Felder richtig | Eingabe-Tokens (Ø) | Dauer (Ø) |
|---|---|---|---|---|
| einordnen.v1 | 13/16 | 8/16 | 140 | 2,15 s |
| einordnen.v2 | 15/16 | 11/16 | 620 | 2,15 s |
| einordnen.v3 | 14/16 | 9/16 | 337 | 1,94 s |

**Auswertung:**

Version 3 benötigt gegenüber Version 2 etwa 45,6 % weniger Eingabe-Tokens und war im Test durchschnittlich 0,21 Sekunden schneller.

Allerdings sank die vollständige Trefferquote von 11/16 auf 9/16. Somit ist Version 3 effizienter, aber weniger genau als Version 2.

Das Ziel, mit weniger Tokens die gleiche Genauigkeit wie Version 2 zu erreichen, wurde nicht vollständig erreicht.


