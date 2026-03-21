import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: 'dashboard', loadComponent: () => import('./views/dashboard/dashboard.component').then(m => m.DashboardComponent) },
  { path: 'expedientes', loadComponent: () => import('./views/expedientes/expedientes.component').then(m => m.ExpedientesComponent) },
  { path: 'organismos', loadComponent: () => import('./views/organismos/organismos.component').then(m => m.OrganismosComponent) },
  { path: 'titulaciones', loadComponent: () => import('./views/titulaciones/titulaciones.component').then(m => m.TitulacionesComponent) },
  { path: 'titulares', loadComponent: () => import('./views/titulares/titulares.component').then(m => m.TitularesComponent) },
  { path: 'ciudades', loadComponent: () => import('./views/ciudades/ciudades.component').then(m => m.CiudadesComponent) },
  { path: 'edit-expediente', loadComponent: () => import('./views/edit-expediente/edit-expediente.component').then(m => m.EditExpedienteComponent) },
  { path: 'new-titulacion', loadComponent: () => import('./views/new-titulacion/new-titulacion.component').then(m => m.NewTitulacionComponent) },
  { path: 'new-organismo', loadComponent: () => import('./views/new-organismo/new-organismo.component').then(m => m.NewOrganismoComponent) },
  { path: 'edit-ciudad', loadComponent: () => import('./views/edit-ciudad/edit-ciudad.component').then(m => m.EditCiudadComponent) },
];
