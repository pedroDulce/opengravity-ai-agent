## 2️⃣ `knowledge/angular-guidelines/architecture.md`

```markdown
# 🏗️ Arquitectura Angular Corporativa

## Patrones Aprobados

### 1. Module per Feature (Recomendado)
```
features/
├── auth/
│   ├── components/
│   │   ├── login/
│   │   └── register/
│   ├── services/
│   ├── auth-routing.module.ts
│   └── auth.module.ts
└── users/
```

### 2. Lazy Loading Obligatorio
```typescript
// app-routing.module.ts
const routes: Routes = [
  { 
    path: 'auth', 
    loadChildren: () => import('./features/auth/auth.module')
      .then(m => m.AuthModule) 
  },
  { 
    path: 'users', 
    loadChildren: () => import('./features/users/users.module')
      .then(m => m.UsersModule),
    canLoad: [AuthGuard]  // ✅ Guard para lazy loading
  }
];
```

### 3. Smart/Dumb Components
```typescript
// ✅ Smart Component (contenedor con lógica)
@Component({ selector: 'app-user-list' })
export class UserListComponent {
  users$ = this.userService.getUsers();
  onSelect(user: User) { this.router.navigate(['/users', user.id]); }
}

// ✅ Dumb Component (presentacional, sin dependencias)
@Component({ 
  selector: 'app-user-card',
  changeDetection: ChangeDetectionStrategy.OnPush  // ✅ Performance
})
export class UserCardComponent {
  @Input() user!: User;
  @Output() selected = new EventEmitter<User>();
}
```

---

## Inyección de Dependencias

### Jerarquía de providers
```typescript
// ✅ Root (singleton en toda la app)
@Injectable({ providedIn: 'root' })
export class UserService {}

// ✅ Feature module (singleton en el módulo)
@NgModule({
  providers: [FeatureService]
})
export class FeatureModule {}

// ✅ Component (instancia por componente)
@Component({
  providers: [ComponentService]
})
export class MyComponent {}
```

---

## Guards y Resolvers

### AuthGuard (obligatorio en rutas protegidas)
```typescript
@Injectable({ providedIn: 'root' })
export class AuthGuard implements CanActivate {
  constructor(private authService: AuthService, private router: Router) {}

  canActivate(route: ActivatedRouteSnapshot): Observable<boolean> {
    return this.authService.isAuthenticated$.pipe(
      tap(authenticated => {
        if (!authenticated) {
          this.router.navigate(['/login'], { 
            queryParams: { returnUrl: route.url.join('/') } 
          });
        }
      })
    );
  }
}
```

### Resolver (para precargar datos)
```typescript
@Injectable({ providedIn: 'root' })
export class UserResolver implements Resolve<User> {
  constructor(private userService: UserService) {}

  resolve(route: ActivatedRouteSnapshot): Observable<User> {
    const id = route.paramMap.get('id');
    return this.userService.getUserById(Number(id));
  }
}
```

---

## Interceptores Corporativos

### AuthInterceptor
```typescript
@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const token = this.authService.getToken();
    
    if (token) {
      req = req.clone({
        setHeaders: { Authorization: `Bearer ${token}` }
      });
    }
    
    return next.handle(req);
  }
}
```

### ErrorInterceptor
```typescript
@Injectable()
export class ErrorInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    return next.handle(req).pipe(
      catchError((error: HttpErrorResponse) => {
        if (error.status === 401) {
          this.authService.logout();
        } else if (error.status >= 500) {
          this.toast.error('Error del servidor');
        }
        return throwError(() => error);
      })
    );
  }
}
```

### Registro en app.module.ts
```typescript
@NgModule({
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true },
    { provide: HTTP_INTERCEPTORS, useClass: ErrorInterceptor, multi: true }
  ]
})
export class AppModule {}
```