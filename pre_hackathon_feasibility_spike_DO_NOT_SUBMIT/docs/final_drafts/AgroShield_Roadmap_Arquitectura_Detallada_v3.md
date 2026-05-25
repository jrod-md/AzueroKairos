# AgroShield Roadmap y Arquitectura Detallada v3

**Documento académico preparatorio. No constituye entrega oficial del hackathon. El código, dashboard, resultados finales y entregables oficiales serán generados durante la ventana oficial de competencia.**

## Portada textual

**Título:** AgroShield Roadmap y Arquitectura Detallada v3

**Subtítulo:** Arquitectura por fases con fallback seguro para un MVP Copernicus de seguridad alimentaria

**Nota:** Documento académico preparatorio, no entrega oficial del hackathon.

## Resumen ejecutivo

AgroShield se diseña como una escalera de fases, no como una apuesta única y frágil. Cada fase produce una salida demostrable, conserva un fallback seguro y evita que una función avanzada bloquee el valor central. La arquitectura parte de evidencia Copernicus reproducible, clasifica confianza satelital, aplica un screening hidro-sedimentario exploratorio solo cuando la evidencia lo permite y comunica resultados mediante un brief agrícola controlado.

La decisión técnica actual es construir un MVP oficial con foco en `corridor_wide` como AOI primario, `river` como vista secundaria y cache reproducible como base de demo. El producto no intenta detectar químicos ni validar de forma fuerte una crisis específica. Su ambición es más defendible: convertir Sentinel-2 en una herramienta que indique cuándo interpretar, cuándo revisar y cuándo no inferir.

El roadmap maximiza ambición sin depender de piezas inciertas. Si CDSE limita llamadas, se usa cache. Si la IA no está disponible, se usan plantillas. Si la señal de riesgo no es robusta, el producto conserva valor como Satellite Confidence Semáforo. Si el AOI de río falla, `corridor_wide` sostiene la operación. Esta arquitectura permite competir con una propuesta seria, reproducible y alineada con seguridad alimentaria.

## 1. Principios de arquitectura

1. **Cada fase debe ser shippable.** Ninguna fase avanzada debe impedir entregar la anterior.
2. **Cache-first.** La demo debe funcionar sin depender de conectividad o cuota CDSE en vivo.
3. **No live dependency for demo.** El live refresh es opcional y limitado.
4. **AI communicates, does not decide.** La IA redacta; no calcula índices, umbrales ni estados.
5. **Claim firewall before display.** Todo texto visible pasa por validación determinística.
6. **`corridor_wide` primary.** El AOI operacional principal es el corredor agrícola-ribereño amplio.
7. **`river` secondary.** El AOI de río se usa como zoom técnico, no como única base del producto.
8. **No chemical claims.** No se afirma detección de pesticidas, atrazina, patógenos, metales ni calidad hídrica completa.
9. **Reproducibility over spectacle.** Es preferible un brief trazable a una visualización llamativa sin base clara.
10. **Fresh official repo during hackathon.** El código oficial, dashboard y resultados finales se generan durante la ventana oficial.

## 2. Arquitectura MVP

| Módulo | Responsabilidad | Salida |
|---|---|---|
| Data ingestion | Cargar AOI, parámetros y fechas confirmadas | Configuración validada |
| Catalog discovery | Identificar adquisiciones Sentinel-2 L2A | Fechas candidatas reales |
| Statistical processing | Obtener estadísticas MNDWI/NDTI por AOI | JSON crudo y filas procesadas |
| Cache layer | Guardar y reutilizar resultados Copernicus | Demo reproducible |
| Processing layer | Normalizar índices, conteos y metadatos | CSV analítico |
| Confidence classifier | Clasificar `usable`, `low_confidence`, `invalid` | `confidence_state` |
| Risk classifier | Generar `normal`, `watch`, `review`, `do_not_infer` | `risk_state` |
| Explainability engine | Explicar reglas y límites aplicados | Mensajes auditables |
| AI BriefWriter | Redactar salidas por audiencia | Brief controlado |
| Claim Firewall | Bloquear claims peligrosos | Texto seguro o fallback |
| UI layer | Mostrar AOI, fecha, semáforos, charts y brief | Demo navegable |
| Export layer | Generar evidencia compartible | Brief exportable |
| Prediction Ledger | Registrar inferencias y versiones | Trazabilidad |

## 3. Flujo de datos

El flujo recomendado es:

1. **Copernicus Catalog API** identifica adquisiciones Sentinel-2 L2A que intersectan el AOI.
2. Las adquisiciones se convierten en **candidate dates** con fecha, datetime, nubosidad, identificador y bbox.
3. **Statistical API** calcula estadísticas para MNDWI y NDTI usando AOI reproyectado a EPSG:32617.
4. La respuesta cruda se guarda como **raw JSON cache** sin credenciales ni secretos.
5. El pipeline genera **processed CSV** con medias, desviaciones, conteos y porcentaje válido.
6. El **confidence classifier** determina si la observación es `usable`, `low_confidence` o `invalid`.
7. El **risk classifier** produce una lectura hidro-sedimentaria exploratoria, condicionada por la confianza.
8. El **explainability engine** documenta por qué se asignó cada estado.
9. El **AI BriefWriter**, si está disponible, transforma el JSON estructurado en texto por audiencia.
10. El **Claim Firewall** revisa cualquier texto antes de mostrarlo.
11. La **UI, export y ledger** presentan o registran la salida final.

## 4. Esquema de datos

| Campo | Tipo | Descripción |
|---|---|---|
| `date` | string | Fecha de observación o fecha candidata. |
| `datetime` | string | Timestamp de adquisición Sentinel-2 cuando exista. |
| `aoi_label` | string | `corridor_wide`, `river`, `broad` u otro nodo futuro. |
| `aoi_type` | string | Corredor, zoom río, baseline amplio o réplica regional. |
| `index` | string | `mndwi`, `ndti` u otro índice permitido. |
| `mndwi_mean` | number/null | Media MNDWI procesada. |
| `mndwi_stdev` | number/null | Desviación estándar MNDWI. |
| `ndti_mean` | number/null | Media NDTI procesada. |
| `ndti_stdev` | number/null | Desviación estándar NDTI. |
| `sampleCount` | integer | Conteo total reportado por Statistical API. |
| `noDataCount` | integer | Conteo sin datos o inválido. |
| `validPercent` | number | Porcentaje aproximado de observaciones válidas. |
| `confidence_state` | string | `usable`, `low_confidence` o `invalid`. |
| `risk_state` | string | `normal`, `watch`, `review` o `do_not_infer`. |
| `recommendation_code` | string | Código corto de recomendación agrícola. |
| `explanation_rules` | array/string | Reglas que justifican la salida. |
| `source_mode` | string | `cache` o `live`. |
| `cdse_item_id` | string/null | Identificador de adquisición si está disponible. |
| `generated_at` | string | Fecha de generación del resultado. |
| `algorithm_version` | string | Versión de reglas del MVP. |
| `limitations` | array/string | Limitaciones visibles para usuario y jurado. |

## 5. Reglas de decisión

### Confidence state

| Estado | Regla inicial | Consecuencia |
|---|---:|---|
| `invalid` | `validPercent < 10` | No interpretar riesgo. |
| `low_confidence` | `10 <= validPercent < 30` | Mostrar cautela y posible revisión. |
| `usable` | `validPercent >= 30` | Permitir comparación exploratoria. |

### Risk state

| Estado | Uso previsto |
|---|---|
| `do_not_infer` | Obligatorio cuando confidence es `invalid`. |
| `normal` | Señal sin desviación exploratoria relevante. |
| `watch` | Señal que merece atención, no acción automática. |
| `review` | Señal que justifica priorizar verificación local. |

Los umbrales exactos de riesgo deben ajustarse durante la construcción oficial. No se debe fingir calibración operacional ni presentar estas reglas como validación definitiva. Si las estadísticas no sostienen diferenciación, la salida correcta es limitar el producto al estado de confianza y recomendación de revisión o no inferencia.

## 6. IA y seguridad de claims

El AI BriefWriter opera en tres modos de proveedor: `none`, `gemini` u `openrouter`. El modo `none` activa plantillas locales. Los modos con LLM solo reciben JSON estructurado; no reciben secretos, archivos `.env`, credenciales ni contexto oculto.

**Reglas de seguridad:**

| Regla | Implementación |
|---|---|
| La IA no altera `risk_state` | El estado llega precomputado. |
| La IA no altera `confidence_state` | El estado llega precomputado. |
| La IA no agrega fuentes | Solo resume campos del input. |
| La IA no emite claims químicos | Claim Firewall bloquea frases prohibidas. |
| La IA no genera órdenes obligatorias | Recomendaciones se formulan como apoyo. |
| Todo texto queda auditable | Se registran proveedor, plantilla, versión y bloqueos. |

**Patrones bloqueados:**

| Categoría | Ejemplos de patrón |
|---|---|
| Chemical detection | atrazina, pesticida, contaminación química, metales pesados |
| Safety certification | agua segura, safe water, calidad hídrica completa |
| Operational certainty | tiempo real, cierre automático, suspensión obligatoria |
| Crisis overclaim | validamos la crisis, crisis validated |
| Prediction certainty | predicción garantizada, guaranteed prediction |

Si el firewall detecta una frase peligrosa, reemplaza el texto por una plantilla segura y registra `blocked_claim=true` con categoría y timestamp. La salida segura debe recordar que AgroShield no reemplaza muestreo local ni laboratorio.

## 7. UI architecture

La UI oficial se construirá durante el hackathon. La arquitectura visual debe priorizar claridad operativa sobre decoración.

| Pantalla | Función |
|---|---|
| Landing | Presenta problema, alcance y modo demo/cache. |
| AOI/date selector | Permite elegir `corridor_wide`, `river` y fecha catalogada. |
| Confidence panel | Muestra semáforo de confianza y porcentaje válido. |
| Risk panel | Muestra screening hidro-sedimentario si procede. |
| Charts | Presenta MNDWI/NDTI y comparación simple. |
| Explainability panel | Explica reglas, límites y razón de estado. |
| AI brief | Muestra texto por audiencia con fallback local. |
| Ledger | Lista inferencias, versión de algoritmo y limitaciones. |
| Export | Prepara brief reproducible para discusión. |
| Roadmap | Muestra expansión regional sin prometer producción. |

Los componentes mínimos son mapa, badge de AOI, selector de fecha, badge de confianza, badge de riesgo, barra de píxeles válidos, tabla de evidencia, explicación, recomendación, caja de limitaciones y modo cache/live.

## 8. Roadmap por fases

| Phase | Name | Objective | Build | Input | Output | Success criterion | Fallback | Risk | Demo value | Priority | Status |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 0 | Evidence Kernel | Probar evidencia mínima reproducible | Cache loader, schema, filas procesadas | CSV/JSON Copernicus | Tabla base | Datos cargan y se trazan | Dataset estático | Datos incompletos | Base creíble | 1 | core |
| 1 | Satellite Confidence Semáforo | Clasificar calidad de observación | Reglas `validPercent` | Processed rows | Confidence state | Estados consistentes | Solo tabla de confianza | Umbrales simples | Diferenciación central | 2 | core |
| 2 | Hydro-Sedimentary Screening | Evaluar señal óptica exploratoria | Reglas MNDWI/NDTI | Confidence usable/low | Risk state | No infiere con invalid | Confidence-only | Señal débil | Valor agrícola | 3 | core |
| 3 | Agricultural Decision Brief | Traducir estado a recomendación | Brief local | Estados y reglas | Recomendación | Usuario entiende acción prudente | Mensaje manual | Lenguaje ambiguo | Demo útil | 4 | core |
| 4 | Risk Explainability Panel | Defender por qué salió un estado | Motor de reglas visible | Evidencia + estados | Explicación | Jurado entiende límites | Texto estático | Complejidad | Q&A fuerte | 5 | core |
| 5 | Multi-AOI Decision Mode | Comparar AOI primario/secundario | Selector AOI | `corridor_wide`, `river` | Comparación | AOI no confunden | Solo `corridor_wide` | River frágil | Profundidad técnica | 6 | stretch |
| 6 | Evidence Packet Export | Compartir salida reproducible | Export Markdown/CSV | Brief + ledger | Evidence packet | Export abre sin errores | Copia pantalla/CSV | Formato falla | Material de revisión | 7 | stretch |
| 7 | Optional Live Refresh | Mostrar una llamada en vivo limitada | Botón refresh | CDSE creds locales | Nueva fila | Una fecha actualiza | Cache-only | Rate limit | Credibilidad técnica | 10 | stretch |
| 8 | AI BriefWriter | Adaptar lenguaje por audiencia | LLM o templates | JSON estructurado | Brief por audiencia | Fallback funciona | Plantillas locales | LLM falla | Madurez producto | 8 | stretch |
| 9 | AI Claim Firewall | Bloquear claims peligrosos | Validador regex/reglas | Texto AI/template | Texto seguro | Bloquea ejemplos prohibidos | Plantilla segura | Falso negativo | Confianza ética | 9 | stretch |
| 10 | Prediction Ledger | Registrar decisiones y versión | Tabla ledger | Resultados finales | Historial | Cada inferencia trazable | CSV simple | Sobrecarga | Trust differentiator | 11 | stretch |
| 11 | Food Security Impact Layer | Conectar a impacto agroalimentario | Indicadores cualitativos | Cultivos/contexto | Impact notes | No exagera impacto | Texto de contexto | Falta fuente | Historia sectorial | 15 | roadmap |
| 12 | Regional Replication Pack | Mostrar cómo escalar ALC | Plantilla nodo | GeoJSON + metadata | Pack regional | Nuevo nodo se define | Ejemplo conceptual | Prometer demasiado | Escalabilidad | 12 | stretch |
| 13 | Controlled Community Verification | Incorporar revisión local | Formulario/bitácora | Observación campo | Verificación posterior | No reemplaza lab | Plan metodológico | Datos sensibles | Puente campo | 16 | post-hackathon |
| 14 | Sentinel-1 Cloud-Resilience Layer | Reducir impacto de nubosidad | Capa SAR futura | S1 GRD/RTC | Indicador alterno | Mejora fechas nubladas | S2-only | Complejidad SAR | Resiliencia | 17 | post-hackathon |
| 15 | Institutional Policy Brief Mode | Comunicar a institución | Brief institucional | Estados/impacto | Policy note | Lenguaje prudente | Brief técnico | Overclaim | B2G | 18 | roadmap |
| 16 | Crop Corridor Overlay | Relacionar AOI con cultivo | Overlay agrícola | Capas cultivo | Contexto productivo | No inventa cultivos | Texto genérico | Fuente faltante | Food security link | 19 | roadmap |
| 17 | Water Productivity / Irrigation Stress Roadmap | Explorar eficiencia hídrica | Diseño futuro | ET/clima/cultivo | Roadmap | Queda separado del MVP | Documento futuro | Scope creep | Visión técnica | 20 | roadmap |
| 18 | Anticipatory Action Trigger Design | Diseñar triggers prudentes | Matriz conceptual | Señal + confianza | Trigger design | No automatiza órdenes | Recomendación manual | Falsa alarma | Acción anticipatoria | 21 | roadmap |
| 19 | Resilience Scorecard | Evaluar madurez de corredor | Scorecard | Historial + contexto | Puntuación cualitativa | Transparente | Checklist simple | Subjetividad | Visión sistémica | 22 | roadmap |
| 20 | Production Architecture Roadmap | Diseñar despliegue futuro | AWS/hosting plan | MVP probado | Arquitectura | No se mezcla con MVP | Documento conceptual | Costo | Camino piloto | 23 | post-hackathon |

## 9. Build order recomendado

**Hackathon core:** fases 0, 1, 2, 3 y 4. Estas fases producen el producto defendible mínimo: evidencia, confianza, screening, recomendación y explicación.

**Strong demo:** fases 5 y 6. Multi-AOI y export elevan la presentación sin cambiar el núcleo científico.

**AI maturity:** fases 8 y 9. AI BriefWriter y Claim Firewall muestran madurez, siempre con fallback.

**Trust differentiator:** fase 10. Prediction Ledger convierte la demo en sistema auditable.

**Regional scalability:** fase 12. El replication pack permite narrar expansión a ALC sin prometer nodos ya construidos.

**Post-hackathon:** fases 11, 13, 14, 15, 16, 17, 18, 19 y 20. Estas funciones requieren fuentes, validación o ingeniería adicional.

## 10. Fallback strategy

| Escenario | Qué se entrega |
|---|---|
| Risk signal no mueve | Satellite Confidence Semáforo + recomendación de no inferir o verificar localmente. |
| CDSE rate limit | Demo cache-first con registro de fuente y explicación de cuota. |
| AI falla | Plantillas locales por audiencia. |
| Live refresh falla | Modo cache reproducible, sin afectar demo central. |
| River AOI falla | `corridor_wide` como AOI operacional primario. |
| UI no llega a polish | Brief tabular con semáforos y explicación mínima. |
| Export falla | Mostrar ledger y permitir descarga CSV simple. |
| Jurado cuestiona química | Responder que no se detectan químicos; se hace screening óptico exploratorio y se recomienda verificación local. |

## 11. Arquitectura de producción futura

La arquitectura de producción pertenece a una etapa posterior al MVP. Una versión piloto podría usar:

| Componente futuro | Uso posible |
|---|---|
| AWS Lambda | Procesamiento programado por AOI y fecha. |
| S3 | Almacenamiento de JSON crudo, CSV, briefs y exports. |
| DynamoDB | Ledger de observaciones y estados. |
| EventBridge | Programación de actualizaciones controladas. |
| Secrets Manager | Manejo seguro de credenciales CDSE y proveedores AI. |
| CloudFront o hosting Streamlit | Publicación institucional o piloto. |
| Twilio opcional | Notificación, solo si existe protocolo institucional. |
| Sentinel-1 | Capa de resiliencia ante nubosidad. |
| CHIRPS/ERA5 opcional | Contexto climático, no núcleo inicial. |

Nada de esta arquitectura debe presentarse como parte obligatoria del MVP core. Su función es demostrar que el proyecto puede evolucionar si la validación científica y de usuario lo justifica.

## 12. Plan de escalabilidad regional

La unidad de réplica regional es un nodo de cuenca o corredor productivo:

`new basin node = GeoJSON + metadata + crop/food security context + dates + rules`

Para escalar a América Latina y el Caribe, cada nuevo nodo debe definir AOI, cultivo o cadena alimentaria relevante, fuente Copernicus, calendario de observaciones, reglas de confianza, límites y mecanismo de verificación local. La arquitectura no promete 52 nodos construidos en el hackathon; promete una plantilla clara para replicar con disciplina.

El valor regional está en separar el motor común de las condiciones locales. El motor clasifica confianza y genera briefs; el contexto local ajusta AOI, cultivos, umbrales exploratorios y actores.

## 13. Riesgos técnicos

| Riesgo | Mitigación | Fallback |
|---|---|---|
| Rate limit | Cache-first, max requests, backoff | Demo sin live refresh |
| Cloud cover | Catalog API, confidence rules | `do_not_infer` |
| Weak signal | No forzar NDTI; explicar incertidumbre | Confidence-only |
| AOI geometry | `corridor_wide` primario, `river` secundario | Ajustar AOI |
| Resolution | EPSG:32617 y resolución métrica explícita | Usar 20 m |
| AI hallucination | Input estructurado + firewall | Plantillas |
| Eligibility | Repo fresco y no copiar código spike | Reimplementar desde specs |
| Cost | Evitar servicios cloud en MVP | Local/cache |
| Security | No imprimir secretos, `.env` ignorado | Modo offline |
| Overengineering | Fases core primero | Cortar stretch |
| Demo failure | Cache reproducible | CSV + brief |

## 14. Métricas de éxito

**Métricas técnicas:**

| Métrica | Éxito esperado |
|---|---|
| CDSE auth works | Autenticación funcional durante construcción oficial. |
| Catalog returns dates | Fechas Sentinel-2 reales para AOI. |
| Stats return rows | MNDWI/NDTI procesables. |
| Usable dates exist | Al menos un AOI produce filas `usable`. |
| Confidence classifier works | Estados coherentes con `validPercent`. |
| Risk classifier works | No interpreta cuando confidence es `invalid`. |
| UI demo loads from cache | Demo independiente de red. |
| Claim firewall blocks bad text | Frases prohibidas se reemplazan. |
| MVP reproducible | Datos, reglas y versión son trazables. |

**Métricas de producto:**

| Métrica | Éxito esperado |
|---|---|
| Usuario entiende infer/review/not infer | La recomendación es clara y proporcional. |
| Profesora/jurado entiende food security link | Agua se presenta como infraestructura agrícola. |
| Escala por GeoJSON | Nuevo nodo se explica sin rehacer producto. |
| No prohibited claims | No hay afirmaciones químicas ni operacionales indebidas. |

## 15. Conclusión estratégica

AgroShield gana si no intenta parecer omnisciente. Gana si demuestra que Copernicus puede convertirse en decisiones agrícolas honestas bajo incertidumbre.

La arquitectura recomendada protege la elegibilidad, reduce fragilidad técnica y sostiene una narrativa competitiva: no otro dashboard de mapas, sino una herramienta que decide cuándo la evidencia satelital es confiable, cuándo debe revisarse y cuándo no debe inferirse. Esa disciplina es precisamente lo que hace defendible su aplicación en seguridad alimentaria.
