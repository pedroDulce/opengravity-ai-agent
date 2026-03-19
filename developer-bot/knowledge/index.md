## 9️⃣ `knowledge/index.md`

```markdown
# 📚 Base de Conocimiento OpenGravity

## Estructura de Carpetas

```
knowledge/
├── angular-guidelines/
│   ├── coding-standards.md      # Estándares de código Angular
│   ├── component-library.md     # Catálogo de componentes UI
│   ├── architecture.md          # Patrones arquitectónicos
│   └── styling-guide.md         # Guías de estilos SCSS
│
├── examples/
│   ├── login-component.ts       # Ejemplo de componente login
│   ├── user-service.ts          # Ejemplo de servicio HTTP
│   └── api-interceptor.ts       # Ejemplo de interceptor
│
└── api-contracts/
    ├── swagger-parser.ts        # Parser de OpenAPI/Swagger
    └── test-analyzer.ts         # Analizador de tests backend
```

## Cómo Usar

### 1. Buscar documentación
```
/context search [término]
Ej: /context search interceptor
```

### 2. Generar código desde Swagger
```
/swagger [url_o_ruta]
Ej: /swagger https://api.corp.com/v1/openapi.json
```

### 3. Generar frontend desde tests
```
/tests [ruta]
Ej: /tests C:/backend/src/users
```

## Comandos Relacionados

| Comando | Descripción |
|---------|-------------|
| `/context list` | Lista documentos disponibles |
| `/context reload` | Recarga documentos desde disco |
| `/context search [term]` | Busca por palabra clave |
| `/swagger [url]` | Genera Angular desde OpenAPI |
| `/tests [ruta]` | Genera frontend desde tests backend |

## Actualizar la Base

1. Añade/modifica archivos en `knowledge/`
2. Ejecuta `/context reload` en Telegram
3. Verifica con `/context search [término]`

## Convenciones

- Archivos en **Markdown** para documentación
- Archivos en **TypeScript** para ejemplos de código
- Nombres en **kebab-case** para archivos
- Encoding **UTF-8** sin BOM
```