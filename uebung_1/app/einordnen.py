"""Teil D: Anfragen an den Campus-Assistenten strukturiert einordnen.

Das Modell soll aus einer Mail drei Dinge herauslesen: das Anliegen,
den Studiengang und eine Frist. Das Ergebnis verarbeitet ein Programm
weiter, es muss also immer die gleiche Form haben.

Aufruf:
    docker compose run --rm app einordnen.py
    docker compose run --rm app einordnen.py "Eure eigene Mail"

Eure Aufgaben stehen bei den TODO-Kommentaren.
"""

import json
import sys
from typing import Literal

from pydantic import BaseModel, ValidationError, field_validator

from llm import MODEL, client

SYSTEM_PROMPT = (
    "Du ordnest Mails von Studierenden an die HTWG Konstanz ein. "
    "Antworte ausschließlich mit JSON. "
    "anliegen ist pruefung, mensa, bibliothek oder sonstiges. "
    "studiengang ist das Kürzel (z. B. AIN, WIN, MSI) oder null. "
    "frist ist die Frist aus der Mail, so wie sie dort steht, oder null."
)
SYSTEM_PROMPT2 = """
Du ordnest Mails von Studierenden an die HTWG Konstanz ein. Antworte ausschließlich mit JSON
nach folgender Definition:
{
    "type": "object",
    "properties": {
        "anliegen": {
            "type": "string",
            "enum": [
                "pruefung",
                "mensa",
                "bibliothek",
                "sonstiges"
            ]
        },
        "studiengang": {
            "type": ["string", "null"]
        },
        "frist": {
            "type": ["string", "null"]
        }
    },
    "required": [
        "anliegen",
        "studiengang",
        "frist"
    ]
}
Antworte ausschließlich in folgendem JSON-Format:

{
    "anliegen": "pruefung",
    "studiengang": "AIN",
    "frist": null
}
"""


class Anfrage(BaseModel):
    anliegen: Literal["pruefung", "mensa", "bibliothek", "sonstiges"]
    studiengang: str | None
    frist: str | None
 

    @field_validator("studiengang", "frist", mode="before")
    @classmethod
    def leer_zu_none(cls, wert):
        if isinstance(wert, str):
            if wert.strip().lower() in ("null", "none", ""):
                return None

        return wert


    @field_validator("studiengang")
    @classmethod
    def studiengang_validieren(cls, wert):
        if wert is None:
            return None
    
        erlaubte_studiengaenge = {"AIN", "WIN", "MSI"}
    
        if wert.upper() not in erlaubte_studiengaenge:
            return None
    
        return wert.upper()

def schema_von(modell: type[BaseModel]) -> dict:
    """Verpackt das JSON-Schema einer Pydantic-Klasse für response_format."""
    return {
        "type": "json_schema",
        "json_schema": {
            "name": modell.__name__.lower(),
            "schema": modell.model_json_schema(),
        },
    }


def einordnen(mail: str, versuche: int = 3) -> Anfrage:
    """Fragt das Modell und gibt eine geprüfte Anfrage zurück."""
    nachricht = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": mail},
    ]
    # TODO 1: Ruft das Modell auf. Wählt eine passende temperature
    #         und übergebt response_format=schema_von(Anfrage).

    for i in range(versuche):
        antwort = client.chat.completions.create(
                model=MODEL,
                messages=nachricht,
                temperature=0,
                response_format=schema_von(Anfrage),
                )
        anfrageRaw = antwort.choices[0].message.content or ""

        #print("anfrageRaw")
        #print(anfrageRaw)
    # TODO 2: Prüft die Antwort mit Anfrage.model_validate_json(...).
        
        try:
            anfrage = Anfrage.model_validate_json(anfrageRaw)
            return anfrage
 # TODO 3: Schlägt die Prüfung fehl (ValidationError), versucht es
    #         erneut, höchstens `versuche`-mal. Gebt bei jedem
    #         Fehlversuch eine kurze Meldung aus. Klappt es gar
    #         nicht, werft einen RuntimeError.
        except ValidationError as fehler:
            print(f"Versuch {i + 1}/{versuche} fehlgeschlagen: {fehler}")
   

    raise RuntimeError(
        f"Nach {versuche} Versuchen keine gültige Antwort erhalten."
    )

def auswerten() -> None:
    """Ordnet alle Test-Mails ein und vergleicht mit dem Erwarteten."""
    with open("mails.json", encoding="utf-8") as f:
        faelle = json.load(f)
    richtig = 0
    for fall in faelle:
        ergebnis = einordnen(fall["mail"])
        # TODO 4: Vergleicht ergebnis mit fall["erwartet"]. Zählt einen
        #         Fall als richtig, wenn das Anliegen stimmt. Gebt für
        #         jeden Fall Mail, Ergebnis und ✓ oder ✗ aus.
        ist_richtig = ergebnis.anliegen == fall["erwartet"]["anliegen"]

        if ist_richtig:
            richtig += 1

        symbol = "✓" if ist_richtig else "✗"

        print(f"Mail: {fall['mail']}")
        print(f"Ergebnis: {ergebnis}")
        print(f"Erwartet: {fall['erwartet']}")
        print(f"Bewertung: {symbol}\n")

    print(f"\n{richtig} von {len(faelle)} Anliegen richtig ({MODEL})")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(einordnen(" ".join(sys.argv[1:])).model_dump_json(indent=2))
    else:
        auswerten()
