# Dag 2 – REST API-testning + Protocol Buffers

**Tisdag 29 september · ca 3–4 timmar**

> **Tips:** Öppna den här filen i VS Code och tryck `Ctrl+Shift+V` för att se den formaterad.

| Del | Innehåll | Tid | Prioritet |
|---|---|---|---|
| 0 | Förberedelser | 10 min | Måste |
| A | REST API-testning | 2–2,5 h | **Viktigast** |
| B | Protocol Buffers | 1 h | Om du hinner |
| C | Pub/Sub och GraphQL (bara läsa) | 15 min | Om du hinner |

---

## Del 0 – Förberedelser (10 min)

Öppna Git Bash i projektmappen och aktivera din virtuella miljö:

```bash
cd ~/Downloads/First_day_job/digital-key-testbench/digital-key-testbench
source .venv/Scripts/activate
```

Installera dagens paket:

```bash
pip install fastapi uvicorn httpx protobuf grpcio-tools requests
```

Kontrollera att allt fungerar:

```bash
pytest -v
```

- [ ] Alla gamla tester är gröna
- [ ] De nya testerna i `test_api.py` körs (några hoppas över, det är dagens övningar)

**Nya filer i projektet idag:**

| Fil | Vad den är |
|---|---|
| `src/digital_key/api.py` | En REST API-server ("nyckelservern") byggd ovanpå din `KeyManager` |
| `tests/test_api.py` | API-tester med exempel och övningar |
| `proto/unlock.proto` | Protobuf-schema för ett upplåsningsmeddelande |
| `tests/test_proto.py` | Protobuf-tester |

---

## Del A – REST API-testning (2–2,5 h)

### A1. Starta servern och klicka runt (20 min)

```bash
uvicorn digital_key.api:app --reload --app-dir src
```

Öppna **http://127.0.0.1:8000/docs** i webbläsaren. Det är **Swagger UI**, en interaktiv sida som skapas automatiskt från koden. Här kan du prova alla anrop utan att skriva någon kod.

Gör så här för varje anrop: klicka på det → **Try it out** → fyll i → **Execute**.

- [ ] `GET /health` – ska ge `{"status": "ok"}`
- [ ] `POST /keys` **utan** token – titta på felet (401)
- [ ] `POST /keys` **med** token – skriv `test-token` i fältet **x-api-token** och registrera en nyckel
- [ ] `POST /vehicles/{vehicle_id}/commands` – lås upp bilen med din nyckel
- [ ] `DELETE /keys/{key_id}` – spärra nyckeln
- [ ] Försök låsa upp igen – vad händer nu?

Stoppa servern med `Ctrl+C` när du är klar.

### A2. Förstå grunderna i REST (15 min läsning)

Ett API-anrop består av:

| Del | Exempel i projektet | Förklaring |
|---|---|---|
| **Metod** | `GET`, `POST`, `DELETE` | Vad du vill göra: läsa, skapa/utföra, ta bort |
| **Sökväg** | `/vehicles/R1S-001/keys` | Vad du pratar om. `R1S-001` är en *path parameter* |
| **Header** | `X-API-Token: test-token` | Extra information, t.ex. inloggning |
| **Body (JSON)** | `{"key_id": "K1", "command": "unlock"}` | Data du skickar |
| **Statuskod** | `201`, `403` … | Serverns korta svar |

**Statuskoderna i projektet** (du kommer att se dem varje dag på jobbet):

| Kod | Betydelse | När i projektet |
|---|---|---|
| 200 | OK | Anropet lyckades |
| 201 | Created | Nyckel registrerad |
| 204 | No Content | Nyckel spärrad (inget att skicka tillbaka) |
| 400 | Bad Request | Ogiltigt kommando |
| 401 | Unauthorized | Token saknas eller är fel |
| 403 | Forbidden | Giltigt anrop men inte tillåtet (spärrad, utgången, fel bil) |
| 404 | Not Found | Nyckeln finns inte |
| 409 | Conflict | Nyckeln är redan registrerad |
| 422 | Unprocessable | JSON saknar fält eller har fel typ |

> **Kom ihåg:** Ett bra API-test kontrollerar nästan alltid **både** statuskoden **och** innehållet i svaret.

### A3. Kör och läs testerna (30 min)

```bash
pytest -v tests/test_api.py
```

Läs `tests/test_api.py` uppifrån och ned. Lägg märke till:

- [ ] **`client`-fixturen** skapar en helt ny app för varje test. Inget test kan påverka ett annat.
- [ ] **`registered_key`-fixturen** använder själva API:et för att skapa testdata
- [ ] **Sektion 2** testar inloggning med `parametrize` (saknad, fel och tom token)
- [ ] **Sektion 4** testar en hel användarresa: registrera → använd → spärra → nekas

**Tips:** Samma knep som igår fungerar här. Lägg till `print(response.json())` i ett test och kör med `-s` för att se exakt vad servern svarar.

### A4. Övningar (1 h)

Längst ned i `tests/test_api.py`. Ta bort `@pytest.mark.skip`-raden och skriv testet.

- [ ] **Övning 1:** Spärra en nyckel som inte finns → förvänta dig **404**
- [ ] **Övning 2:** Skicka kommandot `"self_destruct"` → förvänta dig **400** och texten "invalid command"
- [ ] **Övning 3:** Försök låsa upp **fel bil** (`"R2-003"`) → förvänta dig **403** och `"wrong_vehicle"`
- [ ] **Övning 4:** Parametrisera ett test över de tre giltiga kommandona (`unlock`, `lock`, `open_trunk`)
- [ ] **Övning 5:** `GET /vehicles/{id}/keys` utan token → förvänta dig **401**

> **Fundera på:** Borde `/health` kräva en token? Varför eller varför inte?

Kör bara ett test i taget medan du arbetar:

```bash
pytest -v -s tests/test_api.py::test_revoking_unknown_key_returns_404
```

### A5. Bonus – testa en server som körs "på riktigt" (15 min)

På jobbet anropar många tester en riktig server över nätverket med biblioteket `requests`.

1. Starta servern i ett Git Bash-fönster: `uvicorn digital_key.api:app --reload --app-dir src`
2. Öppna ett **nytt** Git Bash-fönster, aktivera venv och skriv `python`
3. Prova:

```python
>>> import requests
>>> r = requests.get("http://127.0.0.1:8000/health")
>>> r.status_code
>>> r.json()
```

`requests` och `TestClient` fungerar nästan likadant (`.get`, `.post`, `.status_code`, `.json()`), så allt du lär dig idag gäller båda.

---

## Del B – Protocol Buffers (1 h)

### B1. Vad och varför? (10 min läsning)

- **JSON** är text. Det är lätt att läsa men stort.
- **Protobuf** är binärt. Det är litet och snabbt, och båda sidor delar ett strikt schema (`.proto`-filen).
- Bilar och IoT-enheter använder protobuf eftersom bandbredd och batteri är begränsade.

Öppna `proto/unlock.proto` och läs kommentarerna.

> **Viktigt:** Siffrorna i `.proto`-filen (`= 1`, `= 2` …) är **fält-ID:n**, inte värden.

### B2. Generera Python-koden

```bash
python -m grpc_tools.protoc -I proto --python_out=src/digital_key proto/unlock.proto
```

- [ ] Filen `src/digital_key/unlock_pb2.py` har skapats

> Redigera **aldrig** `unlock_pb2.py` för hand. Ändra `.proto`-filen och kör kommandot igen.

### B3. Kör testerna

```bash
pytest -v -s tests/test_proto.py
```

- [ ] Alla 4 tester är gröna
- [ ] Du ser hur många byte protobuf sparar jämfört med JSON (32 mot 103)

### B4. Övning

Längst ned i `tests/test_proto.py`: skriv en `validate()`-funktion och två tester för den.

> **Fundera på som testare:** Protobuf fyller i standardvärden (tom text, 0) när ett fält saknas. Varför kan det vara farligt?

---

## Del C – Pub/Sub och GraphQL (bara läsa, 15 min)

**Pub/Sub** (Publish/Subscribe)
- En avsändare **publicerar** ett meddelande till ett **topic**. Mottagare **prenumererar** på topicet.
- Avsändare och mottagare pratar aldrig direkt med varandra.
- Meddelanden kan komma **mer än en gång** eller **i fel ordning**. Bra tester kontrollerar hur systemet hanterar dubbletter och ordning.

**GraphQL**
- Oftast bara **en** adress (`POST /graphql`). Klienten bestämmer exakt vilka fält den vill ha.
- Fel kommer ofta tillbaka med status **200** och en lista `"errors"` i svaret.
- **Därför räcker det inte att bara kontrollera statuskoden!**

---

## När du är klar

```bash
pytest -v
git add .
git commit -m "Day 2: REST API and protobuf tests"
git push
```

- [ ] Alla tester är gröna (utom de övningar du inte hunnit)
- [ ] Arbetet är pushat till GitHub

**Klistra in dina övningssvar i chatten så går jag igenom dem som i en kodgranskning.**
