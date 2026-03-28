import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule, Shield, MapPin, PlusCircle, Download, FileText, History, ChevronRight, Plus, Search, Filter, ArrowRight, Users, Building2, Clock } from 'lucide-angular';
import { RouterLink } from '@angular/router';
import { FirestoreService } from '../../services/firestore.service';
import { Expediente, Actividad } from '../../models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, RouterLink],
  template: `
    <div class="space-y-10">
      <header class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 class="font-display text-4xl font-extrabold text-on-surface tracking-tight mb-2">Resumen Operativo</h1>
          <p class="text-on-surface-variant text-lg max-w-2xl font-light">Bienvenido al panel central de MUFACE. Monitorice la distribución de expedientes y gestione las solicitudes activas en tiempo real.</p>
        </div>
        <button (click)="seedTestData()" class="bg-secondary text-on-secondary rounded-full px-6 py-3 font-bold hover:brightness-105 transition">Cargar datos de prueba</button>
      </header>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div *ngFor="let kpi of kpis; trackBy: trackByLabel; let i = index" class="bg-surface-container-lowest p-6 rounded-2xl shadow-sm border-l-4 border-primary">
          <div class="flex justify-between items-start mb-4">
            <div class="p-2.5 bg-surface-container-low rounded-xl text-primary">
              <lucide-icon [name]="kpi.icon" [size]="24"></lucide-icon>
            </div>
            <span *ngIf="kpi.trend" class="text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full">{{ kpi.trend }}</span>
          </div>
          <p class="text-xs font-bold text-on-surface-variant opacity-60 uppercase tracking-widest mb-1">{{ kpi.label }}</p>
          <p class="text-3xl font-display font-black text-on-surface">{{ kpi.value }}</p>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div class="lg:col-span-8 bg-surface-container-lowest rounded-3xl overflow-hidden shadow-sm flex flex-col">
          <div class="p-6 bg-surface-container-high flex justify-between items-center">
            <h3 class="font-display font-bold text-lg text-primary flex items-center gap-2">
              <lucide-icon [img]="MapPin" [size]="20"></lucide-icon>
              Distribución de Expedientes (España)
            </h3>
            <div class="flex bg-surface-container-low p-1 rounded-xl gap-1">
              <button class="text-xs font-bold px-4 py-1.5 bg-white rounded-lg shadow-sm">Mensual</button>
              <button class="text-xs font-bold px-4 py-1.5 text-on-surface-variant">Anual</button>
            </div>
          </div>
          <div class="relative min-h-[420px] bg-surface-container-low/30 flex items-center justify-center p-6">
            <img
              src="https://upload.wikimedia.org/wikipedia/commons/9/99/Spain_location_map.svg"
              alt="Mapa de España"
              (error)="useMapFallback = true"
              [class.opacity-100]="!useMapFallback"
              [class.opacity-70]="useMapFallback"
              class="absolute inset-0 w-full h-full object-contain"
            />
            <div *ngIf="useMapFallback" class="absolute inset-0 bg-gradient-to-br from-blue-50 via-white to-blue-100 flex flex-col items-center justify-center text-blue-800 text-xl font-bold opacity-90">
              <span>Mapa no disponible</span>
              <span>Mostrando fallback</span>
            </div>
            <div class="absolute inset-0">
              <div *ngFor="let point of mapData; trackBy: trackByCity" class="absolute transform -translate-x-1/2 -translate-y-1/2 bg-white/90 text-gray-900 rounded-full p-1.5 text-xs font-bold shadow-lg" [style.top]="point.top" [style.left]="point.left">
                {{point.city}} ({{point.count}})
              </div>
            </div>
            <div class="relative z-10 w-full">
              <div class="text-center text-on-surface-variant mb-4">
                <p class="text-sm font-bold">Expedientes por ciudad</p>
              </div>
            </div>
          </div>
          <div class="p-6 bg-surface-container-lowest flex flex-col gap-4">
            <h4 class="font-display text-lg font-bold text-on-surface">Expedientes por Estado</h4>
            <div class="space-y-3">
              <div *ngFor="let item of chartData; trackBy: trackByLabel">
                <div class="flex justify-between text-sm uppercase tracking-wider font-semibold text-on-surface-variant mb-1">
                  <span>{{item.label}}</span>
                  <span>{{item.value}}</span>
                </div>
                <div class="h-2 rounded-full bg-surface-container-low overflow-hidden">
                  <div class="h-full bg-primary" [style.width.%]="(expedientes.length ? (item.value / expedientes.length * 100) : 0)"></div>
                </div>
              </div>
            </div>
            <p class="text-xs text-on-surface-variant">Total expedientes: {{expedientes.length}}</p>
          </div>

        <div class="lg:col-span-4 space-y-6">
          <div class="bg-primary p-8 rounded-3xl text-white shadow-xl shadow-primary/20 relative overflow-hidden">
            <div class="absolute -right-8 -bottom-8 opacity-10 text-white">
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
              <div *ngFor="let act of activity | slice:0:3; trackBy: trackById">
                <div class="flex gap-4">
                  <div class="w-10 h-10 rounded-full bg-surface-container-low flex items-center justify-center text-on-surface-variant flex-shrink-0">
                    <lucide-icon [img]="History" [size]="18"></lucide-icon>
                  </div>
                  <div class="flex-1">
                    <p class="text-sm font-bold text-on-surface">{{ act.descripcion }}</p>
                    <p class="text-xs text-on-surface-variant font-medium opacity-60">{{ act.fecha | date:'short' }}</p>
                  </div>
                </div>
              </div>
            </div>
            <button class="w-full mt-8 text-primary font-bold text-xs uppercase tracking-widest hover:underline">Ver todo el historial</button>
          </div>
        </div>
      </div>
    </div>
  `
})
export class DashboardComponent implements OnInit {
  kpis = [
    { label: 'Total Expedientes', value: '0', trend: '+12.5%', icon: FileText, color: 'primary' },
    { label: 'Organismos Activos', value: '0', icon: Building2, color: 'primary' },
    { label: 'Titulares Registrados', value: '0', icon: Users, color: 'primary' },
    { label: 'Pendientes de Firma', value: '0', icon: Clock, color: 'on-tertiary-fixed-variant' },
  ];

  activity: Actividad[] = [];
  expedientes: Expediente[] = [];
  titulares: any[] = [];
  ciudades: any[] = [];  useMapFallback = false;  mapData = [
    { city: 'Madrid', count: 0, top: '45%', left: '55%' },
    { city: 'Barcelona', count: 0, top: '30%', left: '80%' },
    { city: 'Sevilla', count: 0, top: '70%', left: '40%' },
  ];
  chartData = [{ label: 'Activo', value: 0 }, { label: 'Pendiente', value: 0 }, { label: 'Resuelto', value: 0 }];
  activeRatio = 0;

  constructor(private firestoreService: FirestoreService) {}

  public Shield = Shield;
  public MapPin = MapPin;
  public PlusCircle = PlusCircle;
  public Download = Download;
  public FileText = FileText;
  public History = History;

  ngOnInit() {
    this.loadData();
  }

  loadData() {
    this.firestoreService.getExpedientes().subscribe((expedientes) => {
      this.expedientes = expedientes;
      this.kpis[0].value = expedientes.length.toString();
      const estados = { Activo: 0, Pendiente: 0, Resuelto: 0 };
      expedientes.forEach((e) => { estados[e.estado] = (estados[e.estado] ?? 0) + 1; });
      this.chartData = [
        { label: 'Activo', value: estados.Activo },
        { label: 'Pendiente', value: estados.Pendiente },
        { label: 'Resuelto', value: estados.Resuelto },
      ];
      this.updateMapData();
    });

    this.firestoreService.getTitulares().subscribe((titulares) => {
      this.titulares = titulares;
      this.kpis[2].value = titulares.length.toString();
      const activos = titulares.filter(t => t.status === 'Activo').length;
      this.activeRatio = titulares.length ? Math.round((activos / titulares.length) * 100) : 0;
    });

    this.firestoreService.getCiudades().subscribe((ciudades) => {
      this.ciudades = ciudades;
      this.updateMapData();
    });

    this.firestoreService.getOrganismos().subscribe((organismos) => {
      this.kpis[1].value = organismos.length.toString();
    });

    this.firestoreService.getActividad().subscribe((actividad) => {
      this.activity = actividad.sort((a, b) => 
        new Date(b.fecha).getTime() - new Date(a.fecha).getTime()
      );
    });
  }

  private updateMapData() {
    const cityCount = this.expedientes.reduce((acc, e) => {
      const cityObj = this.ciudades.find(c => c.id === e.ciudad_id || c.nombre === e.ciudad_id);
      const cityName = cityObj ? cityObj.nombre : (e.ciudad_id ?? 'Desconocido');
      acc[cityName] = (acc[cityName] ?? 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const template: Record<string, { top: string; left: string }> = {
      Madrid: { top: '45%', left: '55%' },
      Barcelona: { top: '30%', left: '78%' },
      Sevilla: { top: '70%', left: '38%' },
      Valencia: { top: '62%', left: '69%' },
      Zaragoza: { top: '30%', left: '58%' },
      Desconocido: { top: '50%', left: '50%' },
    };

    this.mapData = Object.entries(cityCount).map(([city, count]) => ({
      city,
      count,
      top: template[city]?.top ?? '50%',
      left: template[city]?.left ?? '50%',
    }));
  }

  async seedTestData() {
    try {
      await this.firestoreService.seedTestData();
      this.loadData();
      console.log('Datos de prueba sembrados correctamente');
    } catch (error) {
      console.error('Error al sembrar datos de prueba', error);
    }
  }

  trackByLabel(index: number, item: any): string {
    return item.label;
  }

  trackByCity(index: number, item: any): string {
    return item.city;
  }

  trackById(index: number, item: any): string {
    return item.id;
  }
}
