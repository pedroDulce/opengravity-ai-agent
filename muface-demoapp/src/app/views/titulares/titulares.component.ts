import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-titulares',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, RouterLink],
  template: `
    <div class="space-y-10">
      <header class="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div class="max-w-2xl">
          <nav class="flex items-center gap-2 text-[10px] font-bold text-on-surface-variant uppercase tracking-[0.2em] mb-4">
            <span>Censo</span>
            <lucide-icon name="chevron-right" [size]="10"></lucide-icon>
            <span class="text-primary">Titulares</span>
          </nav>
          <h1 class="font-display text-5xl font-extrabold text-on-surface tracking-tight leading-tight mb-2">Censo de Titulares</h1>
          <p class="text-on-surface-variant text-lg font-light leading-relaxed">Gestión integral de los mutualistas activos, jubilados y beneficiarios del sistema MUFACE.</p>
        </div>
        <div class="flex gap-3">
          <button class="bg-surface-container-highest text-primary px-6 py-4 rounded-full font-display font-bold text-sm tracking-widest uppercase flex items-center gap-3 hover:bg-surface-container-high transition-all">
            <lucide-icon name="download" [size]="18"></lucide-icon>
            Exportar
          </button>
          <button class="bg-primary text-white px-8 py-4 rounded-full font-display font-bold text-sm tracking-widest uppercase flex items-center gap-3 shadow-xl shadow-primary/20 hover:scale-105 transition-transform">
            <lucide-icon name="plus" [size]="18"></lucide-icon>
            Alta Titular
          </button>
        </div>
      </header>

      <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div class="lg:col-span-3 bg-surface-container-lowest rounded-3xl overflow-hidden shadow-sm">
          <div class="p-8 border-b border-outline-variant/10 flex justify-between items-center">
            <div class="flex gap-4">
              <button class="px-4 py-2 bg-primary text-white rounded-xl text-xs font-bold">Todos</button>
              <button class="px-4 py-2 text-on-surface-variant hover:bg-surface-container-low rounded-xl text-xs font-bold">Activos</button>
              <button class="px-4 py-2 text-on-surface-variant hover:bg-surface-container-low rounded-xl text-xs font-bold">Jubilados</button>
            </div>
            <div class="relative w-72">
              <lucide-icon name="search" class="absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant/40" [size]="18"></lucide-icon>
              <input type="text" placeholder="Buscar por DNI o Nombre..." class="w-full bg-surface-container-low border-none rounded-2xl py-3 pl-12 pr-4 text-sm font-sans focus:ring-2 focus:ring-primary/20" />
            </div>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-surface-container-low/30 border-b border-outline-variant/10">
                  <th class="px-8 py-4 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Titular</th>
                  <th class="px-8 py-4 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">DNI</th>
                  <th class="px-8 py-4 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Provincia</th>
                  <th class="px-8 py-4 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Estado</th>
                  <th class="px-8 py-4 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest text-right">Acciones</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-surface-container-high">
                @for (tit of titulares; track tit.dni) {
                  <tr class="hover:bg-surface-container-low/50 transition-colors">
                    <td class="px-8 py-5">
                      <p class="font-bold text-on-surface text-sm">{{tit.name}}</p>
                      <p class="text-[10px] text-on-surface-variant font-medium opacity-60">Afiliado desde 2015</p>
                    </td>
                    <td class="px-8 py-5 font-mono text-xs text-on-surface-variant">{{tit.dni}}</td>
                    <td class="px-8 py-5 text-sm text-on-surface-variant">{{tit.prov}}</td>
                    <td class="px-8 py-5">
                      <div class="flex items-center gap-2">
                        <div class="w-1.5 h-1.5 rounded-full" [ngClass]="{
                          'bg-on-tertiary-fixed-variant': tit.alert,
                          'bg-emerald-500': !tit.alert
                        }"></div>
                        <span class="text-xs font-bold text-on-surface">{{tit.status}}</span>
                      </div>
                    </td>
                    <td class="px-8 py-5 text-right">
                      <button class="p-2 text-on-surface-variant/40 hover:text-primary transition-colors"><lucide-icon name="chevron-right" [size]="18"></lucide-icon></button>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        </div>

        <div class="space-y-6">
          <div class="bg-primary p-8 rounded-3xl text-white shadow-xl shadow-primary/20">
            <h3 class="font-display font-bold text-lg mb-6">Estadísticas Censo</h3>
            <div class="space-y-6">
              <div>
                <div class="flex justify-between text-xs font-bold uppercase tracking-widest mb-2 opacity-60">
                  <span>Activos</span>
                  <span>72%</span>
                </div>
                <div class="h-2 bg-white/10 rounded-full overflow-hidden">
                  <div class="h-full bg-white w-[72%]"></div>
                </div>
              </div>
              <div>
                <div class="flex justify-between text-xs font-bold uppercase tracking-widest mb-2 opacity-60">
                  <span>Jubilados</span>
                  <span>28%</span>
                </div>
                <div class="h-2 bg-white/10 rounded-full overflow-hidden">
                  <div class="h-full bg-white w-[28%]"></div>
                </div>
              </div>
            </div>
            <div class="mt-8 pt-8 border-t border-white/10">
              <p class="text-3xl font-display font-black">892.412</p>
              <p class="text-[10px] font-bold uppercase tracking-widest opacity-60">Total Mutualistas</p>
            </div>
          </div>

          <div class="bg-surface-container-lowest p-8 rounded-3xl shadow-sm border border-outline-variant/10">
            <h3 class="font-display font-bold text-on-surface mb-4">Próximas Revisiones</h3>
            <div class="space-y-4">
              @for (rev of revisions; track rev.id) {
                <div class="p-4 bg-surface-container-low rounded-2xl flex items-center gap-4">
                  <div class="w-10 h-10 rounded-xl bg-white flex items-center justify-center text-primary shadow-sm">
                    <lucide-icon name="clock" [size]="18"></lucide-icon>
                  </div>
                  <div>
                    <p class="text-xs font-bold text-on-surface">{{rev.title}}</p>
                    <p class="text-[10px] text-on-surface-variant opacity-60">{{rev.time}}</p>
                  </div>
                </div>
              }
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class TitularesComponent {
  titulares = [
    { name: 'MARTÍNEZ SÁEZ, ROBERTO', dni: '12345678A', prov: 'Madrid', status: 'Activo' },
    { name: 'LÓPEZ RUIZ, ELENA', dni: '87654321B', prov: 'Barcelona', status: 'Activo' },
    { name: 'GÓMEZ CANO, JAVIER', dni: '45678901C', prov: 'Sevilla', status: 'Baja', alert: true },
    { name: 'FERNÁNDEZ DÍAZ, ANA', dni: '23456789D', prov: 'Valencia', status: 'Activo' },
  ];

  revisions = [
    { id: 1, title: 'Revisión Trienal', time: 'Expira en 14 días' },
    { id: 2, title: 'Revisión Trienal', time: 'Expira en 21 días' },
  ];
}
