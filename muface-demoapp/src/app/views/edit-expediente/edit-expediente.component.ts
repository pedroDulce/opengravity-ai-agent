import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-edit-expediente',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, RouterLink],
  template: `
    <div class="max-w-5xl mx-auto space-y-12">
      <header class="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <button 
            routerLink="/expedientes"
            class="inline-flex items-center gap-2 text-primary font-bold text-[10px] uppercase tracking-widest mb-4 hover:translate-x-[-4px] transition-transform"
          >
            <lucide-icon name="arrow-left" [size]="14"></lucide-icon>
            Volver a Expedientes
          </button>
          <h1 class="font-display text-4xl font-extrabold tracking-tight text-on-surface mb-2">Edición de Expediente</h1>
          <p class="text-on-surface-variant text-sm font-medium opacity-60 uppercase tracking-widest">Referencia: EXP-2024-042 • Ayuda Asistencial</p>
        </div>
        <div class="flex gap-4">
          <button class="px-8 py-4 rounded-full border border-outline-variant/20 text-on-surface-variant font-bold text-xs uppercase tracking-widest hover:bg-surface-container-low transition-all">
            Imprimir Resumen
          </button>
          <button class="px-8 py-4 rounded-full bg-primary text-white font-bold text-xs uppercase tracking-widest shadow-xl shadow-primary/20 hover:scale-105 transition-all">
            Guardar Cambios
          </button>
        </div>
      </header>

      <div class="grid grid-cols-1 lg:grid-cols-12 gap-10">
        <div class="lg:col-span-8 space-y-10">
          <section class="bg-surface-container-lowest rounded-[40px] p-10 shadow-sm border border-outline-variant/5">
            <h3 class="font-display font-bold text-lg text-primary mb-8 flex items-center gap-3">
              <lucide-icon name="user" [size]="22"></lucide-icon>
              Datos del Titular
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div class="space-y-2">
                <label class="text-[10px] font-black text-on-surface-variant/40 uppercase tracking-widest ml-1">Nombre Completo</label>
                <input type="text" value="Sánchez Ruiz, Pedro" class="w-full bg-surface-container-low border-none rounded-2xl p-4 font-display font-bold text-on-surface" />
              </div>
              <div class="space-y-2">
                <label class="text-[10px] font-black text-on-surface-variant/40 uppercase tracking-widest ml-1">DNI / NIE</label>
                <input type="text" value="87654321B" class="w-full bg-surface-container-low border-none rounded-2xl p-4 font-mono font-bold text-on-surface" />
              </div>
              <div class="space-y-2">
                <label class="text-[10px] font-black text-on-surface-variant/40 uppercase tracking-widest ml-1">Número de Afiliación</label>
                <input type="text" value="28/12345678/90" class="w-full bg-surface-container-low border-none rounded-2xl p-4 font-mono font-bold text-on-surface" />
              </div>
              <div class="space-y-2">
                <label class="text-[10px] font-black text-on-surface-variant/40 uppercase tracking-widest ml-1">Provincia de Residencia</label>
                <select class="w-full bg-surface-container-low border-none rounded-2xl p-4 font-display font-bold text-on-surface appearance-none">
                  <option>Madrid</option>
                  <option>Barcelona</option>
                  <option>Sevilla</option>
                  <option>Valencia</option>
                </select>
              </div>
            </div>
          </section>

          <section class="bg-surface-container-lowest rounded-[40px] p-10 shadow-sm border border-outline-variant/5">
            <h3 class="font-display font-bold text-lg text-primary mb-8 flex items-center gap-3">
              <lucide-icon name="file-text" [size]="22"></lucide-icon>
              Detalles del Trámite
            </h3>
            <div class="space-y-8">
              <div class="space-y-2">
                <label class="text-[10px] font-black text-on-surface-variant/40 uppercase tracking-widest ml-1">Descripción de la Solicitud</label>
                <textarea rows="4" class="w-full bg-surface-container-low border-none rounded-3xl p-6 font-sans text-on-surface">Solicitud de ayuda asistencial por gastos extraordinarios derivados de tratamiento médico especializado no cubierto íntegramente por el sistema público.</textarea>
              </div>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="p-5 bg-surface-container-low rounded-2xl border border-primary/10">
                  <p class="text-[10px] font-black text-primary uppercase tracking-widest mb-2">Cuantía Solicitada</p>
                  <p class="text-2xl font-display font-black text-on-surface">1.450,00 €</p>
                </div>
                <div class="p-5 bg-surface-container-low rounded-2xl border border-outline-variant/10">
                  <p class="text-[10px] font-black text-on-surface-variant/40 uppercase tracking-widest mb-2">Fecha de Registro</p>
                  <p class="text-xl font-display font-bold text-on-surface">10 Mar 2024</p>
                </div>
                <div class="p-5 bg-surface-container-low rounded-2xl border border-outline-variant/10">
                  <p class="text-[10px] font-black text-on-surface-variant/40 uppercase tracking-widest mb-2">Prioridad</p>
                  <p class="text-xl font-display font-bold text-amber-600">Alta</p>
                </div>
              </div>
            </div>
          </section>
        </div>

        <div class="lg:col-span-4 space-y-8">
          <div class="bg-surface-container-lowest rounded-[40px] p-8 shadow-sm border border-outline-variant/5">
            <h3 class="font-display font-bold text-on-surface mb-6">Documentación Adjunta</h3>
            <div class="space-y-3">
              @for (doc of documents; track doc.name) {
                <div class="flex items-center justify-between p-4 bg-surface-container-low rounded-2xl group hover:bg-primary/5 transition-all cursor-pointer">
                  <div class="flex items-center gap-3">
                    <lucide-icon name="file-text" [size]="18" class="text-primary"></lucide-icon>
                    <div>
                      <p class="text-xs font-bold text-on-surface">{{doc.name}}</p>
                      <p class="text-[10px] text-on-surface-variant opacity-60">{{doc.size}}</p>
                    </div>
                  </div>
                  <lucide-icon name="download" [size]="16" class="text-on-surface-variant/40 group-hover:text-primary"></lucide-icon>
                </div>
              }
              <button class="w-full mt-4 py-4 border-2 border-dashed border-outline-variant/30 rounded-2xl text-on-surface-variant/60 font-bold text-xs uppercase tracking-widest hover:border-primary hover:text-primary transition-all flex items-center justify-center gap-2">
                <lucide-icon name="plus" [size]="16"></lucide-icon>
                Añadir Documento
              </button>
            </div>
          </div>

          <div class="bg-surface-container-lowest rounded-[40px] p-8 shadow-sm border border-outline-variant/5">
            <h3 class="font-display font-bold text-on-surface mb-6">Historial de Estados</h3>
            <div class="space-y-6 relative before:absolute before:left-[19px] before:top-2 before:bottom-2 before:w-0.5 before:bg-surface-container-high">
              @for (h of history; track h.state) {
                <div class="flex gap-6 relative z-10">
                  <div class="w-10 h-10 rounded-full flex items-center justify-center border-4 border-surface-container-lowest" [ngClass]="{
                    'bg-primary': h.active,
                    'text-white': h.active,
                    'bg-surface-container-high': !h.active,
                    'text-on-surface-variant': !h.active
                  }">
                    <lucide-icon name="clock" [size]="16"></lucide-icon>
                  </div>
                  <div>
                    <p class="text-xs font-bold" [ngClass]="{
                      'text-primary': h.active,
                      'text-on-surface': !h.active
                    }">{{h.state}}</p>
                    <p class="text-[10px] text-on-surface-variant opacity-60">{{h.date}}</p>
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
export class EditExpedienteComponent {
  documents = [
    { name: 'DNI_Escaneado.pdf', size: '1.2 MB' },
    { name: 'Informe_Medico.pdf', size: '4.5 MB' },
    { name: 'Factura_Gasto.pdf', size: '0.8 MB' },
  ];

  history = [
    { state: 'En Trámite', date: 'Hoy, 10:45', active: true },
    { state: 'Validación Técnica', date: 'Ayer, 16:20' },
    { state: 'Registrado', date: '10 Mar, 09:00' },
  ];
}
