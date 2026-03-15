## 1️⃣ `knowledge/angular-guidelines/coding-standards.md`

```markdown
# 🅰️ Estándares de Código Angular - Corporativo

## ✅ Convenciones Obligatorias

### Nomenclatura

#### Componentes
```typescript
// ✅ Correcto
@Component({ selector: 'app-user-profile', ... })
export class UserProfileComponent {}

// ❌ Incorrecto
@Component({ selector: 'UserProfile', ... })  // selector debe ser kebab-case
export class userProfileComponent {}          // clase debe ser PascalCase
```

#### Servicios
```typescript
// ✅ Correcto
@Injectable({ providedIn: 'root' })
export class UserService {
  constructor(private http: HttpClient) {}
}

// ❌ Incorrecto
export class userApi { }  // Debe tener sufijo Service y ser PascalCase
```

#### Pipes y Directivas
```typescript
// ✅ Correcto
@Pipe({ name: 'formatCurrency' })
export class FormatCurrencyPipe {}

@Directive({ selector: '[appHighlight]' })
export class HighlightDirective {}

// ❌ Incorrecto
@Pipe({ name: 'format_currency' })  // snake_case no permitido
```

---

## 📁 Estructura de Proyectos

### Estructura recomendada (por feature)
```
src/app/
├── core/                    # Singleton services, interceptors, guards
│   ├── interceptors/
│   ├── guards/
│   ├── services/
│   └── core.module.ts
│
├── shared/                  # Componentes/pipes/directivas reutilizables
│   ├── components/
│   ├── pipes/
│   ├── directives/
│   └── shared.module.ts
│
├── features/                # Módulos de funcionalidad (lazy loaded)
│   ├── users/
│   │   ├── components/
│   │   ├── services/
│   │   ├── users-routing.module.ts
│   │   └── users.module.ts
│   └── auth/
│
├── app-routing.module.ts
└── app.module.ts
```

### Reglas de módulos
| Módulo | Propósito | providedIn |
|--------|-----------|------------|
| `CoreModule` | Servicios singleton, interceptors | `root` |
| `SharedModule` | Componentes reutilizables | NO (se importa donde se usa) |
| `FeatureModule` | Funcionalidad específica | `root` o lazy loaded |

---

## 🔧 Manejo de HTTP

### Interceptors obligatorios
```typescript
// ✅ Todos los proyectos deben incluir:
// 1. AuthInterceptor - Añade token JWT
// 2. ErrorInterceptor - Manejo centralizado de errores
// 3. LoggingInterceptor - Log de requests/responses (dev only)
```

### Patrón de servicio HTTP
```typescript
@Injectable({ providedIn: 'root' })
export class UserService {
  private readonly apiUrl = environment.apiUrl + '/users';

  constructor(private http: HttpClient) {}

  // ✅ GET con tipo de retorno explícito
  getUsers(): Observable<User[]> {
    return this.http.get<User[]>(this.apiUrl);
  }

  // ✅ POST con request tipado
  createUser(user: CreateUserRequest): Observable<User> {
    return this.http.post<User>(this.apiUrl, user);
  }

  // ✅ Manejo de errores centralizado
  getUserById(id: number): Observable<User> {
    return this.http.get<User>(`${this.apiUrl}/${id}`)
      .pipe(catchError(this.handleError));
  }

  private handleError(error: HttpErrorResponse): Observable<never> {
    // Logging corporativo (NO console.log)
    this.logger.error('HTTP Error', error);
    return throwError(() => new Error('Error de conexión'));
  }
}
```

---

## 🧠 Gestión de Estado

### Nivel 1: Estado simple (BehaviorSubject)
```typescript
// ✅ Para estado local de componente/servicio
private readonly userSubject = new BehaviorSubject<User | null>(null);
public readonly user$ = this.userSubject.asObservable();

updateUser(user: User): void {
  this.userSubject.next(user);
}
```

### Nivel 2: Estado complejo (NgRx/Akita)
```typescript
// ✅ Solo si aprobado por arquitectura
// - Múltiples componentes comparten estado
// - Historial de acciones necesario
// - Time-travel debugging requerido
```

### ❌ Prohibido
```typescript
// ❌ Estado global en variables públicas
public static currentUser: User;  // NO usar

// ❌ Modificar inputs directamente
@Input() user: User;
updateName() {
  this.user.name = 'New';  // ❌ Mutación directa
}

// ✅ Usar inmutabilidad
updateName() {
  this.userChanged.emit({ ...this.user, name: 'New' });
}
```

---

## 📝 Validación de Formularios

### Reactivos (recomendado)
```typescript
form = this.fb.group({
  email: ['', [
    Validators.required,
    Validators.email,
    Validators.maxLength(100)
  ]],
  password: ['', [
    Validators.required,
    Validators.minLength(8),
    Validators.pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/)
  ]]
});
```

### Mensajes de error centralizados
```typescript
private readonly errorMessages = {
  email: {
    required: 'El email es obligatorio',
    email: 'Formato de email inválido',
    maxlength: 'Máximo 100 caracteres'
  },
  password: {
    required: 'La contraseña es obligatoria',
    minlength: 'Mínimo 8 caracteres',
    pattern: 'Debe incluir mayúscula, minúscula y número'
  }
};
```

---

## 🚫 Prohibido

| Práctica | Alternativa |
|----------|-------------|
| `console.log()` | `LoggerService` corporativo |
| Suscripciones sin `takeUntil` o `async` pipe | `takeUntil(this.destroy$)` |
| `any` en tipos | Interfaces TypeScript explícitas |
| URLs hardcoded | `environment.ts` files |
| Tokens/keys en código | Variables de entorno + Azure Key Vault |
| Modificar `@Input()` directamente | Emitir eventos con `@Output()` |
| `setTimeout` para async | `timer()` de RxJS |

---

## 🧪 Testing

### Cobertura mínima requerida
| Tipo | Cobertura |
|------|-----------|
| Servicios core | 90% |
| Componentes compartidos | 80% |
| Componentes feature | 60% |
| Pipes/Directivas | 80% |

### Patrón de test
```typescript
describe('UserService', () => {
  let service: UserService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        UserService,
        { provide: HttpClient, useValue: jasmine.createSpyObj('HttpClient', ['get', 'post']) }
      ]
    });
    service = TestBed.inject(UserService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();  // ✅ Verificar no hay requests pendientes
  });

  it('debe obtener usuarios', () => {
    const mockUsers: User[] = [{ id: 1, name: 'Test' }];
    
    service.getUsers().subscribe(users => {
      expect(users.length).toBe(1);
      expect(users[0].name).toBe('Test');
    });

    const req = httpMock.expectOne('/api/users');
    expect(req.request.method).toBe('GET');
    req.flush(mockUsers);
  });
});
```