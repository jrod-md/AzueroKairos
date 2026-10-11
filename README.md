# Azuero Kairós

Un sistema de confianza para evidencia territorial basado en Copernicus.

Azuero Kairós convierte observaciones de Sentinel-2 en decisiones responsables,
trazables y compartibles. Su promesa no es detectar lo invisible. Su promesa es
evitar la inferencia cuando la evidencia satelital disponible no es suficiente.

## Resumen del hackathon

El piloto se concentra en el corredor del río La Villa, en Azuero, Panamá. Con
datos de Copernicus, el sistema responde una pregunta concreta:

> ¿Esta observación satelital contiene suficiente evidencia válida para usarse
> con cautela, requiere revisión o no es apta para inferir?

La salida principal no es una alerta ambiental ni una certificación de campo.
Es una decisión sobre la confianza de la observación:

- `USABLE`: la escena tiene suficiente evidencia válida para una lectura
  exploratoria con límites explícitos.
- `REVISAR`: la escena contiene evidencia parcial o requiere cautela adicional.
- `NO INFERIR`: la escena no sostiene una inferencia responsable.

## Por qué importa

Muchos productos satelitales muestran mapas y métricas aunque la escena sea
débil. Kairós hace lo contrario: bloquea la inferencia cuando la evidencia es
insuficiente y documenta por qué.

El caso central de la demo es el contraste:

| Fecha | AOI | validPercent | Decisión |
| --- | --- | ---: | --- |
| 2025-06-10 | `corridor_wide` | 2.26% | `NO INFERIR` |
| 2025-06-30 | `corridor_wide` | 71.06% | `USABLE` |

Esperar una adquisición usable produce aproximadamente `31.4x` más evidencia
válida. Esa es la tesis del producto: una decisión responsable puede ser
esperar, revisar o documentar límites.

## Qué incluye

- Frontend público en React/Vite organizado como una sola bitácora de
  observación, con tres vistas y un selector de fecha compartido.
- Observación: un gráfico de reglas limnimétricas con la cobertura válida de
  Sentinel-2 por adquisición y los umbrales de decisión de 10% y 30% dibujados
  a escala; el veredicto `USABLE`, `REVISAR` o `NO INFERIR` de la fecha
  seleccionada; y los tres nodos del río La Villa con su contexto auxiliar de
  radar, lluvia y cobertura del suelo.
- Acción: cola de casos para revisión responsable, con preparación ligera de
  verificación de campo dentro de cada caso y sin afirmaciones nuevas.
- Registro: Passport verificable a través de `/trust/v1`, cadena de eventos del
  ledger, resumen del paquete con respaldo determinístico y reporte de
  validación de la exportación.
- Acerca: la regla de decisión, el ciclo de evidencia, las cifras del piloto,
  las audiencias y los límites.
- Trust Layer v1: JSON público y estático con decisiones, Passports, eventos de
  ledger, hashes y un reporte de validación.

## Capturas de pantalla

Un recorrido de escritorio por la demo pública de Azuero Kairós. Estas vistas
ilustran la exportación pública reproducible; no son un tablero operativo en
vivo.

### Observación: cobertura válida por adquisición y el veredicto NO INFERIR

![Reglas de cobertura y veredicto](screenshots/01-observation-gauge.png)

### Acción: cola de revisión y preparación de verificación de campo

![Cola de acción](screenshots/02-action-queue.png)

### Registro: Passport de la capa Trust y cadena de eventos del ledger

![Registro verificable](screenshots/03-verifiable-record.png)

### Acerca: la regla, el ciclo y los límites

![La regla y los límites](screenshots/04-rule-and-limits.png)

## Documentación

Los documentos enlazados están en inglés.

- [Arquitectura](docs/architecture.md): el pipeline implementado, de Copernicus
  al ledger.
- [Reglas de decisión](docs/decision_rules.md): clasificación determinística y
  salvaguardas de las capas auxiliares.
- [Límites científicos](docs/scientific_limits.md): las afirmaciones que el
  sistema no hace.
- [Reporte de calidad de la demo](docs/demo_quality_report.md): el resumen de
  validación de la exportación pública incluido en el repositorio.

## Flujo de la demo de 3 minutos

La interfaz incluye un control `Demo guiada` que recorre el pitch:

1. Observación, `2025-06-10`: la API respondió, 2.26% válido, `NO INFERIR`.
2. Observación, `2025-06-30`: 71.06% válido, `USABLE`.
3. Nodos: tres nodos y un contexto auxiliar que nunca cambia la clase.
4. Acción: de la brecha de evidencia a un caso de revisión.
5. Registro: Passport, eventos de ledger enlazados y hash de verificación.
6. Acerca: la regla y lo que Kairós no afirma.

## Datos oficiales del piloto

Resultados oficiales de Sentinel-2 para `corridor_wide`:

| Fecha | validPercent | Clase |
| --- | ---: | --- |
| 2025-06-02 | 49.15% | `USABLE` |
| 2025-06-10 | 2.26% | `NO INFERIR` |
| 2025-06-15 | 44.22% | `USABLE` |
| 2025-06-30 | 71.06% | `USABLE` |
| 2025-07-15 | 52.22% | `USABLE` |

Los datos públicos están sanitizados. El JSON que sirve el frontend no expone
rutas internas a artefactos crudos, archivos CSV procesados ni archivos
privados. Las referencias públicas usan `/data/...` y `/trust/v1/...`.

## Cómo ejecutar el frontend

Desde la raíz del repositorio:

```powershell
cd frontend
npm install
npm.cmd run dev
```

Para crear un build de producción:

```powershell
cd frontend
npm.cmd run build
```

La aplicación consume JSON estático desde:

```text
frontend/public/data
frontend/public/trust/v1
```

Los datos de la demo pública son locales; no se requieren llamadas a APIs
externas. Las tipografías se cargan desde Google Fonts y tienen respaldo del
sistema si no hay conexión.

## Validación de la entrega

Comandos recomendados antes de presentar:

```powershell
cd frontend
npm.cmd run build
cd ..
python scripts/validate_public_demo.py
```

El validador comprueba:

- las observaciones oficiales esperadas;
- el contraste entre `2025-06-10` y `2025-06-30`;
- el aumento de evidencia;
- la cobertura de Corredor, SAR, CLMS e HydroClimate;
- los hashes del ledger y de los Passports;
- la ausencia de rutas internas, secretos, cabeceras o payloads crudos en los
  datos públicos;
- la ausencia de mojibake en los artefactos generados;
- la ausencia de afirmaciones positivas prohibidas.

Estado de calidad actual: `12/12` comprobaciones, `0` advertencias, `0` fallos.

## Cortafuegos oficial de afirmaciones

El cortafuegos oficial de afirmaciones vive en
`scripts/validate_public_demo.py`. No es un grep suelto sobre todo el
repositorio. Es una validación enfocada en la superficie pública de la entrega.

Comando oficial:

```powershell
python scripts/validate_public_demo.py
```

Protege los siguientes límites:

- `/data` y `/trust/v1` no deben exponer secretos, cabeceras, rutas locales ni
  payloads crudos.
- La capa Trust no debe contener afirmaciones positivas sobre contaminación,
  detección química, validación sanitaria, potabilidad, seguridad del agua,
  estado de crisis, cierre automático, preparación operativa, decisiones de
  autoridad, desempeño medido o pérdida medida.
- Las declaraciones de límites son válidas cuando niegan explícitamente esos
  alcances, por ejemplo: "no certifica condiciones químicas, sanitarias ni
  operativas".

La regla es simple: Kairós verifica la confianza de la observación y su
trazabilidad. No certifica condiciones del territorio.

## Trust Layer v1

La capa Trust es estática y de solo lectura. Permite verificar un Passport sin
base de datos ni API externa.

Rutas principales:

```text
/trust/v1/index.json
/trust/v1/passports/<passport_id>.json
/trust/v1/decisions/<decision_id>.json
/trust/v1/ledger/<event_id>.json
/trust/v1/validation_report.json
/trust/v1/openapi.json
```

El Passport verifica la trazabilidad del paquete de evidencia: fecha, AOI o
nodo, clase de confianza, porcentaje válido, estado de la API, capa primaria,
capas auxiliares, ledger, hash y límites de uso.

No certifica territorio, agua, contaminación, condiciones químicas,
condiciones sanitarias ni preparación operativa.

## Pipeline técnico

El pipeline interno puede ejecutarse con credenciales del Copernicus Data Space
Ecosystem provistas mediante variables de entorno:

```powershell
$env:CDSE_CLIENT_ID = "your-client-id"
$env:CDSE_CLIENT_SECRET = "your-client-secret"
```

Comandos principales:

```powershell
python scripts/run_official_s2_batch.py
python scripts/build_evidence_ledger.py
python scripts/export_public_data.py
python scripts/export_public_watch_data.py
python scripts/export_public_decision_cases.py
python scripts/export_trust_layer.py
python scripts/validate_public_demo.py
```

Pueden existir artefactos internos bajo `outputs/`, pero la entrega pública usa
exportaciones sanitizadas bajo `frontend/public`.

## Límites científicos

Azuero Kairós no detecta plaguicidas, atrazina, patógenos, metales pesados,
contaminación química disuelta ni potabilidad. No determina si el agua es
segura para consumo, riego, animales o contacto humano.

No valida crisis, no ordena cierres, no reemplaza pruebas de laboratorio, no
reemplaza a una autoridad competente y no toma decisiones de pago, crédito,
seguro o sanción.

La salida es una evaluación de la confianza de una observación satelital de
Sentinel-2, apoyada por contexto auxiliar que nunca cambia la clasificación
primaria.

## Alcance del repositorio

Este repositorio contiene la entrega reproducible de Azuero Kairós para el
hackathon. El código entregado, la instantánea de artefactos oficiales, la
interfaz pública, el ledger, la capa Trust y los Passports se preparan desde
este repositorio para revisión técnica.
