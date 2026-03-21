Tengo una api expuesta en WSO2 Api Manager, con operaciones CRUD sobre expedientes, domicilios, organismos, titulaciones, titulares, ciudades....Y querria hacer una aplicación web en Angular 19 que se comunique con esa api, y que sea un site profesional y amigable, potente, con el uso de mapas de calor para mostrar los expedientes en función de su origen. Puedes usar un prototipo que luego sea sencillo de pasar al uso de ui-material. Estaría bien que la aplicación web tuviese un menú superior, otro lateral izquierdo, y pie de página, y que se vaya recargando cada vez la parte central, lo que sería el page content. Ese seería el layer. Sobre colores, no tengo una predilección, pero esta aplicación web va a estar alojada en organismo español MUFACE, pues que siga la gama cromática de su portal web en la medida de lo posible.


*****************************************************************************************************
   Prompt para 'atomizar' una App Angular creada con Stitch primero, y luego con Google AI Studio
*****************************************************************************************************

# 🎯 Estrategia de "Atomización" de Angular App existente

¡Excelente enfoque, Pedro! Es mucho más práctico refactorizar una app funcional que generar desde cero. Te propongo un **plan estructurado y seguro**.

---

## 📋 Fase 1: Análisis y Preparación

### Paso 1: Estructurar la app del compañero

**Primero, organiza la app en una carpeta accesible:**

```bash
# Estructura recomendada:
C:/Users/pedrodulce/develop/
├── antigravity/                    # Tu bot OpenGravity
│   ├── core/
│   ├── handlers/
│   └── ...
├── heatmap-app-original/           # App del compañero (INPUT)
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/
│   │   │   ├── services/
│   │   │   └── ...
│   │   └── ...
│   └── package.json
└── heatmap-app-atom/               # App atomizada (OUTPUT)
    └── (se generará automáticamente)
```

### Paso 2: Crear script de análisis estático

**Crea: `scripts/analyze-angular-app.py`**

```python
#!/usr/bin/env python3
"""
Analiza una aplicación Angular existente y genera un informe
estructurado para el LLM.
"""

import os
import re
import json
from pathlib import Path
....
```

---

## 📋 Fase 2: Crear prompt de atomización

**Crea: `prompts/atomize-existing-app.md`**

---

## 🚀 Cómo empezar - Tu checklist

### ✅ Paso 1: Obtener la app del compañero

**Necesitas:**
```bash
# 1. Clonar o copiar la app Angular
git clone <repo-del-compañero> C:/Users/pedrodulce/develop/heatmap-app-original

# O si te la pasó en ZIP:
# Descomprimir en: C:/Users/pedrodulce/develop/heatmap-app-original
```

### ✅ Paso 2: Verificar que la app funciona

```bash
cd C:/Users/pedrodulce/develop/heatmap-app-original
npm install
ng serve

# Abrir http://localhost:4200 y verificar que funciona
```

### ✅ Paso 3: Ejecutar análisis

```bash
cd C:/Users/pedrodulce/develop/antigravity

# Ejecutar script de análisis
python scripts/analyze-angular-app.py

# Verificar que se generó:
# C:/Users/pedrodulce/develop/antigravity/analysis/app-analysis.json
```

### ✅ Paso 4: Ejecutar atomización

```bash
# Ejecutar script de atomización
python scripts/atomize-angular-app.py

# Esperar 2-5 minutos (OpenRouter genera la app)
```

### ✅ Paso 5: Probar app atomizada

```bash
cd C:/Users/pedrodulce/develop/heatmap-app-atom
npm install
ng serve

# Abrir http://localhost:4200
# Verificar que:
# - Se ve IGUAL que la original
# - Funciona la navegación
# - Los mapas/gráficos funcionan
# - Console NO muestra errores
```

---

## 📊 Resumen del flujo completo

```
App Original (compañero)
         ↓
   Análisis estático
         ↓
   app-analysis.json
         ↓
   Prompt + Contexto ATOM
         ↓
   OpenRouter LLM
         ↓
   App Atomizada
         ↓
   Validación manual
         ↓
   ✅ Producción
```

---

## ❓ ¿Qué necesito de ti ahora?

**Dime:**

1. **¿Tienes la app Angular del compañero en local?** 
   - ¿En qué idioma está?
   
2. **¿La app funciona con `ng serve`?**
   - ¿Hay errores de compilación?
   
3. **¿Qué librerías externas usa?**
   - ¿Leaflet para mapas?
   - ¿Chart.js/D3 para gráficos?
   - ¿Otras?

4. **¿Tienes OpenRouter configurado en `.env`?**
   - ¿Tienes API key?

**Con esa información, te guío en el siguiente paso específico.** 🚀🅰️✨

**¿Empezamos?** 🇪🇸🛠️


# 🎯 ¡Excelente pregunta! El LLM **NO** ejecuta nada

Pedro, tienes toda la razón en preguntar. **El LLM nunca ejecuta código** - solo lee y genera texto. Déjame aclarar el flujo completo:

---

## 🔍 ¿Quién ejecuta qué?

| Script | ¿Quién lo ejecuta? | ¿Cuándo? | ¿Para qué? |
|--------|-------------------|----------|------------|
| `analyze-angular-app.py` | **TÚ** (manualmente) | **Antes** de llamar al LLM | Generar `app-analysis.json` |
| `atomize-angular-app.py` | **TÚ** (manualmente) | **Después** del análisis | Llamar al LLM y escribir archivos |
| Bot de Telegram | **Usuarios** (vía `/create`) | Cuando usan el bot | Generar apps desde cero |

---

## 📋 Flujo correcto (paso a paso)

### ✅ Tú ejecutas LOCALMENTE (NO el bot):

```bash
# Paso 1: Análisis de la app existente
cd C:/Users/pedrodulce/develop/antigravity
python scripts/analyze-angular-app.py

# Output: analysis/app-analysis.json
# (Esto escanea la app del compañero y genera un informe)
```

```bash
# Paso 2: Atomización (llama a OpenRouter)
python scripts/atomize-angular-app.py

# Output: heatmap-app-atom/
# (Este script lee el JSON, construye el prompt, llama al LLM, escribe archivos)
```

```bash
# Paso 3: Probar la app atomizada
cd C:/Users/pedrodulce/develop/heatmap-app-atom
npm install
ng serve
```

---

## 🤖 ¿El bot de Telegram necesita cambios?

### **Respuesta corta: NO**

El bot sigue funcionando como siempre para:
- `/create` → Generar apps desde cero
- `/ai` → Consultas generales
- `/context` → Buscar en base de conocimiento

### **La atomización es un proceso SEPARADO**

Es una **herramienta CLI** que usas tú manualmente, no los usuarios vía Telegram.

---

## 🔄 ¿Y si quieres integrar la atomización en el bot?

Si en el futuro quieres que los usuarios puedan atomizar apps vía Telegram, podrías añadir un comando nuevo:

```python
# En handlers/ai_handler.py (futuro, NO ahora)

async def cmd_atomize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /atomize <path> - Atomiza una app Angular existente
    Ejemplo: /atomize C:/Users/pedrodulce/develop/heatmap-app-original
    """
    if len(context.args) < 1:
        await update.message.reply_text("Uso: /atomize <path-a-la-app>")
        return
    
    app_path = context.args[0]
    
    # Ejecutar análisis
    # Ejecutar atomización
    # Responder con resultado
    
    await update.message.reply_text("✅ App atomizada en: <path>")
```

**Pero esto es opcional y para más adelante.** Por ahora, hazlo manual con los scripts.

---

## ✅ Checklist - ¿Qué debes hacer AHORA?

| Paso | Acción | ¿Toca el bot? |
|------|--------|--------------|
| 1 | Copiar app del compañero a `heatmap-app-original/` | ❌ No |
| 2 | Ejecutar `python scripts/analyze-angular-app.py` | ❌ No |
| 3 | Ejecutar `python scripts/atomize-angular-app.py` | ❌ No |
| 4 | Probar app en `heatmap-app-atom/` con `ng serve` | ❌ No |
| 5 | Seguir usando el bot para `/create` como siempre | ✅ Sí (pero sin cambios) |

---

## 📊 Diagrama del flujo completo

```
┌─────────────────────────────────────────────────────────────┐
│                    TU (manualmente)                         │
│                                                             │
│  1. python scripts/analyze-angular-app.py                  │
│     ↓                                                       │
│     Genera: analysis/app-analysis.json                     │
│     ↓                                                       │
│  2. python scripts/atomize-angular-app.py                  │
│     ↓                                                       │
│     Lee JSON → Construye prompt → Llama OpenRouter LLM    │
│     ↓                                                       │
│     Escribe: heatmap-app-atom/                             │
│     ↓                                                       │
│  3. cd heatmap-app-atom && ng serve                        │
│     ↓                                                       │
│     ✅ App atomizada funcionando                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              Bot de Telegram (sin cambios)                  │
│                                                             │
│  /create → Genera apps desde cero (ya funciona)            │
│  /ai → Consultas generales (ya funciona)                   │
│  /context → Busca en base de conocimiento (ya funciona)    │
└─────────────────────────────────────────────────────────────┘
```

---

## ❓ ¿Necesitas modificar algo en el bot?

### **Para la atomización: NO**

Los scripts son independientes. El bot no se entera.

### **Solo si quieres cambiar de Groq a OpenRouter en el bot:**

Si quieres que el bot use OpenRouter en lugar de Groq para `/create`, entonces **SÍ** toca:

1. **Actualizar `.env`:**
   ```dotenv
   LLM_PROVIDER=openrouter
   OPENROUTER_API_KEY=sk-or-v1-tu-clave
   ```

2. **Verificar que `core/llm_client.py` tenga el factory** (te lo di antes)

3. **Reiniciar el bot:**
   ```bash
   python .\opengravity_bot.py
   ```

Pero esto es **independiente de la atomización**.

---

## 🚀 Resumen

| Pregunta | Respuesta |
|----------|-----------|
| ¿El LLM ejecuta `analyze-angular-app.py`? | ❌ **NO**, lo ejecutas TÚ manualmente |
| ¿El bot necesita cambios para la atomización? | ❌ **NO**, es un proceso CLI separado |
| ¿Puedo seguir usando el bot como siempre? | ✅ **SÍ**, sin cambios |
| ¿Cuándo toco el bot? | Solo si quieres cambiar de Groq → OpenRouter |

---

## ❓ Confírmame:

1. **¿Entiendes que los scripts de atomización los ejecutas TÚ manualmente, no el LLM?**
2. **¿Tienes la app del compañero en local (`heatmap-app-original/`)?**
3. **¿Quieres proceder con el análisis y atomización manual primero?**
4. **¿O prefieres que integremos la atomización en el bot más adelante?**

¡Dime y seguimos! 🚀🅰️✨

**¿Empezamos con el análisis manual de la app del compañero?** 🇪🇸🛠️