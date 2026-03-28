import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-titulaciones',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, RouterLink],
  template: `
    <div class="space-y-10">
      <header class="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div class="max-w-2xl">
          <nav class="flex items-center gap-2 text-[10px] font-bold text-on-surface-variant uppercase tracking-[0.2em] mb-4">
            <span>Admin</span>
            <lucide-icon name="chevron-right" [size]="10"></lucide-icon>
            <span class="text-primary">Titulaciones</span>
          </nav>
          <h1 class="font-display text-5xl font-extrabold text-on-surface tracking-tight leading-tight mb-2">Catálogo de Titulaciones</h1>
          <p class="text-on-surface-variant text-lg font-light leading-relaxed">Registro oficial de grados, másteres y certificaciones habilitantes para el acceso a la función pública.</p>
        </div>
        <button 
          routerLink="/new-titulacion"
          class="bg-primary text-white px-8 py-4 rounded-full font-display font-bold text-sm tracking-widest uppercase flex items-center gap-3 shadow-xl shadow-primary/20 hover:scale-105 transition-transform active:scale-95"
        >
          <lucide-icon name="plus" [size]="18"></lucide-icon>
          Nueva Titulación
        </button>
      </header>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        @for (stat of stats; track stat.label) {
          <div class="bg-surface-container-lowest p-6 rounded-2xl shadow-sm border-b-2 border-primary/10">
            <div class="flex items-center gap-4">
              <div class="p-3 bg-surface-container-low rounded-xl text-primary">
                <lucide-icon [name]="stat.icon" [size]="20"></lucide-icon>
              </div>
              <div>
                <p class="text-[10px] font-bold text-on-surface-variant/60 uppercase tracking-widest">{{stat.label}}</p>
                <p class="text-2xl font-display font-black text-on-surface">{{stat.value}}</p>
              </div>
            </div>
          </div>
        }
      </div>

      <div class="bg-surface-container-lowest rounded-3xl overflow-hidden shadow-sm">
        <div class="bg-surface-container-high px-8 py-5 flex justify-between items-center">
          <h3 class="font-display font-bold text-on-surface-variant text-xs uppercase tracking-[0.2em]">Registro de Títulos</h3>
          <div class="relative w-64">
            <lucide-icon name="magnifying-glass" class="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/40" [size]="14"></lucide-icon>
            <input type="text" placeholder="Filtrar títulos..." class="w-full bg-white border-none rounded-lg py-2 pl-9 pr-4 text-xs font-sans focus:ring-1 focus:ring-primary/20" />
          </div>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-surface-container-lowest border-b border-outline-variant/10">
                <th class="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Código BOE</th>
                <th class="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Denominación</th>
                <th class="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Nivel MECES</th>
                <th class="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Estado</th>
                <th class="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-surface-container-high">
              @for (tit of titulaciones; track tit.id) {
                <tr class="hover:bg-surface-container-low transition-colors">
                  <td class="px-8 py-6 font-mono text-sm text-primary font-bold">{{tit.id}}</td>
                  <td class="px-8 py-6 font-bold text-on-surface">{{tit.name}}</td>
                  <td class="px-8 py-6 text-sm text-on-surface-variant">{{tit.level}}</td>
                  <td class="px-8 py-6">
                    <span class="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider" [class.bg-amber-100]="tit.alert" [class.text-amber-700]="tit.alert" [class.bg-emerald-100]="!tit.alert" [class.text-emerald-700]="!tit.alert">
                      {{tit.status}}
                    </span>
                  </td>
                  <td class="px-8 py-6 text-right">
                    <button class="p-2 text-on-surface-variant/40 hover:text-primary transition-colors"><lucide-icon name="more-vertical" [size]="20"></lucide-icon></button>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `
})
export class TitulacionesComponent {
  stats = [
    { label: 'Total Títulos', value: '1.240', icon: 'graduation-cap' },
    { label: 'En Revisión', value: '14', icon: 'clock' },
    { label: 'Homologados', value: '98%', icon: 'users' },
  ];

  titulaciones = [
    { id: 'BOE-A-2023-1', name: 'Grado en Derecho', level: 'Nivel 2 (Grado)', status: 'Activo' },
    { id: 'BOE-A-2023-4', name: 'Máster en Gestión Pública', level: 'Nivel 3 (Máster)', status: 'Activo' },
    { id: 'BOE-A-2024-2', name: 'Grado en Ingeniería de Datos', level: 'Nivel 2 (Grado)', status: 'Pendiente', alert: true },
  ];
}
