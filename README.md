# Generative AI - Capstone Project 2: Alternative Cover Art Generation

**Author:** Turayev Komiljon
**Organization:** EPAM Systems, Inc.
**Email:** komiljon_torayev@epam.com
**GitHub:** https://github.com/KomiljonTurayev/data_inside_app

## Project Overview

This project demonstrates **self-hosted image generation** using **ComfyUI** and Stable Diffusion to create alternative cover art for books, movies, and music albums. The solution is fully reproducible and does not rely on public APIs.

### Objectives

- Generate alternative **book cover art** using AI
- Generate alternative **movie/DVD cover art**
- Generate alternative **music album cover art**
- Use a **fully self-hosted** solution
- Export reproducible **ComfyUI workflow** (JSON)

## Technical Stack

| Component       | Details                              |
|-----------------|--------------------------------------|
| Platform        | ComfyUI                             |
| Model           | DreamShaper 8 (Stable Diffusion 1.5)|
| Model Size      | ~2 GB (pruned safetensors)           |
| Language        | Python 3.12.8                        |
| Web Framework   | Flask                                |
| Containerization| Docker Compose                       |
| Execution Mode  | CPU (`--cpu`)                        |

### KSampler Settings

| Parameter  | Value            |
|------------|------------------|
| Seed       | 8845206238271    |
| Steps      | 20               |
| CFG Scale  | 8                |
| Sampler    | Euler            |
| Scheduler  | Simple           |
| Resolution | 512 x 512 pixels |

## Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/KomiljonTurayev/data_inside_app.git
cd CapstoneProject2
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up ComfyUI

```bash
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
pip install -r requirements.txt
cd ..
```

### 5. Download the DreamShaper 8 model

Download `dreamshaper_8.safetensors` (~2 GB) and place it in:

```
ComfyUI/models/checkpoints/dreamshaper_8.safetensors
```

### 6. Start ComfyUI (in a separate terminal)

```bash
cd ComfyUI && python main.py --cpu
```

ComfyUI will be available at **http://127.0.0.1:8188**.

### 7. Run the web application

```bash
python run.py
```

The web application will be available at **http://localhost:8080**.

### Optional: Export ComfyUI workflows

```bash
python run.py --export-workflows
```

## Docker Setup (Alternative)

You can run the entire application using Docker Compose instead of manual setup.

### 1. Build the containers

```bash
docker compose build
```

### 2. Copy the DreamShaper 8 model into the container

```bash
docker compose up -d comfyui
docker cp ComfyUI/models/checkpoints/dreamshaper_8.safetensors \
  "$(docker compose ps -q comfyui):/app/models/checkpoints/"
docker compose restart comfyui
```

### 3. Start all services

```bash
docker compose up
```

- **ComfyUI** will be available at **http://localhost:8188**
- **Web application** will be available at **http://localhost:8080**

### Docker Architecture

| Service   | Image Base        | Port | Description                  |
|-----------|-------------------|------|------------------------------|
| `comfyui` | python:3.12.8-slim| 8188 | ComfyUI with DreamShaper 8   |
| `web`     | python:3.12.8-slim| 8080 | Flask web application        |

Named volumes are used for persistent storage:
- `comfyui-models` — DreamShaper 8 checkpoint
- `generated-images` — Generated cover art images
- `outputs` — Exported images

## Generated Cover Art

| Cover Type  | Description                                         |
|-------------|-----------------------------------------------------|
| Book        | *Crime and Punishment* by Fyodor Dostoevsky - dark psychological theme |
| Movie       | *Interstellar* - cinematic sci-fi design             |
| Music Album | Abstract electronic/ambient vinyl artwork            |

### Prompts Used

**Book Cover - Positive Prompt:**
> book cover design, title 'CRIME AND PUNISHMENT', dark city background, dramatic lighting, professional typography

**Negative Prompt (shared):**
> blurry, low quality, deformed, misspelled text

## Project Structure

```
CapstoneProject2/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── generator.py         # ComfyUI API client for image generation
│   ├── routes.py            # Flask routes and API endpoints
│   ├── workflow.py          # ComfyUI workflow JSON generator
│   ├── static/
│   │   ├── css/style.css    # UI styling
│   │   ├── js/app.js        # Frontend JavaScript
│   │   └── images/generated/ # Generated images (web-served)
│   └── templates/
│       ├── base.html        # Base template
│       ├── index.html       # Generation page
│       └── gallery.html     # Image gallery
├── ComfyUI/                 # ComfyUI installation (self-hosted)
│   └── models/checkpoints/  # DreamShaper 8 model (~2 GB)
├── outputs/                 # Exported generated images
├── workflows/               # Exported ComfyUI workflow JSONs
├── config.py                # Project configuration & constants
├── run.py                   # Application entry point
├── requirements.txt         # Python dependencies
├── Dockerfile               # Flask web app container
├── Dockerfile.comfyui       # ComfyUI container
├── docker-compose.yml       # Multi-service orchestration
├── .dockerignore            # Docker build exclusions
└── README.md
```

## API Endpoints

| Method | Endpoint              | Description                         |
|--------|-----------------------|-------------------------------------|
| GET    | `/`                   | Main generation UI                  |
| GET    | `/gallery`            | Browse generated images             |
| POST   | `/api/generate`       | Generate a cover art image          |
| GET    | `/api/status`         | Check generation progress           |
| GET    | `/api/presets`        | Get available preset configurations |
| POST   | `/api/workflow`       | Generate ComfyUI workflow JSON      |
| POST   | `/api/workflow/export`| Export workflow JSON to disk         |
| GET    | `/api/gallery`        | Get list of generated images        |

## ComfyUI Workflow

The workflow includes:
- **CheckpointLoaderSimple** - Loads DreamShaper 8 model
- **CLIPTextEncode** (x2) - Positive and negative prompt encoding
- **EmptyLatentImage** - 512x512 latent space
- **KSampler** - Euler sampler, 20 steps, CFG 8
- **VAEDecode** - Latent to pixel space
- **SaveImage** - Output to file

Workflow JSON files can be imported directly into ComfyUI for reproduction.

## Conclusion

This project demonstrates a fully self-hosted Generative AI solution for alternative cover art creation using ComfyUI and Stable Diffusion (DreamShaper 8), executed entirely in CPU mode. The web interface provides an interactive way to generate, customize, and export cover art with reproducible ComfyUI workflows. The application is containerized with Docker Compose for easy deployment.
