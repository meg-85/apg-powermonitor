# APG Powermonitor für Home Assistant

Custom Integration, die die prognostizierten **Spitzenzeiten des österreichischen Stromnetzes** von Austrian Power Grid (APG) in Home Assistant bringt.

Spitzenzeiten sind Stunden, in denen die Residuallast (Verbrauch minus Einspeisung aus Wind, PV, Laufwasser und Biomasse) über 3.000 MW liegt. Die Prognose für die nächsten Tage wird von APG täglich am Vormittag aktualisiert. Stromsparen bzw. Verbrauch verschieben wirkt in diesen Stunden besonders.

## Entitäten

| Entität | Beschreibung |
|---|---|
| Binary Sensor **Spitzenzeit** | `on`, solange die aktuelle Stunde eine Spitzenstunde ist. Attribute: Beginn/Ende des aktuellen bzw. nächsten Spitzenblocks |
| Sensor **Spitzenzeit Beginn** / **Ende** | Zeitstempel des aktuellen bzw. nächsten Spitzenblocks |
| Sensor **Spitzenstunden heute** / **morgen** | Anzahl Spitzenstunden am jeweiligen Tag (Ortszeit) |
| Kalender **Spitzenzeiten** | Alle prognostizierten Spitzenblöcke als Termine |

Die API wird stündlich abgefragt; der Spitzenzeit-Status wird zusätzlich zu jeder vollen Stunde neu berechnet.

## Installation (HACS)

1. HACS → ⋮ → *Benutzerdefinierte Repositories* → URL dieses Repos, Typ *Integration*.
2. *APG Powermonitor* herunterladen, Home Assistant neu starten.
3. *Einstellungen → Geräte & Dienste → Integration hinzufügen → APG Powermonitor*.

## Datenquelle

`GET https://awareness.cloud.apg.at/api/v1/PeakHourStatus` (öffentlich, ohne API-Key). Die Antwort listet nur Stunden, deren Status vom `DefaultStatus` abweicht; diese werden als Spitzenstunden behandelt.

## Entwicklung

```bash
pip install aiohttp pytest
pytest -q
```

## Hinweis

Mehr zum Thema sichere Stromversorgung & Zahlen, Daten, Fakten zur Welt des Stroms bzw. zur Energiewende finden Sie unter [www.apg.at/powermonitor](https://www.apg.at/powermonitor/).

More about the security of supply & all data, facts and figures regarding the world of electricity and the energy transition can be found at [www.apg.at/powermonitor](https://www.apg.at/powermonitor/).

Inoffizielles Projekt, nicht mit APG verbunden.
