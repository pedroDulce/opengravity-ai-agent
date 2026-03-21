import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-new-titulacion',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, RouterLink],
  template: `
    <div class="max-w-3xl mx-auto space-y-10">
      <header>
        <button routerLink="/titulaciones" class="text-primary font-bold text-xs uppercase tracking-widest mb-4 flex items-center gap-2">
          <lucide-icon name="arrow-left" [size]="14"></lucide-icon>
          Volver
        </button>
        <h1 class="font-display text-4xl font-extrabold text-on-surface">Nueva Titulación</h1>
      </header>
      <div class="bg-surface-container-lowest p-10 rounded-[40px] shadow-sm border border-outline-variant/5">
        <div class="space-y-6">
          <div class="space-y-2">
            <label class="text-[10px] font-black text-on-surface-variant/40 uppercase tracking-widest">Denominación del Título</label>
            <input type="text" class="w-full bg-surface-container-low border-none rounded-2xl p-4 font-bold" placeholder="Ej: Grado en Medicina" />
          </div>
          <div class="grid grid-cols-2 gap-6">
            <div class="space-y-2">
              <label class="text-[10px] font-black text-on-surface-variant/40 uppercase tracking-widest">Código BOE</label>
              <input type="text" class="w-full bg-surface-container-low border-none rounded-2xl p-4 font-mono font-bold" placeholder="BOE-A-XXXX" />
            </div>
            <div class="space-y-2">
              <label class="text-[10px] font-black text-on-surface-variant/40 uppercase tracking-widest">Nivel MECES</label>
              <select class="w-full bg-surface-container-low border-none rounded-2xl p-4 font-bold">
                <option>Nivel 1 (Técnico)</option>
                <option>Nivel 2 (Grado)</option>
                <option>Nivel 3 (Máster)</option>
                <option>Nivel 4 (Doctorado)</option>
              </select>
            </div>
          </div>
          <button class="w-full bg-primary text-white py-4 rounded-2xl font-bold uppercase tracking-widest shadow-lg shadow-primary/20">Crear Titulación</button>
        </div>
      </div>
    </div>
  `
})
export class NewTitulacionComponent {}
