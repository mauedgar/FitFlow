# Ejemplos de uso — repo-packager

## Preparación (una sola vez por repo)

```bash
# Desde la raíz del repositorio que quieres empaquetar (ej. Fitflow)
npx repomix --style json --compress -o repo.json
```

El archivo `repo.json` es la base. El script cachea el grafo en `.repo-packager-cache/`.

---

## 1. Contexto reducido (overview)

```bash
python /ruta/a/repo-packager/scripts/pack.py reducido \
  --json repo.json \
  --budget 8000
```

Con personalización (archivos que el usuario está tocando):

```bash
python .../pack.py reducido \
  --json repo.json \
  --budget 6000 \
  --personalize src/checkout/CheckoutService.ts src/cart/CartContext.ts
```

Máxima compresión (solo firmas + imports):

```bash
python .../pack.py reducido \
  --json repo.json \
  --budget 4000 \
  --signatures-only
```

**Qué recibe el agente:**
- Lista de paths seleccionados + score
- Lista de candidatos a expansión (con razón y tokens estimados)
- Contenido del pack

---

## 2. Drill-down (mapa fino de una zona)

```bash
python .../pack.py drill-down \
  --json repo.json \
  --focus src/checkout \
  --budget 5000
```

Útil cuando el overview muestra que la zona importante es `src/checkout` y quieres un mapa más preciso de ese subárbol sin pedir aún el código completo.

---

## 3. Ampliado (código real)

```bash
python .../pack.py ampliado \
  --paths src/checkout/CheckoutService.ts,src/checkout/hooks,src/payments/PaymentProvider.ts
```

- Máximo 10 paths.
- Sin `--compress` → código fuente real.
- Se puede pedir **directamente**, sin haber pedido reducido antes.

---

## Flujo típico del agente

1. Generar / reutilizar `repo.json`
2. Pedir **reducido** → obtener mapa + candidatos
3. Decidir:
   - ¿Alcanza? → trabajar con eso
   - ¿Necesito afinar una zona? → **drill-down**
   - ¿Necesito implementación real? → **ampliado** de los paths candidatos relevantes
4. Repetir solo si es necesario

La skill nunca decide el siguiente paso. Solo empaqueta lo que se le pide.

---

## Notas de integración con OpenCode

Si la skill vive en `Fitflow-ai/.opencode/skills/repo-packager/`, el agente puede invocarla con la ruta relativa o absoluta al script.

Ejemplo de regla sugerida para el agente:

```
Cuando necesites contexto de código del core (Fitflow):
- Usa la skill repo-packager en modo reducido primero.
- Luego decide si pedir drill-down o ampliado.
- Nunca envíes el repo completo.
```