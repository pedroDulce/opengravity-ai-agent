// knowledge/examples/login-component.ts
// Ejemplo de componente login siguiendo estándares corporativos

import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { AuthService, LoginRequest, AuthResponse } from '@corp/auth';
import { ToastService } from '@corp/ui';
import { HttpErrorResponse } from '@angular/common/http';
import { LoggerService } from '@corp/core';

@Component({
    selector: 'app-login',
    templateUrl: './login.component.html',
    styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit, OnDestroy {
    private readonly destroy$ = new Subject<void>();

    form: FormGroup;
    loading = false;
    returnUrl: string;

    private readonly errors = {
        email: {
            required: 'El email es obligatorio',
            email: 'Formato de email inválido',
            maxlength: 'Máximo 100 caracteres'
        },
        password: {
            required: 'La contraseña es obligatoria',
            minlength: 'Mínimo 8 caracteres'
        }
    };

    constructor(
        private fb: FormBuilder,
        private authService: AuthService,
        private router: Router,
        private route: ActivatedRoute,
        private toast: ToastService,
        private logger: LoggerService
    ) { }

    ngOnInit(): void {
        this.initForm();
        this.returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/dashboard';
    }

    private initForm(): void {
        this.form = this.fb.group({
            email: ['', [
                Validators.required,
                Validators.email,
                Validators.maxLength(100)
            ]],
            password: ['', [
                Validators.required,
                Validators.minLength(8)
            ]]
        });
    }

    onSubmit(): void {
        if (this.form.invalid || this.loading) {
            this.form.markAllAsTouched();
            return;
        }

        this.loading = true;
        const { email, password } = this.form.value;

        const request: LoginRequest = {
            email: email.toLowerCase().trim(),
            password
        };

        this.authService.login(request)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response: AuthResponse) => this.handleSuccess(response),
                error: (error: HttpErrorResponse) => this.handleError(error),
                complete: () => { this.loading = false; }
            });
    }

    private handleSuccess(response: AuthResponse): void {
        this.logger.info('Login exitoso', { userId: response.user.id });

        this.router.navigate([this.returnUrl], {
            state: { loginTimestamp: new Date().toISOString() }
        });

        this.toast.success(`Bienvenido, ${response.user.name} `);
    }

    private handleError(error: HttpErrorResponse): void {
        const message = error.status === 401
            ? 'Email o contraseña inválidos'
            : error.status === 0
                ? 'Error de conexión. Verifica tu red.'
                : 'Error del servidor. Inténtalo más tarde.';

        this.toast.error(message);
        this.logger.warn('Login fallido', {
            error: error.message,
            status: error.status,
            email: this.form.value.email
        });
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }
}
