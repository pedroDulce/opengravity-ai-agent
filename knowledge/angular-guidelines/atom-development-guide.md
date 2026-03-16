markdown
<!-- KEYWORDS: atom, lib-, standalone, OnPush, inject, signal, computed, m3-theme, muface-lib, angular-material, corporate, component, service, interceptor -->
# 🧩 Guía de Desarrollo de Componentes ATOM - Corporativo

## 📦 Versiones Requeridas
- Angular: 18.2.0
- Angular Material: 18.2.0
- Bootstrap (si se usa): 5.3.3

---

## 🏗️ Patrón de Componente ATOM

### 1. Clase Base Abstracta (OBLIGATORIO)
```typescript
// lib-base.component.ts
import { Directive, Input, Output, EventEmitter, inject } from '@angular/core';

@Directive()
export abstract class LibBaseComponent<T> {
  // ✅ Input de estructura (encapsulado en objeto genérico)
  @Input() estructura!: AutocompleteEstructura<T>;
  
  // ✅ Input de DTO(s)
  @Input() dtos!: T[];  // o T si es único
  
  // ✅ Output para eventos (opcional)
  @Output() dataChanged = new EventEmitter<T>();
  
  // ✅ Inyección de servicios vía inject()
  protected readonly fb = inject(FormBuilder);
}

2. Componente Standalone (OBLIGATORIO)
// lib-autocomplete.component.ts
import { Component, ChangeDetectionStrategy, OnInit, AfterViewInit, OnDestroy } from '@angular/core';
import { LibBaseComponent } from './lib-base.component';

@Component({
  selector: 'lib-autocomplete',  // ✅ Prefijo "lib-"
  standalone: true,               // ✅ Standalone OBLIGATORIO
  imports: [CommonModule, ReactiveFormsModule, MatAutocompleteModule],
  templateUrl: './lib-autocomplete.component.html',
  styleUrl: './lib-autocomplete.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,  // ✅ OnPush OBLIGATORIO
})
export class LibAutocompleteComponent<T> 
  extends LibBaseComponent<T> 
  implements OnInit, AfterViewInit, OnDestroy 
{
  // ✅ Usar signals para estado interno
  private readonly _loading = signal(false);
  private readonly _results = computed(() => this._filteredData());
  
  // ✅ Lifecycle hooks obligatorios
  ngOnInit(): void {
    this.initForm();
  }
  
  ngAfterViewInit(): void {
    this.setupDom();
  }
  
  ngOnDestroy(): void {
    this.cleanup();
  }
  
  // ✅ Evitar CSS en línea, estilos acotados a .scss del componente
}
🎨 Aplicación de Estilos ATOM
En styles.scss global (OBLIGATORIO):
// ✅ Importar temas ATOM/Material
@use '@angular/material' as mat;
@use '@muface-lib/muface-lib/estilos/m3-theme' as muf-theme;

@include mat.core();

:root {
  @include mat.all-component-themes(muf-theme.$light-theme);
}

En el componente .scss:
// ✅ Estilos acotados al componente, sin CSS global
:host {
  display: block;
  width: 100%;
}

.lib-autocomplete {
  &__input {
    width: 100%;
  }
  &__panel {
    max-height: 250px;
    overflow-y: auto;
  }
}

## ✅ Checklist de Validación ATOM

| Requisito | Cómo verificar |
|-----------|---------------|
| ✅ Selector comienza con `lib-` | `selector: 'lib-*'` |
| ✅ Nombre de clase comienza con `Lib` | `export class Lib*Component` |
| ✅ `standalone: true` | En @Component decorator |
| ✅ `changeDetection: OnPush` | En @Component decorator |
| ✅ Inyección vía `inject()` | No usar constructor para DI |
| ✅ Usar `signal()`/`computed()` | Para estado reactivo |
| ✅ Lifecycle hooks implementados | OnInit, AfterViewInit, OnDestroy |
| ✅ Estilos en archivo `.scss` separado | No CSS inline |
| ✅ Accesibilidad ARIA | Atributos `role`, `aria-*` |
| ✅ Tema ATOM aplicado | `@use '@muface-lib/...'` en styles.scss |

---

## ❌ Prohibido en Componentes ATOM

```typescript
// ❌ NO usar constructor para inyección
constructor(private fb: FormBuilder) {}  // ❌

// ✅ USAR inject()
private readonly fb = inject(FormBuilder);  // ✅

// ❌ NO usar CSS en línea
template: `<div style="color: red">`  // ❌

// ✅ USAR archivo .scss separado
styleUrl: './component.scss'  // ✅

// ❌ NO omitir ChangeDetectionStrategy.OnPush
changeDetection: ChangeDetectionStrategy.Default  // ❌

// ✅ USAR OnPush
changeDetection: ChangeDetectionStrategy.OnPush  // ✅
```
```

---

### 🔹 `knowledge/angular-guidelines/atom-styles-guide.md`

```markdown
# 🎨 Guía de Estilos ATOM - Aplicación de Temas

## Configuración Global (styles.scss)

### Paso 1: Importar módulos requeridos
```scss
// styles.scss - RAÍZ del proyecto Angular
@use '@angular/material' as mat;
@use '@muface-lib/muface-lib/estilos/m3-theme' as muf-theme;

@include mat.core();
```

### Paso 2: Aplicar tema ATOM
```scss
:root {
  @include mat.all-component-themes(muf-theme.$light-theme);
}

// Para modo oscuro (opcional):
@media (prefers-color-scheme: dark) {
  :root {
    @include mat.all-component-themes(muf-theme.$dark-theme);
  }
}
```

### Paso 3: Overrides corporativos (si son necesarios)
```scss
// Ejemplo: personalizar color primario de botones
.lib-button--primary {
  --mat-button-background-color: #{muf-theme.$corp-primary};
  --mat-button-hover-state-layer-color: #{muf-theme.$corp-primary-dark};
}
```

---

## Estilos por Componente

### Reglas:
1. ✅ Usar BEM naming: `.component__element--modifier`
2. ✅ Estilos acotados con `:host`
3. ✅ No usar `!important` salvo excepción justificada
4. ✅ Usar variables de tema ATOM, no hardcodear colores

### Ejemplo correcto:
```scss
// lib-card.component.scss
:host {
  display: block;
  border: 1px solid var(--mat-divider-color);
  border-radius: 8px;
}

.lib-card {
  &__header {
    padding: var(--spacing-md);
    background: var(--mat-sys-surface);
  }
  
  &__content {
    padding: var(--spacing-md);
  }
  
  &--elevated {
    box-shadow: var(--mat-sys-elevation-level2);
  }
}
```

### Ejemplo incorrecto:
```scss
// ❌ Hardcodear colores corporativos
.lib-card {
  border-color: #0066CC;  // ❌ Usar variable de tema
}

// ❌ CSS global que afecta a otros componentes
.card {  // ❌ Sin :host, afecta globalmente
  margin: 10px;
}
