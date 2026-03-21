import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-ciudades',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, RouterLink],
  template: `
    <div class="space-y-10">
      <header class="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div class="max-w-2xl">
          <nav class="flex items-center gap-2 text-[10px] font-bold text-on-surface-variant uppercase tracking-[0.2em] mb-4">
            <span>Territorio</span>
            <lucide-icon name="chevron-right" [size]="10"></lucide-icon>
            <span class="text-primary">Ciudades</span>
          </nav>
          <h1 class="font-display text-5xl font-extrabold text-on-surface tracking-tight leading-tight mb-2">Gestión de Ciudades</h1>
          <p class="text-on-surface-variant text-lg font-light leading-relaxed">Administración de delegaciones territoriales, centros de atención y zonificación de servicios.</p>
        </div>
        <button 
          routerLink="/edit-ciudad"
          class="bg-primary text-white px-8 py-4 rounded-full font-display font-bold text-sm tracking-widest uppercase flex items-center gap-3 shadow-xl shadow-primary/20 hover:scale-105 transition-transform"
        >
          <lucide-icon name="plus" [size]="18"></lucide-icon>
          Añadir Ciudad
        </button>
      </header>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        @for (city of cities; track city.code) {
          <div 
            class="bg-surface-container-lowest rounded-3xl overflow-hidden shadow-sm group cursor-pointer hover:-translate-y-2 transition-transform duration-300"
            routerLink="/edit-ciudad"
          >
            <div class="h-2 {{city.color}}"></div>
            <div class="p-8">
              <div class="flex justify-between items-start mb-6">
                <div>
                  <h3 class="font-display font-black text-2xl text-on-surface mb-1">{{city.name}}</h3>
                  <p class="text-[10px] font-bold text-on-surface-variant/40 uppercase tracking-widest">{{city.code}}</p>
                </div>
                <div class="p-3 rounded-2xl" [ngClass]="{
                  'bg-amber-50': city.alert,
                  'text-amber-600': city.alert,
                  'bg-primary/5': !city.alert,
                  'text-primary': !city.alert
                }">
                  <lucide-icon name="map-pin" [size]="24"></lucide-icon>
                </div>
              </div>
              
              <div class="grid grid-cols-2 gap-4 mb-8">
                <div class="p-4 bg-surface-container-low rounded-2xl">
                  <p class="text-[10px] font-bold text-on-surface-variant/40 uppercase tracking-widest mb-1">Centros</p>
                  <p class="text-xl font-display font-black text-on-surface">{{city.centers}}</p>
                </div>
                <div class="p-4 bg-surface-container-low rounded-2xl">
                  <p class="text-[10px] font-bold text-on-surface-variant/40 uppercase tracking-widest mb-1">Estado</p>
                  <p class="text-xs font-bold" [class.text-amber-600]="city.alert" [class.text-emerald-600]="!city.alert">{{city.status}}</p>
                </div>
              </div>

              <div class="flex items-center justify-between pt-6 border-t border-outline-variant/10">
                <div class="flex -space-x-2">
                  @for (i of [1,2,3]; track i) {
                    <div class="w-8 h-8 rounded-full border-2 border-surface-container-lowest bg-surface-container-high flex items-center justify-center text-[10px] font-bold text-on-surface-variant">
                      {{i}}
                    </div>
                  }
                </div>
                <button class="text-primary font-bold text-xs uppercase tracking-widest flex items-center gap-2 group-hover:gap-3 transition-all">
                  Gestionar
                  <lucide-icon name="arrow-right" [size]="14"></lucide-icon>
                </button>
              </div>
            </div>
          </div>
        }
      </div>
    </div>
  `
})
export class CiudadesComponent {
  cities = [
    { name: 'Madrid', code: 'MAD-01', centers: 12, status: 'Operativo', color: 'bg-primary' },
    { name: 'Barcelona', code: 'BCN-02', centers: 8, status: 'Operativo', color: 'bg-primary' },
    { name: 'Valencia', code: 'VLC-03', centers: 5, status: 'Mantenimiento', color: 'bg-amber-500', alert: true },
    { name: 'Sevilla', code: 'SVQ-04', centers: 6, status: 'Operativo', color: 'bg-primary' },
    { name: 'Zaragoza', code: 'ZAZ-05', centers: 4, status: 'Operativo', color: 'bg-primary' },
    { name: 'Málaga', code: 'AGP-06', centers: 3, status: 'Operativo', color: 'bg-primary' },
  ];
}
