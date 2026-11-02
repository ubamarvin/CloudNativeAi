"""Anfragen an den Campus-Assistenten strukturiert einordnen.

Wie in Übung 1, mit einem Unterschied: Der Prompt steht nicht mehr im
Code, sondern in einer versionierten Datei unter prompts/.

Aufruf:
    docker compose run --rm app einordnen.py
    docker compose run --rm app einordnen.py --prompt prompts/einordnen.v2.yaml
    docker compose run --rm app einordnen.py "Eure eigene Mail"
"""

import argparse
import json
import time
from typing import Literal

from pydantic import BaseModel, ValidationError, field_validator

from llm import MODEL, client
from prompts import Prompt, lade

STANDARD_PROMPT = "prompts/einordnen.v1.yaml"


class Anfrage(BaseModel):
    anliegen: Literal["pruefung", "mensa", "bibliothek", "sonstiges"]
    studiengang: Literal["AIN", "WIN", "MSI"] | None
    frist: str | None

    ## @field_validator("studiengang", "frist", mode="before")
    ## @classmethod
    ## def leer_zu_none(cls, wert):
    ##     if isinstance(wert, str):
    ##         if wert.strip().lower() in ("null", "none", ""):
    ##             return None
    ##     return wert
    ## @field_validator("studiengang")
    ## @classmethod
    ## def studiengang_validieren(cls, wert):
    ##     if wert is None:
    ##         return None
    ## 
    ##     erlaubte_studiengaenge = {"AIN", "WIN", "MSI"}
    ## 
    ##     if wert.upper() not in erlaubte_studiengaenge:
    ##         return None
    ## 
    ##     return wert.upper()


def schema_von(modell: type[BaseModel]) -> dict:
    """Verpackt das JSON-Schema einer Pydantic-Klasse für response_format."""
    return {
        "type": "json_schema",
        "json_schema": {
            "name": modell.__name__.lower(),
            "schema": modell.model_json_schema(),
        },
    }


def einordnen(
    mail: str, prompt: Prompt, versuche: int = 3, protokoll: list | None = None
) -> Anfrage:
    """Fragt das Modell und gibt eine geprüfte Anfrage zurück.

    Wer eine Liste als protokoll übergibt, bekommt pro Aufruf ein Paar
    (Eingabe-Tokens, Sekunden) angehängt. vergleich.py nutzt das.
    """
    ### range(start, stop, step)
    for versuch in range(1, versuche + 1):
        start = time.perf_counter()
        antwort = client.chat.completions.create(
            model=MODEL,
            temperature=prompt.temperature,
            messages=prompt.nachrichten(mail),
            response_format=schema_von(Anfrage),
        )
        if protokoll is not None:
            protokoll.append(
                (antwort.usage.prompt_tokens, time.perf_counter() - start)
            )
        text = antwort.choices[0].message.content or ""
        try:
            return Anfrage.model_validate_json(text)
        except ValidationError as fehler:
            print(f"  Versuch {versuch} ungültig: {fehler.error_count()} Fehler")
    raise RuntimeError(f"Nach {versuche} Versuchen keine gültige Antwort")


def felder_richtig(ergebnis: Anfrage, erwartet: dict) -> dict[str, bool]:
    """Vergleicht jedes Feld mit dem erwarteten Wert.

    Anliegen und Studiengang müssen exakt stimmen. Eine Frist zählt als
    richtig, wenn die erwartete Frist im Ergebnis enthalten ist:
    "Freitag, 16.10." passt also zu "16.10.".
    """
    ## ternary expression... wert_wenn_wahr if bedingung else wert_wenn_falsch, so hässlich
    frist_ok = (
        ergebnis.frist is None
        if erwartet["frist"] is None
        else erwartet["frist"].lower() in (ergebnis.frist or "").lower()
    )
    return {
        "anliegen": ergebnis.anliegen == erwartet["anliegen"],
        "studiengang": ergebnis.studiengang == erwartet["studiengang"],
        "frist": frist_ok,
    }


def auswerten(prompt: Prompt) -> None:
    """Ordnet alle Test-Mails ein und vergleicht mit dem Erwarteten."""
    with open("mails.json", encoding="utf-8") as f:
        faelle = json.load(f)
    # chained assignment
    # gleichwertig zu:
    # anliegen_ok = 0
    # alles_ok = 0
    anliegen_ok = alles_ok = 0
    for fall in faelle:
        ergebnis = einordnen(fall["mail"], prompt)
        ok = felder_richtig(ergebnis, fall["erwartet"])
        ## python behandelt boolesche Werte bei arithmetischen Operationen wie Zahlen.
        anliegen_ok += ok["anliegen"]
        ## all prüft ob alle werte true sind
        alles_ok += all(ok.values())
        zeichen = "".join("✓" if v else "✗" for v in ok.values())
        print(f"{zeichen}  {fall['mail'][:70]}")
        print(f"     {ergebnis.model_dump()}")
        print(f"     {fall["erwartet"]}")
    n = len(faelle)
    print(f"\n{prompt.kennung} mit {MODEL}:")
    print(f"  Anliegen richtig:   {anliegen_ok} von {n}")
    print(f"  Alle Felder richtig: {alles_ok} von {n}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    #positions Argument
    parser.add_argument("mail", nargs="*", help="eigene Mail statt mails.json")
    #optionales Argument
    parser.add_argument("--prompt", default=STANDARD_PROMPT)
    # ab hier werden Kommandozeilen argumente eingelsen
    args = parser.parse_args()
    prompt = lade(args.prompt)
    if args.mail:
        print(einordnen(" ".join(args.mail), prompt).model_dump_json(indent=2))
    else:
        auswerten(prompt)
