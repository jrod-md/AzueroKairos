# AgroShield Confidence Brief v3

**Documento académico preparatorio. No constituye entrega oficial del hackathon. El código, dashboard, resultados finales y entregables oficiales serán generados durante la ventana oficial de competencia.**

## Universidad Tecnológica de Panamá

**Proyecto:** AgroShield  
**Área:** Seguridad alimentaria, agricultura sostenible y observación de la Tierra  
**Evento objetivo:** 3er CopernicusLAC Hackathon 2026 - Seguridad Alimentaria  
**Versión:** v3  
**Autor/equipo:** [Campo editable]  
**Fecha:** [Campo editable]

## Título

**AgroShield Confidence Brief: una capa de confianza satelital para decisiones agrícolas en Azuero**

## Subtítulo

**Uso de Copernicus Sentinel para decidir cuándo una observación satelital permite interpretar, cuándo exige revisión y cuándo la respuesta responsable es no inferir.**

## Resumen

AgroShield es una propuesta de herramienta de apoyo a decisiones agrícolas para el corredor agrícola-ribereño del Río La Villa, en Azuero, Panamá. El proyecto no busca detectar químicos, pesticidas ni declarar si el agua es segura. Su objetivo es más específico y defendible: convertir evidencia satelital de Copernicus en un semáforo de confianza que indique si una observación permite interpretar condiciones hidro-sedimentarias observables o si la incertidumbre impide llegar a una conclusión responsable.

La propuesta se centra en el **AgroShield Confidence Brief**, un reporte breve que resume la fecha analizada, el área de interés, la calidad de la observación satelital, los indicadores ópticos calculados, la decisión recomendada y las limitaciones científicas. Si la observación es confiable, el sistema permite una lectura exploratoria. Si es débil, recomienda revisión. Si no hay evidencia suficiente, activa el modo **do_not_infer**.

La idea principal es que, en seguridad alimentaria, una mala inferencia también es un riesgo. AgroShield protege la decisión al mostrar cuándo Copernicus puede apoyar una lectura agrícola y cuándo debe solicitarse verificación local o esperar una nueva adquisición satelital.

## 1. Planteamiento del problema

En Azuero, el agua del Río La Villa no es solamente un recurso natural. También funciona como infraestructura agrícola. De ella dependen decisiones relacionadas con riego, lavado, inocuidad, producción local, agroexportación y continuidad de actividades productivas.

Durante eventos de lluvia, nubosidad o cambios en el río, puede ser difícil saber si una observación satelital realmente permite interpretar lo que ocurre en el territorio. Un error común sería tratar una imagen con poca información válida como si fuera evidencia suficiente. Otro error sería confundir la ausencia de señal con ausencia de riesgo.

AgroShield responde a ese problema con una pregunta sencilla:

**¿Esta observación satelital es suficientemente confiable para apoyar una decisión agrícola?**

Si la respuesta es sí, el sistema entrega una lectura exploratoria. Si la respuesta es no, el sistema no fuerza conclusiones.

## 2. Idea central del proyecto

La idea ganadora de AgroShield es:

**AgroShield Confidence Brief: una capa de confianza satelital que convierte datos Copernicus en una decisión agrícola responsable: interpretar, revisar o no inferir.**

El producto no se presenta como detector de contaminación. Tampoco como sistema operacional de cierre de tomas o suspensión de riego. Se presenta como una herramienta de apoyo que ayuda a ordenar la evidencia y reducir decisiones ciegas.

La frase central del proyecto es:

**“AgroShield no reemplaza laboratorio ni declara agua segura. Convierte observaciones Sentinel en una decisión de confianza: interpretar, revisar o no inferir.”**

## 3. Qué hace AgroShield

AgroShield analiza una fecha satelital y un área de interés agrícola-ribereña. A partir de esa información produce una decisión clara:

| Estado | Significado | Acción sugerida |
|---|---|---|
| `usable` | La observación tiene suficiente información válida para una lectura exploratoria. | Interpretar con cautela y revisar indicadores. |
| `low_confidence` | Hay algo de información, pero no suficiente para un claim fuerte. | Revisar y considerar verificación local. |
| `do_not_infer` | La observación no tiene evidencia suficiente. | No hacer inferencia satelital; esperar nueva imagen o solicitar verificación local. |

La innovación no está en mostrar un mapa más. Está en decidir si el mapa y los índices deben usarse o no.

## 4. Cómo funciona, explicado de forma simple

El funcionamiento de AgroShield se puede resumir en siete pasos:

1. **Seleccionar fecha y área de interés.**  
   El sistema trabaja sobre el corredor agrícola-ribereño del Río La Villa, usando `corridor_wide` como área principal y `river` como vista secundaria.

2. **Consultar datos Copernicus.**  
   Se usan adquisiciones Sentinel confirmadas por catálogo. Esto evita escoger fechas arbitrarias.

3. **Calcular indicadores satelitales.**  
   El sistema calcula indicadores ópticos como MNDWI y NDTI. MNDWI apoya la lectura de agua o humedad observable. NDTI funciona como proxy exploratorio de condiciones hidro-sedimentarias.

4. **Medir calidad de evidencia.**  
   El dato más importante no es solo el valor del índice, sino cuánta observación válida existe. Para eso se usan métricas como `validPercent`, `sampleCount` y `noDataCount`.

5. **Clasificar confianza.**  
   Si hay suficiente evidencia, la fecha es `usable`. Si hay poca, es `low_confidence`. Si prácticamente no hay datos válidos, el sistema responde `do_not_infer`.

6. **Generar una recomendación proporcional.**  
   La salida no es una orden automática. Es una recomendación prudente: interpretar, revisar, verificar localmente o no inferir.

7. **Crear el Confidence Brief.**  
   El resultado final es un brief que explica qué se observó, qué se puede decir, qué no se puede decir y qué acción responsable se recomienda.

## 5. Núcleo Copernicus del producto

El primer nivel del sistema es el núcleo satelital. Este nivel es obligatorio e intocable porque sostiene la validez del producto.

Incluye:

- Fecha de adquisición Sentinel.
- Área de interés.
- MNDWI.
- NDTI.
- `validPercent`.
- `sampleCount`.
- `noDataCount`.
- Estado de confianza.
- Decisión recomendada.
- Ruta o referencia de evidencia procesada.

Esta pantalla debe responder en pocos segundos:

**¿Puedo usar esta observación o no?**

Si el sistema no responde eso con claridad, el producto pierde su valor.

## 6. Área de estudio

El caso piloto es el corredor agrícola-ribereño del Río La Villa, cerca de Chitré-La Arena, en Azuero. Esta zona se selecciona por su relación entre agua superficial, producción agrícola, inocuidad, riego y vulnerabilidad ante eventos hidroclimáticos.

El área primaria propuesta es `corridor_wide`. Esta zona es más específica que una caja amplia urbana-agrícola, pero más estable que un polígono demasiado estrecho siguiendo solo el cauce del río.

También se considera `river` como vista secundaria o zoom técnico. Su valor es mostrar qué ocurre cerca del cauce, pero no debe ser la única base del producto porque puede tener pocos píxeles útiles en fechas nubladas o complejas.

## 7. Resultados preliminares que guían la propuesta

Las pruebas internas descartables permitieron comprobar que la base técnica funciona:

- La autenticación con CDSE funciona.
- La consulta a Sentinel Hub / Statistical API funciona.
- La búsqueda de fechas con Catalog API funciona.
- La reproyección geográfica necesaria funciona.
- MNDWI y NDTI devuelven estadísticas.
- `corridor_wide` es actualmente el área de interés más defendible como unidad principal.

Un resultado especialmente importante fue la fecha **2025-06-10**, cercana al 11 de junio. Esa fecha dio `validPercent = 0.00%` para el área principal. La lectura correcta no es que el sistema falló. La lectura correcta es:

**AgroShield protegió la decisión al no inventar evidencia.**

Ese caso se convierte en una escena central del demo: cuando Copernicus no tiene suficiente observación válida, AgroShield responde **do_not_infer**.

## 8. Workflow de decisión

AgroShield no debe verse como un dashboard descriptivo. Debe verse como un flujo de decisión.

El flujo propuesto es:

**Satellite Observation → Confidence Engine → Decision State → Field Verification → Human Confirmation → Confidence Brief Final**

En una interfaz, esto puede mostrarse como una barra de proceso:

1. Sentinel acquisition.
2. AOI statistics.
3. Confidence classification.
4. Brief generated.
5. Field evidence requested.
6. Field officer review.
7. Final status.

Los estados posibles serían:

- `Satellite usable`.
- `Low confidence, review needed`.
- `Do not infer`.
- `Field evidence pending`.
- `Field-confirmed visible condition`.
- `Escalated to laboratory / authority`.

Este flujo hace que AgroShield sea una herramienta activa de decisión, no solo una visualización.

## 9. Verificación territorial y peritaje

El segundo nivel del producto es el workflow de verificación territorial. Esta capa debe apoyar, no reemplazar, el juicio humano.

Cuando la confianza satelital es baja o inválida, AgroShield puede solicitar evidencia de campo. Un inspector, técnico o monitor local podría adjuntar:

- Fecha de inspección.
- Coordenadas.
- Nombre o rol del inspector.
- Fotografía.
- Nota descriptiva.
- Condición visible observada.
- Recomendación local.
- Confirmación humana.

Ejemplos de condiciones visibles aceptables:

- Agua turbia visible.
- Sedimento.
- Coloración anómala.
- Obstrucción.
- Descarga visible.
- Erosión de ribera.
- Material arrastrado por lluvia.

El sistema puede organizar esta evidencia y adjuntarla al brief, pero no debe declarar contaminación química. Para químicos, pesticidas o seguridad sanitaria, siempre debe indicarse:

**“Requires laboratory confirmation.”**

## 10. Inteligencia asistida

El tercer nivel es inteligencia asistida. Esta capa puede mejorar la comunicación, pero no debe convertirse en el motor científico del proyecto.

La IA puede ayudar a:

- Resumir el brief para diferentes audiencias.
- Detectar campos incompletos en un formulario.
- Sugerir qué evidencia falta documentar.
- Redactar una nota operativa.
- Comparar si la foto, fecha y coordenadas corresponden al caso analizado.
- Preparar una explicación para productor, técnico, institución o jurado.

La IA no puede:

- Calcular el riesgo científico.
- Cambiar el estado de confianza.
- Validar contaminación.
- Declarar agua segura.
- Sustituir al inspector.
- Sustituir al laboratorio.
- Emitir una orden obligatoria de cierre o suspensión.

La frase correcta es:

**“AI-assisted evidence organizer.”**

No es:

**“AI contamination detector.”**

## 11. Claim Firewall

Para evitar errores de comunicación, AgroShield debe incluir un filtro de claims. Este filtro revisa los textos del sistema, plantillas y salidas asistidas por IA.

Debe bloquear frases que sugieran:

- Detección de atrazina.
- Detección de pesticidas.
- Detección de contaminación química.
- Agua segura.
- Calidad hídrica completa.
- Validación de crisis.
- Sistema en tiempo real.
- Cierre automático de tomas.
- Suspensión obligatoria de riego.
- Predicción garantizada.
- Reemplazo de laboratorio.

Si aparece una frase peligrosa, el sistema debe reemplazarla por una versión segura:

**“Esta salida resume evidencia satelital Copernicus disponible. No detecta químicos ni reemplaza verificación local o laboratorio.”**

## 12. Interfaz propuesta

La UI debe sentirse como una consola de decisión agrícola, no como una página decorativa.

### Pantalla 1: Decision Console

Debe mostrar:

- Estado principal del semáforo.
- Fecha.
- AOI.
- `validPercent`.
- `sampleCount`.
- `noDataCount`.
- MNDWI.
- NDTI.
- Decisión.
- Razón.
- Acción recomendada.

Para la fecha 2025-06-10 debe verse de forma clara:

**DO NOT INFER**

Y debajo:

**“No hay suficiente evidencia satelital válida para una inferencia responsable.”**

### Pantalla 2: Evidence Workflow

Muestra el estado del caso:

- Satélite procesado.
- Brief generado.
- Evidencia de campo pendiente.
- Revisión humana.
- Escalado si corresponde.

Esta pantalla convierte el producto en una herramienta operativa.

### Pantalla 3: Field Evidence

Permite registrar evidencia territorial:

- Foto.
- Coordenadas.
- Nota.
- Condición visible.
- Confirmación humana.

Debe decir claramente:

**“Visual evidence, not chemical validation.”**

### Pantalla 4: Confidence Brief

Muestra el reporte final con:

- Qué se observó.
- Qué puede inferirse.
- Qué no puede inferirse.
- Qué recomienda el sistema.
- Qué evidencia respalda la salida.
- Qué limitaciones aplican.

## 13. Ejemplo de caso: 2025-06-10

La fecha 2025-06-10 es una escena clave porque está cerca de la pregunta histórica sobre junio 2025, pero el sistema encontró 0.00% de cobertura válida sobre el área principal.

Una herramienta débil podría intentar forzar una conclusión. AgroShield no lo hace.

Salida esperada:

| Campo | Valor |
|---|---|
| Fecha | 2025-06-10 |
| AOI | `corridor_wide` |
| validPercent | 0.00% |
| Estado | `do_not_infer` |
| Razón | No hay observación válida suficiente después de filtros de nube/no-data. |
| Acción recomendada | Esperar nueva adquisición o solicitar verificación local. |
| Limitación | No se puede afirmar contaminación, seguridad del agua ni validación de crisis. |

Mensaje para demo:

**“AgroShield no falló. AgroShield protegió la decisión.”**

## 14. Qué puede ganar AgroShield

AgroShield puede competir porque une cuatro elementos:

1. **Copernicus real.**  
   Usa Sentinel y estadísticas derivadas de observación de la Tierra.

2. **Decisión clara.**  
   No se queda en mapas; produce interpretar, revisar o no inferir.

3. **Honestidad científica.**  
   Reconoce límites y evita claims peligrosos.

4. **Workflow operativo.**  
   Conecta satélite, evidencia territorial, confirmación humana y brief final.

La ventaja competitiva no es ser el proyecto más grande. Es ser el más difícil de atacar científicamente.

## 15. Qué no debe ser AgroShield

AgroShield no debe convertirse en:

- Un dashboard genérico.
- Un detector de contaminación.
- Un detector de crisis.
- Una herramienta de cierre automático.
- Una app de IA que inventa conclusiones.
- Una plataforma de producción con claims operacionales.
- Un sistema que oculta incertidumbre.

Mientras más prometa, más débil se vuelve. Mientras mejor controle su alcance, más fuerte será ante un jurado técnico.

## 16. Alcance recomendado para el MVP oficial

El MVP oficial debe construirse desde cero durante la ventana del hackathon.

### Core MVP

- Satellite Confidence Semáforo.
- AgroShield Confidence Brief.
- Evidence Ledger.
- AOI `corridor_wide`.
- AOI `river` como zoom secundario.
- Sentinel-2 como fuente principal.
- MNDWI y NDTI.
- Modo `do_not_infer`.
- Claim Firewall.

### Enhanced demo si hay tiempo

- Workflow de verificación territorial.
- Formulario de peritaje.
- Subida local de imagen.
- Estado de revisión humana.

### Stretch

- AI-assisted evidence organizer.
- Resumen automático por audiencia.
- Sentinel-1 como contexto de continuidad si se implementa de forma simple y honesta.

## 17. Impacto esperado

AgroShield puede apoyar a productores, técnicos, instituciones y organizaciones agrícolas que necesitan tomar decisiones bajo incertidumbre.

Su impacto está en:

- Reducir decisiones agrícolas ciegas.
- Evitar inferencias falsas.
- Priorizar verificación local.
- Hacer visible la calidad de la evidencia.
- Conectar observación satelital con decisión operativa.
- Facilitar trazabilidad.
- Crear una plantilla replicable a otros corredores agrícolas de América Latina y el Caribe.

En vez de prometer certeza absoluta, AgroShield propone una decisión más madura: reconocer cuándo hay evidencia y cuándo no.

## 18. Limitaciones

AgroShield no detecta químicos, pesticidas, atrazina, patógenos, metales pesados ni calidad hídrica completa. Tampoco certifica agua segura. Sentinel-2 permite observar condiciones ópticas de superficie, pero no reemplaza laboratorio.

Las nubes, sombras, resolución espacial, mezcla de píxeles y geometría del AOI pueden afectar la interpretación. Por eso el sistema incluye un semáforo de confianza antes de cualquier lectura de riesgo.

El MVP oficial no debe presentarse como sistema operacional listo. Debe presentarse como herramienta reproducible de apoyo a decisiones agrícolas con límites explícitos.

## 19. Regla de elegibilidad

Este documento es material académico preparatorio.

No debe presentarse como entrega oficial del hackathon. El repositorio oficial, código, dashboard, resultados, briefs finales, documentación final y video de entrega deben generarse durante la ventana oficial de competencia.

Las pruebas internas previas solo sirven para decidir viabilidad y orientar el diseño. No deben copiarse como entregables finales.

## 20. Conclusión

AgroShield gana si no intenta parecer omnisciente.

Su valor no está en afirmar que detecta todo, sino en proteger decisiones agrícolas bajo incertidumbre. Primero mide la confianza de la observación Sentinel. Si la evidencia es suficiente, permite una lectura exploratoria. Si es débil, recomienda revisión. Si no hay evidencia válida, responde **do_not_infer**.

La idea final es:

**AgroShield Confidence Brief es una plataforma de decisión que combina Copernicus y verificación humana: primero mide la confianza de la observación satelital; si la evidencia es suficiente, genera una lectura exploratoria; si no lo es, activa modo do_not_infer y solicita verificación territorial. El sistema no reemplaza laboratorio ni perito: organiza evidencia y protege la decisión.**

En seguridad alimentaria, una mala inferencia también es un riesgo. AgroShield convierte Copernicus en una capa de confianza para decidir cuándo interpretar, cuándo revisar y cuándo no inferir.
