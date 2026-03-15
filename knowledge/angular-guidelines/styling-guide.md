## 3️⃣ `knowledge/angular-guidelines/styling-guide.md`

```markdown
# 🎨 Guía de Estilos Corporativa

## Variables SCSS Globales

### Colores
```scss
// styles/_variables.scss
$corp-primary: #0066CC;
$corp-primary-dark: #004C99;
$corp-primary-light: #3385D6;

$corp-secondary: #6C757D;
$corp-success: #28A745;
$corp-danger: #DC3545;
$corp-warning: #FFC107;
$corp-info: #17A2B8;

$corp-white: #FFFFFF;
$corp-black: #000000;
$corp-gray-100: #F8F9FA;
$corp-gray-200: #E9ECEF;
$corp-gray-300: #DEE2E6;
$corp-gray-400: #CED4DA;
$corp-gray-500: #ADB5BD;
$corp-gray-600: #6C757D;
$corp-gray-700: #495057;
$corp-gray-800: #343A40;
$corp-gray-900: #212529;
```

### Spacing
```scss
$spacing-xs: 4px;
$spacing-sm: 8px;
$spacing-md: 16px;
$spacing-lg: 24px;
$spacing-xl: 32px;
$spacing-2xl: 48px;
```

### Typography
```scss
$font-family-base: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
$font-family-mono: 'Consolas', 'Monaco', 'Courier New', monospace;

$font-size-xs: 10px;
$font-size-sm: 12px;
$font-size-base: 14px;
$font-size-lg: 16px;
$font-size-xl: 20px;
$font-size-2xl: 24px;
$font-size-3xl: 32px;

$font-weight-light: 300;
$font-weight-normal: 400;
$font-weight-medium: 500;
$font-weight-bold: 700;

$line-height-base: 1.5;
$line-height-tight: 1.25;
```

### Breakpoints
```scss
$breakpoint-xs: 0;
$breakpoint-sm: 576px;
$breakpoint-md: 768px;
$breakpoint-lg: 992px;
$breakpoint-xl: 1200px;
$breakpoint-2xl: 1400px;
```

---

## BEM Naming Convention

```scss
// ✅ Correcto (BEM)
.user-card {                    // Block
  &__header {                   // Element
    &--highlighted {            // Modifier
      background: $corp-primary;
    }
  }
  
  &__title {
    font-size: $font-size-lg;
  }
  
  &__actions {
    @media (min-width: $breakpoint-md) {
      display: flex;
    }
  }
}

// ❌ Incorrecto
.userCardHeader { }             // camelCase
.user-card-header { }           // kebab sin BEM
.card .header { }               // Anidamiento semántico incorrecto
```

---

## Mixins Corporativos

### Responsive
```scss
@mixin respond-to($breakpoint) {
  @if $breakpoint == sm {
    @media (min-width: $breakpoint-sm) { @content; }
  } @else if $breakpoint == md {
    @media (min-width: $breakpoint-md) { @content; }
  } @else if $breakpoint == lg {
    @media (min-width: $breakpoint-lg) { @content; }
  }
}

// Uso
.container {
  padding: $spacing-md;
  @include respond-to(md) {
    padding: $spacing-lg;
  }
}
```

### Truncate Text
```scss
@mixin text-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

// Uso
.title {
  @include text-truncate;
  max-width: 300px;
}
```

### Center Flexbox
```scss
@mixin flex-center {
  display: flex;
  justify-content: center;
  align-items: center;
}

// Uso
.modal-content {
  @include flex-center;
  min-height: 200px;
}
```

---

## Estilos de Componente

### ViewEncapsulation
```typescript
// ✅ Default (Emulated) - usar en 95% de casos
@Component({
  selector: 'app-user-card',
  templateUrl: './user-card.component.html',
  styleUrls: ['./user-card.component.scss']
})

// ✅ ShadowDom - cuando se necesita aislamiento total
@Component({
  selector: 'app-widget',
  templateUrl: './widget.component.html',
  styleUrls: ['./widget.component.scss'],
  encapsulation: ViewEncapsulation.ShadowDom
})

// ❌ None - solo para librerías de temas
@Component({
  encapsulation: ViewEncapsulation.None  // Requiere aprobación
})
```

### Estructura de archivo SCSS
```scss
// user-card.component.scss

// 1. Imports
@import '../../styles/variables';
@import '../../styles/mixins';

// 2. Variables locales
$local-primary: darken($corp-primary, 10%);

// 3. Estilos del componente (BEM)
.user-card {
  padding: $spacing-md;
  border: 1px solid $corp-gray-300;
  border-radius: 4px;
  
  &__header {
    @include flex-center;
    margin-bottom: $spacing-sm;
  }
  
  &__title {
    @include text-truncate;
    font-size: $font-size-lg;
    font-weight: $font-weight-bold;
    color: $corp-gray-900;
  }
  
  &__content {
    font-size: $font-size-base;
    line-height: $line-height-base;
  }
  
  &--selected {
    border-color: $corp-primary;
    box-shadow: 0 0 0 2px $corp-primary-light;
  }
}
```
```