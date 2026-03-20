Arquitectura:

┌─────────────────────────────────────────────────────────────┐
│  USUARIO: "¿Qué servicios están operativos y sus endpoints?"│
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  LLM (OpenRouter) analiza la intención y determina:         │
│  • Qué comandos kubectl necesita                            │
│  • Con qué parámetros                                       │
│  • Si requiere confirmación (comandos destructivos)         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  BOT ejecuta los comandos seguros:                          │
│  • kubectl get services -n atom                             │
│  • kubectl get endpoints -n atom                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  LLM formatea la respuesta en lenguaje natural              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  USUARIO recibe respuesta clara y estructurada              │
└─────────────────────────────────────────────────────────────┘