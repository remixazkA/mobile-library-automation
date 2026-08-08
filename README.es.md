# Automatización de una biblioteca móvil

Automatización local y orientada a la privacidad para limpiar una biblioteca fotográfica saturada y ordenar un archivo personal de documentos.

El proyecto nació al cambiar de móvil. Durante la migración aparecieron miles de imágenes aleatorias, memes y contenido recibido por WhatsApp mezclados con fotografías útiles. Al mismo tiempo, años de documentos de texto conservaban nombres opacos, repetidos o poco informativos. La solución debía inventariar, clasificar, detectar duplicados, proponer nombres y verificar el resultado sin subir contenido personal a servicios externos.

> Repositorio de portfolio: los datos originales, manifiestos, hashes, embeddings faciales e identificadores del dispositivo no se publican. El código expone únicamente las partes reutilizables y seguras mediante configuración sintética.

## Autoría y método de trabajo

Este es un proyecto abiertamente asistido por IA. El responsable del proyecto identificó el problema real, explicó el resultado que necesitaba, estableció los límites de privacidad y seguridad, revisó los resultados y pidió utilizar el menor número de tokens de modelo posible. Codex, un agente de programación con IA, produjo la implementación y la documentación siguiendo esa orientación.

El repositorio demuestra capacidad para definir problemas, delegar con claridad en un sistema de IA, establecer restricciones, validar iterativamente y entregar de forma responsable. No afirma que el responsable diseñara o escribiera personalmente cada línea de código.

[English README](README.md)

## Resultados de la ejecución real

| Área | Resultado |
| --- | ---: |
| Archivos copiados al área local | 17.569 |
| Imágenes inventariadas y procesadas | 14.664 |
| Imágenes seleccionadas para la biblioteca limpia | 954 |
| Copias exactas separadas mediante SHA-256 | 42 |
| Documentos inventariados y clasificados | 315 |
| Documentos renombrados o normalizados | 179 |
| Cobertura del procesamiento | 100 % |

La cobertura indica que todos los elementos inventariados recibieron un resultado. No implica una precisión del 100 %: los modelos zero-shot necesitan validación humana sobre una muestra etiquetada.

## Capacidades demostradas

- Automatización integral con Windows MTP, Python y PowerShell.
- Inventario incremental en SQLite para no recalcular archivos sin cambios.
- Duplicados exactos mediante SHA-256; la similitud visual nunca autoriza un borrado.
- Clasificación semántica configurable con OpenCLIP y visión artificial local opcional.
- Renombrado documental basado en metadatos y evidencias extraídas del contenido.
- Planes en seco, manifiestos auditables, verificación y diseño orientado a rollback.
- Procesamiento local de imágenes y documentos privados.
- Colaboración eficiente entre persona e IA con una restricción explícita de ahorro de tokens.

## Inicio rápido

```bash
python -m venv .venv
python -m pip install -e .
mobile-library scan ./sample-data --db ./run/library.sqlite
mobile-library plan-documents ./sample-data/documents --config config.example.toml --output ./run/document-plan.json
mobile-library verify-plan ./sample-data/documents ./run/document-plan.json
python -m unittest discover -s tests -v
```

Para activar la clasificación visual local:

```bash
python -m pip install -e ".[ml]"
mobile-library score-photos ./photos --config config.example.toml --output ./run/photo-scores.json
```

La primera ejecución descarga los pesos de OpenCLIP, pero las imágenes permanecen en el equipo.

## Principios de seguridad

1. Copiar desde MTP a un área local sin modificar el teléfono.
2. Inventariar y calcular hashes antes de proponer cambios.
3. Ejecutar en modo simulación por defecto.
4. Rechazar rutas que salgan de la raíz declarada.
5. Considerar duplicados eliminables solo los archivos con SHA-256 idéntico.
6. Conservar un manifiesto y verificar recuentos en cada etapa.

Consulta el [caso de estudio](docs/CASE_STUDY.md) y los [límites de privacidad](docs/PRIVACY.md).
