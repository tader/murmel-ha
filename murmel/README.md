# Gebruik

Zie de [installatiestappen](https://github.com/tader/murmel-ha#installeren).

## Configuratie

- **hf_token**: Hugging Face-token met toegang tot het goedgekeurde model. Wordt niet gelogd.
- **model_revision**: standaard `main`. De eerste geslaagde download wordt vastgelegd in de persistente opslag en blijft bij herstarts ongewijzigd. Voor reproduceerbare installaties kun je een volledige modelcommit-SHA opgeven. Een wijziging downloadt die revisie bij de volgende start.
- **beam_size**: standaard 4; lagere waarden zijn sneller maar kunnen minder nauwkeurig zijn. Bereik 1–16.
- **cpu_threads**: 0 kiest automatisch maximaal vier threads, met waar mogelijk één kern vrij voor Home Assistant. Bereik 0–64.
- **hotwords**: lijst met namen of termen die Murmel bij voorkeur correct moet spellen. Bijvoorbeeld `["werkkamer", "schemerlamp"]`. Dit vervangt geen Assist-entiteitsconfiguratie.

**log_transcripts**: standaard uit. Schakel **Transcripties loggen** in om elke definitieve transcriptie op INFO-niveau in het applog te tonen, inclusief lege resultaten als `Transcriptie: '''. Regeleinden worden zichtbaar als `\n` weergegeven, zodat elke transcriptie één logregel blijft. Gesproken tekst kan persoonsgegevens bevatten en blijft volgens de logbewaring van Home Assistant beschikbaar. Schakel de optie na controle weer uit.

Herstart de app na een wijziging. De modelcache blijft behouden bij updates en herstarts. Backups sluiten de grote modelcache uit; na herstel is opnieuw een download nodig.

## Probleemoplossing

**Model laden mislukt:** controleer of de modelaanvraag is goedgekeurd, het token toegang heeft, de revisie bestaat, er voldoende opslag/geheugen is en Hugging Face bereikbaar is bij de eerste download. Token en foutdetails worden bewust niet naar logs geschreven.

**Geen discovery:** wacht tot het model geladen is. De app probeert Supervisor-discovery iedere 30 seconden opnieuw bij tijdelijke fouten. Je kunt ook handmatig Wyoming Protocol toevoegen met de interne hostname van de app en poort 10300.

**Traag:** probeer beam_size 1 of 2 en vergelijk met 4. Houd CPU-capaciteit vrij voor andere apps. Gelijktijdige verzoeken worden achter elkaar verwerkt.

**Geen tekst:** controleer de Nederlandse pipeline, microfoon, opnamevolume en spraakdetectie van Home Assistant. Stilte kan terecht een leeg transcript geven.

**Andere host:** schakel desgewenst de hostpoort in bij Netwerk. Gebruik uitsluitend een vertrouwd lokaal netwerk; Wyoming versleutelt of authenticeert de verbinding niet.
