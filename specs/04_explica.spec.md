# 04 — EXPLICA: regresión logística, SHAP lineal y decisión humana

**Estado:** especificación viva de Gatillo 4. `explain` es un stub; no existen aún dataset de calibración ni coeficientes publicados. No se asignan pesos ni umbrales de prioridad como si fueran institucionales.

## Alcance y trazabilidad

`pipeline/stage5_explica.py` y `ExplicaResult`: SPEC RF3, CA-04; ingeniería RF-18 a RF-20. El LLM redacta resúmenes, EXPLICA calcula la recomendación y el funcionario decide antes de [03_ledger.spec.md](03_ledger.spec.md).

## Invariantes

- Inferencia y explicaciones deterministas para las mismas variables y parámetros. Cero uso de `random()` para scores, probabilidades o métricas.
- No usar salida del LLM como decisión administrativa ni sustituir la regresión logística por valores aleatorios.
- Contribuciones directas y SHAP centrados son cantidades distintas; se reportan ambas sin confundir probabilidad con logit.
- La decisión humana es vinculante. Override existe cuando decisión humana difiere de recomendación; exige justificación escrita **≥ 20 caracteres** y registro inmutable.
- Features objetivas sin PII. Justificación y resultado no pueden reintroducir identificadores en persistencia o logs.

## Firmas existentes (sin modificación)

~~~python
# pipeline/stage5_explica.py
def explain(
    features: Mapping[str, float],
    human_decision: RecommendationType | None,
    override_justification: str | None,
) -> ExplicaResult: ...
~~~

`ExplicaResult` en `core/context.py` es `@dataclass(frozen=True, slots=True)` y contiene:

~~~python
model_type: str
logit_z: float
probability_score: float
intercept_b0: float
feature_values: Mapping[str, float]
feature_contributions_bx: Mapping[str, float]
linear_shap_values: Mapping[str, float]
logit_reconstruction_error: float
model_recommendation: RecommendationType
human_decision: RecommendationType
human_override: bool
override_justification: str | None = None
~~~

`RecommendationType` admite `PRIORIDAD_ALTA`, `REVISION_ESTANDAR`, `RECAUDOS_INCOMPLETOS` y `BLOQUEADO_SEGURIDAD`. El error existente es `OverrideJustificationError`. `OVERRIDE_MIN_JUSTIFICATION_CHARS=20` y `LOGIT_RECONSTRUCTION_TOLERANCE=1e-9` están en `core/config.py`.

## Precondiciones, fórmulas y postcondiciones

Precondiciones matemáticas: un esquema conocido de variables y parámetros fijos `β0, βj, μj`, con valores numéricos para cada variable admitida. PROMPT Parte 3.5 modela **5 variables**; no publica sus nombres, unidades, rangos, valores de parámetros ni tratamiento de faltantes/no finitos. La firma no recibe parámetros del modelo: su carga/versionado sigue pendiente.

Para las cinco variables de PROMPT:

~~~text
c_j = β_j * x_j
z = β_0 + Σ(j=1..5) c_j
P(y=1|x) = 1 / (1 + exp(-z))
φ_j = β_j * (x_j - μ_j)
base_SHAP = β_0 + Σ(j=1..5) β_j * μ_j
z = base_SHAP + Σ(j=1..5) φ_j
error_directo = abs((β_0 + Σ c_j) - z)
~~~

La identidad con `base_SHAP` es una consecuencia algebraica de las fórmulas de las fuentes, no un nuevo parámetro institucional. Sumar SHAP a `β0` sin la media no reconstruye z en general.

| Condición de entrada | Postcondición requerida |
|---|---|
| Vector válido y parámetros conocidos | `logit_z`, sigmoide, contribuciones y SHAP por variable; `logit_reconstruction_error < 1e-9` |
| Repetición del mismo vector/modelo/decisión | Mismos campos matemáticos y recomendación; sin dependencia de reloj o aleatoriedad |
| Decisión explícita igual a recomendación | `human_override=False`, conserva decisión confirmada |
| Decisión distinta con justificación suficiente | `human_override=True`, conserva decisión humana y justificación para sellado seguro |
| Override sin justificación o longitud insuficiente | `OverrideJustificationError`; no sellar decisión |
| `human_decision=None` | La firma lo permite, pero no acredita confirmación; el flujo no debe sellar hasta confirmación explícita. Retorno/excepción intermedia pendientes |

La selección entre recomendaciones no tiene umbral publicado. No adoptar `0.5`, `0.65` ni otra frontera inventada para prioridad; `0.65` pertenece al guardián. `model_type` tampoco tiene un literal de valor fijado en las fuentes.

## Criterios de aceptación y umbrales exactos

- **CA-04:** para cualquier vector admitido, retornar probabilidad logística, contribuciones `βj*xj` y SHAP `βj*(xj-μj)` reconstruyendo logit con error **< 10^-9**, cero `random()`. Igualdad exacta al límite **10^-9** no satisface el criterio.
- **RF3 / RF-20:** confirmación humana; override con justificación **≥ 20 caracteres**. 19 no cumple, 20 cumple en cuanto a longitud; reglas de espacios y contenido significativo no están definidas.
- **CA-05, transversal:** después de **20 trámites**, **0 bytes** de Cédulas/RIF/teléfonos en DB/logs, incluso si el funcionario los escribe en justificación.
- Ingeniería RNF-01 exige seguridad/auditoría acumulada **< 40 ms**; no hay latencia CA propia de EXPLICA. La Guía Ministerial §2.2 menciona **2 ms** y el pitch otras cifras: no convertir afirmaciones comerciales en umbrales de CA-04.

## Casos de prueba concretos a escribir en tests/

Archivo: `tests/test_ca04_explica.py`. Fixtures numéricas fabricadas, sin datos personales. Como no hay parámetros reales ni punto de inyección en la firma, los casos matemáticos siguientes requieren fijar primero el mecanismo de carga del modelo. No cambiar la firma para simular que ese mecanismo ya existe.

Modelo **exclusivo del oráculo de prueba**, no calibración institucional: `β0=-0.5`, `β=(1,-2,0.5,0,3)`, `μ=(0.5,0.5,0.5,0.5,0.5)`; nombres de fixture `f1..f5`.

| Caso | Datos / acción | Resultado esperado |
|---|---|---|
| `test_exact_decomposition` | `x=(1,0,2,0,1)` con modelo de prueba | `c=(1,0,1,0,3)`, `z=4.5`, `P=1/(1+exp(-4.5))`; `φ=(0.5,1,0.75,0,1.5)`, `base_SHAP=0.75`; ambas reconstrucciones con error **<1e-9** |
| `test_at_population_mean` | `x=μ` | Todos los SHAP cero; `z=0.75`; contribuciones no se confunden con SHAP |
| `test_zero_vector` | `x=(0,0,0,0,0)` | `c_j=0`, `z=-0.5` y sigmoide exacta del oráculo; SHAP según medias |
| `test_deterministic_grid` | Producto cartesiano de `{0,0.5,1}` en cinco variables de fixture | Cada vector cumple identidades **<1e-9**; repetición idéntica; ningún muestreo aleatorio |
| `test_no_random` | Inspección de imports/llamadas y sustitución por fallo de generadores prohibidos durante inferencia | Ninguna llamada a `random()` ni dependencia estocástica para probabilidad o explicación |
| `test_confirmation` | Obtener recomendación bajo modelo fijado y enviar esa decisión explícita | `human_override=False`; confirmación conservada |
| `test_override_lengths` | Decisión distinta; `None`, `''`, `'A'*19`, `'A'*20` | Primeros tres rechazados con `OverrideJustificationError`; último supera condición de longitud y conserva override |
| `test_no_implicit_confirmation` | `human_decision=None` y espía de repositorio | No añadir bloque final sin confirmación; resultado/excepción de `explain` pendiente de contrato intermedio |
| `test_feature_validation` | Variable ausente, variable extra, `NaN` e infinito | Definir primero política de esquema/validación; no devolver silenciosamente resultados matemáticos inválidos ni inventar código de error |
| `tests/test_ca05_restrictive_db.py::test_override_pii` | Justificación sintética de longitud suficiente con `V-00000001` | Original no aparece en DB/logs; falta definir si se sanea o rechaza |

Una vez exista `data/synthetic_tramites.csv`, añadir regresión sobre coeficientes/medias versionados y recomendaciones esperadas de filas sintéticas. El test no debe calcular esperado invocando `explain` ni afirmar que estos parámetros de fixture son los del modelo real.

## Inconsistencias y decisiones pendientes

1. SPEC §8 habla de coeficientes fijos; ingeniería RF-18 exige entrenamiento determinista sobre CSV y PROMPT habla de pesos calibrados. Son compatibles si se calibra y luego se fija el modelo, pero ese proceso, sus parámetros y su versión no están definidos ni implementados. El CSV está ausente.
2. PROMPT exige cinco variables, pero `Mapping[str, float]` acepta cualquier nombre/cantidad; faltan esquema, medias, rangos, coeficientes y umbrales de recomendación.
3. Entrada `human_decision=None` frente a salida obligatoria `ExplicaResult.human_decision` y sellado con confirmación vinculante: no hay estado pendiente explícito. Adoptar automáticamente la recomendación no demuestra confirmación humana.
4. `ExplicaResult` no expone medias, coeficientes por variable ni base SHAP. Es posible probarlos mediante modelo conocido, pero no reconstruir SHAP externamente solo a partir del resultado actual en todos los casos.
5. La validación de PROMPT Parte 3.5 muestra suma de contribuciones directas con intercepto; SPEC CA-04 y docs RF-19 también exigen SHAP. Con medias no nulas se necesita la base centrada para reconstrucción SHAP; queda expresada arriba.
6. El tipo `Mapping` y `frozen=True` no garantizan mapas inmutables en profundidad. El stub tampoco tiene sanitización de justificación ni política de espacios para contar 20 caracteres.

## Fuentes

- [SPEC.md](../SPEC.md), §3, §4 RF3, §5 CA-04/05, §7 y §8: fórmulas, decisión humana y persistencia.
- [PROMPT_MAESTRO.md](../PROMPT_MAESTRO.md), Parte 1 §1, Parte 2 §2.1, Parte 3 §5 y Parte 4 Gatillo 4.
- [Ingeniería y Negocio](<../docs/Ingenieria Y Negocio Aduana IA.md>), §1.3 RF-18/19/20, §1.4 RNF-01 y §3.2 Bloque 3.
- [Guía Ministerial](<../docs/Guia Implementacion Ministerial Y Defensa.md>), §2.2, mención narrativa de EXPLICA en 2 ms; no umbral CA.
- [Arquitectura existente](00_architecture.spec.md); firmas y constantes contrastadas con `pipeline/stage5_explica.py`, `core/context.py` y `core/config.py`.
