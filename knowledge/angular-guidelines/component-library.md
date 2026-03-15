# 📄 Contenido para `knowledge/angular-guidelines/component-library.md`

# 🧩 Librería de Componentes Corporativos Angular

```markdown
## Componentes UI Base Disponibles

Todos los componentes están en el paquete `@corp/ui-components` y deben usarse en lugar de elementos HTML nativos.

---

## `corp-button`

Botón corporativo con variantes predefinidas.

### Uso básico
```typescript
<corp-button 
  variant="primary"
  (clicked)="onAction()">
  Click me
</corp-button>
```

### Propiedades
| Input | Tipo | Valores | Requerido |
|-------|------|---------|-----------|
| `variant` | string | `primary` \| `secondary` \| `danger` \| `ghost` | No (default: primary) |
| `size` | string | `small` \| `medium` \| `large` | No (default: medium) |
| `loading` | boolean | `true` \| `false` | No |
| `disabled` | boolean | `true` \| `false` | No |
| `icon` | string | Nombre de icono Material | No |

### Outputs
| Output | Tipo | Descripción |
|--------|------|-------------|
| `clicked` | `EventEmitter<void>` | Click del botón |

### Ejemplo completo
```typescript
<corp-button 
  variant="primary"
  size="medium"
  [loading]="isLoading"
  [disabled]="!form.valid"
  icon="save"
  (clicked)="onSave()">
  Guardar
</corp-button>
```

---

## `corp-form-field` + `corp-input`

Campo de formulario con label, validación y mensajes de error integrados.

### Uso básico
```typescript
<form [formGroup]="form">
  <corp-form-field 
    label="Email" 
    [errorMessages]="emailErrors"
    [required]="true">
    <corp-input 
      formControlName="email" 
      type="email"
      placeholder="usuario@empresa.com">
    </corp-input>
  </corp-form-field>
</form>
```

### Propiedades `corp-form-field`
| Input | Tipo | Descripción |
|-------|------|-------------|
| `label` | string | Label del campo |
| `errorMessages` | `Record<string, string>` | Mensajes por tipo de error |
| `required` | boolean | Muestra asterisco de requerido |
| `hint` | string | Texto de ayuda debajo del campo |

### Propiedades `corp-input`
| Input | Tipo | Valores |
|-------|------|---------|
| `type` | string | `text` \| `email` \| `password` \| `number` \| `tel` |
| `placeholder` | string | Placeholder del input |
| `maxLength` | number | Máximo de caracteres |
| `minLength` | number | Mínimo de caracteres |

### Ejemplo con validación
```typescript
// Componente
emailErrors = {
  required: 'El email es obligatorio',
  email: 'Formato de email inválido',
  maxlength: 'Máximo 100 caracteres'
};

form = this.fb.group({
  email: ['', [Validators.required, Validators.email, Validators.maxLength(100)]]
});

// Template
<corp-form-field 
  label="Email corporativo" 
  [errorMessages]="emailErrors"
  [required]="true"
  hint="Usa tu email @empresa.com">
  <corp-input 
    formControlName="email" 
    type="email"
    placeholder="usuario@empresa.com"
    [maxLength]="100">
  </corp-input>
</corp-form-field>
```

---

## `corp-table`

Tabla de datos con paginación, sorting y filtros corporativos.

### Uso básico
```typescript
<corp-table 
  [data]="users$"
  [columns]="userColumns"
  [pageSizeOptions]="[10, 25, 50]"
  [showPagination]="true"
  (rowClick)="onUserSelected($event)"
  (sortChange)="onSort($event)">
  
  <!-- Columna custom -->
  <ng-template corpColumnDef="actions" let-row>
    <corp-button 
      size="small" 
      variant="secondary" 
      (clicked)="edit(row)">
      Editar
    </corp-button>
  </ng-template>
</corp-table>
```

### Propiedades
| Input | Tipo | Descripción |
|-------|------|-------------|
| `data` | `T[]` | Array de datos para mostrar |
| `columns` | `ColumnDef[]` | Definición de columnas |
| `pageSizeOptions` | `number[]` | Opciones de paginación |
| `showPagination` | boolean | Mostrar/ocultar paginador |
| `loading` | boolean | Estado de carga |

### Outputs
| Output | Tipo | Descripción |
|--------|------|-------------|
| `rowClick` | `EventEmitter<T>` | Click en fila |
| `sortChange` | `EventEmitter<SortEvent>` | Cambio de orden |
| `pageChange` | `EventEmitter<PageEvent>` | Cambio de página |

### Definición de columnas
```typescript
userColumns: ColumnDef[] = [
  { key: 'name', label: 'Nombre', sortable: true },
  { key: 'email', label: 'Email', sortable: true },
  { key: 'role', label: 'Rol', sortable: false },
  { key: 'actions', label: 'Acciones', sortable: false, template: 'actions' }
];
```

---

## `corp-modal`

Ventana modal para diálogos, confirmaciones y formularios.

### Uso básico
```typescript
<!-- Trigger -->
<corp-button (clicked)="modal.open()">Abrir modal</corp-button>

<!-- Modal -->
<corp-modal #modal [title]="'Confirmar acción'">
  <div modal-content>
    <p>¿Estás seguro de continuar?</p>
  </div>
  <div modal-footer>
    <corp-button variant="ghost" (clicked)="modal.close()">Cancelar</corp-button>
    <corp-button variant="primary" (clicked)="onConfirm()">Confirmar</corp-button>
  </div>
</corp-modal>
```

### Propiedades
| Input | Tipo | Descripción |
|-------|------|-------------|
| `title` | string | Título del modal |
| `size` | string | `small` \| `medium` \| `large` \| `fullscreen` |
| `closeOnBackdrop` | boolean | Cerrar al hacer click fuera |
| `closeOnEscape` | boolean | Cerrar con tecla Escape |

### Outputs
| Output | Tipo | Descripción |
|--------|------|-------------|
| `opened` | `EventEmitter<void>` | Modal abierto |
| `closed` | `EventEmitter<void>` | Modal cerrado |
| `dismissed` | `EventEmitter<void>` | Modal descartado |

---

## `corp-toast`

Notificaciones toast para feedback de acciones.

### Uso desde servicio
```typescript
constructor(private toast: ToastService) {}

onSuccess() {
  this.toast.success('Operación completada correctamente');
}

onError() {
  this.toast.error('Hubo un error al procesar la solicitud');
}

onWarning() {
  this.toast.warning('Algunos campos no se pudieron guardar');
}

onInfo() {
  this.toast.info('Nueva versión disponible');
}
```

### Propiedades del servicio
| Método | Parámetros | Descripción |
|--------|-----------|-------------|
| `success(message, duration?)` | `string, number` | Toast verde (default 3000ms) |
| `error(message, duration?)` | `string, number` | Toast rojo (default 5000ms) |
| `warning(message, duration?)` | `string, number` | Toast amarillo (default 4000ms) |
| `info(message, duration?)` | `string, number` | Toast azul (default 3000ms) |

---

## `corp-spinner`

Indicador de carga corporativo.

### Uso básico
```typescript
<!-- Spinner centrado -->
<corp-spinner [show]="isLoading"></corp-spinner>

<!-- Spinner inline -->
<corp-button [loading]="loading">
  Guardar
</corp-button>
<!-- El botón ya incluye spinner interno cuando loading=true -->
```

### Propiedades
| Input | Tipo | Descripción |
|-------|------|-------------|
| `show` | boolean | Mostrar/ocultar spinner |
| `size` | string | `small` \| `medium` \| `large` |
| `overlay` | boolean | Mostrar overlay oscuro de fondo |

---

## Patrones de Composición

### ✅ Correcto
```typescript
<!-- Los componentes hijos NO conocen a sus padres -->
<corp-form-field label="Nombre">
  <corp-input formControlName="name"></corp-input>
</corp-form-field>

<!-- Usar ContentProjection para flexibilidad -->
<corp-modal title="Editar usuario">
  <ng-container modal-content>
    <app-user-form [user]="selectedUser"></app-user-form>
  </ng-container>
</corp-modal>
```

### ❌ Incorrecto
```typescript
<!-- El hijo NO debe llamar métodos del padre directamente -->
<app-user-form (save)="parentSaveMethod($event)"></app-user-form>

<!-- Usar siempre outputs para comunicación -->
<app-user-form (saveClicked)="onSave($event)"></app-user-form>
```

---

## Testing de Componentes

### Mínimo requerido
- 80% coverage en componentes compartidos (`@corp/ui-*`)
- 60% coverage en componentes de feature

### Ejemplo de test
```typescript
describe('CorpButtonComponent', () => {
  let component: CorpButtonComponent;
  let fixture: ComponentFixture<CorpButtonComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CorpButtonComponent]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(CorpButtonComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crear el componente', () => {
    expect(component).toBeTruthy();
  });

  it('debe emitir clicked al hacer click', () => {
    spyOn(component.clicked, 'emit');
    
    const button = fixture.nativeElement.querySelector('button');
    button.click();
    
    expect(component.clicked.emit).toHaveBeenCalledTimes(1);
  });

  it('debe estar disabled cuando loading=true', () => {
    component.loading = true;
    fixture.detectChanges();
    
    const button = fixture.nativeElement.querySelector('button');
    expect(button.disabled).toBeTrue();
  });
});
```

---

## Estilos y SCSS

### Variables corporativas disponibles
```scss
// styles/_variables.scss

// Colores
$corp-primary: #0066CC;
$corp-secondary: #6C757D;
$corp-danger: #DC3545;
$corp-success: #28A745;
$corp-warning: #FFC107;

// Spacing
$spacing-xs: 4px;
$spacing-sm: 8px;
$spacing-md: 16px;
$spacing-lg: 24px;
$spacing-xl: 32px;

// Typography
$font-family-base: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
$font-size-base: 14px;
$font-size-lg: 16px;
$font-size-sm: 12px;

// Breakpoints
$breakpoint-sm: 576px;
$breakpoint-md: 768px;
$breakpoint-lg: 992px;
$breakpoint-xl: 1200px;
```

### Uso en componentes
```scss
// user-component.component.scss
@import 'variables';

.user-component {
  padding: $spacing-md;
  
  &__title {
    color: $corp-primary;
    font-size: $font-size-lg;
    margin-bottom: $spacing-sm;
  }
  
  &__content {
    font-size: $font-size-base;
    
    @media (min-width: $breakpoint-md) {
      display: flex;
    }
  }
}
```

---

## Recursos Adicionales

- 📁 Ejemplos completos: `knowledge/examples/`
- 📁 Guías de estilo: `knowledge/angular-guidelines/coding-standards.md`
- 📁 Patrones de arquitectura: `knowledge/angular-guidelines/architecture.md`

