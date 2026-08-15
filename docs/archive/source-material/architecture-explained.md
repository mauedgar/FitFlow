# FitFlow: explicacion de la arquitectura

**Tipo:** Material de referencia para personas

**Actualizado:** 2026-08-15

**Documento canonico relacionado:** `architecture.md`

## 1. Objetivo

Este documento explica las decisiones contenidas en `architecture.md`. No
define reglas nuevas y no sustituye al documento canonico.

## 2. Que arquitectura tiene FitFlow

FitFlow es actualmente un monolito organizado por capas tecnicas. El backend es
una unica aplicacion, se despliega como una unidad y utiliza PostgreSQL como
fuente persistente principal.

La organizacion por capas separa responsabilidades:

- routers para HTTP;
- services para casos de uso y reglas de negocio;
- CRUD para acceso y persistencia;
- modelos SQLAlchemy para representar la base;
- schemas Pydantic para contratos de entrada y salida.

Los dominios no estan agrupados fisicamente en carpetas verticales. Se
reconocen mediante archivos equivalentes distribuidos entre las capas. Esta
estructura sigue siendo valida para un monolito y permite evolucionar hacia un
monolito modular sin una reorganizacion inmediata del repositorio.

## 3. Por que los schemas no forman una capa lineal

La secuencia `Request -> Schema -> Router -> Service -> CRUD -> Model` puede
inducir a una interpretacion incorrecta. FastAPI recibe la solicitud, resuelve
la ruta y valida los datos declarados antes de ejecutar el handler. El router
coordina el limite HTTP y entrega datos validados al service.

En la respuesta, el service puede devolver un objeto ORM ya cargado o un DTO
derivado. FastAPI aplica el schema declarado como `response_model` y genera el
JSON final.

Por eso, Pydantic participa en los bordes de entrada y salida, pero no es una
capa de persistencia entre services y modelos.

## 4. Responsabilidad de routers y services

El router conoce HTTP. Puede conocer el usuario autenticado, los parametros de
la solicitud, el status code esperado y la forma publica de la respuesta. No
debe decidir si una membresia habilita una reserva, calcular recurrencias ni
consultar tablas directamente.

El service representa el caso de uso. Decide que validaciones aplicar, que
operaciones coordinar y que error de dominio producir. Una funcion service no
necesita ser async por pertenecer a esa capa: solo es async cuando coordina
operaciones de entrada/salida.

Los calculos sobre objetos ya cargados y los mappers puros son correctamente
sync. Su uso no viola la separacion mientras no provoquen consultas implicitas.

## 5. Responsabilidad de CRUD

CRUD concentra el conocimiento de SQLAlchemy y PostgreSQL. Esto incluye
consultas, filtros, eager loading, inserciones, actualizaciones y operaciones
atomicas.

Separar estas operaciones evita que cada service construya consultas distintas
para el mismo concepto. Tambien permite revisar con mayor claridad donde se
aplican locks, transacciones y garantias de consistencia.

Una operacion CRUD puede ser especifica del dominio cuando necesita garantizar
atomicidad. La politica que decide cuando ejecutar esa operacion sigue
perteneciendo al service.

## 6. Relaciones ORM y carga explicita

El backend async no debe depender de lazy loading implicito. Los CRUD cargan las
relaciones requeridas por cada caso de uso mediante estrategias explicitas.

El service puede recorrer relaciones ya cargadas. Si necesita una relacion que
la consulta no incluyo, debe corregirse el metodo CRUD correspondiente. No debe
abrirse una consulta secundaria de manera accidental desde un mapper.

Esta regla es especialmente importante cuando las relaciones usan
`lazy="raise"`, porque convierte una carga omitida en un error visible en lugar
de producir I/O inesperado.

## 7. Circularidad de imports

Los ciclos se evitan mediante una direccion estable de dependencias. Routers
dependen de services; services dependen de CRUD; CRUD depende de modelos. Las
capas inferiores no importan capas superiores.

Los archivos `*_refs.py` resuelven ciclos entre contratos Pydantic anidados.
Contienen schemas compactos y sin dependencias hacia services, CRUD o modelos
ORM. No solucionan ciclos provocados por consultas SQLAlchemy ubicadas en
services.

Los imports locales y `TYPE_CHECKING` pueden ser utiles para anotaciones, pero
no reemplazan la correccion de una dependencia bidireccional real.

## 8. Estado actual y transicion

El repositorio todavia contiene routers que acceden directamente a CRUD y
services que ejecutan consultas ORM. Esto describe el estado actual, no la
arquitectura aprobada para codigo nuevo.

La correccion se realiza gradualmente al intervenir cada caso de uso:

1. el router delega en un service;
2. el service conserva decisiones y calculos;
3. las consultas y la persistencia pasan a CRUD;
4. las relaciones necesarias se cargan de forma explicita;
5. el contrato HTTP se valida con Pydantic v2.

No se requiere una reescritura completa para declarar una direccion
arquitectonica. La regla evita aumentar la deuda y permite reducirla mediante
tareas acotadas.

## 9. Monolito modular como objetivo

Un monolito modular continua siendo una sola aplicacion desplegable. La
modularidad surge de limites internos claros, cohesion de dominio y dependencias
controladas, no solamente de la disposicion de carpetas.

La estructura actual por capas puede sostener esos limites durante el MVP. Una
organizacion vertical por dominio puede evaluarse cuando el volumen del codigo,
el ownership o el mantenimiento justifiquen el costo de migracion.

La arquitectura no incorpora microservicios como objetivo automatico. Extraer
un modulo exigiria separar datos, contratos, seguridad, observabilidad,
despliegue y pruebas. El monolito modular mantiene abierta esa posibilidad sin
pagar anticipadamente la complejidad distribuida.

## 10. Auditoria

El sistema conserva timestamps, estados operativos y eliminacion logica donde
corresponde. Esto no equivale a una auditoria uniforme por actor.

Agregar `created_by` en funciones aisladas produciria una politica incompleta.
La auditoria por actor debe definir previamente alcance, identidad del actor,
acciones registradas, retencion, permisos, modelo persistente y migraciones.
Hasta entonces, no forma parte del contrato obligatorio de generacion de
sesiones.

## 11. Uso de la documentacion

`architecture.md` responde como debe organizarse y evolucionar el sistema.
`current-state.md` responde que esta implementado y que desviaciones existen.
`quality-and-validation.md` responde como se comprueba. Las tareas delimitan
cambios concretos y sus resultados conservan evidencia.

Esta separacion evita que un informe de agente convierta una observacion del
codigo en una nueva decision arquitectonica.
