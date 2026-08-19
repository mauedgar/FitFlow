# FitFlow contracts v2

Draft: JSON Schema 2020-12.

`common.schema.json` contiene definiciones compartidas. Los artefactos declaran
un `schema_version` constante y rechazan propiedades desconocidas. Los adapters
validan al entrar y salir de AI Core.

`developer` es el actor contractual v2. `human` solo existe en schemas v1 y en
la tabla de migracion.
