```markdown
# ⚡ ATOM Quick Reference - Resumen Ejecutivo

## Reglas NO NEGOCIABLES para componentes ATOM

### ✅ DEBE tener:
```typescript
@Component({
  selector: 'lib-*',              // Prefijo obligatorio
  standalone: true,               // Standalone obligatorio
  changeDetection: OnPush,        // OnPush obligatorio
  // ...
})
export class Lib*Component<T> extends LibBaseComponent<T> {
  private readonly service = inject(MyService);  // inject() obligatorio
  private readonly state = signal<T>(initial);   // signal() para estado
  // Lifecycle: ngOnInit, ngAfterViewInit, ngOnDestroy
}
```

### ❌ NUNCA hacer:
```typescript
// ❌ Constructor para DI
constructor(private s: Service) {}  // → Usar inject()

// ❌ CSS inline
<div style="color:red">  // → Usar archivo .scss separado

// ❌ ChangeDetection default
changeDetection: ChangeDetectionStrategy.Default  // → OnPush
```

### 🎨 Estilos globales (styles.scss - OBLIGATORIO):
```scss
@use '@angular/material' as mat;
@use '@muface-lib/muface-lib/estilos/m3-theme' as muf-theme;
@include mat.core();
:root { @include mat.all-component-themes(muf-theme.$light-theme); }
```

### 🧩 Componentes UI disponibles:
| Componente | Selector | Uso principal |
|------------|----------|--------------|
| Button | `corp-button` | Acciones primarias/secundarias |
| Form Field | `corp-form-field` + `corp-input` | Formularios con validación |
| Table | `corp-table` | Listados con paginación/sorting |
| Modal | `corp-modal` | Diálogos y confirmaciones |
| Toast | `ToastService` | Notificaciones de feedback |
| Spinner | `corp-spinner` | Indicadores de carga |

### 🔑 Keywords para búsqueda:
`atom`, `lib-`, `standalone`, `OnPush`, `inject`, `signal`, `computed`, `m3-theme`, `muface-lib`, `LibBaseComponent`
```

---

### 3️⃣ Mejorar `atom-development-guide.md` con ejemplo COMPLETO

**Añade un ejemplo de componente ATOM completo al final del archivo:**

```markdown
## 📦 Ejemplo Completo: LibCiudadesListComponent

```typescript
// lib-ciudades-list.component.ts
import { Component, ChangeDetectionStrategy, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { LibBaseComponent } from './lib-base.component';
import { Ciudad, CiudadesEstructura } from '../models/ciudad.model';
import { CiudadesService } from '../services/ciudades.service';
import { CorpTableComponent } from '@corp/ui-table';
import { CorpButtonComponent } from '@corp/ui-button';
import { ToastService } from '@corp/ui-toast';

@Component({
  selector: 'lib-ciudades-list',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, CorpTableComponent, CorpButtonComponent],
  templateUrl: './lib-ciudades-list.component.html',
  styleUrl: './lib-ciudades-list.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LibCiudadesListComponent 
  extends LibBaseComponent<Ciudad>
  implements OnInit, OnDestroy 
{
  private readonly ciudadesService = inject(CiudadesService);
  private readonly toast = inject(ToastService);
  private readonly destroy$ = new Subject<void>();
  
  // Estado reactivo con signals
  private readonly _loading = signal(false);
  private readonly _ciudades = signal<Ciudad[]>([]);
  readonly ciudades$ = this._ciudades.asObservable();
  
  // Inputs heredados de LibBaseComponent:
  // @Input() estructura!: CiudadesEstructura;
  // @Input() dtos!: Ciudad[];
  
  ngOnInit(): void {
    this.loadCiudades();
  }
  
  private loadCiudades(): void {
    this._loading.set(true);
    this.ciudadesService.getAll()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this._ciudades.set(data);
          this._loading.set(false);
        },
        error: () => {
          this.toast.error('Error cargando ciudades');
          this._loading.set(false);
        }
      });
  }
  
  onEditar(ciudad: Ciudad): void {
    // Emitir evento vía output heredado
    this.dataChanged.emit(ciudad);
  }
  
  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
```

```html
<!-- lib-ciudades-list.component.html -->
<corp-spinner [show]="_loading()" overlay></corp-spinner>

<corp-table 
  [data]="ciudades$ | async"
  [columns]="columnasDef"
  (rowClick)="onEditar($event)">
  
  <ng-template corpColumnDef="acciones" let-row>
    <corp-button size="small" variant="secondary" (clicked)="onEditar(row)">
      Editar
    </corp-button>
  </ng-template>
</corp-table>
```

```scss
// lib-ciudades-list.component.scss
:host {
  display: block;
  padding: var(--spacing-md);
}

.lib-ciudades-list {
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
  }
}

