import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { LucideAngularModule, Shield, LayoutDashboard, FileText, Building2, GraduationCap, Users, MapPin, Search, Bell, HelpCircle, Settings, LogOut, ChevronRight, Plus, Filter, ArrowRight, ArrowLeft, User, Download, Clock, History, PlusCircle, MoreVertical } from 'lucide-angular';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive, LucideAngularModule],
  template: `
    <div style="min-height: 100vh; background: #F8F9FF; font-family: system-ui; color: #191C20; display: flex;">
      <!-- Top Nav -->
      <nav style="position: fixed; top: 0; width: 100%; height: 64px; background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(12px); border-bottom: 1px solid rgba(195, 198, 207, 0.1); display: flex; align-items: center; justify-content: space-between; padding: 0 32px; z-index: 50;">
        <span style="font-size: 24px; font-weight: 900; color: #0056D2;">MUFACE</span>
        <div style="flex: 1; max-width: 500px; margin: 0 48px; display: none;">
          <input type="text" placeholder="Buscar expedientes..." style="width: 100%; background: #E8E7F0; border: none; border-radius: 24px; padding: 10px 16px; font-size: 14px;" />
        </div>
        <div style="display: flex; gap: 12px;">
          <button style="padding: 10px; border-radius: 50%; background: transparent; cursor: pointer;">🔔</button>
          <button style="padding: 10px; border-radius: 50%; background: transparent; cursor: pointer;">❓</button>
          <div style="width: 40px; height: 40px; border-radius: 50%; background: #D7E2FF; display: flex; align-items: center; justify-content: center; cursor: pointer; color: #0056D2; font-weight: bold; font-size: 12px;">JD</div>
        </div>
      </nav>

      <!-- Sidebar -->
      <aside style="position: fixed; left: 0; top: 0; height: 100vh; width: 256px; background: #F3F3FA; border-right: 1px solid rgba(195, 198, 207, 0.1); display: flex; flex-direction: column; z-index: 40; padding-top: 64px;">
        <div style="padding: 32px 24px;">
          <div style="display: flex; align-items: center; gap: 12px;">
            <div style="width: 40px; height: 40px; border-radius: 8px; background: #0056D2; display: flex; align-items: center; justify-content: center; color: white; box-shadow: 0 0 20px rgba(0, 86, 210, 0.2);">🛡️</div>
            <div>
              <h2 style="font-weight: bold; color: #0056D2; line-height: 1.2;">Gestión Pública</h2>
              <p style="font-size: 10px; color: #43474E; text-transform: uppercase; letter-spacing: 0.15em; font-weight: bold; opacity: 0.6;">Panel de Control</p>
            </div>
          </div>
        </div>

        <nav style="flex: 1; padding: 0 12px; display: flex; flex-direction: column; gap: 4px;">
          <a href="/dashboard" style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 8px; cursor: pointer; color: #43474E; text-decoration: none; transition: all 0.3s;">
            📊 <span style="font-size: 14px;">Dashboard</span>
          </a>
          <a href="/expedientes" style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 8px; cursor: pointer; color: #43474E; text-decoration: none; transition: all 0.3s;">
            📄 <span style="font-size: 14px;">Expedientes</span>
          </a>
          <a href="/organismos" style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 8px; cursor: pointer; color: #43474E; text-decoration: none; transition: all 0.3s;">
            🏢 <span style="font-size: 14px;">Organismos</span>
          </a>
          <a href="/titulaciones" style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 8px; cursor: pointer; color: #43474E; text-decoration: none; transition: all 0.3s;">
            🎓 <span style="font-size: 14px;">Titulaciones</span>
          </a>
          <a href="/titulares" style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 8px; cursor: pointer; color: #43474E; text-decoration: none; transition: all 0.3s;">
            👥 <span style="font-size: 14px;">Titulares</span>
          </a>
          <a href="/ciudades" style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 8px; cursor: pointer; color: #43474E; text-decoration: none; transition: all 0.3s;">
            📍 <span style="font-size: 14px;">Ciudades</span>
          </a>
        </nav>

        <div style="padding: 16px; margin-top: auto; border-top: 1px solid rgba(195, 198, 207, 0.1); display: flex; flex-direction: column; gap: 4px;">
          <button style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; color: #43474E; background: transparent; border: none; cursor: pointer; border-radius: 8px; font-size: 14px; transition: all 0.3s;">
            ⚙️ <span>Ajustes</span>
          </button>
          <button style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; color: #8B1A00; background: transparent; border: none; cursor: pointer; border-radius: 8px; font-size: 14px; transition: all 0.3s;">
            🚪 <span>Cerrar Sesión</span>
          </button>
        </div>
      </aside>

      <!-- Main Content -->
      <main style="margin-left: 256px; margin-top: 64px; min-height: calc(100vh - 64px); background: white;">
        <div style="padding: 40px; max-width: 1600px; margin: 0 auto;">
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
