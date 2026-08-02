# Fundex — sistem za upravljanje investicionim fondom

Sistem se sastoji iz tri veb servisa i četiri pomoćne komponente, i pokreće se kao
celina pomoću Kubernetes-a.

| Komponenta | Uloga | Port u klasteru | Spolja |
|---|---|---|---|
| `authentication` | registracija, prijava, brisanje naloga | 5000 | 30000 |
| `employee` | pretraga imovine, predlozi kupovine i prodaje (3 replike) | 5001 | 30001 |
| `director` | pregled i odobravanje zahteva, izveštaj | 5002 | 30002 |
| `mysql` | podaci o korisnicima | 3306 | — |
| `mongo` | podaci o imovini | 27017 | — |
| `redis` | zahtevi koji čekaju odluku | 6379 | — |
| `ganache` | simulator Ethereum mreže | 8545 | 30003 |

---

## Preduslovi

1. **Docker Desktop** — pokrenut.
2. **Kubernetes u Docker Desktop-u** — `Settings → Kubernetes → Enable Kubernetes`.
   Prvi put skida svoje sistemske image-e, dakle **traži internet**. Uradi ovo pre
   nego što mreža nestane.
3. **kubectl** — dolazi uz Docker Desktop.

Provera da je sve spremno:

```bash
kubectl get nodes
```

Treba da ispiše čvor u stanju `Ready`.

---

## Da li treba ručno instalirati requirements?

| Šta | Ručna instalacija? | Zašto |
|---|---|---|
| **Sam sistem** (tri servisa) | **NE, nikad** | `pip install` se izvršava unutar `docker build`, definisan u Dockerfile-ovima |
| **Grejder** (testovi) | **DA, jednom** | grejder se izvršava na tvom računaru, ne u kontejneru |
| **Ponovna kompilacija ugovora** | samo ako menjaš `Voting.sol` | gotov `Voting.json` je već u repozitorijumu |
| `venv/` u korenu projekta | **NE treba ti** | ostatak razvojnog rada, sistem ga ne koristi |

---

## 1. Podešavanje — jednom, dok ima interneta

```bash
./setup.sh
```

Skripta radi sve što traži mrežu:

- povlači `python:3.12-slim`, `mysql:8`, `mongo:7`, `redis:7-alpine`, `trufflesuite/ganache`
- gradi `auth-service:1.0`, `employee-service:1.0`, `director-service:1.0`
- prepoznaje koji Kubernetes koristiš i, ako treba (minikube, kind), ubacuje image-e u njega
- ispisuje tačne adrese na koje grejder treba da gađa

Ako Kubernetes nije uključen, skripta će to reći i prekinuti — uključi ga pa pokreni ponovo.

---

## 2. Pokretanje sistema — radi i offline

```bash
kubectl apply -f k8s/fundex.yaml
```

Praćenje dok se ne podigne:

```bash
kubectl get pods -w
```

Gotovo je kad svih 9 podova bude `1/1 Running` (obično 30–60 sekundi).
Podovi `employee` i `director` čekaju da baze budu spremne — to je normalno i
vidi se kao stanje `Init:0/1`.

### Brza provera da radi

```bash
curl -X POST http://127.0.0.1:30000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"onlymoney@gmail.com","password":"evenmoremoney"}'
```

Treba da vrati `{"accessToken":"..."}`.

---

## 3. Pokretanje grejdera

### Prvi put — priprema okruženja (traži internet)

```bash
python3 -m venv grader-venv
grader-venv/bin/pip install -r iep_grader/requirements-pytest.txt
```

Na **Python-u 3.12 i novijem** dodaj još i:

```bash
grader-venv/bin/pip install "setuptools<81"
```

Bez toga grejder puca sa `ModuleNotFoundError: No module named 'pkg_resources'`,
jer njegov `web3==6.5.0` koristi paket koji je izbačen iz novijih Python verzija.

### Pokretanje

```bash
./test.sh --reset
```

Očekivano: **179.00 / 179.00 (100%)**, 98 testova prošlo.

Skripta sama radi sve što treba: sačeka da svih 9 podova bude spremno, po potrebi
prebaci režim rada, obriše podatke iz prethodnog prolaza, i pozove grejder sa
tačnim argumentima.

| Poziv | Šta radi |
|---|---|
| `./test.sh` | pokreće testove nad zatečenim stanjem |
| `./test.sh --reset` | prvo obriše podatke, pa pokrene — **ovo koristi obično** |
| `./test.sh --reset --no-blockchain` | isto, ali u režimu bez glasanja (očekivano 180.00 / 180.00) |

`--reset` je gotovo uvek potreban jer je grejder stateful — ostavlja imovinu u
bazi, a prvi test pretrage očekuje da je baza prazna.

### Zašto se ne poziva `pytest` direktno

Može, ali zahteva podugačku komandu, jer grejder nije deo sistema — izvršava se
van klastera i ne može da pročita našu konfiguraciju, pa mu se sve mora reći
kroz argumente:

```bash
cd iep_grader
../grader-venv/bin/python -m pytest -q --type all --wait-for-services \
  --authentication-url http://127.0.0.1:30000 \
  --jwt-secret super-secret-key-change-in-production \
  --roles-field role --employee-role employee --director-role director \
  --with-authentication \
  --employee-url http://127.0.0.1:30001 \
  --director-url http://127.0.0.1:30002 \
  --with-blockchain --provider-url http://127.0.0.1:30003 \
  --grade-report-file grade_report.json
```

`--jwt-secret` mu treba da bi sam dekodovao token i proverio njegov sadržaj, a
`--roles-field` i `--*-role` zato što specifikacija ne propisuje kako se polje
sa ulogom zove — to je bio naš izbor.

> **Napomena:** `--reset` briše sadržaj baza **u mestu**, umesto da ruši i ponovo
> diže servise. Rušenje svih Service objekata tera CoreDNS da iznova učita
> zapise, a dok to traje imena poput `mongo` mogu nakratko da se ne razreše
> unutar podova, što obara pokoji test bez ikakve veze sa ispravnošću koda.

---

## 4. Gašenje i reset

**Zaustavljanje, uz čuvanje podataka:**

```bash
kubectl delete deployment --all
```

**Brisanje podataka** pred novi prolaz grejdera — radi `./test.sh --reset`, ne treba ništa ručno.

**Potpuno rušenje i ponovno dizanje** (retko potrebno):

```bash
kubectl delete -f k8s/fundex.yaml
kubectl apply -f k8s/fundex.yaml
```

---

## 5. Ako menjaš pametni ugovor

`contracts/Voting.json` (rezultat prevođenja) je već u repozitorijumu, pa ti
Solidity prevodilac normalno **ne treba**. Ako izmeniš `Voting.sol`:

```bash
cd director-service
pip install -r requirements-dev.txt
python compile_contract.py
```

pa ponovo sagradi image i restartuj servis:

```bash
cd ..
docker build -t director-service:1.0 director-service/
kubectl rollout restart deployment/director
```

---

## 6. Ako nešto ne radi

| Simptom | Uzrok i rešenje |
|---|---|
| `ErrImagePull` / `ImagePullBackOff` | image nije sagrađen — pokreni `./setup.sh` |
| Pod stoji u `Init:0/1` duže od minut | baza se još diže; vidi na šta čeka sa `kubectl logs <pod> -c wait-for-dependencies` |
| `Connection refused` na portu 30000 | podovi još nisu spremni, proveri `kubectl get pods` |
| Grejder: `No module named 'pkg_resources'` | `grader-venv/bin/pip install "setuptools<81"` |
| Grejder: prvi test pretrage pada | baza nije prazna — pokreni `./test.sh --reset` |
| Grejder: `Name or service not known` u logovima | prolazni CoreDNS problem posle rušenja servisa; pokreni ponovo sa `./test.sh --reset` |
| Blockchain testovi padaju na finansiranju glasača | Ganache mora imati `--chain.hardfork muirGlacier` (već je u manifestu) |

Korisne komande:

```bash
kubectl get pods                          # stanje svih podova
kubectl logs deployment/authentication    # logovi servisa
kubectl logs deployment/director          # uključujući listener
kubectl describe pod <ime-poda>           # zašto pod ne startuje
```

---

## Podrazumevani nalog direktora

Kreira se automatski pri prvom pokretanju:

```
onlymoney@gmail.com  /  evenmoremoney
```

---

## Sažetak: šta se kuca u laboratoriji

```bash
# 1. Docker Desktop -> Settings -> Kubernetes -> Enable   (traži internet)

# 2. dok ima interneta
./setup.sh
python3 -m venv grader-venv
grader-venv/bin/pip install -r iep_grader/requirements-pytest.txt "setuptools<81"

# 3. od ovog trenutka sve radi bez interneta
kubectl apply -f k8s/fundex.yaml

# 4. provera da sve radi
./test.sh --reset
```
