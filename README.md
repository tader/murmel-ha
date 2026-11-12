# Murmel voor Home Assistant

Lokale Nederlandse spraakherkenning met **murmel-flash-m-v5**, via het Wyoming-protocol. Voor **Home Assistant OS op amd64** (Intel/AMD mini-pc of VM), met CPU-inferentie.

[Voeg de app-repository toe](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Ftader%2Fmurmel-ha)

## Installeren

1. Voeg `https://github.com/tader/murmel-ha` toe onder **Instellingen → Apps → App Store → Repositories**.
2. Installeer **Murmel**.
3. Vraag toegang aan tot [het model](https://huggingface.co/theaifactorybv/murmel-flash-m-v5), accepteer de licentie en wacht op goedkeuring.
4. Maak een Hugging Face-token met leestoegang tot dit model. Vul het uitsluitend in het wachtwoordveld **Hugging Face-token** van de appconfiguratie in.
5. Start de app. De eerste start downloadt circa 512 MB aan gewichten en kan enkele minuten duren.
6. Wacht op **Murmel gereed** in het logboek. Bevestig de ontdekte **Wyoming Protocol**-integratie onder **Instellingen → Apparaten & diensten**.
7. Kies **Murmel** als spraak-naar-tekstprovider in een Nederlandse Assist-pipeline.

Meer configuratie en probleemoplossing: [apphandleiding](murmel/DOCS.md).

## Werking en privacy

Audio gaat van Home Assistant via lokaal TCP naar deze app. Murmel wordt eenmaal geladen; na het einde van de opname volgt één definitief transcript. Home Assistant verzorgt het einde van de spraakopdracht. Audio en transcripties worden niet opgeslagen of gelogd door deze app. Home Assistant zelf kan pipelinegegevens bewaren.

Alleen de eerste modeldownload vereist Hugging Face. Daarna wordt het gecachete model rechtstreeks lokaal geladen, ook zonder netwerk. Tokens staan in de private appconfiguratie; behandel Home Assistant-backups als gevoelige gegevens. Modelgewichten worden niet in het containerimage meegeleverd.

## Grenzen

- amd64, CPU; geen ARM64- of GPU-ondersteuning in deze versie.
- Maximaal vier actieve opnamen, maximaal 60 seconden per opname, één inferentie tegelijk.
- Geen tussentijdse transcripties. Murmel herkent de taal zelf; de Assist-provider is gericht op Nederlands.
- Prestaties en geheugengebruik hangen af van de host. Een echte modeltest en meting op de doelhardware zijn nodig voordat je andere STT-diensten vervangt.
- Wyoming heeft geen authenticatie: de hostpoort staat standaard uit. Stel deze alleen beschikbaar op een vertrouwd netwerk.

## Ontwikkelen

Python 3.13. Installeer voor protocoltests `wyoming==1.11.0 numpy==2.2.6 PyYAML==6.0.3`.

```sh
PYTHONPATH=murmel python -m unittest discover -s tests -v
python scripts/check_metadata.py
docker build -t murmel-ha murmel
```

Voor een echte proef: configureer een lokaal bestand buiten Git met dezelfde opties als de app, start `PYTHONPATH=murmel python -m wyoming_murmel --options /pad/naar/options.json --data-dir /pad/naar/cache` en gebruik `scripts/transcribe.py`.

CI test het protocol zonder modelgewichten en bouwt het amd64-image. Een `vX.Y.Z`-tag publiceert het image met versie `X.Y.Z`, die gelijk moet zijn aan de appversie. Maak de GHCR-package bij de eerste publicatie openbaar zodat Supervisor zonder registry-token kan installeren.

## Licenties

De eigen wrappercode is MIT-gelicentieerd. [Murmel-code en -gewichten](https://github.com/The-AI-Factory/murmel-flash-dutch-stt) hebben een afzonderlijke licentie met gebruiksvoorwaarden; deze wrapper wijzigt die voorwaarden niet. Elke gebruiker regelt eigen toegang tot het model. Wyoming is MIT-gelicentieerd; overige afhankelijkheden behouden hun eigen licenties.
