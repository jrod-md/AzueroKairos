# Azuero Kairós — DESIGN.md v2

## Metáfora visual

Azuero Kairós es una bitácora de campo activa.
No un dashboard. No un centro de control.
Una estación de observación territorial donde los datos
Sentinel-2 se convierten en decisiones documentadas.

El pergamino es el canvas. El río es el dato.
La decisión es una anotación oficial sobre el territorio.

## Product Posture

Decisión primero, evidencia después.
La primera pantalla responde en menos de 10 segundos
si la observación es usable, requiere revisión,
o no debe inferirse.

## Palette

### Valores exactos

| Token                | Hex       | Uso                                      |
|----------------------|-----------|------------------------------------------|
| --bg-base            | #ede4cc   | Fondo principal (pergamino)              |
| --bg-surface         | #f5eedd   | Superficies elevadas, cards              |
| --bg-archive         | #e0d4b8   | Evidencia, zonas de archivo              |
| --text-primary       | #1d3557   | Navy — texto principal, títulos          |
| --text-secondary     | #6b5040   | Marrón cálido — labels, contexto         |
| --text-muted         | #9a8878   | Texto terciario, límites                 |
| --border             | #d4c4a0   | Separadores, bordes de cards             |
| --state-usable       | #4a8fa0   | USABLE — teal río                        |
| --state-no-inferir   | #b84c2c   | NO INFERIR — terracota                   |
| --state-revisar      | #e8922e   | REVISAR — ámbar/sol                      |
| --state-ok           | #1d3557   | Sistema OK — navy                        |
| --accent             | #4a8fa0   | Interactivo, hover, activo               |

### Reglas irrompibles de color
- Terracota es solo para evidencia insuficiente o riesgo de mala inferencia.
- Teal es solo para confianza usable confirmada.
- Ámbar es para revisión, contexto, o precaución.
- Sin colores neón. Sin verde agrícola genérico.
- El navy nunca se usa como color de estado — solo como color estructural.

## Tipografía

### Stack
- **Serif (display):** Playfair Display o Lora — headlines, nombres de sección
- **Monoespaciada (datos):** JetBrains Mono o IBM Plex Mono — 
  porcentajes, fechas, IDs, valores técnicos, ledger
- **Sans-serif (UI):** Inter — navegación, labels, botones

### Regla tipográfica central
Todo valor numérico técnico usa monoespaciada.
Los labels de sección usan sans-serif en mayúsculas con letter-spacing 0.12em.
Los headlines de decisión usan serif.

## Componentes visuales clave

### 1. Confidence Compass (gauge circular)
- SVG puro, sin librerías de charts
- Arco de 270° que se llena según validPercent
- Zona 0–30%: color --state-no-inferir
- Zona 30–60%: color --state-revisar  
- Zona 60–100%: color --state-usable
- Centro: porcentaje en JetBrains Mono, 48px
- Animación: 600ms ease-out al cambiar de fecha
- Estética: brújula cartográfica, no velocímetro sci-fi

### 2. Decision Stamp (sello de decisión)
- Elemento visual tipo tampón de caucho sobre papel
- Texto: USABLE / REVISAR / NO INFERIR
- Color: el del estado correspondiente
- Border: irregular, textura de ink stamp (SVG path o CSS)
- Animación de entrada: scale 0.8→1.0 + opacity, 300ms
- No es un badge genérico. Es un sello oficial.

### 3. Gate Chain (cadena de compuertas)
- Diagrama de flujo fluvial — curvas orgánicas, no líneas rectas
- 4 nodos: API → Calidad → Inferencia → Acción
- Nodos pasados: color --state-usable con glow sutil
- Nodo de falla: color --state-no-inferir con ícono prohibición
- SVG inline, no librería de diagramas

### 4. Azuero Lens (el corredor del río)
- Ilustración SVG del corredor Río La Villa
- Estilo consistente con el logo: capas de color planas,
  forma orgánica, sin pretender ser mapa exacto
- Tres nodos como markers con anillos de sonar pulsantes
- Color de anillo = estado Sentinel-2 del nodo
- Hover en nodo: ficha de campo flotante con datos clave
- Disclaimer obligatorio: "Vista esquemática. No es imagen satelital."
- NO es un mapa de GIS. NO es 3D. Es una ilustración interactiva.

## Screens

### Decisión
Executive report. Confidence Compass + Decision Stamp + Gate Chain.
No raw JSON paths. No MNDWI en la vista principal.

### Corredor (Kairós Watch)
Azuero Lens como hero full-width.
Matriz 3 nodos × 5 fechas debajo.
Layer toggles: S-2 / SAR / CLMS / HYDRO.

### Acción (Kairós Cases)
Tarjetas de expedición por caso.
Estado, prioridad, acción recomendada, brecha de evidencia.

### Evidencia
Archivo de auditoría.
Fondo --bg-archive. Ledger en monoespaciada.
Qué sabemos / Qué no sabemos / Por qué / Qué sigue.

## Animaciones

- Compass fill: 600ms ease-out
- Decision Stamp entrada: 300ms scale + opacity
- Sonar rings en Lens: 4s pulse, infinite, staggered por nodo
- Status bar color transition: 400ms ease
- Hover states: 150ms ease

## Non-Negotiables

- Sin reclamaciones químicas, de seguridad del agua, o de IA.
- Sin mapas falsos. El Lens es ilustración esquemática declarada.
- Sin dashboard genérico. Sin verde agrícola. Sin neón.
- Sin capa de datos sin razón de decisión.
- "No inferir" es una fortaleza del producto, no una falla.
- Preservar trazabilidad. Preservar incertidumbre.