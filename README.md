# Replicate AI Image Generator

Webová aplikace pro generování obrázků pomocí AI modelů z platformy Replicate.com s využitím GPT-4 pro vylepšování promptů.

## Funkce

- Generování obrázků pomocí různých AI modelů
- Vylepšování promptů pomocí GPT-4
- Galerie vygenerovaných obrázků s paginací
- Správa obrázků (mazání, kopírování nastavení)
- Ukládání nastavení formuláře
- Responzivní design s tmavým tématem
- Docker podpora pro snadné nasazení

## Podporované modely

- Flux Pro
- Flux 1.1 Pro Ultra
- Flux 1.1 Pro
- Flux Schnell LoRA

## Technologie

- Backend: Python, Flask
- Frontend: HTML5, CSS3, JavaScript (jQuery)
- Styling: Bootstrap 5.3
- Ikony: Font Awesome
- Kontejnerizace: Docker

## Požadavky

- Python 3.11+
- Docker a Docker Compose (volitelné)
- API klíče:
  - Replicate API Token
  - OpenAI API Key

## Instalace

### Lokální instalace

1. Naklonujte repositář:
```bash
git clone <repository-url>
cd replicate-ai
```

2. Vytvořte a aktivujte virtuální prostředí:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. Nainstalujte závislosti:
```bash
pip install -r requirements.txt
```

4. Vytvořte soubor `.env` s API klíči:
```
REPLICATE_API_TOKEN=your_replicate_token
OPENAI_API_KEY=your_openai_key
```

5. Spusťte aplikaci:
```bash
python app.py
```

Aplikace bude dostupná na `http://localhost:5000`

### Docker instalace

1. Naklonujte repositář:
```bash
git clone <repository-url>
cd replicate-ai
```

2. Vytvořte soubor `.env` s API klíči:
```
REPLICATE_API_TOKEN=your_replicate_token
OPENAI_API_KEY=your_openai_key
```

3. Sestavte a spusťte kontejnery:
```bash
docker-compose up -d
```

Aplikace bude dostupná na `http://localhost:5000`

## Použití

1. Otevřete aplikaci v prohlížeči
2. Zadejte prompt pro generování obrázku
3. Volitelně můžete prompt vylepšit pomocí GPT-4
4. Vyberte požadovaný model a poměr stran
5. Klikněte na "Generovat"
6. Počkejte na dokončení generování (max. 2 minuty)
7. Vygenerovaný obrázek se zobrazí v galerii

### Správa obrázků

- Kliknutím na obrázek v galerii zobrazíte ovládací prvky
- Můžete:
  - Kopírovat nastavení do formuláře
  - Smazat obrázek
- Galerie podporuje stránkování po 12 obrázcích

## API Endpointy

### `POST /api/generate-image`
Generování nového obrázku
```json
{
  "prompt": "string",
  "model": "string",
  "aspect_ratio": "string"
}
```

### `POST /api/improve-prompt`
Vylepšení promptu pomocí GPT-4
```json
{
  "prompt": "string"
}
```

### `GET /api/images`
Seznam obrázků s paginací
```
?page=1&per_page=12
```

### `GET /api/metadata/<image_id>`
Získání metadat obrázku

### `DELETE /api/image/<image_id>`
Smazání obrázku

## Struktura projektu

```
replicate-ai/
├── api/
│   ├── replicate_client.py
│   └── openai_client.py
├── static/
│   └── js/
│       └── main.js
├── templates/
│   └── index.html
├── utils/
│   └── storage.py
├── app.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Řešení problémů

### Časté chyby

1. "API key not found"
   - Zkontrolujte přítomnost a správnost API klíčů v `.env` souboru

2. "Error generating image"
   - Ověřte připojení k internetu
   - Zkontrolujte platnost Replicate API tokenu
   - Zkontrolujte, zda není překročen limit API

3. "Error improving prompt"
   - Ověřte platnost OpenAI API klíče
   - Zkontrolujte, zda není překročen limit API

### Logy

- Aplikace používá JSON logging
- Logy jsou dostupné v terminálu nebo Docker logu
- Pro detailní debugging nastavte v `app.py` úroveň logování na `DEBUG`

## Licence

MIT