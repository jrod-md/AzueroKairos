# AgroShield: Propuesta Técnica Académica v3

**Documento académico preparatorio. No constituye entrega oficial del hackathon. El código, dashboard, resultados finales y entregables oficiales serán generados durante la ventana oficial de competencia.**

## Portada textual

**Universidad Tecnológica de Panamá**  
**Facultad de Ingeniería de Sistemas Computacionales**

**Proyecto:** AgroShield

**Título:** AgroShield: semáforo Copernicus de confianza satelital y riesgo hídrico agrícola en Azuero

**Subtítulo:** Brief reproducible para decidir cuándo la evidencia Sentinel-2 permite interpretar riesgo hidro-sedimentario y cuándo la incertidumbre exige verificación local

**Autor/equipo:** [Campo editable]

**Fecha:** [Campo editable]

**Nota:** Documento académico preparatorio, no entrega oficial del hackathon.

## Resumen ejecutivo

La seguridad alimentaria en Azuero depende de decisiones agrícolas tomadas bajo incertidumbre hídrica. En el corredor del Río La Villa, el agua funciona como infraestructura de producción: sostiene riego, lavado, inocuidad, agroexportación y continuidad de abastecimiento. Cuando ocurren eventos de lluvia, turbidez, nubosidad o cambios rápidos en el cauce, productores e instituciones pueden quedar entre dos riesgos: actuar sin evidencia suficiente o interpretar como ausencia de riesgo una observación satelital débil.

AgroShield propone una herramienta de apoyo a decisiones agrícolas basada en Copernicus Sentinel-2 L2A. Su núcleo no es declarar contaminación, sino clasificar la confianza de la observación satelital mediante un **Satellite Confidence Semáforo** y, cuando la evidencia es suficiente, generar un screening exploratorio de señal hidro-sedimentaria usando MNDWI y NDTI. El resultado se resume en un **AgroShield Confidence Brief** que comunica fecha, AOI, píxeles válidos, índices, estado de confianza, estado de riesgo exploratorio, explicación y recomendación proporcional.

Las pruebas internas descartables demuestran que CDSE, Catalog API, Statistical API, reproyección a EPSG:32617 y estadísticas MNDWI/NDTI son técnicamente viables. La validación fuerte de una crisis de junio de 2025 no está probada. La decisión técnica actual es **GO TECHNICAL / ADJUST SCIENTIFIC**. El MVP oficial, con código fresco y entregables generados durante la competencia, debe construirse como evidencia reproducible con cache Copernicus y live refresh opcional.

## 1. Introducción

En Azuero, el agua de río no debe entenderse únicamente como un recurso natural aislado. Para la agricultura, es parte de la infraestructura productiva que permite regar, lavar productos, sostener calendarios de cosecha, reducir pérdidas y mantener condiciones mínimas de inocuidad. Cuando la lectura del estado hídrico es incierta, las decisiones agrícolas pueden volverse reactivas, tardías o basadas en percepción local incompleta.

El problema no es solo detectar un evento visible. También importa saber cuándo la evidencia disponible no alcanza para inferir. Una observación con demasiada nube, pocos píxeles válidos, AOI mal definido o señal óptica débil puede producir una falsa sensación de seguridad. En seguridad alimentaria, una conclusión prematura puede ser tan riesgosa como la ausencia total de monitoreo.

AgroShield nace como una propuesta para reducir decisiones ciegas en el corredor agrícola-ribereño del Río La Villa. Su enfoque es deliberadamente conservador: primero evalúa si la evidencia satelital es interpretable; después, y solo si la calidad mínima se cumple, genera un screening hidro-sedimentario exploratorio. Esta lógica convierte Copernicus en una herramienta de decisión prudente, no en un sustituto de laboratorio ni en un sistema operacional cerrado.

## 2. Planteamiento del problema

La producción agrícola en zonas ribereñas depende de agua disponible y suficientemente controlada para operaciones como riego, lavado, manejo poscosecha y planificación de labores. En el área de Chitré-La Arena y el entorno del Río La Villa, un evento hidro-sedimentario puede afectar la forma en que productores, operadores técnicos o instituciones priorizan revisión local.

Actualmente existen tres vacíos prácticos. Primero, los datos satelitales de Copernicus no siempre llegan al usuario agrícola como una decisión comprensible. Segundo, durante lluvia o nubosidad, la falta de señal interpretable puede confundirse con falta de riesgo. Tercero, muchos tableros muestran mapas o series temporales sin explicar si la observación base es suficientemente confiable para apoyar una recomendación.

Por ello, AgroShield plantea que antes de un semáforo de riesgo debe existir un semáforo de confianza. Si el sistema no puede sostener una inferencia satelital mínima, la salida correcta no es normalidad, sino **do not infer** y recomendación de verificación local. Esta distinción protege la utilidad agrícola del producto y evita transformar incertidumbre técnica en certeza falsa.

## 3. Justificación

AgroShield se justifica desde seguridad alimentaria porque conecta observación satelital con decisiones que influyen en continuidad productiva, inocuidad agrícola y respuesta temprana ante condiciones hídricas inciertas. La propuesta se enfoca en productores, asociaciones agropecuarias, operadores técnicos e instituciones que necesitan priorizar revisión sin depender únicamente de reportes manuales o percepción visual.

Su relevancia para Azuero surge de la relación entre agricultura, agua superficial y vulnerabilidad a eventos hidroclimáticos. El Río La Villa permite construir un caso local concreto, pero el diseño se formula para ser replicable en América Latina y el Caribe mediante nuevos AOI, metadatos de cultivo y reglas documentadas.

El uso de Copernicus es sustantivo porque la propuesta no usa imágenes como elemento decorativo. El MVP se fundamenta en Sentinel-2 L2A, Catalog API, Statistical API, cache reproducible, MNDWI, NDTI y clasificación explícita de confianza. La contribución no es otro dashboard descriptivo: es una capa de interpretación que responde si la evidencia satelital permite decidir, revisar o abstenerse de inferir.

## 4. Objetivo general

Crear una herramienta de apoyo a decisiones agrícolas que use evidencia Copernicus para clasificar la confianza satelital y generar un screening exploratorio de riesgo hidro-sedimentario en un corredor agrícola-ribereño del Río La Villa.

## 5. Objetivos específicos

1. Obtener fechas Sentinel-2 L2A confirmadas mediante Copernicus Data Space Ecosystem / Sentinel Hub Catalog API para el corredor de estudio.
2. Calcular estadísticas MNDWI y NDTI con CDSE/Sentinel Hub Statistical API sobre AOI definidos y documentados.
3. Clasificar cada observación en estados de confianza: `usable`, `low_confidence` o `invalid`.
4. Generar un estado exploratorio de riesgo hidro-sedimentario condicionado por la confianza de la observación.
5. Producir un **AgroShield Confidence Brief** con evidencia, explicación, recomendación proporcional y limitaciones.
6. Integrar un panel de explicabilidad que muestre por qué el sistema permitió o bloqueó una inferencia.
7. Diseñar una capa de IA controlada que redacte briefs por audiencia sin alterar cálculos, estados ni reglas científicas.

## 6. Alcance del MVP

El MVP oficial se construirá durante la ventana oficial del hackathon en un repositorio fresco. Este documento solo define alcance académico preparatorio.

**El MVP sí incluye:**

| Componente | Inclusión prevista |
|---|---|
| CDSE/Sentinel Hub Statistical API | Sí, para estadísticas Copernicus sobre AOI seleccionados. |
| Sentinel-2 L2A | Sí, como fuente óptica principal. |
| `corridor_wide` AOI | Sí, como AOI operacional primario. |
| `river` AOI | Sí, como vista secundaria o zoom técnico si el tiempo lo permite. |
| MNDWI/NDTI | Sí, como indicadores exploratorios. |
| Cache reproducible | Sí, para demo estable y trazabilidad. |
| Streamlit o UI simple | Sí, durante el hackathon, no antes. |
| Confidence state | Sí, como salida central. |
| Exploratory risk state | Sí, condicionado por confianza suficiente. |
| Explainability panel | Sí, para justificar estados y límites. |
| AI BriefWriter | Opcional, con fallback local. |
| Claim Firewall | Sí, para bloquear afirmaciones peligrosas. |

**El MVP no incluye:**

| Exclusión | Razón |
|---|---|
| Detección química | Sentinel-2 no permite afirmar pesticidas, atrazina, metales o patógenos. |
| Validación de crisis de junio 2025 | El spike no probó validación fuerte de ese evento. |
| Sentinel-1 como núcleo | Puede ser expansión si el core está completo. |
| AWS producción | Pertenece a arquitectura futura, no al MVP core. |
| Twilio | No habrá alertas operacionales en el MVP. |
| Alertas obligatorias | La salida es apoyo a decisión, no mandato automático. |
| NitroSync | Fuera de alcance del MVP. |
| 52 nodos | La replicabilidad se diseña, no se promete construida. |
| Laboratorio | No sustituye muestreo físico ni análisis químico. |
| Decisiones automáticas | No cierra tomas ni suspende riego por sí mismo. |

## 7. Metodología

### 7.1 Área de estudio

El área inicial se ubica en Azuero, Panamá, con énfasis en el corredor agrícola-ribereño del Río La Villa cerca de Chitré-La Arena. La hipótesis operacional usa `corridor_wide` como unidad primaria porque busca equilibrar dos necesidades: capturar señal asociada al entorno agrícola-ribereño y evitar que una caja demasiado amplia diluya el fenómeno.

El AOI `river` se mantiene como zoom técnico para observar comportamiento más cercano al cauce, aunque las pruebas internas sugieren que puede producir menos fechas útiles por estrechez, resolución, nube o geometría. La delimitación exacta debe revisarse durante el hackathon y, si el proyecto evoluciona, con apoyo de conocimiento local o cartografía validada.

### 7.2 Datos Copernicus

La fuente principal es Sentinel-2 L2A mediante Copernicus Data Space Ecosystem / Sentinel Hub. El Catalog API permite identificar adquisiciones reales disponibles para el AOI, evitando seleccionar fechas arbitrarias. El Statistical API permite calcular estadísticas por índice y AOI sin descargar escenas completas.

El MVP debe operar en modo cache-first. Esto significa que los resultados Copernicus procesados durante la competencia se guardan de forma reproducible y la demo no depende de una llamada en vivo. Un live refresh puede existir como demostración limitada si la cuota y la conectividad lo permiten.

### 7.3 Índices

**MNDWI** se usa como soporte para observar presencia o condición de superficie hídrica:

`MNDWI = (B03 - B11) / (B03 + B11)`

Su utilidad en AgroShield no es certificar calidad del agua, sino apoyar la interpretación de condiciones hídricas observables.

**NDTI** se usa como proxy exploratorio hidro-sedimentario:

`NDTI = (B04 - B03) / (B04 + B03)`

Su lectura debe tratarse como aproximación óptica, no como medición directa de sedimentos en campo. NDCI puede quedar fuera del MVP o considerarse como expansión si existe justificación científica y tiempo de implementación.

### 7.4 Semáforo de confianza

El semáforo de confianza clasifica la observación antes de permitir interpretación de riesgo:

| Estado | Regla inicial | Interpretación |
|---|---:|---|
| `invalid` | `validPercent < 10` | No inferir riesgo desde la observación satelital. |
| `low_confidence` | `10 <= validPercent < 30` | Lectura posible, pero de baja confianza. |
| `usable` | `validPercent >= 30` | Evidencia suficiente para comparación exploratoria. |

La regla crítica es: si `confidence_state = invalid`, entonces `risk_state = do_not_infer`.

### 7.5 Screening hidro-sedimentario

El screening hidro-sedimentario se expresa como `normal`, `watch`, `review` o `do_not_infer`. No debe presentarse como validación operacional, predicción garantizada ni medición química. Su función es priorizar atención y revisión local cuando la señal Copernicus es interpretable y se desvía de una referencia exploratoria.

Los umbrales exactos se ajustarán durante la construcción oficial, usando datos cacheados y reglas transparentes. Si NDTI no diferencia condiciones de interés, el producto puede seguir siendo defendible como Satellite Confidence Semáforo con recomendación de no inferir riesgo hidro-sedimentario.

### 7.6 IA controlada

El componente de IA se limita a comunicación. El **AI BriefWriter** recibe un JSON estructurado con estados ya calculados y redacta una explicación según audiencia: productor, operador técnico, jurado o institución. La IA no calcula índices, no define umbrales, no cambia estados y no agrega datos externos ocultos.

Antes de mostrarse, cualquier texto generado pasa por un **Claim Firewall** determinístico. Si aparecen afirmaciones prohibidas, el sistema bloquea o reemplaza el texto con una plantilla segura.

### 7.7 Reproducibilidad

El MVP debe guardar datos crudos, CSV procesados, versión de algoritmo, fecha de generación, AOI y limitaciones. La demo se basará en cache reproducible para evitar que conectividad, cuota o rate limits determinen el resultado frente al jurado.

Un ledger de predicciones puede registrar fecha, AOI, estados, recomendación, versión y limitaciones. Su propósito no es declarar verdad histórica inmediata, sino crear trazabilidad para comparación futura con observaciones de campo.

## 8. Resultados preliminares del spike interno

Las pruebas internas descartables resolvieron los bloqueos técnicos principales. La autenticación CDSE funciona. Las llamadas al Catalog API y Statistical API devuelven datos. La reproyección desde CRS84/lonlat a EPSG:32617 fue necesaria para que la resolución en metros se interpretara correctamente. Con esa corrección, MNDWI y NDTI retornan estadísticas para AOI definidos.

La comparación preliminar de AOI mostró que `broad` devuelve más datos, pero puede mezclar áreas urbanas, agrícolas y ribereñas de forma que diluye la señal. `river` es científicamente cercano al cauce, pero más frágil por tener menos píxeles y fechas útiles. `corridor_wide` aparece como el compromiso primario más defendible para el MVP: captura contexto agrícola-ribereño sin promediar toda la caja amplia.

La crisis de junio de 2025 no quedó validada. El hallazgo honesto es **GO TECHNICAL / ADJUST SCIENTIFIC**: la base Copernicus funciona, pero la narrativa científica debe mantenerse exploratoria, con incertidumbre explícita y sin claims de detección química.

Estos resultados pertenecen a un spike interno de factibilidad y no constituyen entrega oficial del hackathon.

## 9. Propuesta de solución

AgroShield se presenta como un **AgroShield Confidence Brief**. En lugar de entregar solo un mapa, el brief organiza evidencia y decisión:

| Elemento | Función |
|---|---|
| Mapa | Contextualiza el AOI seleccionado. |
| AOI | Define si se analiza `corridor_wide`, `river` u otro nodo futuro. |
| Fecha | Identifica adquisición Sentinel-2 o fecha derivada de catálogo. |
| Confidence semáforo | Indica si la observación permite inferir. |
| Risk semáforo exploratorio | Resume condición hidro-sedimentaria solo si hay confianza suficiente. |
| Valid pixels | Explica cuánta evidencia sostiene la lectura. |
| MNDWI/NDTI | Muestra indicadores ópticos usados. |
| Explicación | Justifica reglas aplicadas y limitaciones. |
| Recomendación agrícola | Sugiere interpretar, revisar, verificar localmente o no inferir. |
| Export/brief | Permite registrar la salida para discusión técnica. |

La propuesta se diferencia de un tablero genérico porque empieza con una pregunta de calidad de evidencia: ¿la observación satelital es suficientemente confiable para apoyar una decisión agrícola?

## 10. Componente de IA

La IA puede aumentar claridad sin ocupar el lugar del motor científico. En AgroShield, el riesgo se calcula con reglas determinísticas sobre datos Copernicus procesados. La IA solo traduce esa estructura en lenguaje útil para distintas audiencias.

**Dónde entra la IA:**

| Uso | Descripción |
|---|---|
| Productor | Resume acción recomendada con lenguaje no técnico. |
| Técnico | Explica validPercent, AOI, índices y reglas. |
| Jurado | Enfatiza reproducibilidad, límites y valor Copernicus. |
| Institución | Formula recomendación prudente para priorización o coordinación. |

**Dónde no entra la IA:**

| Prohibición | Motivo |
|---|---|
| Calcular MNDWI/NDTI | Lo hace el pipeline geoespacial. |
| Cambiar `risk_state` | El estado proviene de reglas auditables. |
| Declarar contaminación | No hay base satelital directa para ello. |
| Inventar eventos o fuentes | Solo usa input estructurado. |
| Emitir órdenes obligatorias | El sistema es apoyo a decisión. |

Los proveedores posibles son Gemini Flash/Flash-Lite, OpenRouter o modo `none`. Si no hay proveedor disponible, se usan plantillas locales. En todos los casos, el texto pasa por Claim Firewall antes de mostrarse.

**Ejemplos de salida controlada:**

| Audiencia | Ejemplo seguro |
|---|---|
| Productor | “Para esta fecha, la evidencia satelital del corredor agrícola se clasifica como usable. La señal hidro-sedimentaria sugiere revisar condiciones locales antes de decisiones sensibles. Esta lectura no detecta químicos ni reemplaza muestreo local.” |
| Técnico | “La observación presenta píxeles válidos suficientes para una comparación exploratoria. MNDWI y NDTI deben interpretarse como indicadores ópticos, no como validación de calidad hídrica completa.” |
| Jurado | “AgroShield convierte evidencia Copernicus en un semáforo de confianza y una recomendación proporcional, priorizando reproducibilidad y límites explícitos.” |
| Institución | “La salida puede apoyar priorización de verificación local, sin constituir orden automática ni certificación sanitaria.” |

## 11. Impacto esperado

El impacto esperado se concentra en mejorar decisiones bajo incertidumbre. Para productores, AgroShield puede ayudar a diferenciar entre una fecha interpretable y una fecha donde conviene no inferir. Para operadores técnicos, puede ordenar evidencia Copernicus en un brief trazable. Para instituciones, puede servir como mecanismo de priorización inicial antes de coordinar verificación local.

En seguridad alimentaria, el valor no reside en prometer certeza absoluta. El valor está en reducir decisiones ciegas en riego, lavado e inocuidad agrícola cuando existe evidencia satelital útil, y en advertir cuando esa evidencia no alcanza. La replicabilidad regional se logra al convertir cada nuevo nodo en una combinación de GeoJSON, metadatos agrícolas, fechas catalogadas, reglas y limitaciones explícitas.

## 12. Limitaciones

AgroShield no detecta químicos, pesticidas, atrazina, patógenos, metales pesados ni calidad hídrica completa. Sentinel-2 ofrece evidencia óptica de superficie, no medición de laboratorio. La nubosidad, sombras, resolución espacial, mezcla de píxeles y geometría del AOI pueden afectar la interpretación.

`corridor_wide` es un compromiso entre estabilidad estadística y relevancia agrícola-ribereña, no una delimitación final validada en campo. `river` puede ser útil como zoom, pero su estrechez puede reducir fechas interpretables. El MVP no será un sistema de producción ni una herramienta operacional lista. Las llamadas CDSE pueden enfrentar rate limits, por lo que la cache reproducible es parte del diseño técnico y de la estrategia de demo.

Toda recomendación debe entenderse como apoyo a decisión, no como sustituto de muestreo local, laboratorio, criterio técnico institucional o protocolos sanitarios.

## 13. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación | Fallback |
|---|---|---|---|
| Cloud cover | Fechas sin evidencia útil | Usar Catalog API, filtrar calidad y mostrar confidence | `do_not_infer` |
| Rate limit | Demo en vivo falla | Cache-first, pocas llamadas, live refresh opcional | Demo 100% cache |
| Weak signal | NDTI no diferencia condiciones | Enfatizar confidence semáforo y límites | Satellite Confidence Semáforo |
| AI hallucination | Texto con claims peligrosos | Input estructurado y Claim Firewall | Plantillas locales |
| Eligibility | Riesgo de preconstrucción | Repo oficial fresco y código nuevo durante competencia | Usar docs solo como guía |
| Overengineering | MVP incompleto | Fases core 0-4 antes de extras | Entregar core sin IA |
| UI delay | Demo confusa | UI mínima con datos cacheados | Brief tabular simple |
| Secret leakage | Exposición de credenciales | Variables de entorno, `.gitignore`, no logs de secretos | Modo cache sin API |

## 14. Plan de trabajo oficial del hackathon

**Día 1:** crear repositorio oficial fresco, README inicial, `.gitignore`, estructura mínima y esquema de datos. Reimplementar desde cero el loader de cache y la lógica básica del pipeline. Construir una UI mínima que lea CSV cacheado o generado durante la competencia.

**Días 2-3:** implementar Satellite Confidence Semáforo, clasificación por `validPercent`, integración de MNDWI/NDTI y primer risk screening exploratorio. Validar que `invalid` siempre produzca `do_not_infer`.

**Días 4-5:** construir panel de explicabilidad, recomendaciones agrícolas proporcionales, AI BriefWriter opcional, plantillas locales y Claim Firewall determinístico.

**Días 6-7:** agregar export de brief, prediction ledger, pulido visual, narrativa de demo, revisión de claims, revisión de elegibilidad y preparación final de entrega oficial.

Si el tiempo es limitado, el orden de prioridad es: Evidence Kernel, Satellite Confidence Semáforo, Hydro-Sedimentary Screening, Agricultural Decision Brief y Risk Explainability Panel. Los módulos AI, export y live refresh son secundarios frente a una demo honesta y funcional.

## 15. Conclusión

AgroShield no promete certeza artificial. Su valor es mostrar cuándo Copernicus permite inferir y cuándo obliga a no inferir. En seguridad alimentaria, reconocer incertidumbre a tiempo también es una decisión.

La propuesta es técnicamente viable y científicamente defendible si mantiene su alcance: evidencia satelital derivada de Copernicus, semáforo de confianza, screening hidro-sedimentario exploratorio y recomendación agrícola proporcional. La estrategia recomendada es continuar con AgroShield, ajustar el diseño científico alrededor de `corridor_wide`, construir el MVP oficial desde cero durante el hackathon y proteger todas las comunicaciones con un firewall de claims.
