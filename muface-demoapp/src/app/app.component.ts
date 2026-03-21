import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { LucideAngularModule, Shield, LayoutDashboard, FileText, Building2, GraduationCap, Users, MapPin, Search, Bell, HelpCircle, Settings, LogOut, ChevronRight, Plus, Filter, ArrowRight, ArrowLeft, User, Download, Clock, History, PlusCircle, MoreVertical } from 'lucide-angular';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive, LucideAngularModule],
  template: `
    <div className="min-h-screen bg-surface-container-lowest font-sans text-on-surface selection:bg-primary/10 selection:text-primary">
      <!-- Top Nav -->
      <nav class="fixed top-0 w-full h-16 glass-header border-b border-outline-variant/5 flex items-center justify-between px-8 z-50">
        <div class="flex items-center gap-4">
          <span class="text-2xl font-display font-black tracking-tighter text-primary">MUFACE</span>
        </div>

        <div class="flex-1 max-w-xl mx-12 hidden md:block">
          <div class="relative group">
            <lucide-icon name="search" class="absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant/40 group-focus-within:text-primary transition-colors" [size]="18"></lucide-icon>
            <input 
              type="text" 
              placeholder="Buscar expedientes, titulares o trámites..." 
              class="w-full bg-surface-container-high border-none rounded-full py-2.5 pl-12 pr-4 focus:ring-2 focus:ring-primary/20 transition-all font-sans text-sm"
            />
          </div>
        </div>

        <div class="flex items-center gap-3">
          <button class="p-2.5 rounded-full hover:bg-surface-container-high transition-all text-on-surface-variant relative">
            <lucide-icon name="bell" [size]="20"></lucide-icon>
            <span class="absolute top-2 right-2 w-2 h-2 bg-on-tertiary-fixed-variant rounded-full border-2 border-white"></span>
          </button>
          <button class="p-2.5 rounded-full hover:bg-surface-container-high transition-all text-on-surface-variant">
            <lucide-icon name="help-circle" [size]="20"></lucide-icon>
          </button>
          <div class="h-10 w-10 rounded-full bg-primary-container flex items-center justify-center text-white font-bold text-xs cursor-pointer hover:scale-105 transition-transform">
            JD
          </div>
        </div>
      </nav>

      <!-- Sidebar -->
      <aside class="fixed left-0 top-0 h-screen w-64 bg-surface-container-low border-r border-outline-variant/10 flex flex-col z-40 pt-16">
        <div class="px-6 py-8">
          <div class="flex items-center gap-3 mb-2">
            <div class="w-10 h-10 rounded-xl bg-primary flex items-center justify-center text-white shadow-lg shadow-primary/20">
              <lucide-icon name="shield" [size]="20"></lucide-icon>
            </div>
            <div>
              <h2 class="font-display font-bold text-primary leading-tight">Gestión Pública</h2>
              <p class="text-[10px] text-on-surface-variant uppercase tracking-[0.15em] font-bold opacity-60">Panel de Control</p>
            </div>
          </div>
        </div>

        <nav class="flex-1 px-3 space-y-1">
          @for (item of navItems; track item.id) {
            <a
              [routerLink]="['/' + item.id]"
              routerLinkActive="bg-primary-container/10 text-primary font-bold"
              #rla="routerLinkActive"
              class="w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 group text-on-surface-variant hover:bg-surface-container-high"
              [ngClass]="{
                'bg-primary-container/10': rla.isActive,
                'text-primary': rla.isActive,
                'font-bold': rla.isActive
              }"
            >
              <lucide-icon [name]="item.icon" [size]="20" [class]="rla.isActive ? 'text-primary' : 'opacity-60 group-hover:opacity-100'"></lucide-icon>
              <span class="font-display text-sm">{{item.label}}</span>
              @if (rla.isActive) {
                <div class="ml-auto w-1.5 h-1.5 rounded-full bg-primary"></div>
              }
            </a>
          }
        </nav>

        <div class="p-4 mt-auto space-y-1 border-t border-outline-variant/10">
          <button class="w-full flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container-high rounded-xl transition-all text-sm font-display">
            <lucide-icon name="settings" [size]="18" class="opacity-60"></lucide-icon>
            <span>Ajustes</span>
          </button>
          <button class="w-full flex items-center gap-3 px-4 py-3 text-on-tertiary-fixed-variant hover:bg-tertiary-fixed/30 rounded-xl transition-all text-sm font-display">
            <lucide-icon name="log-out" [size]="18" class="opacity-60"></lucide-icon>
            <span>Cerrar Sesión</span>
          </button>
        </div>
      </aside>

      <!-- Main Content -->
      <main class="pl-64 pt-16 min-h-screen">
        <div class="p-10 max-w-[1600px] mx-auto">
          <router-outlet></router-outlet>
        </div>
      </main>
    </div>
  `,
  styles: [`
    .glass-header {
      background: rgba(255, 255, 255, 0.8);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
    }
  `]
})
export class AppComponent {
  navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: 'layout-dashboard' },
    { id: 'expedientes', label: 'Expedientes', icon: 'file-text' },
    { id: 'organismos', label: 'Organismos', icon: 'building-2' },
    { id: 'titulaciones', label: 'Titulaciones', icon: 'graduation-cap' },
    { id: 'titulares', label: 'Titulares', icon: 'users' },
    { id: 'ciudades', label: 'Ciudades', icon: 'map-pin' },
  ];
}
