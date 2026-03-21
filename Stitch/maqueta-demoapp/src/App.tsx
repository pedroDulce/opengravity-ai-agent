/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Icons } from './components/Icons';

// --- Types ---

type View = 'dashboard' | 'expedientes' | 'organismos' | 'titulaciones' | 'titulares' | 'ciudades' | 'edit-expediente' | 'new-titulacion' | 'new-organismo' | 'edit-ciudad';

interface NavItem {
  id: View;
  label: string;
  icon: keyof typeof Icons;
}

// --- Constants ---

const NAV_ITEMS: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: 'Dashboard' },
  { id: 'expedientes', label: 'Expedientes', icon: 'Expedientes' },
  { id: 'organismos', label: 'Organismos', icon: 'Organismos' },
  { id: 'titulaciones', label: 'Titulaciones', icon: 'Titulaciones' },
  { id: 'titulares', label: 'Titulares', icon: 'Titulares' },
  { id: 'ciudades', label: 'Ciudades', icon: 'Ciudades' },
];

// --- Components ---

const Sidebar = ({ currentView, onViewChange }: { currentView: View, onViewChange: (v: View) => void }) => (
  <aside className="fixed left-0 top-0 h-screen w-64 bg-surface-container-low border-r border-outline-variant/10 flex flex-col z-40 pt-16">
    <div className="px-6 py-8">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center text-white shadow-lg shadow-primary/20">
          <Icons.Shield size={20} />
        </div>
        <div>
          <h2 className="font-display font-bold text-primary leading-tight">Gestión Pública</h2>
          <p className="text-[10px] text-on-surface-variant uppercase tracking-[0.15em] font-bold opacity-60">Panel de Control</p>
        </div>
      </div>
    </div>

    <nav className="flex-1 px-3 space-y-1">
      {NAV_ITEMS.map((item) => {
        const Icon = Icons[item.icon];
        const isActive = currentView === item.id || (item.id === 'expedientes' && currentView === 'edit-expediente') || (item.id === 'titulaciones' && currentView === 'new-titulacion') || (item.id === 'organismos' && currentView === 'new-organismo') || (item.id === 'ciudades' && currentView === 'edit-ciudad');
        return (
          <button
            key={item.id}
            onClick={() => onViewChange(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 group ${
              isActive 
                ? 'bg-primary-container/10 text-primary font-bold' 
                : 'text-on-surface-variant hover:bg-surface-container-high'
            }`}
          >
            <Icon size={20} className={isActive ? 'text-primary' : 'opacity-60 group-hover:opacity-100'} />
            <span className="font-display text-sm">{item.label}</span>
            {isActive && (
              <motion.div 
                layoutId="active-nav"
                className="ml-auto w-1.5 h-1.5 rounded-full bg-primary"
              />
            )}
          </button>
        );
      })}
    </nav>

    <div className="p-4 mt-auto space-y-1 border-t border-outline-variant/10">
      <button className="w-full flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container-high rounded-xl transition-all text-sm font-display">
        <Icons.Settings size={18} className="opacity-60" />
        <span>Ajustes</span>
      </button>
      <button className="w-full flex items-center gap-3 px-4 py-3 text-on-tertiary-fixed-variant hover:bg-tertiary-fixed/30 rounded-xl transition-all text-sm font-display">
        <Icons.LogOut size={18} className="opacity-60" />
        <span>Cerrar Sesión</span>
      </button>
    </div>
  </aside>
);

const TopNav = () => (
  <nav className="fixed top-0 w-full h-16 glass-header border-b border-outline-variant/5 flex items-center justify-between px-8 z-50">
    <div className="flex items-center gap-4">
      <span className="text-2xl font-display font-black tracking-tighter text-primary">MUFACE</span>
    </div>

    <div className="flex-1 max-w-xl mx-12 hidden md:block">
      <div className="relative group">
        <Icons.Search className="absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant/40 group-focus-within:text-primary transition-colors" size={18} />
        <input 
          type="text" 
          placeholder="Buscar expedientes, titulares o trámites..." 
          className="w-full bg-surface-container-high border-none rounded-full py-2.5 pl-12 pr-4 focus:ring-2 focus:ring-primary/20 transition-all font-sans text-sm"
        />
      </div>
    </div>

    <div className="flex items-center gap-3">
      <button className="p-2.5 rounded-full hover:bg-surface-container-high transition-all text-on-surface-variant relative">
        <Icons.Bell size={20} />
        <span className="absolute top-2 right-2 w-2 h-2 bg-on-tertiary-fixed-variant rounded-full border-2 border-white"></span>
      </button>
      <button className="p-2.5 rounded-full hover:bg-surface-container-high transition-all text-on-surface-variant">
        <Icons.Help size={20} />
      </button>
      <div className="h-10 w-10 rounded-full bg-primary-container flex items-center justify-center text-white font-bold text-xs cursor-pointer hover:scale-105 transition-transform">
        JD
      </div>
    </div>
  </nav>
);

// --- Views ---

const DashboardView = ({ onViewChange }: { onViewChange: (v: View) => void }) => (
  <div className="space-y-10">
    <header>
      <h1 className="font-display text-4xl font-extrabold text-on-surface tracking-tight mb-2">Resumen Operativo</h1>
      <p className="text-on-surface-variant text-lg max-w-2xl font-light">Bienvenido al panel central de MUFACE. Monitorice la distribución de expedientes y gestione las solicitudes activas en tiempo real.</p>
    </header>

    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {[
        { label: 'Total Expedientes', value: '14.285', trend: '+12.5%', icon: 'Expedientes', color: 'primary' },
        { label: 'Organismos Activos', value: '342', icon: 'Organismos', color: 'primary' },
        { label: 'Titulares Registrados', value: '892k', icon: 'Titulares', color: 'primary' },
        { label: 'Pendientes de Firma', value: '128', icon: 'Clock', color: 'on-tertiary-fixed-variant' },
      ].map((kpi, i) => {
        const Icon = Icons[kpi.icon as keyof typeof Icons];
        return (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            key={i} 
            className="bg-surface-container-lowest p-6 rounded-2xl shadow-sm border-l-4 border-primary"
          >
            <div className="flex justify-between items-start mb-4">
              <div className="p-2.5 bg-surface-container-low rounded-xl text-primary">
                <Icon size={24} />
              </div>
              {kpi.trend && <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full">{kpi.trend}</span>}
            </div>
            <p className="text-xs font-bold text-on-surface-variant/60 uppercase tracking-widest mb-1">{kpi.label}</p>
            <p className="text-3xl font-display font-black text-on-surface">{kpi.value}</p>
          </motion.div>
        );
      })}
    </div>

    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
      <div className="lg:col-span-8 bg-surface-container-lowest rounded-3xl overflow-hidden shadow-sm flex flex-col">
        <div className="p-6 bg-surface-container-high flex justify-between items-center">
          <h3 className="font-display font-bold text-lg text-primary flex items-center gap-2">
            <Icons.Ciudades size={20} />
            Distribución de Expedientes (España)
          </h3>
          <div className="flex bg-surface-container-low p-1 rounded-xl">
            <button className="text-xs font-bold px-4 py-1.5 bg-white rounded-lg shadow-sm">Mensual</button>
            <button className="text-xs font-bold px-4 py-1.5 text-on-surface-variant">Anual</button>
          </div>
        </div>
        <div className="relative flex-1 min-h-[400px] bg-surface-container-low/30 flex items-center justify-center p-12">
          <img 
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuAh_ucLzQa_5MYwc9TVWgADRrdcjVNSYvFVpe7J2jpP7HTOHDPQreOWnqs9mgwDOLWBC9YO-7E36tq8d21hopqPusUMIofQwKSU_AREy9D9rld9poFgIslZnO_BcA0eMk7BZQRoHvXw9V-gvq9iVAXXqauI3-c35vpf7Qs-rYnGt_sQivWQc1f-4mEmeuzJkzbIL5ssWrcrC-hpPmRq72fvzYhCWSf6C8z0K8-VgFZQGiHNcck9Lbl2TyUlazTR3Vxmy7eiQAN5BEQ" 
            alt="Mapa de España" 
            className="absolute inset-0 w-full h-full object-contain opacity-10 grayscale"
            referrerPolicy="no-referrer"
          />
          <div className="relative z-10 grid grid-cols-3 gap-12 text-center">
            {[
              { city: 'Madrid', val: '4.2k', size: 'w-16 h-16' },
              { city: 'Barcelona', val: '2.1k', size: 'w-12 h-12' },
              { city: 'Sevilla', val: '1.5k', size: 'w-10 h-10' },
            ].map((d, i) => (
              <div key={i} className="flex flex-col items-center group cursor-pointer">
                <div className={`${d.size} rounded-full bg-primary/10 border-2 border-primary/40 group-hover:bg-primary/20 group-hover:scale-110 transition-all duration-500 mb-3 flex items-center justify-center`}>
                  <div className="w-2 h-2 rounded-full bg-primary animate-ping"></div>
                </div>
                <p className="text-xs font-bold text-primary uppercase tracking-widest">{d.city}</p>
                <p className="text-xl font-display font-black">{d.val}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="lg:col-span-4 space-y-6">
        <div className="bg-primary p-8 rounded-3xl text-white shadow-xl shadow-primary/20 relative overflow-hidden group">
          <div className="absolute -right-8 -bottom-8 opacity-10 group-hover:scale-110 transition-transform duration-700">
            <Icons.Shield size={160} />
          </div>
          <h3 className="font-display font-bold text-xl mb-6 relative z-10">Acciones Rápidas</h3>
          <div className="space-y-3 relative z-10">
            <button className="w-full bg-white/10 hover:bg-white/20 transition-all p-4 rounded-2xl flex items-center gap-4 text-white font-bold text-sm">
              <Icons.PlusCircle size={20} />
              Alta Nuevo Titular
            </button>
            <button className="w-full bg-white/10 hover:bg-white/20 transition-all p-4 rounded-2xl flex items-center gap-4 text-white font-bold text-sm">
              <Icons.Download size={20} />
              Carga por Lotes
            </button>
            <button className="w-full bg-white/10 hover:bg-white/20 transition-all p-4 rounded-2xl flex items-center gap-4 text-white font-bold text-sm">
              <Icons.FileText size={20} />
              Informes de Ciudad
            </button>
          </div>
        </div>

        <div className="bg-surface-container-lowest p-8 rounded-3xl shadow-sm">
          <h3 className="font-display font-bold text-lg text-on-surface mb-6">Actividad Reciente</h3>
          <div className="space-y-6">
            {[
              { title: 'Expediente #9021 Modificado', time: 'Hace 12 minutos', icon: 'FileText', status: 'bg-emerald-500' },
              { title: 'Cierre Mensual Completado', time: 'Hace 2 horas • Automático', icon: 'Clock', status: '' },
              { title: 'Incidencia en Organismo 452', time: 'Hace 5 horas • Atención', icon: 'Alert', status: 'bg-amber-500' },
            ].map((act, i) => (
              <div key={i} className="flex gap-4">
                <div className="relative">
                  <div className="w-10 h-10 rounded-full bg-surface-container-low flex items-center justify-center text-on-surface-variant">
                    <Icons.History size={18} />
                  </div>
                  {act.status && <div className={`absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full border-2 border-white ${act.status}`}></div>}
                </div>
                <div>
                  <p className="text-sm font-bold text-on-surface">{act.title}</p>
                  <p className="text-xs text-on-surface-variant font-medium opacity-60">{act.time}</p>
                </div>
              </div>
            ))}
          </div>
          <button className="w-full mt-8 text-primary font-bold text-xs uppercase tracking-widest hover:underline">Ver todo el historial</button>
        </div>
      </div>
    </div>
  </div>
);

const OrganismosView = ({ onViewChange }: { onViewChange: (v: View) => void }) => (
  <div className="space-y-10">
    <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
      <div className="max-w-2xl">
        <nav className="flex items-center gap-2 text-[10px] font-bold text-on-surface-variant uppercase tracking-[0.2em] mb-4">
          <span>Admin</span>
          <Icons.ChevronRight size={10} />
          <span className="text-primary">Organismos</span>
        </nav>
        <h1 className="font-display text-5xl font-extrabold text-on-surface tracking-tight leading-tight mb-2">Organismos Públicos</h1>
        <p className="text-on-surface-variant text-lg font-light leading-relaxed">Gestión y supervisión de las entidades colaboradoras y delegaciones territoriales vinculadas a MUFACE.</p>
      </div>
      <button 
        onClick={() => onViewChange('new-organismo')}
        className="bg-primary text-white px-8 py-4 rounded-full font-display font-bold text-sm tracking-widest uppercase flex items-center gap-3 shadow-xl shadow-primary/20 hover:scale-105 transition-transform"
      >
        <Icons.Plus size={18} />
        Nuevo Organismo
      </button>
    </header>

    <div className="bg-surface-container-lowest rounded-3xl overflow-hidden shadow-sm">
      <div className="bg-surface-container-high px-8 py-5 flex justify-between items-center">
        <div className="flex gap-4">
          <button className="text-xs font-bold px-4 py-2 bg-white rounded-lg shadow-sm text-primary">Todos</button>
          <button className="text-xs font-bold px-4 py-2 text-on-surface-variant hover:bg-white/50 rounded-lg transition-all">Delegaciones</button>
          <button className="text-xs font-bold px-4 py-2 text-on-surface-variant hover:bg-white/50 rounded-lg transition-all">Sedes</button>
        </div>
        <div className="relative w-64">
          <Icons.Search className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/40" size={14} />
          <input type="text" placeholder="Buscar organismo..." className="w-full bg-white border-none rounded-lg py-2 pl-9 pr-4 text-xs font-sans focus:ring-1 focus:ring-primary/20" />
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-container-lowest border-b border-outline-variant/10">
              <th className="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">ID / DIR3</th>
              <th className="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Organismo</th>
              <th className="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Localización</th>
              <th className="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Estado</th>
              <th className="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest text-right">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-container-high">
            {[
              { id: 'ORG-28001', name: 'Sede Central MUFACE', loc: 'Madrid', status: 'Activo', type: 'Sede' },
              { id: 'ORG-08002', name: 'Delegación Provincial Barcelona', loc: 'Barcelona', status: 'Activo', type: 'Delegación' },
              { id: 'ORG-41003', name: 'Oficina de Atención Sevilla', loc: 'Sevilla', status: 'Mantenimiento', type: 'Oficina', alert: true },
              { id: 'ORG-46004', name: 'Delegación Provincial Valencia', loc: 'Valencia', status: 'Activo', type: 'Delegación' },
            ].map((org, i) => (
              <tr key={i} className="hover:bg-surface-container-low transition-colors">
                <td className="px-8 py-6 font-mono text-xs text-primary font-bold">{org.id}</td>
                <td className="px-8 py-6">
                  <p className="font-bold text-on-surface">{org.name}</p>
                  <p className="text-[10px] text-on-surface-variant font-medium opacity-60 uppercase tracking-widest">{org.type}</p>
                </td>
                <td className="px-8 py-6 text-sm text-on-surface-variant">{org.loc}</td>
                <td className="px-8 py-6">
                  <span className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${org.alert ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'}`}>
                    {org.status}
                  </span>
                </td>
                <td className="px-8 py-6 text-right">
                  <button className="p-2 text-on-surface-variant/40 hover:text-primary transition-colors"><Icons.More size={20} /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  </div>
);

const ExpedientesView = ({ onViewChange }: { onViewChange: (v: View) => void }) => (
  <div className="space-y-10">
    <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
      <div className="max-w-2xl">
        <nav className="flex items-center gap-2 text-[10px] font-bold text-on-surface-variant uppercase tracking-[0.2em] mb-4">
          <span>Gestión</span>
          <Icons.ChevronRight size={10} />
          <span className="text-primary">Expedientes</span>
        </nav>
        <h1 className="font-display text-5xl font-extrabold text-on-surface tracking-tight leading-tight mb-2">Expedientes Administrativos</h1>
        <p className="text-on-surface-variant text-lg font-light leading-relaxed">Seguimiento y tramitación de solicitudes, prestaciones y expedientes de mutualistas.</p>
      </div>
      <button 
        onClick={() => onViewChange('edit-expediente')}
        className="bg-primary text-white px-8 py-4 rounded-full font-display font-bold text-sm tracking-widest uppercase flex items-center gap-3 shadow-xl shadow-primary/20 hover:scale-105 transition-transform"
      >
        <Icons.Plus size={18} />
        Nuevo Expediente
      </button>
    </header>

    <div className="bg-surface-container-lowest rounded-3xl overflow-hidden shadow-sm">
      <div className="bg-surface-container-high px-8 py-5 flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="flex gap-2 overflow-x-auto pb-2 md:pb-0 no-scrollbar w-full md:w-auto">
          {['Todos', 'Pendientes', 'En Trámite', 'Completados', 'Urgentes'].map((tab, i) => (
            <button key={i} className={`px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all ${i === 0 ? 'bg-primary text-white' : 'text-on-surface-variant hover:bg-white/50'}`}>
              {tab}
            </button>
          ))}
        </div>
        <div className="flex gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Icons.Search className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/40" size={14} />
            <input type="text" placeholder="Buscar por ID o Titular..." className="w-full bg-white border-none rounded-lg py-2 pl-9 pr-4 text-xs font-sans focus:ring-1 focus:ring-primary/20" />
          </div>
          <button className="p-2 bg-white rounded-lg text-on-surface-variant hover:text-primary transition-colors border border-outline-variant/10">
            <Icons.Filter size={18} />
          </button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-container-lowest border-b border-outline-variant/10">
              <th className="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Referencia</th>
              <th className="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Titular</th>
              <th className="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Tipo de Trámite</th>
              <th className="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Fecha Alta</th>
              <th className="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Estado</th>
              <th className="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest text-right">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-container-high">
            {[
              { id: 'EXP-2024-001', name: 'García López, María', type: 'Prestación Dentaria', date: '12/03/2024', status: 'En Trámite', color: 'text-primary' },
              { id: 'EXP-2024-042', name: 'Sánchez Ruiz, Pedro', type: 'Ayuda Asistencial', date: '10/03/2024', status: 'Pendiente', color: 'text-amber-600', alert: true },
              { id: 'EXP-2024-089', name: 'Rodríguez Gil, Juan', type: 'Baja por Enfermedad', date: '08/03/2024', status: 'Completado', color: 'text-emerald-600' },
              { id: 'EXP-2024-112', name: 'Martín Sanz, Lucía', type: 'Subsidio Jubilación', date: '05/03/2024', status: 'Urgente', color: 'text-on-tertiary-fixed-variant', urgent: true },
            ].map((exp, i) => (
              <tr key={i} className="hover:bg-surface-container-low transition-colors group cursor-pointer" onClick={() => onViewChange('edit-expediente')}>
                <td className="px-8 py-6 font-mono text-xs text-primary font-bold">{exp.id}</td>
                <td className="px-8 py-6 font-bold text-on-surface">{exp.name}</td>
                <td className="px-8 py-6 text-sm text-on-surface-variant">{exp.type}</td>
                <td className="px-8 py-6 text-sm text-on-surface-variant">{exp.date}</td>
                <td className="px-8 py-6">
                  <div className="flex items-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full ${exp.urgent ? 'bg-on-tertiary-fixed-variant animate-pulse' : exp.alert ? 'bg-amber-500' : 'bg-emerald-500'}`}></div>
                    <span className={`text-[10px] font-black uppercase tracking-widest ${exp.color}`}>{exp.status}</span>
                  </div>
                </td>
                <td className="px-8 py-6 text-right">
                  <button className="p-2 text-on-surface-variant/40 hover:text-primary transition-colors"><Icons.ArrowRight size={18} /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  </div>
);

const EditExpedienteView = ({ onViewChange }: { onViewChange: (v: View) => void }) => (
  <div className="max-w-5xl mx-auto space-y-12">
    <header className="flex flex-col md:flex-row md:items-center justify-between gap-6">
      <div>
        <button 
          onClick={() => onViewChange('expedientes')}
          className="inline-flex items-center gap-2 text-primary font-bold text-[10px] uppercase tracking-widest mb-4 hover:translate-x-[-4px] transition-transform"
        >
          <Icons.ArrowLeft size={14} />
          Volver a Expedientes
        </button>
        <h1 className="font-display text-4xl font-extrabold tracking-tight text-on-surface mb-2">Edición de Expediente</h1>
        <p className="text-on-surface-variant text-sm font-medium opacity-60 uppercase tracking-widest">Referencia: EXP-2024-042 • Ayuda Asistencial</p>
      </div>
      <div className="flex gap-4">
        <button className="px-8 py-4 rounded-full border border-outline-variant/20 text-on-surface-variant font-bold text-xs uppercase tracking-widest hover:bg-surface-container-low transition-all">
          Imprimir Resumen
        </button>
        <button className="px-8 py-4 rounded-full bg-primary text-white font-bold text-xs uppercase tracking-widest shadow-xl shadow-primary/20 hover:scale-105 transition-all">
          Guardar Cambios
        </button>
      </div>
    </header>

    <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
      <div className="lg:col-span-8 space-y-10">
        <section className="bg-surface-container-lowest rounded-[40px] p-10 shadow-sm border border-outline-variant/5">
          <h3 className="font-display font-bold text-lg text-primary mb-8 flex items-center gap-3">
            <Icons.User size={22} />
            Datos del Titular
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-2">
              <label className="text-[10px] font-black text-on-surface-variant/40 uppercase tracking-widest ml-1">Nombre Completo</label>
              <input type="text" defaultValue="Sánchez Ruiz, Pedro" className="w-full bg-surface-container-low border-none rounded-2xl p-4 font-display font-bold text-on-surface" />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-black text-on-surface-variant/40 uppercase tracking-widest ml-1">DNI / NIE</label>
              <input type="text" defaultValue="87654321B" className="w-full bg-surface-container-low border-none rounded-2xl p-4 font-mono font-bold text-on-surface" />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-black text-on-surface-variant/40 uppercase tracking-widest ml-1">Número de Afiliación</label>
              <input type="text" defaultValue="28/12345678/90" className="w-full bg-surface-container-low border-none rounded-2xl p-4 font-mono font-bold text-on-surface" />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-black text-on-surface-variant/40 uppercase tracking-widest ml-1">Provincia de Residencia</label>
              <select className="w-full bg-surface-container-low border-none rounded-2xl p-4 font-display font-bold text-on-surface appearance-none">
                <option>Madrid</option>
                <option>Barcelona</option>
                <option>Sevilla</option>
                <option>Valencia</option>
              </select>
            </div>
          </div>
        </section>

        <section className="bg-surface-container-lowest rounded-[40px] p-10 shadow-sm border border-outline-variant/5">
          <h3 className="font-display font-bold text-lg text-primary mb-8 flex items-center gap-3">
            <Icons.FileText size={22} />
            Detalles del Trámite
          </h3>
          <div className="space-y-8">
            <div className="space-y-2">
              <label className="text-[10px] font-black text-on-surface-variant/40 uppercase tracking-widest ml-1">Descripción de la Solicitud</label>
              <textarea rows={4} className="w-full bg-surface-container-low border-none rounded-3xl p-6 font-sans text-on-surface">Solicitud de ayuda asistencial por gastos extraordinarios derivados de tratamiento médico especializado no cubierto íntegramente por el sistema público.</textarea>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-5 bg-surface-container-low rounded-2xl border border-primary/10">
                <p className="text-[10px] font-black text-primary uppercase tracking-widest mb-2">Cuantía Solicitada</p>
                <p className="text-2xl font-display font-black text-on-surface">1.450,00 €</p>
              </div>
              <div className="p-5 bg-surface-container-low rounded-2xl border border-outline-variant/10">
                <p className="text-[10px] font-black text-on-surface-variant/40 uppercase tracking-widest mb-2">Fecha de Registro</p>
                <p className="text-xl font-display font-bold text-on-surface">10 Mar 2024</p>
              </div>
              <div className="p-5 bg-surface-container-low rounded-2xl border border-outline-variant/10">
                <p className="text-[10px] font-black text-on-surface-variant/40 uppercase tracking-widest mb-2">Prioridad</p>
                <p className="text-xl font-display font-bold text-amber-600">Alta</p>
              </div>
            </div>
          </div>
        </section>
      </div>

      <div className="lg:col-span-4 space-y-8">
        <div className="bg-surface-container-lowest rounded-[40px] p-8 shadow-sm border border-outline-variant/5">
          <h3 className="font-display font-bold text-on-surface mb-6">Documentación Adjunta</h3>
          <div className="space-y-3">
            {[
              { name: 'DNI_Escaneado.pdf', size: '1.2 MB' },
              { name: 'Informe_Medico.pdf', size: '4.5 MB' },
              { name: 'Factura_Gasto.pdf', size: '0.8 MB' },
            ].map((doc, i) => (
              <div key={i} className="flex items-center justify-between p-4 bg-surface-container-low rounded-2xl group hover:bg-primary/5 transition-all cursor-pointer">
                <div className="flex items-center gap-3">
                  <Icons.FileText size={18} className="text-primary" />
                  <div>
                    <p className="text-xs font-bold text-on-surface">{doc.name}</p>
                    <p className="text-[10px] text-on-surface-variant opacity-60">{doc.size}</p>
                  </div>
                </div>
                <Icons.Download size={16} className="text-on-surface-variant/40 group-hover:text-primary" />
              </div>
            ))}
            <button className="w-full mt-4 py-4 border-2 border-dashed border-outline-variant/30 rounded-2xl text-on-surface-variant/60 font-bold text-xs uppercase tracking-widest hover:border-primary hover:text-primary transition-all flex items-center justify-center gap-2">
              <Icons.Plus size={16} />
              Añadir Documento
            </button>
          </div>
        </div>

        <div className="bg-surface-container-lowest rounded-[40px] p-8 shadow-sm border border-outline-variant/5">
          <h3 className="font-display font-bold text-on-surface mb-6">Historial de Estados</h3>
          <div className="space-y-6 relative before:absolute before:left-[19px] before:top-2 before:bottom-2 before:w-0.5 before:bg-surface-container-high">
            {[
              { state: 'En Trámite', date: 'Hoy, 10:45', active: true },
              { state: 'Validación Técnica', date: 'Ayer, 16:20' },
              { state: 'Registrado', date: '10 Mar, 09:00' },
            ].map((h, i) => (
              <div key={i} className="flex gap-6 relative z-10">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center border-4 border-surface-container-lowest ${h.active ? 'bg-primary text-white' : 'bg-surface-container-high text-on-surface-variant'}`}>
                  <Icons.Clock size={16} />
                </div>
                <div>
                  <p className={`text-xs font-bold ${h.active ? 'text-primary' : 'text-on-surface'}`}>{h.state}</p>
                  <p className="text-[10px] text-on-surface-variant opacity-60">{h.date}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  </div>
);

const TitulacionesView = ({ onViewChange }: { onViewChange: (v: View) => void }) => (
  <div className="space-y-10">
    <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
      <div className="max-w-2xl">
        <nav className="flex items-center gap-2 text-[10px] font-bold text-on-surface-variant uppercase tracking-[0.2em] mb-4">
          <span>Admin</span>
          <Icons.ChevronRight size={10} />
          <span className="text-primary">Titulaciones</span>
        </nav>
        <h1 className="font-display text-5xl font-extrabold text-on-surface tracking-tight leading-tight mb-2">Catálogo de Titulaciones</h1>
        <p className="text-on-surface-variant text-lg font-light leading-relaxed">Registro oficial de grados, másteres y certificaciones habilitantes para el acceso a la función pública.</p>
      </div>
      <button 
        onClick={() => onViewChange('new-titulacion')}
        className="bg-primary text-white px-8 py-4 rounded-full font-display font-bold text-sm tracking-widest uppercase flex items-center gap-3 shadow-xl shadow-primary/20 hover:scale-105 transition-transform active:scale-95"
      >
        <Icons.Plus size={18} />
        Nueva Titulación
      </button>
    </header>

    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {[
        { label: 'Total Títulos', value: '1.240', icon: 'Titulaciones' },
        { label: 'En Revisión', value: '14', icon: 'Clock' },
        { label: 'Homologados', value: '98%', icon: 'Titulares' },
      ].map((stat, i) => {
        const Icon = Icons[stat.icon as keyof typeof Icons];
        return (
          <div key={i} className="bg-surface-container-lowest p-6 rounded-2xl shadow-sm border-b-2 border-primary/10">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-surface-container-low rounded-xl text-primary">
                <Icon size={20} />
              </div>
              <div>
                <p className="text-[10px] font-bold text-on-surface-variant/60 uppercase tracking-widest">{stat.label}</p>
                <p className="text-2xl font-display font-black text-on-surface">{stat.value}</p>
              </div>
            </div>
          </div>
        );
      })}
    </div>

    <div className="bg-surface-container-lowest rounded-3xl overflow-hidden shadow-sm">
      <div className="bg-surface-container-high px-8 py-5 flex justify-between items-center">
        <h3 className="font-display font-bold text-on-surface-variant text-xs uppercase tracking-[0.2em]">Registro de Títulos</h3>
        <div className="relative w-64">
          <Icons.Search className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/40" size={14} />
          <input type="text" placeholder="Filtrar títulos..." className="w-full bg-white border-none rounded-lg py-2 pl-9 pr-4 text-xs font-sans focus:ring-1 focus:ring-primary/20" />
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-container-lowest border-b border-outline-variant/10">
              <th className="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Código BOE</th>
              <th className="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Denominación</th>
              <th className="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Nivel MECES</th>
              <th className="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Estado</th>
              <th className="px-8 py-5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest text-right">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-container-high">
            {[
              { id: 'BOE-A-2023-1', name: 'Grado en Derecho', level: 'Nivel 2 (Grado)', status: 'Activo' },
              { id: 'BOE-A-2023-4', name: 'Máster en Gestión Pública', level: 'Nivel 3 (Máster)', status: 'Activo' },
              { id: 'BOE-A-2024-2', name: 'Grado en Ingeniería de Datos', level: 'Nivel 2 (Grado)', status: 'Pendiente', alert: true },
            ].map((tit, i) => (
              <tr key={i} className="hover:bg-surface-container-low transition-colors">
                <td className="px-8 py-6 font-mono text-sm text-primary font-bold">{tit.id}</td>
                <td className="px-8 py-6 font-bold text-on-surface">{tit.name}</td>
                <td className="px-8 py-6 text-sm text-on-surface-variant">{tit.level}</td>
                <td className="px-8 py-6">
                  <span className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${tit.alert ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'}`}>
                    {tit.status}
                  </span>
                </td>
                <td className="px-8 py-6 text-right">
                  <button className="p-2 text-on-surface-variant/40 hover:text-primary transition-colors"><Icons.More size={20} /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  </div>
);

const TitularesView = ({ onViewChange }: { onViewChange: (v: View) => void }) => (
  <div className="space-y-10">
    <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
      <div className="max-w-2xl">
        <nav className="flex items-center gap-2 text-[10px] font-bold text-on-surface-variant uppercase tracking-[0.2em] mb-4">
          <span>Censo</span>
          <Icons.ChevronRight size={10} />
          <span className="text-primary">Titulares</span>
        </nav>
        <h1 className="font-display text-5xl font-extrabold text-on-surface tracking-tight leading-tight mb-2">Censo de Titulares</h1>
        <p className="text-on-surface-variant text-lg font-light leading-relaxed">Gestión integral de los mutualistas activos, jubilados y beneficiarios del sistema MUFACE.</p>
      </div>
      <div className="flex gap-3">
        <button className="bg-surface-container-highest text-primary px-6 py-4 rounded-full font-display font-bold text-sm tracking-widest uppercase flex items-center gap-3 hover:bg-surface-container-high transition-all">
          <Icons.Download size={18} />
          Exportar
        </button>
        <button className="bg-primary text-white px-8 py-4 rounded-full font-display font-bold text-sm tracking-widest uppercase flex items-center gap-3 shadow-xl shadow-primary/20 hover:scale-105 transition-transform">
          <Icons.Plus size={18} />
          Alta Titular
        </button>
      </div>
    </header>

    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      <div className="lg:col-span-3 bg-surface-container-lowest rounded-3xl overflow-hidden shadow-sm">
        <div className="p-8 border-b border-outline-variant/10 flex justify-between items-center">
          <div className="flex gap-4">
            <button className="px-4 py-2 bg-primary text-white rounded-xl text-xs font-bold">Todos</button>
            <button className="px-4 py-2 text-on-surface-variant hover:bg-surface-container-low rounded-xl text-xs font-bold">Activos</button>
            <button className="px-4 py-2 text-on-surface-variant hover:bg-surface-container-low rounded-xl text-xs font-bold">Jubilados</button>
          </div>
          <div className="relative w-72">
            <Icons.Search className="absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant/40" size={18} />
            <input type="text" placeholder="Buscar por DNI o Nombre..." className="w-full bg-surface-container-low border-none rounded-2xl py-3 pl-12 pr-4 text-sm font-sans focus:ring-2 focus:ring-primary/20" />
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container-low/30 border-b border-outline-variant/10">
                <th className="px-8 py-4 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Titular</th>
                <th className="px-8 py-4 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">DNI</th>
                <th className="px-8 py-4 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Provincia</th>
                <th className="px-8 py-4 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">Estado</th>
                <th className="px-8 py-4 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-container-high">
              {[
                { name: 'MARTÍNEZ SÁEZ, ROBERTO', dni: '12345678A', prov: 'Madrid', status: 'Activo' },
                { name: 'LÓPEZ RUIZ, ELENA', dni: '87654321B', prov: 'Barcelona', status: 'Activo' },
                { name: 'GÓMEZ CANO, JAVIER', dni: '45678901C', prov: 'Sevilla', status: 'Baja', alert: true },
                { name: 'FERNÁNDEZ DÍAZ, ANA', dni: '23456789D', prov: 'Valencia', status: 'Activo' },
              ].map((tit, i) => (
                <tr key={i} className="hover:bg-surface-container-low/50 transition-colors">
                  <td className="px-8 py-5">
                    <p className="font-bold text-on-surface text-sm">{tit.name}</p>
                    <p className="text-[10px] text-on-surface-variant font-medium opacity-60">Afiliado desde 2015</p>
                  </td>
                  <td className="px-8 py-5 font-mono text-xs text-on-surface-variant">{tit.dni}</td>
                  <td className="px-8 py-5 text-sm text-on-surface-variant">{tit.prov}</td>
                  <td className="px-8 py-5">
                    <div className="flex items-center gap-2">
                      <div className={`w-1.5 h-1.5 rounded-full ${tit.alert ? 'bg-on-tertiary-fixed-variant' : 'bg-emerald-500'}`}></div>
                      <span className="text-xs font-bold text-on-surface">{tit.status}</span>
                    </div>
                  </td>
                  <td className="px-8 py-5 text-right">
                    <button className="p-2 text-on-surface-variant/40 hover:text-primary transition-colors"><Icons.ChevronRight size={18} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="space-y-6">
        <div className="bg-primary p-8 rounded-3xl text-white shadow-xl shadow-primary/20">
          <h3 className="font-display font-bold text-lg mb-6">Estadísticas Censo</h3>
          <div className="space-y-6">
            <div>
              <div className="flex justify-between text-xs font-bold uppercase tracking-widest mb-2 opacity-60">
                <span>Activos</span>
                <span>72%</span>
              </div>
              <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                <div className="h-full bg-white w-[72%]"></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs font-bold uppercase tracking-widest mb-2 opacity-60">
                <span>Jubilados</span>
                <span>28%</span>
              </div>
              <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                <div className="h-full bg-white w-[28%]"></div>
              </div>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-white/10">
            <p className="text-3xl font-display font-black">892.412</p>
            <p className="text-[10px] font-bold uppercase tracking-widest opacity-60">Total Mutualistas</p>
          </div>
        </div>

        <div className="bg-surface-container-lowest p-8 rounded-3xl shadow-sm border border-outline-variant/10">
          <h3 className="font-display font-bold text-on-surface mb-4">Próximas Revisiones</h3>
          <div className="space-y-4">
            {[1, 2].map((_, i) => (
              <div key={i} className="p-4 bg-surface-container-low rounded-2xl flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center text-primary shadow-sm">
                  <Icons.Clock size={18} />
                </div>
                <div>
                  <p className="text-xs font-bold text-on-surface">Revisión Trienal</p>
                  <p className="text-[10px] text-on-surface-variant opacity-60">Expira en 14 días</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  </div>
);

const CiudadesView = ({ onViewChange }: { onViewChange: (v: View) => void }) => (
  <div className="space-y-10">
    <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
      <div className="max-w-2xl">
        <nav className="flex items-center gap-2 text-[10px] font-bold text-on-surface-variant uppercase tracking-[0.2em] mb-4">
          <span>Territorio</span>
          <Icons.ChevronRight size={10} />
          <span className="text-primary">Ciudades</span>
        </nav>
        <h1 className="font-display text-5xl font-extrabold text-on-surface tracking-tight leading-tight mb-2">Gestión de Ciudades</h1>
        <p className="text-on-surface-variant text-lg font-light leading-relaxed">Administración de delegaciones territoriales, centros de atención y zonificación de servicios.</p>
      </div>
      <button 
        onClick={() => onViewChange('edit-ciudad')}
        className="bg-primary text-white px-8 py-4 rounded-full font-display font-bold text-sm tracking-widest uppercase flex items-center gap-3 shadow-xl shadow-primary/20 hover:scale-105 transition-transform"
      >
        <Icons.Plus size={18} />
        Añadir Ciudad
      </button>
    </header>

    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
      {[
        { name: 'Madrid', code: 'MAD-01', centers: 12, status: 'Operativo', color: 'bg-primary' },
        { name: 'Barcelona', code: 'BCN-02', centers: 8, status: 'Operativo', color: 'bg-primary' },
        { name: 'Valencia', code: 'VLC-03', centers: 5, status: 'Mantenimiento', color: 'bg-amber-500', alert: true },
        { name: 'Sevilla', code: 'SVQ-04', centers: 6, status: 'Operativo', color: 'bg-primary' },
        { name: 'Zaragoza', code: 'ZAZ-05', centers: 4, status: 'Operativo', color: 'bg-primary' },
        { name: 'Málaga', code: 'AGP-06', centers: 3, status: 'Operativo', color: 'bg-primary' },
      ].map((city, i) => (
        <motion.div 
          key={i}
          whileHover={{ y: -8 }}
          className="bg-surface-container-lowest rounded-3xl overflow-hidden shadow-sm group cursor-pointer"
        >
          <div className={`h-2 ${city.color}`}></div>
          <div className="p-8">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h3 className="font-display font-black text-2xl text-on-surface mb-1">{city.name}</h3>
                <p className="text-[10px] font-bold text-on-surface-variant/40 uppercase tracking-widest">{city.code}</p>
              </div>
              <div className={`p-3 rounded-2xl ${city.alert ? 'bg-amber-50 text-amber-600' : 'bg-primary/5 text-primary'}`}>
                <Icons.Ciudades size={24} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 mb-8">
              <div className="p-4 bg-surface-container-low rounded-2xl">
                <p className="text-[10px] font-bold text-on-surface-variant/60 uppercase tracking-widest mb-1">Centros</p>
                <p className="text-xl font-display font-black text-on-surface">{city.centers}</p>
              </div>
              <div className="p-4 bg-surface-container-low rounded-2xl">
                <p className="text-[10px] font-bold text-on-surface-variant/60 uppercase tracking-widest mb-1">Estado</p>
                <p className={`text-xs font-bold ${city.alert ? 'text-amber-600' : 'text-emerald-600'}`}>{city.status}</p>
              </div>
            </div>
            <button className="w-full py-4 rounded-xl border border-outline-variant/20 text-on-surface-variant font-bold text-xs uppercase tracking-widest group-hover:bg-primary group-hover:text-white group-hover:border-primary transition-all flex items-center justify-center gap-2">
              Gestionar Ciudad
              <Icons.ArrowRight size={14} />
            </button>
          </div>
        </motion.div>
      ))}
    </div>
  </div>
);

const NewTitulacionView = ({ onViewChange }: { onViewChange: (v: View) => void }) => (
  <div className="max-w-4xl mx-auto space-y-12">
    <header className="text-center">
      <button 
        onClick={() => onViewChange('titulaciones')}
        className="inline-flex items-center gap-2 text-primary font-bold text-[10px] uppercase tracking-widest mb-6 hover:translate-x-[-4px] transition-transform"
      >
        <Icons.ArrowLeft size={14} />
        Volver al Catálogo
      </button>
      <h1 className="font-display text-5xl font-extrabold tracking-tight text-on-surface mb-4">Nueva Titulación</h1>
      <p className="text-on-surface-variant text-lg font-light max-w-xl mx-auto">Registre una nueva titulación académica en el sistema oficial de homologaciones de MUFACE.</p>
    </header>

    <div className="bg-surface-container-lowest rounded-[40px] p-12 shadow-xl border border-outline-variant/5">
      <form className="space-y-10">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          <div className="space-y-3">
            <label className="text-xs font-black text-primary uppercase tracking-widest ml-1">Denominación del Título</label>
            <input type="text" placeholder="Ej: Grado en Administración de Empresas" className="w-full bg-surface-container-low border-none rounded-2xl p-5 font-display font-bold text-on-surface focus:ring-2 focus:ring-primary/20 placeholder:opacity-30" />
          </div>
          <div className="space-y-3">
            <label className="text-xs font-black text-primary uppercase tracking-widest ml-1">Código BOE / Referencia</label>
            <input type="text" placeholder="Ej: BOE-A-2024-XXXX" className="w-full bg-surface-container-low border-none rounded-2xl p-5 font-mono font-bold text-on-surface focus:ring-2 focus:ring-primary/20 placeholder:opacity-30" />
          </div>
          <div className="space-y-3">
            <label className="text-xs font-black text-primary uppercase tracking-widest ml-1">Nivel Académico (MECES)</label>
            <select className="w-full bg-surface-container-low border-none rounded-2xl p-5 font-display font-bold text-on-surface focus:ring-2 focus:ring-primary/20 appearance-none">
              <option>Seleccione nivel...</option>
              <option>Nivel 1 (Técnico Superior)</option>
              <option>Nivel 2 (Grado)</option>
              <option>Nivel 3 (Máster)</option>
              <option>Nivel 4 (Doctorado)</option>
            </select>
          </div>
          <div className="space-y-3">
            <label className="text-xs font-black text-primary uppercase tracking-widest ml-1">Área de Conocimiento</label>
            <select className="w-full bg-surface-container-low border-none rounded-2xl p-5 font-display font-bold text-on-surface focus:ring-2 focus:ring-primary/20 appearance-none">
              <option>Seleccione área...</option>
              <option>Ciencias Sociales y Jurídicas</option>
              <option>Ingeniería y Arquitectura</option>
              <option>Artes y Humanidades</option>
              <option>Ciencias de la Salud</option>
            </select>
          </div>
        </div>

        <div className="space-y-3">
          <label className="text-xs font-black text-primary uppercase tracking-widest ml-1">Descripción y Competencias</label>
          <textarea rows={5} placeholder="Describa brevemente el perfil profesional y competencias habilitantes..." className="w-full bg-surface-container-low border-none rounded-3xl p-8 font-sans text-on-surface focus:ring-2 focus:ring-primary/20 placeholder:opacity-30"></textarea>
        </div>

        <div className="pt-6 flex items-center justify-between border-t border-outline-variant/10">
          <div className="flex items-center gap-3 text-on-surface-variant/60">
            <Icons.Shield size={20} />
            <span className="text-xs font-medium">Validación automática activa</span>
          </div>
          <div className="flex gap-4">
            <button type="button" onClick={() => onViewChange('titulaciones')} className="px-8 py-4 rounded-full text-on-surface-variant font-bold text-xs uppercase tracking-widest hover:bg-surface-container-low transition-all">Descartar</button>
            <button type="submit" className="px-12 py-4 rounded-full bg-primary text-white font-bold text-xs uppercase tracking-widest shadow-2xl shadow-primary/30 hover:scale-105 transition-all active:scale-95">Registrar Titulación</button>
          </div>
        </div>
      </form>
    </div>
  </div>
);

const NewOrganismoView = ({ onViewChange }: { onViewChange: (v: View) => void }) => (
  <div className="max-w-4xl mx-auto space-y-12">
    <header className="text-center">
      <button 
        onClick={() => onViewChange('organismos')}
        className="inline-flex items-center gap-2 text-primary font-bold text-[10px] uppercase tracking-widest mb-6 hover:translate-x-[-4px] transition-transform"
      >
        <Icons.ArrowLeft size={14} />
        Volver a Organismos
      </button>
      <h1 className="font-display text-5xl font-extrabold tracking-tight text-on-surface mb-4">Registro de Organismo</h1>
      <p className="text-on-surface-variant text-lg font-light max-w-xl mx-auto">Incorpore una nueva entidad o delegación al ecosistema administrativo de MUFACE.</p>
    </header>

    <div className="bg-surface-container-lowest rounded-[40px] p-12 shadow-xl border border-outline-variant/5">
      <form className="space-y-10">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          <div className="space-y-3">
            <label className="text-xs font-black text-primary uppercase tracking-widest ml-1">Nombre de la Entidad</label>
            <input type="text" placeholder="Ej: Delegación Territorial de Valencia" className="w-full bg-surface-container-low border-none rounded-2xl p-5 font-display font-bold text-on-surface focus:ring-2 focus:ring-primary/20 placeholder:opacity-30" />
          </div>
          <div className="space-y-3">
            <label className="text-xs font-black text-primary uppercase tracking-widest ml-1">Identificador Fiscal / ID</label>
            <input type="text" placeholder="Ej: ORG-46001" className="w-full bg-surface-container-low border-none rounded-2xl p-5 font-mono font-bold text-on-surface focus:ring-2 focus:ring-primary/20 placeholder:opacity-30" />
          </div>
          <div className="space-y-3">
            <label className="text-xs font-black text-primary uppercase tracking-widest ml-1">Tipo de Organismo</label>
            <select className="w-full bg-surface-container-low border-none rounded-2xl p-5 font-display font-bold text-on-surface focus:ring-2 focus:ring-primary/20 appearance-none">
              <option>Seleccione tipo...</option>
              <option>Sede Central</option>
              <option>Delegación Provincial</option>
              <option>Oficina de Atención</option>
              <option>Centro de Gestión</option>
            </select>
          </div>
          <div className="space-y-3">
            <label className="text-xs font-black text-primary uppercase tracking-widest ml-1">Responsable de Área</label>
            <input type="text" placeholder="Nombre del director/a..." className="w-full bg-surface-container-low border-none rounded-2xl p-5 font-display font-bold text-on-surface focus:ring-2 focus:ring-primary/20 placeholder:opacity-30" />
          </div>
        </div>

        <div className="space-y-3">
          <label className="text-xs font-black text-primary uppercase tracking-widest ml-1">Dirección Postal Completa</label>
          <input type="text" placeholder="Calle, número, planta, código postal y ciudad..." className="w-full bg-surface-container-low border-none rounded-2xl p-5 font-sans font-medium text-on-surface focus:ring-2 focus:ring-primary/20 placeholder:opacity-30" />
        </div>

        <div className="pt-6 flex items-center justify-between border-t border-outline-variant/10">
          <div className="flex items-center gap-3 text-on-surface-variant/60">
            <Icons.Building2 size={20} />
            <span className="text-xs font-medium">Alta en Directorio Común (DIR3)</span>
          </div>
          <div className="flex gap-4">
            <button type="button" onClick={() => onViewChange('organismos')} className="px-8 py-4 rounded-full text-on-surface-variant font-bold text-xs uppercase tracking-widest hover:bg-surface-container-low transition-all">Cancelar</button>
            <button type="submit" className="px-12 py-4 rounded-full bg-primary text-white font-bold text-xs uppercase tracking-widest shadow-2xl shadow-primary/30 hover:scale-105 transition-all active:scale-95">Confirmar Registro</button>
          </div>
        </div>
      </form>
    </div>
  </div>
);

const EditCiudadView = ({ onViewChange }: { onViewChange: (v: View) => void }) => (
  <div className="max-w-4xl mx-auto space-y-12">
    <header className="text-center">
      <button 
        onClick={() => onViewChange('ciudades')}
        className="inline-flex items-center gap-2 text-primary font-bold text-[10px] uppercase tracking-widest mb-6 hover:translate-x-[-4px] transition-transform"
      >
        <Icons.ArrowLeft size={14} />
        Volver a Ciudades
      </button>
      <h1 className="font-display text-5xl font-extrabold tracking-tight text-on-surface mb-4">Gestión de Ciudad</h1>
      <p className="text-on-surface-variant text-lg font-light max-w-xl mx-auto">Configure los parámetros territoriales y centros de atención para la demarcación seleccionada.</p>
    </header>

    <div className="bg-surface-container-lowest rounded-[40px] p-12 shadow-xl border border-outline-variant/5">
      <form className="space-y-10">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          <div className="space-y-3">
            <label className="text-xs font-black text-primary uppercase tracking-widest ml-1">Nombre de la Ciudad</label>
            <input type="text" defaultValue="Madrid" className="w-full bg-surface-container-low border-none rounded-2xl p-5 font-display font-bold text-on-surface focus:ring-2 focus:ring-primary/20" />
          </div>
          <div className="space-y-3">
            <label className="text-xs font-black text-primary uppercase tracking-widest ml-1">Código Territorial</label>
            <input type="text" defaultValue="MAD-01" className="w-full bg-surface-container-low border-none rounded-2xl p-5 font-mono font-bold text-on-surface focus:ring-2 focus:ring-primary/20" />
          </div>
          <div className="space-y-3">
            <label className="text-xs font-black text-primary uppercase tracking-widest ml-1">Número de Centros</label>
            <input type="number" defaultValue="12" className="w-full bg-surface-container-low border-none rounded-2xl p-5 font-display font-bold text-on-surface focus:ring-2 focus:ring-primary/20" />
          </div>
          <div className="space-y-3">
            <label className="text-xs font-black text-primary uppercase tracking-widest ml-1">Estado Operativo</label>
            <select className="w-full bg-surface-container-low border-none rounded-2xl p-5 font-display font-bold text-on-surface focus:ring-2 focus:ring-primary/20 appearance-none">
              <option>Operativo</option>
              <option>Mantenimiento</option>
              <option>Cerrado Temporalmente</option>
            </select>
          </div>
        </div>

        <div className="space-y-6">
          <h4 className="text-xs font-black text-primary uppercase tracking-widest ml-1">Centros de Atención Vinculados</h4>
          <div className="space-y-3">
            {[
              { name: 'Sede Central - Calle Mayor', status: 'Activo' },
              { name: 'Oficina Periférica - Chamberí', status: 'Activo' },
              { name: 'Centro de Gestión - Vallecas', status: 'En revisión', alert: true },
            ].map((center, i) => (
              <div key={i} className="flex items-center justify-between p-5 bg-surface-container-low rounded-2xl">
                <div className="flex items-center gap-4">
                  <Icons.Building2 size={18} className="text-on-surface-variant/40" />
                  <span className="text-sm font-bold text-on-surface">{center.name}</span>
                </div>
                <span className={`text-[10px] font-black uppercase tracking-widest ${center.alert ? 'text-on-tertiary-fixed-variant' : 'text-emerald-600'}`}>{center.status}</span>
              </div>
            ))}
            <button type="button" className="w-full py-4 border-2 border-dashed border-outline-variant/30 rounded-2xl text-on-surface-variant/60 font-bold text-xs uppercase tracking-widest hover:border-primary hover:text-primary transition-all flex items-center justify-center gap-2">
              <Icons.Plus size={16} />
              Vincular Nuevo Centro
            </button>
          </div>
        </div>

        <div className="pt-6 flex items-center justify-between border-t border-outline-variant/10">
          <button type="button" className="text-on-tertiary-fixed-variant font-bold text-xs uppercase tracking-widest hover:underline">Eliminar Ciudad</button>
          <div className="flex gap-4">
            <button type="button" onClick={() => onViewChange('ciudades')} className="px-8 py-4 rounded-full text-on-surface-variant font-bold text-xs uppercase tracking-widest hover:bg-surface-container-low transition-all">Cancelar</button>
            <button type="submit" className="px-12 py-4 rounded-full bg-primary text-white font-bold text-xs uppercase tracking-widest shadow-2xl shadow-primary/30 hover:scale-105 transition-all">Guardar Configuración</button>
          </div>
        </div>
      </form>
    </div>
  </div>
);

// --- Main App ---

export default function App() {
  const [currentView, setCurrentView] = useState<View>('dashboard');

  const renderView = () => {
    switch (currentView) {
      case 'dashboard': return <DashboardView onViewChange={setCurrentView} />;
      case 'expedientes': return <ExpedientesView onViewChange={setCurrentView} />;
      case 'edit-expediente': return <EditExpedienteView onViewChange={setCurrentView} />;
      case 'organismos': return <OrganismosView onViewChange={setCurrentView} />;
      case 'new-organismo': return <NewOrganismoView onViewChange={setCurrentView} />;
      case 'titulaciones': return <TitulacionesView onViewChange={setCurrentView} />;
      case 'new-titulacion': return <NewTitulacionView onViewChange={setCurrentView} />;
      case 'titulares': return <TitularesView onViewChange={setCurrentView} />;
      case 'ciudades': return <CiudadesView onViewChange={setCurrentView} />;
      case 'edit-ciudad': return <EditCiudadView onViewChange={setCurrentView} />;
      default: return <DashboardView onViewChange={setCurrentView} />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <TopNav />
      <Sidebar currentView={currentView} onViewChange={setCurrentView} />
      
      <main className="ml-64 pt-24 px-12 pb-20 flex-1 overflow-x-hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentView}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
          >
            {renderView()}
          </motion.div>
        </AnimatePresence>
      </main>

      <footer className="ml-64 py-8 px-12 border-t border-outline-variant/10 bg-surface-container-lowest flex flex-col md:flex-row justify-between items-center gap-6">
        <div className="flex flex-col md:flex-row items-center gap-6">
          <span className="font-display font-black text-primary tracking-tighter text-xl">MUFACE</span>
          <p className="text-[10px] font-medium text-on-surface-variant/60 uppercase tracking-widest">
            © 2024 MUFACE - Ministerio para la Transformación Digital y de la Función Pública
          </p>
        </div>
        <div className="flex gap-8">
          {['Accesibilidad', 'Aviso Legal', 'Privacidad', 'Sede Electrónica'].map((link) => (
            <a key={link} href="#" className="text-[10px] font-bold text-on-surface-variant/60 uppercase tracking-widest hover:text-primary transition-colors">
              {link}
            </a>
          ))}
        </div>
      </footer>
    </div>
  );
}
