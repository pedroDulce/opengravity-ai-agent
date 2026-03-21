#!/usr/bin/env python3
"""
Analiza una aplicación Angular existente y genera un informe
estructurado para el LLM.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any

class AngularAppAnalyzer:
    """Analizador estático de aplicaciones Angular."""
    
    def __init__(self, app_path: str):
        self.app_path = Path(app_path)
        self.src_path = self.app_path / "src" / "app"
        
    def analyze(self) -> Dict[str, Any]:
        """Realiza análisis completo de la app."""
        print(f"🔍 Analizando aplicación en: {self.app_path}")
        
        return {
            "structure": self._analyze_structure(),
            "components": self._analyze_components(),
            "services": self._analyze_services(),
            "modules": self._analyze_modules(),
            "routing": self._analyze_routing(),
            "dependencies": self._analyze_dependencies(),
            "styles": self._analyze_styles(),
        }
    
    def _analyze_structure(self) -> Dict:
        """Analiza la estructura de carpetas."""
        structure = {}
        
        for root, dirs, files in os.walk(self.src_path):
            rel_path = Path(root).relative_to(self.src_path)
            level = str(rel_path).count(os.sep)
            
            if level <= 3:  # Solo primeros 3 niveles
                structure[str(rel_path)] = {
                    "dirs": [d for d in dirs if not d.startswith('.')],
                    "files": [f for f in files if f.endswith(('.ts', '.html', '.scss'))]
                }
        
        return structure
    
    def _analyze_components(self) -> List[Dict]:
        """Extrae información de todos los componentes."""
        components = []
        
        for ts_file in self.src_path.rglob("*.component.ts"):
            content = ts_file.read_text(encoding='utf-8')
            
            # Extraer metadata del decorator @Component
            component_meta = self._parse_component_decorator(content)
            
            # Extraer template
            template_path = ts_file.with_suffix('.html')
            template = template_path.read_text(encoding='utf-8') if template_path.exists() else ""
            
            # Extraer styles
            scss_path = ts_file.with_suffix('.scss')
            styles = scss_path.read_text(encoding='utf-8') if scss_path.exists() else ""
            
            components.append({
                "name": ts_file.stem,
                "path": str(ts_file.relative_to(self.src_path)),
                "selector": component_meta.get('selector', ''),
                "standalone": component_meta.get('standalone', False),
                "imports": component_meta.get('imports', []),
                "template": template,
                "styles": styles,
                "class_code": content,
                "uses_onpush": 'ChangeDetectionStrategy.OnPush' in content,
                "uses_constructor_di": 'constructor(' in content and 'private ' in content,
                "uses_signals": 'signal(' in content or 'computed(' in content,
                "external_libs": self._detect_external_libs(content + template),
            })
        
        return components
    
    def _parse_component_decorator(self, content: str) -> Dict:
        """Parsea el decorator @Component."""
        meta = {}
        
        # Selector
        selector_match = re.search(r"selector:\s*['\"]([^'\"]+)['\"]", content)
        if selector_match:
            meta['selector'] = selector_match.group(1)
        
        # Standalone
        standalone_match = re.search(r"standalone:\s*(true|false)", content)
        if standalone_match:
            meta['standalone'] = standalone_match.group(1) == 'true'
        
        # Imports
        imports_match = re.search(r"imports:\s*\[([^\]]+)\]", content, re.DOTALL)
        if imports_match:
            imports_str = imports_match.group(1)
            meta['imports'] = [imp.strip() for imp in imports_str.split(',')]
        
        return meta
    
    def _detect_external_libs(self, code: str) -> List[str]:
        """Detecta librerías externas usadas."""
        libs = []
        
        # Leaflet
        if 'leaflet' in code.lower() or 'L.' in code:
            libs.append('leaflet')
        
        # Chart.js / ng2-charts
        if 'chart' in code.lower() or 'canvas' in code:
            libs.append('chart.js')
        
        # D3.js
        if 'd3.' in code or 'd3-' in code:
            libs.append('d3')
        
        # ngx-charts
        if 'ngx-charts' in code:
            libs.append('ngx-charts')
        
        return libs
    
    def _analyze_services(self) -> List[Dict]:
        """Extrae información de servicios."""
        services = []
        
        for ts_file in self.src_path.rglob("*.service.ts"):
            content = ts_file.read_text(encoding='utf-8')
            
            # Extraer endpoints HTTP
            http_calls = re.findall(r"(get|post|put|delete)\(['\"]([^'\"]+)['\"]", content)
            
            services.append({
                "name": ts_file.stem,
                "path": str(ts_file.relative_to(self.src_path)),
                "provided_in": "root" if "providedIn: 'root'" in content else "module",
                "http_endpoints": http_calls,
                "methods": re.findall(r"(\w+)\s*\([^)]*\)\s*[:{]", content),
            })
        
        return services
    
    def _analyze_modules(self) -> List[Dict]:
        """Analiza módulos Angular."""
        modules = []
        
        for ts_file in self.src_path.rglob("*.module.ts"):
            content = ts_file.read_text(encoding='utf-8')
            
            modules.append({
                "name": ts_file.stem,
                "path": str(ts_file.relative_to(self.src_path)),
                "declarations": self._extract_array(content, 'declarations'),
                "imports": self._extract_array(content, 'imports'),
                "exports": self._extract_array(content, 'exports'),
            })
        
        return modules
    
    def _analyze_routing(self) -> Dict:
        """Analiza configuración de routing."""
        routes_file = self.src_path / "app.routes.ts"
        
        if not routes_file.exists():
            return {"routes": [], "lazy_loaded": []}
        
        content = routes_file.read_text(encoding='utf-8')
        
        # Extraer rutas
        routes = re.findall(r"path:\s*['\"]([^'\"]+)['\"]", content)
        lazy_loaded = re.findall(r"loadComponent.*?import\(['\"]([^'\"]+)['\"]", content)
        
        return {
            "routes": routes,
            "lazy_loaded": lazy_loaded,
            "has_guard": 'canActivate' in content or 'canDeactivate' in content,
        }
    
    def _analyze_dependencies(self) -> Dict:
        """Analiza package.json."""
        pkg_file = self.app_path / "package.json"
        
        if not pkg_file.exists():
            return {}
        
        pkg = json.loads(pkg_file.read_text(encoding='utf-8'))
        
        return {
            "angular_version": pkg.get('dependencies', {}).get('@angular/core', 'unknown'),
            "material": '@angular/material' in pkg.get('dependencies', {}),
            "external_libs": [
                k for k in pkg.get('dependencies', {}).keys()
                if not k.startswith('@angular') and not k.startswith('@types')
            ],
        }
    
    def _analyze_styles(self) -> Dict:
        """Analiza estilos globales."""
        styles_file = self.src_path.parent / "styles.scss"
        
        if not styles_file.exists():
            return {"uses_material": False, "custom_themes": []}
        
        content = styles_file.read_text(encoding='utf-8')
        
        return {
            "uses_material": '@angular/material' in content,
            "uses_m3_theme": 'mat.theme' in content or 'mat.define-light-theme' in content,
            "custom_variables": re.findall(r"\$(\w+):", content),
        }
    
    def _extract_array(self, content: str, key: str) -> List[str]:
        """Extrae un array del metadata de un módulo."""
        match = re.search(rf"{key}:\s*\[([^\]]+)\]", content, re.DOTALL)
        if match:
            return [item.strip() for item in match.group(1).split(',')]
        return []

def main():
    # Path a la app del compañero
    app_path = "C:/Users/pedrodulce/develop/heatmap-app-original"
    
    # Analizar
    analyzer = AngularAppAnalyzer(app_path)
    report = analyzer.analyze()
    
    # Guardar informe
    output_file = "C:/Users/pedrodulce/develop/antigravity/analysis/app-analysis.json"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Informe guardado en: {output_file}")
    print(f"📊 Componentes encontrados: {len(report['components'])}")
    print(f"🔧 Servicios encontrados: {len(report['services'])}")
    print(f"🛣️  Rutas encontradas: {len(report['routing']['routes'])}")

if __name__ == "__main__":
    main()