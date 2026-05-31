# Primera entrega: Azuero Kairós

## One-liner

Azuero Kairós convierte evidencia satelital Copernicus en decisiones
responsables: usar, revisar o no inferir.

## Descripción corta

Azuero Kairós es una capa de confianza para evidencia territorial en Azuero,
Panamá. El sistema toma observaciones Sentinel-2, calcula calidad de evidencia,
clasifica la escena y empaqueta la decisión en un artefacto verificable.

No intenta probar contaminación, potabilidad ni condiciones sanitarias. Su valor
es más defendible: evita que evidencia satelital débil se convierta en claims
fuertes.

## Problema

En agricultura, seguros, crédito rural y programas públicos, una mala lectura
de datos satelitales puede generar decisiones prematuras. La escena puede tener
nubes, píxeles sin dato, baja cobertura válida o señales auxiliares que parecen
útiles pero no alcanzan para inferir.

Sin una capa de confianza, el usuario ve un mapa o un índice y puede asumir que
la evidencia es suficiente. Kairós pone una compuerta antes de la interpretación.

## Solución

Kairós separa tres cosas que normalmente se mezclan:

- observación satelital;
- contexto auxiliar;
- decisión responsable.

El sistema dice si una escena es `USABLE`, requiere `REVISAR` o debe quedar en
`NO INFERIR`. Luego conserva la trazabilidad en un ledger y genera un Passport
verificable para compartir la decisión con límites claros.

## Qué demuestra esta entrega

La primera entrega ya muestra un ciclo completo:

```text
Copernicus CDSE
  -> Sentinel-2
  -> validPercent / calidad de observación
  -> decisión de confianza
  -> cola de acción
  -> verificación lite
  -> Passport
  -> Trust Layer
  -> Evidencia y ledger
```

Módulos visibles:

| Módulo | Qué comunica |
| --- | --- |
| Sistema | El ciclo completo de evidencia a decisión. |
| Impacto | Por qué esperar una escena usable cambia la calidad del análisis. |
| Decisión | Sello `USABLE`, `REVISAR` o `NO INFERIR` con métricas clave. |
| Corredor | Tres nodos del río La Villa y capas auxiliares. |
| Acción | Cola de casos y siguiente acción responsable. |
| Campo | Ficha de verificación lite sin claims nuevos. |
| Passport | Comprobante portable con hashes, ledger y límites. |
| Evidencia | Archivo auditable y asistente de evidencia. |

## Momento demo

El pitch puede recorrerse con el botón `Demo 3 min`:

1. Sistema: ciclo Kairós.
2. Impacto: `31.4x` de evidencia válida al esperar.
3. Decisión: `2025-06-10`, `NO INFERIR`.
4. Contraste: `2025-06-30`, `USABLE`.
5. Corredor: tres nodos y capas auxiliares.
6. Acción: cola de revisión.
7. Campo: verificación lite.
8. Passport: artefacto Trust.
9. Evidencia: ledger y asistente.

La escena clave es `2025-06-10`: la API responde OK, pero solo hay `2.26%` de
evidencia válida. Kairós no fuerza una conclusión. Dice `NO INFERIR`.

El contraste es `2025-06-30`: la evidencia válida sube a `71.06%`, y la escena
se vuelve `USABLE` para lectura exploratoria con límites.

## Resultados oficiales

| Fecha | AOI | validPercent | Decisión |
| --- | --- | ---: | --- |
| 2025-06-02 | `corridor_wide` | 49.15% | `USABLE` |
| 2025-06-10 | `corridor_wide` | 2.26% | `NO INFERIR` |
| 2025-06-15 | `corridor_wide` | 44.22% | `USABLE` |
| 2025-06-30 | `corridor_wide` | 71.06% | `USABLE` |
| 2025-07-15 | `corridor_wide` | 52.22% | `USABLE` |

El aumento entre `2025-06-10` y `2025-06-30` es aproximadamente `31.4x` en
evidencia válida.

## Uso de Copernicus

La entrega usa Copernicus Data Space Ecosystem y Sentinel-2 como capa primaria.
El pipeline calcula métricas de observación como:

- `validPercent`;
- `sampleCount`;
- `noDataCount`;
- MNDWI;
- NDTI;
- estado de API.

Las capas auxiliares SAR, CLMS e HydroClimate agregan contexto, pero no cambian
la clasificación Sentinel-2 primaria.

## Trust, Passport y evidencia pública

La entrega incluye un Trust Layer v1 estático:

```text
/trust/v1/index.json
/trust/v1/passports/<passport_id>.json
/trust/v1/decisions/<decision_id>.json
/trust/v1/ledger/<event_id>.json
/trust/v1/validation_report.json
```

El Passport permite revisar:

- `passport_id`;
- `decision_id`;
- fecha objetivo;
- AOI o nodo;
- clase de confianza;
- `validPercent`;
- estado API;
- capa primaria;
- resumen de contexto auxiliar;
- hash de ledger;
- hash de verificación;
- límites de claim.

La data pública está sanitizada. No expone rutas internas a raw JSON, CSV
procesado ni briefs privados. Las referencias públicas apuntan a `/data/...` y
`/trust/v1/...`.

## Actores de uso

| Actor | Uso responsable |
| --- | --- |
| Gobierno | Priorizar dónde verificar primero y documentar brechas. |
| Cooperativa | Comunicar cautela y evitar inferencias débiles. |
| Crédito/seguro | Preevaluar si la evidencia alcanza para revisión, nunca para pago automático. |
| Laboratorio/autoridad | Recibir paquete mínimo de evidencia y límites para escalar. |

## Qué no decide Kairós

Kairós no declara potabilidad, contaminación, seguridad del agua, condiciones
sanitarias, cierre operativo, crisis, rendimiento agrícola, pago automático,
cobertura de seguro ni decisión de autoridad.

Tampoco dice que las capas auxiliares modifiquen la clasificación Sentinel-2.
Solo contextualizan.

## Validación actual

La entrega fue validada con:

```powershell
cd frontend
npm.cmd run build
cd ..
python scripts/validate_public_demo.py
```

Resultado actual:

- Build frontend: exitoso.
- Validación pública: `12/12` checks.
- Warnings: `0`.
- Failures: `0`.
- Safety scan: sin secretos, headers, rutas internas ni payloads crudos en
  `/data` o `/trust`.
- Claim scan: sin claims positivos prohibidos.

## Por qué es una buena entrega de hackathon

La mayoría de demos satelitales intentan impresionar con mapas. Kairós impresiona
con disciplina: sabe cuándo no inferir, explica por qué y deja un artefacto
verificable.

Eso lo vuelve útil para organizaciones que necesitan decidir sin sobreprometer:
cooperativas, gobiernos locales, crédito rural, seguros, equipos técnicos y
auditores.

## Frase final

Azuero Kairós no convierte satélites en autoridad. Convierte observaciones
Copernicus en decisiones trazables, prudentes y compartibles.
