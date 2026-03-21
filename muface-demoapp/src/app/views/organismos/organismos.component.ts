import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-organismos',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, RouterLink],
  template: `
    <div class="space-y-10">
      <header class="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div class="max-w-2xl">
          <nav class="flex items-center gap-2 text-[10px] font-bold text-on-surface-variant uppercase tracking-[0.2em] mb-4">
            <span>Admin</span>
            <lucide-icon name="chevron-right" [size]="10"></lucide-icon>
            <span class="text-primary">Organismos</span>
          </nav>
          <h1 class="font-display text-5xl font-extrabold text-on-surface tracking-tight leading-tight mb-2">Organismos Públicos</h1>
          <p class="text-on-surface-variant text-lg font-light leading-relaxed">Gestión y supervisión de las entidades colaboradoras y delegaciones territoriales vinculadas a MUFACE.</p>
        </div>
        <button 
          routerLink="/new-organismo"
          class="bg-primary text-white px-8 py-4 rounded-full font-display font-bold text-sm tracking-widest uppercase flex items-center gap-3 shadow-xl shadow-primary/20 hover:scale-105 transition-transform"
        >
          <lucide-icon name="plus" [size]="18"></lucide-icon>
          Nuevo Organismo
        </button>
      </header>

      <div class="bg-surface-container-lowest rounded-3xl overflow-hidden shadow-sm">
        <div class="bg-surface-container-high px-8 py-5 flex justify-between items-center">
          <div class="flex gap-4">
            <button class="text-xs font-bold px-4 py-2 bg-white rounded-lg shadow-sm text-primary">Todos</button>
            <button class="text-xs font-bold px-4 py-2 text-on-surface-variant hover:bg-white/50 rounded-lg transition-all">Delegaciones</button>
            <button class="text-xs font-bold px-4 py-2 text-on-surface-variant hover:bg-white/50 rounded-lg transition-all">Sedes</button>
          </div>
          <div class="relative w-64">
            <lucide-icon name="search" class="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/40" [size]="14"></lucide-icon>
            <input type="text" placeholder="Buscar organismo..." class="w-full bg-white border-none rounded-lg py-2 pl-9 pr-4 text-xs font-sans focus:ring-1 focus:ring-primary/20" />
          </div>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-surface-container-lowest border-b border-outline-variant/10">
                <th class="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">ID / DIR3</th>
                <th class="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Organismo</th>
                <th class="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Localización</th>
                <th class="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Estado</th>
                <th class="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-surface-container-high">
              @for (org of organismos; track org.id) {
                <tr class="hover:bg-surface-container-low transition-colors">
                  <td class="px-8 py-6 font-mono text-xs text-primary font-bold">{{org.id}}</td>
                  <td class="px-8 py-6">
                    <p class="font-bold text-on-surface">{{org.name}}</p>
                    <p class="text-[10px] text-on-surface-variant font-medium opacity-60 uppercase tracking-widest">{{org.type}}</p>
                  </td>
                  <td class="px-8 py-6 text-sm text-on-surface-variant">{{org.loc}}</td>
                  <td class="px-8 py-6">
                    <span class="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider" [ngClass]="{
                      'bg-amber-100': org.alert,
                      'text-amber-700': org.alert,
                      'bg-emerald-100': !org.alert,
                      'text-emerald-700': !org.alert
                    }">
                      {{org.status}}
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
export class OrganismosComponent {
  organismos = [
    { id: 'ORG-28001', name: 'Sede Central MUFACE', loc: 'Madrid', status: 'Activo', type: 'Sede' },
    { id: 'ORG-08002', name: 'Delegación Provincial Barcelona', loc: 'Barcelona', status: 'Activo', type: 'Delegación' },
    { id: 'ORG-41003', name: 'Oficina de Atención Sevilla', loc: 'Sevilla', status: 'Mantenimiento', type: 'Oficina', alert: true },
    { id: 'ORG-46004', name: 'Delegación Provincial Valencia', loc: 'Valencia', status: 'Activo', type: 'Delegación' },
  ];
}
