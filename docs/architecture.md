# Arquitectura

## Visión general

Monorepo con dos aplicaciones independientes que se comunican vía HTTP/JSON:

- `backend/`: API REST en Django + DRF.
- `frontend/`: SPA con Next.js 15 (App Router).

## Backend: Hexagonal + Vertical Slice

Organizamos el backend por **feature** (vertical slice), y dentro de cada
feature separamos capas (hexagonal pragmático):


backend/
├── config/ # settings, urls raíz, wsgi/asgi
├── shared/ # kernel compartido (errores, paginación, permisos)
│ ├── domain/ # excepciones base, value objects comunes
│ ├── application/ # casos de uso genéricos
│ └── infrastructure/ # adaptadores comunes (DRF handlers, logging)
└── features/
├── usuarios/
│ ├── domain/ # entidades, value objects, interfaces de repo
│ ├── application/ # casos de uso (use cases)
│ ├── infrastructure/ # modelos Django, repos, serializers, views
│ └── tests/
├── autores/
├── articulos/
├── revistas/
└── categorias/

text

### Capas

- **domain**: reglas de negocio puras. Sin imports de Django.
  Excepción pragmática: entidades pueden heredar de `models.Model` cuando
  el coste de mapear a mano no compensa.
- **application**: casos de uso. Orquestan dominio + repositorios.
  Aquí viven los DTOs de entrada/salida.
- **infrastructure**: adaptadores. Aquí sí usamos DRF, Django ORM,
  SimpleJWT, etc. Traducen HTTP ↔ casos de uso.

### Manejo de errores

- Excepciones de dominio en `shared/domain/exceptions.py`.
- Un **exception handler global** en DRF traduce excepciones de dominio a
  respuestas HTTP consistentes (`application/problem+json`).
- Logging estructurado con `structlog` (se añade en Fase 2).

## Frontend: App Router + features
frontend/
├── app/ # rutas (App Router)
├── components/ # UI reutilizable (shadcn/ui)
├── features/ # lógica por feature
│ ├── auth/
│ ├── autores/
│ └── ...
├── lib/ # api client, utils
└── types/ # tipos compartidos

text

## Decisiones arquitectónicas (ADRs)

Se documentarán en `docs/adr/` a medida que surjan.

## Convenciones de commits

Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`.
