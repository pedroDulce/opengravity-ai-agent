
```markdown
# ROL: Arquitecto Angular ATOM Senior

Eres experto en **refactorizar aplicaciones Angular existentes** hacia la arquitectura corporativa ATOM.

# TU MISIÓN

Transformar componentes Angular existentes a **componentes ATOM** manteniendo:
✅ Funcionalidad intacta
✅ Estilo visual idéntico  
✅ Navegación/rutas preservadas
✅ Integración con librerías externas (leaflet, charts, etc.)

# REGLAS DE CONVERSIÓN

## 1. COMPONENTES → ATOM

### Antes (tradicional):
```typescript
@Component({
  selector: 'app-heatmap',
  templateUrl: './heatmap.component.html',
  styleUrls: ['./heatmap.component.scss']
})
export class HeatmapComponent implements OnInit {
  constructor(private service: HeatmapService) {}
  
  ngOnInit() { ... }
}
```

### Después (ATOM):
```typescript
@Component({
  selector: 'lib-heatmap',          // ← Cambiar app-* → lib-*
  standalone: true,                  // ← Siempre standalone
  imports: [CommonModule, MatCardModule],  // ← Imports explícitos
  templateUrl: './lib-heatmap.component.html',
  styleUrls: ['./lib-heatmap.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush  // ← OnPush
})
export class LibHeatmapComponent implements OnInit, OnDestroy {
  private service = inject(HeatmapService);  // ← inject() NO constructor
  private _data = signal([]);               // ← signals cuando aplique
  
  ngOnInit() { ... }
}
```

## 2. SERVICIOS → ArqExternalMicroAdapter

Si el servicio usa HttpClient, envuélvelo en ArqExternalMicroAdapter:

### Antes:
```typescript
@Injectable({providedIn: 'root'})
export class HeatmapService {
  constructor(private http: HttpClient) {}
  
  getCities() {
    return this.http.get('/api/cities');
  }
}
```

### Después:
```typescript
@Injectable({providedIn: 'root'})
export class HeatmapService extends ArqExternalMicroAdapter {
  constructor() {
    super('heatmap-api');  // ← Nombre del micro
  }
  
  getCities(): Observable<CustomPage<CityDTO>> {
    return this.executeGetQueryPagingMethod('/cities');
  }
}
```

## 3. LIBRERÍAS EXTERNAS → Mantener y documentar

Si el componente usa leaflet, d3, charts:
- ✅ **MANTENER** la integración
- ✅ **AÑADIR** a package.json si falta
- ✅ **CREAR** módulo adapter si es complejo

Ejemplo con Leaflet:
```typescript
import * as L from 'leaflet';
import 'leaflet.heat';

@Component({...})
export class LibHeatmapComponent implements AfterViewInit, OnDestroy {
  private map!: L.Map;
  
  ngAfterViewInit() {
    this.map = L.map('mapContainer').setView([40.4168, -3.7038], 6);
    // ... resto de lógica leaflet
  }
  
  ngOnDestroy() {
    this.map?.remove();  // ← Cleanup obligatorio
  }
}
```

## 4. ESTILOS → M3 Theme

Si usa Material, migrar a M3 (Angular 19+):

### Antes:
```scss
@use '@angular/material' as mat;
@include mat.all-component-themes(mat.define-light-theme(...));
```

### Después:
```scss
@use '@angular/material' as mat;
@include mat.core();
:root {
  @include mat.theme((
    color: (primary: mat.$azure-palette),
    typography: Roboto,
    density: 0,
  ));
}
```

## 5. ROUTING → Mantener rutas existentes

Preservar TODAS las rutas del app.routes.ts original.
Solo cambiar referencias de componentes si cambian los selectores.

# PROCESO PASO A PASO

## Paso 1: Analizar informe de la app original
- Revisar `app-analysis.json`
- Identificar componentes a convertir
- Detectar librerías externas usadas
- Mapear servicios y endpoints

## Paso 2: Generar estructura ATOM
1. **package.json**: Añadir dependencias ATOM + librerías externas
2. **app.config.ts**: Configurar providers ATOM
3. **app.routes.ts**: Migrar rutas manteniendo paths
4. **styles.scss**: Tema M3 + imports de librerías externas

## Paso 3: Convertir componentes (uno por uno)
Para CADA componente del informe:
1. Cambiar selector: `app-*` → `lib-*`
2. Hacer standalone: true
3. Añadir imports explícitos
4. Cambiar constructor DI → inject()
5. Añadir OnPush
6. Mantener template y styles intactos
7. Añadir signals si hay estado reactivo

## Paso 4: Convertir servicios
Para CADA servicio que use HttpClient:
1. Extender ArqExternalMicroAdapter
2. Reemplazar HttpClient methods → adapter methods
3. Mantener signatures de métodos públicos

## Paso 5: Validar
- Verificar que todos los imports existen
- Verificar que las rutas funcionan
- Verificar que las librerías externas están en package.json

# FORMATO DE RESPUESTA

Para CADA archivo generado:

=== FILE: src/app/path/to/file.ts ===
```typescript
// Código completo y compilable
```

=== FILE: src/app/path/to/file.html ===
```html
<!-- Template EXACTO del original (sin modificar) -->
```

=== FILE: src/app/path/to/file.scss ===
```scss
/* Styles EXACTOS del original (sin modificar) */
```

# INPUT QUE RECIBIRÁS

Te proporcionaré:
1. **app-analysis.json**: Informe completo de la app original
2. **context_atom.md**: Guías de arquitectura ATOM
3. **archivos originales**: Código fuente completo

# TU RESPUESTA DEBE SER

1. **Completa**: TODOS los archivos refactorizados
2. **Funcional**: La app debe compilar y funcionar igual
3. **ATOM-compliant**: Sigue todas las reglas corporativas
4. **Documentada**: README con pasos de migración

¡COMIENZA LA ATOMIZACIÓN!
```

---

## 📋 Fase 3: Script de atomización automatizada

**Crea: `scripts/atomize-angular-app.py`**

```python
#!/usr/bin/env python3
"""
Atomiza una aplicación Angular existente usando OpenRouter LLM.
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
import re

from core.llm_client import LLMClient
from core.context_manager import ContextManager
from scripts.analyze-angular-app import AngularAppAnalyzer

class AngularAppAtomizer:
    """Refactoriza app Angular a arquitectura ATOM."""
    
    def __init__(
        self,
        original_app_path: str,
        output_app_path: str,
        analysis_report_path: str
    ):
        self.original_path = Path(original_app_path)
        self.output_path = Path(output_app_path)
        self.analysis_path = Path(analysis_report_path)
        
        self.llm_client = LLMClient(provider="openrouter")
        self.context_manager = ContextManager()
        
    def atomize(self):
        """Ejecuta el proceso completo de atomización."""
        print("🚀 Iniciando atomización de Angular App...")
        
        # Paso 1: Cargar análisis
        print("\n📊 Paso 1: Cargando análisis de la app...")
        with open(self.analysis_path, 'r', encoding='utf-8') as f:
            analysis = json.load(f)
        
        # Paso 2: Cargar contexto ATOM
        print("📚 Paso 2: Cargando contexto ATOM...")
        atom_context = self.context_manager.get_context(
            "angular atom standalone component service routing",
            category="angular-guidelines",
            max_tokens=3000
        )
        
        # Paso 3: Generar prompt
        print("🤖 Paso 3: Generando prompt para LLM...")
        prompt = self._build_atomization_prompt(analysis, atom_context)
        
        # Paso 4: Llamar a OpenRouter
        print("⚡ Paso 4: Consultando OpenRouter (esto puede tardar 2-5 min)...")
        response = self.llm_client.generate(
            prompt=prompt,
            system_prompt=self._get_system_prompt()
        )
        
        # Paso 5: Parsear y escribir archivos
        print("📝 Paso 5: Escribiendo archivos atomizados...")
        files_written = self._parse_and_write_files(response)
        
        # Paso 6: Copiar assets y configs
        print("📦 Paso 6: Copiando assets y configuraciones...")
        self._copy_static_files()
        
        print(f"\n✨ ¡Atomización completada!")
        print(f"📁 Ubicación: {self.output_path.absolute()}")
        print(f"📄 Archivos generados: {files_written}")
        print(f"\n🚀 Para probar:")
        print(f"   cd {self.output_path}")
        print(f"   npm install")
        print(f"   ng serve")
        
        return files_written
    
    def _build_atomization_prompt(self, analysis: dict, atom_context: str) -> str:
        """Construye el prompt completo para el LLM."""
        
        # Cargar prompt base
        prompt_file = Path("prompts/atomize-existing-app.md")
        if prompt_file.exists():
            base_prompt = prompt_file.read_text(encoding='utf-8')
        else:
            base_prompt = ""  # Usar inline si no existe
        
        # Resumir análisis (limitar tokens)
        analysis_summary = {
            "components_count": len(analysis.get('components', [])),
            "services_count": len(analysis.get('services', [])),
            "routes": analysis.get('routing', {}).get('routes', []),
            "external_libs": analysis.get('dependencies', {}).get('external_libs', []),
            "uses_material": analysis.get('styles', {}).get('uses_material', False),
        }
        
        # Extraer componentes clave (primeros 5 para no exceder tokens)
        components_sample = analysis.get('components', [])[:5]
        
        prompt = f"""
{base_prompt}

---
ANÁLISIS DE LA APLICACIÓN ORIGINAL:
{json.dumps(analysis_summary, indent=2)}

COMPONENTES A CONVERTIR (muestra):
{json.dumps(components_sample, indent=2, ensure_ascii=False)[:5000]}

SERVICIOS EXISTENTES:
{json.dumps(analysis.get('services', []), indent=2)[:3000]}

ROUTING ACTUAL:
{json.dumps(analysis.get('routing', {}), indent=2)}

DEPENDENCIAS EXTERNAS DETECTADAS:
{', '.join(analysis.get('dependencies', {}).get('external_libs', []))}

---
CONTEXTO ARQUITECTURA ATOM:
{atom_context[:3000]}

---
INSTRUCCIONES:
1. Genera TODA la aplicación refactorizada a ATOM
2. Mantén templates y styles EXACTOS del original
3. Convierte selectores app-* → lib-*
4. Haz todos los componentes standalone
5. Usa inject() en lugar de constructor
6. Añade OnPush change detection
7. Envuelve servicios HTTP en ArqExternalMicroAdapter
8. Mantén TODAS las rutas del routing original
9. Preserva integraciones con librerías externas (leaflet, charts, etc.)
10. Usa Angular Material M3 theme (Angular 19+)

GENERAR AHORA LA APLICACIÓN ATOM COMPLETA:
"""
        
        print(f"📊 Prompt size: {len(prompt)} chars (~{len(prompt)//4} tokens)")
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Retorna el system prompt optimizado."""
        return """Eres un Arquitecto Angular ATOM experto en refactorización.
Tu trabajo es transformar aplicaciones Angular existentes a la arquitectura ATOM corporativa.

REGLAS CRÍTICAS:
1. NUNCA modifiques templates HTML o styles SCSS - deben ser IDÉNTICOS al original
2. SIEMPRE preserva la funcionalidad y navegación
3. SOLO cambia: selectores, decorators, inyección de dependencias
4. MANTÉN todas las librerías externas (leaflet, d3, charts, etc.)
5. USA Angular Material M3 API (mat.theme, NO define-light-theme)

RESPONDE SOLO con archivos en formato: === FILE: path === ```code ```"""
    
    def _parse_and_write_files(self, response: str) -> int:
        """Parsea la respuesta del LLM y escribe archivos."""
        
        files_written = 0
        pattern = r'=== FILE: ([^\s]+) ===\s*```(?:\w+)?\s*(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for file_path, content in matches:
            full_path = self.output_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content.strip(), encoding='utf-8')
            files_written += 1
            print(f"  ✅ {file_path}")
        
        return files_written
    
    def _copy_static_files(self):
        """Copia archivos estáticos de la app original."""
        
        # Archivos a copiar tal cual
        static_files = [
            "package.json",
            "tsconfig.json",
            "tsconfig.app.json",
            "angular.json",
            "README.md",
        ]
        
        for filename in static_files:
            src = self.original_path / filename
            dst = self.output_path / filename
            
            if src.exists() and not dst.exists():
                dst.write_text(src.read_text(encoding='utf-8'), encoding='utf-8')
                print(f"  📋 {filename}")
        
        # Copiar assets
        assets_src = self.original_path / "src" / "assets"
        assets_dst = self.output_path / "src" / "assets"
        
        if assets_src.exists():
            import shutil
            shutil.copytree(assets_src, assets_dst, dirs_exist_ok=True)
            print(f"  📁 assets/ ({len(list(assets_src.rglob('*')))} files)")

def main():
    # Paths
    original_app = "C:/Users/pedrodulce/develop/heatmap-app-original"
    output_app = "C:/Users/pedrodulce/develop/heatmap-app-atom"
    analysis_report = "C:/Users/pedrodulce/develop/antigravity/analysis/app-analysis.json"
    
    # Analizar app original (si no existe el informe)
    if not Path(analysis_report).exists():
        print("🔍 Generando análisis de la app original...")
        analyzer = AngularAppAnalyzer(original_app)
        report = analyzer.analyze()
        
        Path(analysis_report).parent.mkdir(parents=True, exist_ok=True)
        with open(analysis_report, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Atomizar
    atomizer = AngularAppAtomizer(original_app, output_app, analysis_report)
    atomizer.atomize()

if __name__ == "__main__":
    main()

```