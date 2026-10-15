# app_django_nextjs

Aplicación full-stack para gestión de artículos académicos, autores, revistas
y categorías. Monorepo con backend Django REST + frontend Next.js.

## Stack

- **Backend**: Django 5 + Django REST Framework + SimpleJWT
- **Frontend**: Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui + TanStack Query
- **Base de datos**: PostgreSQL 14+
- **Auth**: JWT (access en memoria, refresh en cookie httpOnly)
- **Tests**: pytest + pytest-django
- **CI/CD**: GitHub Actions

## Arquitectura

Hexagonal + Vertical Slice por feature (usuarios, autores, articulos, revistas, categorias).
Ver `docs/architecture.md`.

## Requisitos

- Python 3.14+
- Node.js 20+
- PostgreSQL 14+
- Git

## Puesta en marcha (desarrollo)

### 1. Clonar e instalar dependencias del backend

```bash
git clone https://github.com/jarciadca/app_django_nextjs.git
cd app_django_nextjs
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements/local.txt


app_django_nextjs/
├── backend/ # Django + DRF (se llena en Fase 2)
├── frontend/ # Next.js 15 (se llena en Fase 5)
├── docs/ # Documentación y ADRs
├── .github/workflows # CI/CD (se llena en Fase 1)
├── .env.example
├── .gitignore
└── README.md

text

## Convenciones

- **Commits**: [Conventional Commits](https://www.conventionalcommits.org/)
- **Branches**: `main` (estable), `feat/*`, `fix/*`, `chore/*`
- **Python**: ruff + black + pytest (se configura en Fase 2)
- **TypeScript**: estricto, ESLint + Prettier (se configura en Fase 5)

## Licencia

Privado.
