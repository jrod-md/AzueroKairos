# Azuero Kairos: que hemos construido y que puede hacer

## 1. La idea central

Azuero Kairos es una capa de confianza para evidencia territorial basada en
Copernicus. No intenta decir "que pasa en el agua" como si fuera laboratorio.
Hace algo mas valioso y defendible: decide si una observacion satelital tiene
suficiente calidad para ser usada, si requiere revision, o si no debe usarse
para inferir.

El proyecto convierte datos Sentinel en decisiones trazables:

```text
Copernicus CDSE
  -> JSON crudo oficial
  -> CSV procesado
  -> decision de confianza
  -> brief
  -> ledger
  -> interfaz publica
  -> passport verificable
```

La fuerza del sistema esta en que sabe decir "NO INFERIR". Eso no es una
debilidad, es el producto. Evita que datos debiles se conviertan en claims
fuertes.

## 2. Que hemos construido

### Pipeline oficial de evidencia

El backend de datos ya puede pedir y procesar observaciones Sentinel-2 desde
Copernicus CDSE. Usa AOIs configurados, fechas oficiales y credenciales por
variables de entorno. El resultado se guarda como evidencia cruda y como CSV
procesado.

El motor calcula metricas como `validPercent`, `sampleCount`, `noDataCount`,
MNDWI, NDTI, estado de API y clase de confianza.

### Motor de decision

El sistema clasifica cada observacion en tres estados:

- `USABLE`: la observacion tiene evidencia valida suficiente para una lectura
  exploratoria con limites explicitos.
- `REVISAR`: la observacion tiene senal parcial o requiere cautela.
- `NO INFERIR`: la observacion no sostiene una inferencia responsable.

La decision es deterministica y reproducible. No depende de una opinion del
usuario ni de un modelo generativo.

### Evidence Ledger

El proyecto genera un ledger de evidencia que conecta:

- JSON crudo oficial.
- CSV procesado.
- decision de confianza.
- brief generado.
- hashes o referencias de artefactos.

Esto permite explicar de donde salio cada decision y que archivo la respalda.

### Frontend publico de Kairos

La interfaz evoluciono de demo tecnica a sistema de decision. Hoy muestra:

- Sistema/Ciclo Kairos: explica el ciclo completo desde satelite hasta auditoria.
- Impacto: compara escenas debiles contra escenas usables y muestra el valor de
  esperar una adquisicion valida.
- Decision: resume el estado principal, la cadena de compuertas y los limites.
- Corredor: convierte la evidencia del Rio La Villa en un workbench territorial.
- Accion: organiza los casos en una cola operativa.
- Campo: prepara verificacion lite sin crear claims nuevos.
- Passport: empaqueta una decision en un comprobante portable.
- Evidencia: muestra archivo, ledger y asistente de evidencia.

### Passport v1

Passport v1 convierte una decision en un comprobante compacto. Reune fecha,
AOI, decision, evidencia valida, API CDSE, ledger, hash y limites. La idea es
que un tercero pueda revisar el paquete sin tener que entender toda la app.

No certifica potabilidad, salud publica, contaminacion, aptitud de uso ni
respuesta institucional. Sirve para transportar confianza observacional.

### Action Queue v2

Action Queue v2 convierte los casos en trabajo operativo. La cola separa:

- casos urgentes;
- casos con verificacion recomendada;
- casos usables;
- casos listos para Passport.

Cada caso muestra decision, prioridad, porcentaje valido, accion recomendada,
brechas y una ruta de accion responsable. El objetivo es que el usuario no
salte de "dato" a "claim", sino de "dato" a "siguiente paso seguro".

### Field Verification Lite

Field Verification Lite prepara una salida de campo sin guardar datos ni
pretender reemplazar una autoridad tecnica. Para cada caso crea una ficha local
con checklist, progreso y nota segura.

Sirve para orientar observacion territorial, documentar limites y mantener la
decision `NO INFERIR` cuando la evidencia satelital no alcanza.

### Asistente de Evidencia Kairos

El Asistente de Evidencia Kairos organiza el paquete auditado. Puede preparar
un brief asistido en tres lentes:

- Brief: resumen publico de la evidencia.
- Campo: ficha orientada a observacion territorial.
- Passport: salida lista para comprobante portable.

Tiene fallback deterministico y un proxy same-origin para IA opcional. El
navegador no recibe llaves ni configuracion privada de proveedor. Si el modelo
no esta configurado, el sistema sigue funcionando con resumen local.

La regla central queda visible:

```text
La IA no decide ni crea evidencia; organiza un paquete de evidencia ya auditado.
```

## 3. Que puede hacer hoy el proyecto

### 3.1 Tomar evidencia satelital oficial y convertirla en decision

Kairos puede procesar escenas Sentinel-2 y decir si la observacion es usable,
si requiere revision o si no se debe inferir. La salida no es una alerta
ambiental; es una decision de confianza de observacion.

### 3.2 Evitar inferencias debiles

Cuando la escena tiene baja evidencia valida, el sistema bloquea la lectura.
Esto protege al producto de exagerar resultados y lo vuelve mas creible para
auditores, aseguradoras, instituciones y usuarios tecnicos.

### 3.3 Mostrar el razonamiento de forma comprensible

La interfaz traduce metricas tecnicas en pantallas de decision. Un usuario puede
ver rapidamente:

- que fecha esta evaluando;
- que decision recibio;
- cuanta evidencia valida existe;
- que capas auxiliares hay;
- que falta;
- que accion responsable sigue.

### 3.4 Conservar trazabilidad

Cada decision se puede conectar con artefactos de evidencia. El ledger permite
volver del resultado publico hacia la cadena de datos que lo sostiene.

### 3.5 Preparar evidencia para terceros

Passport y el Asistente de Evidencia permiten generar paquetes mas faciles de
compartir. Esto abre camino a usos con cooperativas, tecnicos agricolas,
aseguradoras, credito rural, programas publicos, compliance ambiental y
auditoria de intervenciones.

### 3.6 Separar evidencia primaria de contexto auxiliar

El proyecto puede mostrar SAR, CLMS, HydroClimate y contexto territorial sin
permitir que esas capas cambien la decision Sentinel-2 primaria. Eso es clave:
las capas auxiliares orientan, pero no sustituyen la calidad de observacion.

### 3.7 Funcionar aunque la IA no este disponible

El sistema no depende de IA para decidir. La IA es opcional y esta limitada a
resumir evidencia ya disponible. Si no hay modelo configurado, el producto cae a
un resumen deterministico.

### 3.8 Ser una base para Trust API/Docs

El proyecto ya tiene los ingredientes para una capa Trust:

- decisiones normalizadas;
- hashes y ledger;
- paquetes Passport;
- limites cientificos explicitos;
- datos publicos sanitizados;
- asistente con claim guard;
- rutas de accion y campo.

El siguiente salto natural seria exponer endpoints read-only para verificar un
Passport, consultar evidencia por fecha/AOI y documentar exactamente que se
puede y que no se puede afirmar.

## 4. Que no hace, a proposito

Kairos no detecta contaminacion quimica, pesticidas, patogenos, metales pesados
ni potabilidad. No declara si el agua es segura para consumo, riego, animales o
contacto humano. No reemplaza laboratorio, autoridad competente ni verificacion
territorial formal.

Tampoco convierte una baja confianza satelital en crisis, cierre operativo o
respuesta institucional. Su funcion es mas precisa: proteger la decision contra
datos debiles y documentar que evidencia existe.

## 5. Por que esto puede volverse muy grande

La mayoria de productos de "AI + satelite" intentan impresionar diciendo mas de
lo que pueden probar. Kairos puede diferenciarse haciendo lo contrario: decir
solo lo que la evidencia permite, conservar trazabilidad y entregar paquetes
verificables.

Eso lo posiciona como infraestructura de confianza, no solo como dashboard.

El valor no esta solo en ver mapas o porcentajes. El valor esta en producir una
decision que una organizacion pueda usar sin quedar expuesta a claims falsos.
En agricultura, seguros, credito, cooperativas y programas publicos, esa
prudencia es una ventaja comercial.

## 6. La frase del producto

Azuero Kairos convierte evidencia satelital oficial en decisiones responsables,
trazables y compartibles. Su promesa no es detectar lo invisible. Su promesa es
evitar inferir cuando la evidencia no alcanza.

