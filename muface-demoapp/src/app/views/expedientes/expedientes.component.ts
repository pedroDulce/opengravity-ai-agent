import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { RouterLink } from '@angular/router';
import { FirestoreService } from '../../services/firestore.service';
import { Expediente } from '../../models';

@Component({
  selector: 'app-expedientes',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, RouterLink],
  template: `
    <div class="space-y-10">
      <header class="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div class="max-w-2xl">
          <nav class="flex items-center gap-2 text-[10px] font-bold text-on-surface-variant uppercase tracking-[0.2em] mb-4">
            <span>Gestión</span>
            <lucide-icon name="chevron-right" [size]="10"></lucide-icon>
            <span class="text-primary">Expedientes</span>
          </nav>
          <h1 class="font-display text-5xl font-extrabold text-on-surface tracking-tight leading-tight mb-2">Expedientes Administrativos</h1>
          <p class="text-on-surface-variant text-lg font-light leading-relaxed">Seguimiento y tramitación de solicitudes, prestaciones y expedientes de mutualistas.</p>
        </div>
        <button 
          routerLink="/edit-expediente"
          class="bg-primary text-white px-8 py-4 rounded-full font-display font-bold text-sm tracking-widest uppercase flex items-center gap-3 shadow-xl shadow-primary/20 hover:scale-105 transition-transform"
        >
          <lucide-icon name="plus" [size]="18"></lucide-icon>
          Nuevo Expediente
        </button>
      </header>

      <div class="bg-surface-container-lowest rounded-3xl overflow-hidden shadow-sm">
        <div class="bg-surface-container-high px-8 py-5 flex flex-col md:flex-row justify-between items-center gap-4">
          <div class="flex gap-2 overflow-x-auto pb-2 md:pb-0 no-scrollbar w-full md:w-auto">
            @for (tab of tabs; track tab; let i = $index) {
              <button class="px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all" [ngClass]="{
                'bg-primary': i === 0,
                'text-white': i === 0,
                'text-on-surface-variant': i !== 0,
                'hover:bg-white/50': i !== 0
              }">
                {{tab}}
              </button>
            }
          </div>
          <div class="flex gap-3 w-full md:w-auto">
            <div class="relative flex-1 md:w-64">
              <lucide-icon name="magnifying-glass" class="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/40" [size]="14"></lucide-icon>
              <input type="text" placeholder="Buscar por ID o Titular..." class="w-full bg-white border-none rounded-lg py-2 pl-9 pr-4 text-xs font-sans focus:ring-1 focus:ring-primary/20" />
            </div>
            <button class="p-2 bg-white rounded-lg text-on-surface-variant hover:text-primary transition-colors border border-outline-variant/10">
              <lucide-icon name="filter" [size]="18"></lucide-icon>
            </button>
          </div>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-surface-container-lowest border-b border-outline-variant/10">
                <th class="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Referencia</th>
                <th class="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Titular</th>
                <th class="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Tipo de Trámite</th>
                <th class="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Fecha Alta</th>
                <th class="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Estado</th>
                <th class="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-surface-container-high">
              @for (exp of expedientes; track exp.id) {
                <tr class="hover:bg-surface-container-low transition-colors group cursor-pointer" routerLink="/edit-expediente">
                  <td class="px-8 py-6 font-mono text-xs text-primary font-bold">{{exp.numero}}</td>
                  <td class="px-8 py-6 font-bold text-on-surface">{{exp.titular_id}}</td>
                  <td class="px-8 py-6 text-sm text-on-surface-variant">{{exp.organismo_id}}</td>
                  <td class="px-8 py-6 text-sm text-on-surface-variant">{{exp.fecha_creacion | date:'shortDate'}}</td>
                  <td class="px-8 py-6">
                    <div class="flex items-center gap-2">
                      <div class="w-1.5 h-1.5 rounded-full" [class.bg-blue-500]="exp.estado === 'Activo'" [class.bg-amber-500]="exp.estado === 'Pendiente'" [class.bg-emerald-500]="exp.estado === 'Resuelto'"></div>
                      <span class="text-[10px] font-black uppercase tracking-widest" [ngClass]="{
                        'text-primary': exp.estado === 'Activo',
                        'text-amber-600': exp.estado === 'Pendiente',
                        'text-emerald-600': exp.estado === 'Resuelto'
                      }">{{exp.estado}}</span>
                    </div>
                  </td>
                  <td class="px-8 py-6 text-right">
                    <button class="p-2 text-on-surface-variant/40 hover:text-primary transition-colors"><lucide-icon name="arrow-right" [size]="18"></lucide-icon></button>
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
export class ExpedientesComponent implements OnInit {
  tabs = ['Todos', 'Pendientes', 'En Trámite', 'Completados', 'Urgentes'];
  expedientes: Expediente[] = [];

  constructor(private firestoreService: FirestoreService) {}

  ngOnInit() {
    this.firestoreService.getExpedientes().subscribe((expedientes) => {
      this.expedientes = expedientes;
    });
  }
}
