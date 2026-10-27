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

