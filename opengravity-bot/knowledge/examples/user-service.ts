// knowledge/examples/user-service.ts
// Ejemplo de servicio HTTP tipado siguiendo estándares corporativos

import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map, shareReplay } from 'rxjs/operators';
import { environment } from '@env/environment';
import { LoggerService } from '@corp/core';

export interface User {
    id: number;
    email: string;
    name: string;
    role: 'admin' | 'user' | 'guest';
    createdAt: Date;
    updatedAt: Date;
}

export interface CreateUserRequest {
    email: string;
    name: string;
    password: string;
    role?: User['role'];
}

export interface UpdateUserRequest {
    name?: string;
    role?: User['role'];
}

export interface UserListResponse {
    data: User[];
    total: number;
    page: number;
    pageSize: number;
}

@Injectable({ providedIn: 'root' })
export class UserService {
    private readonly apiUrl = environment.apiUrl + '/users';

    constructor(
        private http: HttpClient,
        private logger: LoggerService
    ) { }

    getUsers(page = 1, pageSize = 10): Observable<UserListResponse> {
        const params = new HttpParams()
            .set('page', page.toString())
            .set('pageSize', pageSize.toString());

        return this.http.get<UserListResponse>(this.apiUrl, { params })
            .pipe(
                catchError(this.handleError)
            );
    }

    getUserById(id: number): Observable<User> {
        return this.http.get<User>(`${this.apiUrl}/${id}`)
            .pipe(
                catchError(this.handleError)
            );
    }

    createUser(request: CreateUserRequest): Observable<User> {
        return this.http.post<User>(this.apiUrl, request)
            .pipe(
                catchError(this.handleError)
            );
    }

    updateUser(id: number, request: UpdateUserRequest): Observable<User> {
        return this.http.put<User>(`${this.apiUrl}/${id}`, request)
            .pipe(
                catchError(this.handleError)
            );
    }

    deleteUser(id: number): Observable<void> {
        return this.http.delete<void>(`${this.apiUrl}/${id}`)
            .pipe(
                catchError(this.handleError)
            );
    }

    searchUsers(term: string): Observable<User[]> {
        const params = new HttpParams().set('q', term);

        return this.http.get<User[]>(`${this.apiUrl}/search`, { params })
            .pipe(
                map(users => users.map(u => ({ ...u, createdAt: new Date(u.createdAt) }))),
                shareReplay(1),  // Cache para búsquedas repetidas
                catchError(this.handleError)
            );
    }

    private handleError(error: HttpErrorResponse): Observable<never> {
        let message = 'Error de conexión';

        if (error.status === 400) {
            message = 'Datos inválidos';
        } else if (error.status === 401) {
            message = 'No autorizado';
        } else if (error.status === 403) {
            message = 'Acceso denegado';
        } else if (error.status === 404) {
            message = 'Recurso no encontrado';
        } else if (error.status >= 500) {
            message = 'Error del servidor';
        }

        this.logger.error('UserService error', {
            status: error.status,
            message: error.message
        });

        return throwError(() => new Error(message));
    }
}