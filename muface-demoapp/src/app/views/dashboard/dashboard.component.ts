import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, RouterLink],
  template: `
    <div class="space-y-10">
      <header>
        <h1 class="font-display text-4xl font-extrabold text-on-surface tracking-tight mb-2">Resumen Operativo</h1>
        <p class="text-on-surface-variant text-lg max-w-2xl font-light">Bienvenido al panel central de MUFACE. Monitorice la distribución de expedientes y gestione las solicitudes activas en tiempo real.</p>
      </header>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        @for (kpi of kpis; track kpi.label; let i = $index) {
          <div 
            class="bg-surface-container-lowest p-6 rounded-2xl shadow-sm border-l-4 border-primary"
          >
            <div class="flex justify-between items-start mb-4">
              <div class="p-2.5 bg-surface-container-low rounded-xl text-primary">
                <lucide-icon [name]="kpi.icon" [size]="24"></lucide-icon>
              </div>
              @if (kpi.trend) {
                <span class="text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full">{{kpi.trend}}</span>
              }
            </div>
            <p class="text-xs font-bold text-on-surface-variant/60 uppercase tracking-widest mb-1">{{kpi.label}}</p>
            <p class="text-3xl font-display font-black text-on-surface">{{kpi.value}}</p>
          </div>
        }
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div class="lg:col-span-8 bg-surface-container-lowest rounded-3xl overflow-hidden shadow-sm flex flex-col">
          <div class="p-6 bg-surface-container-high flex justify-between items-center">
            <h3 class="font-display font-bold text-lg text-primary flex items-center gap-2">
              <lucide-icon name="map-pin" [size]="20"></lucide-icon>
              Distribución de Expedientes (España)
            </h3>
            <div class="flex bg-surface-container-low p-1 rounded-xl">
              <button class="text-xs font-bold px-4 py-1.5 bg-white rounded-lg shadow-sm">Mensual</button>
              <button class="text-xs font-bold px-4 py-1.5 text-on-surface-variant">Anual</button>
            </div>
          </div>
          <div class="relative flex-1 min-h-[400px] bg-surface-container-low/30 flex items-center justify-center p-12">
            <img 
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuAh_ucLzQa_5MYwc9TVWgADRrdcjVNSYvFVpe7J2jpP7HTOHDPQreOWnqs9mgwDOLWBC9YO-7E36tq8d21hopqPusUMIofQwKSU_AREy9D9rld9poFgIslZnO_BcA0eMk7BZQRoHvXw9V-gvq9iVAXXqauI3-c35vpf7Qs-rYnGt_sQivWQc1f-4mEmeuzJkzbIL5ssWrcrC-hpPmRq72fvzYhCWSf6C8z0K8-VgFZQGiHNcck9Lbl2TyUlazTR3Vxmy7eiQAN5BEQ" 
              alt="Mapa de España" 
              class="absolute inset-0 w-full h-full object-contain opacity-10 grayscale"
              referrerPolicy="no-referrer"
            />
            <div class="relative z-10 grid grid-cols-3 gap-12 text-center">
              @for (d of mapData; track d.city) {
                <div class="flex flex-col items-center group cursor-pointer">
                  <div class="{{d.size}} rounded-full bg-primary/10 border-2 border-primary/40 group-hover:bg-primary/20 group-hover:scale-110 transition-all duration-500 mb-3 flex items-center justify-center">
                    <div class="w-2 h-2 rounded-full bg-primary animate-ping"></div>
                  </div>
                  <p class="text-xs font-bold text-primary uppercase tracking-widest">{{d.city}}</p>
                  <p class="text-xl font-display font-black">{{d.val}}</p>
                </div>
              }
            </div>
          </div>
        </div>

        <div class="lg:col-span-4 space-y-6">
          <div class="bg-primary p-8 rounded-3xl text-white shadow-xl shadow-primary/20 relative overflow-hidden group">
            <div class="absolute -right-8 -bottom-8 opacity-10 group-hover:scale-110 transition-transform duration-700">
              <lucide-icon name="shield" [size]="160"></lucide-icon>
            </div>
            <h3 class="font-display font-bold text-xl mb-6 relative z-10">Acciones Rápidas</h3>
            <div class="space-y-3 relative z-10">
              <button class="w-full bg-white/10 hover:bg-white/20 transition-all p-4 rounded-2xl flex items-center gap-4 text-white font-bold text-sm">
                <lucide-icon name="plus-circle" [size]="20"></lucide-icon>
                Alta Nuevo Titular
              </button>
              <button class="w-full bg-white/10 hover:bg-white/20 transition-all p-4 rounded-2xl flex items-center gap-4 text-white font-bold text-sm">
                <lucide-icon name="download" [size]="20"></lucide-icon>
                Carga por Lotes
              </button>
              <button class="w-full bg-white/10 hover:bg-white/20 transition-all p-4 rounded-2xl flex items-center gap-4 text-white font-bold text-sm">
                <lucide-icon name="file-text" [size]="20"></lucide-icon>
                Informes de Ciudad
              </button>
            </div>
          </div>

          <div class="bg-surface-container-lowest p-8 rounded-3xl shadow-sm">
            <h3 class="font-display font-bold text-lg text-on-surface mb-6">Actividad Reciente</h3>
            <div class="space-y-6">
              @for (act of activity; track act.title) {
                <div class="flex gap-4">
                  <div class="relative">
                    <div class="w-10 h-10 rounded-full bg-surface-container-low flex items-center justify-center text-on-surface-variant">
                      <lucide-icon name="history" [size]="18"></lucide-icon>
                    </div>
                    @if (act.status) {
                      <div class="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full border-2 border-white" [ngClass]="act.status"></div>
                    }
                  </div>
                  <div>
                    <p class="text-sm font-bold text-on-surface">{{act.title}}</p>
                    <p class="text-xs text-on-surface-variant font-medium opacity-60">{{act.time}}</p>
                  </div>
                </div>
              }
            </div>
            <button class="w-full mt-8 text-primary font-bold text-xs uppercase tracking-widest hover:underline">Ver todo el historial</button>
          </div>
        </div>
      </div>
    </div>
  `
})
export class DashboardComponent {
  kpis = [
    { label: 'Total Expedientes', value: '14.285', trend: '+12.5%', icon: 'file-text', color: 'primary' },
    { label: 'Organismos Activos', value: '342', icon: 'building-2', color: 'primary' },
    { label: 'Titulares Registrados', value: '892k', icon: 'users', color: 'primary' },
    { label: 'Pendientes de Firma', value: '128', icon: 'clock', color: 'on-tertiary-fixed-variant' },
  ];

  mapData = [
    { city: 'Madrid', val: '4.2k', size: 'w-16 h-16' },
    { city: 'Barcelona', val: '2.1k', size: 'w-12 h-12' },
    { city: 'Sevilla', val: '1.5k', size: 'w-10 h-10' },
  ];

  activity = [
    { title: 'Expediente #9021 Modificado', time: 'Hace 12 minutos', icon: 'file-text', status: 'bg-emerald-500' },
    { title: 'Cierre Mensual Completado', time: 'Hace 2 horas • Automático', icon: 'clock', status: '' },
    { title: 'Incidencia en Organismo 452', time: 'Hace 5 horas • Atención', icon: 'alert-circle', status: 'bg-amber-500' },
  ];
}
