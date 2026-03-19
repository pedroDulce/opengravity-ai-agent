// knowledge/examples/api-interceptor.ts
// Ejemplo de interceptor HTTP corporativo

import { Injectable } from '@angular/core';
import {
    HttpInterceptor,
    HttpRequest,
    HttpHandler,
    HttpEvent,
    HttpErrorResponse,
    HttpHeaders
} from '@angular/common/http';
import { Observable, throwError, BehaviorSubject } from 'rxjs';
import { catchError, filter, take, switchMap } from 'rxjs/operators';
import { AuthService } from '@corp/auth';
import { LoggerService } from '@corp/core';
import { environment } from '@env/environment';

@Injectable()
export class ApiInterceptor implements HttpInterceptor {
    private isRefreshing = false;
    private refreshTokenSubject: BehaviorSubject<string | null> = new BehaviorSubject(null);

    constructor(
        private authService: AuthService,
        private logger: LoggerService
    ) { }

    intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
        // Skip interceptor para endpoints públicos
        if (req.url.includes('/public/') || req.url.includes('/auth/login')) {
            return next.handle(req);
        }

        const token = this.authService.getToken();

        if (token) {
            req = this.addToken(req, token);
        }

        return next.handle(req).pipe(
            catchError((error: HttpErrorResponse) => {
                if (error.status === 401) {
                    return this.handle401Error(req, next);
                }
                return throwError(() => error);
            })
        );
    }

    private addToken(request: HttpRequest<any>, token: string): HttpRequest<any> {
        return request.clone({
            setHeaders: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        });
    }

    private handle401Error(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
        if (!this.isRefreshing) {
            this.isRefreshing = true;
            this.refreshTokenSubject.next(null);

            return this.authService.refreshToken().pipe(
                switchMap((newToken: string) => {
                    this.isRefreshing = false;
                    this.refreshTokenSubject.next(newToken);
                    return next.handle(this.addToken(request, newToken));
                }),
                catchError((err) => {
                    this.isRefreshing = false;
                    this.authService.logout();
                    this.logger.error('Token refresh failed', err);
                    return throwError(() => err);
                })
            );
        } else {
            return this.refreshTokenSubject.pipe(
                filter(token => token !== null),
                take(1),
                switchMap(token => next.handle(this.addToken(request, token!)))
            );
        }
    }
}