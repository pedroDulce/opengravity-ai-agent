📁 FASE 0: Preparación (Semana 1)
├── ✅ Aclarar herramientas (Hecho)
├── 🔜 Instalar OpenSpec y verificar entorno Node/Angular
   usa: $env:POSTHOG_DISABLED="true"
├── 🔜 Inicializar repositorio Git + estructura base
└── 🔜 Crear primer spec: "Calculadora - Requisitos Mínimos", usar:

   /opsx:propose "Implement calculator component structure based on functional-requirements.md"


📁 FASE 1: Especificaciones con OpenSpec (Semana 1-2)
├── Definir requisitos funcionales (operaciones, historial, validaciones)
├── Definir requisitos no funcionales (responsive, accesibilidad)
├── Crear specs en openspec/specs/calculator/
├── Generar proposal con /opsx:propose
└── Revisar y aprobar specs antes de codificar

📁 FASE 2: Prototipado con Google Stitch (Semana 2)
├── Crear prompt para Stitch: "Calculadora web moderna, minimalista..."
├── Iterar diseño: colores, tipografía, disposición de botones
├── Exportar HTML/CSS desde Stitch
├── Documentar decisiones de UI en specs (vincular con Fase 1)
└── Preparar estructura de componentes Angular basada en el diseño

📁 FASE 3: Implementación Angular (Semana 3-4)
├── ng new calculator-app --standalone
├── Generar componentes: CalculatorDisplay, CalculatorKeypad, CalculatorService
├── Implementar lógica de negocio (servicio con RxJS/Signals)
├── Estilizar con CSS/SCSS basado en prototipo de Stitch
├── Conectar specs de OpenSpec como documentación viva

📁 FASE 4: Testing y Calidad (Semana 4-5)
├── Tests unitarios para CalculatorService (Jest/Jasmine)
├── Tests de componentes (Testing Library)
├── E2E con Cypress (flujo completo de cálculo)
├── Integrar OpenSpec para validar que el código cumple specs

📁 FASE 5: Documentación y Entrega (Semana 5-6)
├── Documentación técnica: README, arquitectura, decisiones
├── Documentación funcional: Manual de usuario (puede generarse desde specs)
├── Generar docs automáticas con Compodoc
├── Build de producción y despliegue (Firebase/Vercel)
└── Retrospectiva: ¿Qué aprendimos de Specs-Driven + Stitch?