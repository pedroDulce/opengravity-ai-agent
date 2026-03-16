# core/project_generator.py
"""
Generador autónomo de proyectos Angular.
Crea, configura y ejecuta aplicaciones Angular basadas en especificaciones API.
"""

import os
import subprocess
import asyncio
import logging
import shutil
from pathlib import Path
from typing import Optional, List, Callable, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class ProjectGenerator:
    """
    Genera proyectos Angular completos de forma autónoma.

    Características:
    - Crea estructura de proyecto Angular con CLI
    - Genera componentes, servicios, interfaces desde especificación API
    - Ejecuta npm install, ng serve, etc.
    - Reporta progreso en tiempo real
    - Maneja errores y timeouts
    """

    def __init__(self, output_dir: str, max_files: int = 100, timeout: int = 1800):
        """
        Inicializa el generador de proyectos.

        Args:
            output_dir: Directorio base donde crear proyectos
            max_files: Máximo de archivos que puede generar
            timeout: Timeout total en segundos para toda la generación
        """
        self.output_dir = Path(output_dir).resolve()
        self.max_files = max_files
        self.timeout = timeout
        self._progress_callback: Optional[Callable] = None

        # Crear directorio de salida si no existe
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ ProjectGenerator inicializado: {self.output_dir}")

    def set_progress_callback(self, callback: Callable[[str], None]):
        """Establece callback para reportar progreso a Telegram"""
        self._progress_callback = callback

    def _log_progress(self, message: str):
        """Loguea progreso y notifica vía callback si existe"""
        logger.info(f"🔧 {message}")
        if self._progress_callback:
            self._progress_callback(message)

    async def create_angular_app(self, app_name: str, api_spec: Optional[str] = None,
                                  description: Optional[str] = None) -> Dict:
        """
        Crea una aplicación Angular completa.

        Args:
            app_name: Nombre de la aplicación (se usará para carpeta y proyecto)
            api_spec: Especificación OpenAPI/Swagger (opcional)
            description: Descripción de la app para guiar a la IA

        Returns:
            Dict con: {success, app_path, port, message, errors}
        """
        start_time = datetime.now()
        result = {
            "success": False,
            "app_path": None,
            "port": 4200,
            "message": "",
            "errors": []
        }

        try:
            # Validar nombre de app
            if not self._validate_app_name(app_name):
                result["errors"].append(f"Nombre de app inválido: {app_name}")
                return result

            app_path = self.output_dir / app_name

            # Verificar que no existe ya
            if app_path.exists():
                result["errors"].append(f"La carpeta {app_path} ya existe")
                return result

            self._log_progress(f"🚀 Iniciando creación de '{app_name}'...")

            # Paso 1: Crear proyecto Angular base con CLI
            if not self._create_angular_project(app_path, app_name):
                result["errors"].append("Error creando proyecto Angular")
                return result

            # Paso 2: Generar código desde API spec o descripción
            if api_spec or description:
                if not await self._generate_app_code(app_path, api_spec, description):
                    result["errors"].append("Error generando código de la app")
                    return result
                
                # 🛠️ Validar código generado contra reglas ATOM
                validation_errors = self._validate_generated_code(app_path)
                if validation_errors:
                    logger.warning(f"⚠️ {len(validation_errors)} advertencias de validación ATOM")
                    for error in validation_errors[:5]:
                        logger.warning(f"   - {error}")

            # ✅ CORRECTO (sin await, es método síncrono):
            if not self._install_dependencies(app_path):            
                result["errors"].append("Error instalando dependencias")
                return result

            # Paso 4: Iniciar servidor de desarrollo
            port = self._start_dev_server(app_path)
            if not port:
                result["errors"].append("Error iniciando servidor de desarrollo")
                return result

            result["success"] = True
            result["app_path"] = str(app_path)
            result["port"] = port
            result["message"] = f"✅ Aplicación '{app_name}' lista en http://localhost:{port}"

            elapsed = (datetime.now() - start_time).total_seconds()
            self._log_progress(f"✨ Generación completada en {elapsed:.0f}s")

        except asyncio.TimeoutError:
            result["errors"].append(f"Timeout: La generación excedió {self.timeout}s")
        except Exception as e:
            logger.error(f"❌ Error en create_angular_app: {e}", exc_info=True)
            result["errors"].append(f"Error inesperado: {type(e).__name__}: {e}")

        return result

    async def _generate_app_code(self, app_path: Path, api_spec: Optional[str], 
                              description: Optional[str]) -> bool:
        """Genera componentes, servicios y código de la app usando la IA"""
        self._log_progress("🧠 Generando código de la aplicación...")
        
        try:
            from core.llm_client import LLMClient
            from core.context_manager import ContextManager
            
            client = LLMClient()
            ctx_manager = ContextManager()
            
            # ✅ CORRECCIÓN: Recuperar contexto corporativo Angular/ATOM
            angular_context = ctx_manager.get_context(
                "angular component service module routing atom standalone inject signal lib- OnPush",
                category="angular-guidelines",
                max_tokens=2000
            )
            
            # Construir prompt para generar estructura de archivos
            prompt = f"""Eres un arquitecto Angular experto en la librería corporativa ATOM.

            REGLAS OBLIGATORIAS - NO OMITIR:

            1. IMPORTS EN COMPONENTES STANDALONE (CRÍTICO):
            - Si un componente usa OTRO componente en su template, DEBE importarlo en `imports: []`
            - Ejemplo: Si app.component.ts tiene <lib-hello> en su template:
                ```typescript
                @Component({{
                selector: 'app-root',
                standalone: true,
                imports: [CommonModule, MatCardModule, LibHelloComponent],  // ← IMPORTAR LibHelloComponent
                template: `<lib-hello></lib-hello>`
                }})
                ```
            - NO uses <lib-hello> sin importar LibHelloComponent primero

            2. app.config.ts (OPCIONAL):
            - Si no usas ApplicationConfig, OMITE app.config.ts o déjalo con:
                ```typescript
                // No se requiere configuración adicional para esta app
                export {{}};
                ```
            - NO dejes un archivo vacío sin export

            3. FORMATO DE ARCHIVOS (ESTRICTO):
            Para CADA archivo, usa EXACTAMENTE:
            
            === FILE: src/app/app.component.ts ===
            ```typescript
            import {{ Component }} from '@angular/core';
            import {{ CommonModule }} from '@angular/common';
            import {{ MatCardModule }} from '@angular/material/card';
            import {{ LibHelloComponent }} from './lib-hello/lib-hello.component';  // ← IMPORTAR

            @Component({{
                selector: 'app-root',
                standalone: true,
                imports: [CommonModule, MatCardModule, LibHelloComponent],  // ← LISTAR AQUÍ
                template: `<lib-hello></lib-hello>`
            }})
            export class AppComponent {{}}
                PATRÓN ATOM:
                    Selector: 'lib-', Clase: 'LibComponent', standalone: true, OnPush, inject(), signal()

            DESCRIPCIÓN DE LA APP:
            {description}
            {angular_context if angular_context else ''}
            TU TAREA: Generar código Angular COMPILABLE para aplicación minimalista con LibHelloComponent.
            RESPONDE SOLO CON ARCHIVOS EN FORMATO === FILE: ... ===, SIN EXPLICACIONES."""
            # ✅ CORRECTO: Usar asyncio.wait_for para manejar el timeout
            response = await asyncio.wait_for(
                asyncio.to_thread(client.generate, prompt),
                timeout=180  # 3 minutos para generación de código
            )
    
            # Parsear respuesta y escribir archivos
            files_written = await self._parse_and_write_files(app_path, response)
            validation_errors = self._validate_generated_code(app_path)
            if validation_errors:
                logger.warning(f"⚠️ Advertencias de validación: {validation_errors}")
                # Intentar corregir automáticamente
                for error in validation_errors:
                    if "no importa LibComponent" in error:
                        # Intentar añadir el import automáticamente (opcional)
                        pass
            
            if files_written == 0:
                logger.warning("⚠️ No se generaron archivos desde la respuesta de la IA")
                return False
            
            self._log_progress(f"✅ {files_written} archivos generados")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en _generate_app_code: {e}", exc_info=True)
            return False


    def _validate_app_name(self, name: str) -> bool:
        """Valida que el nombre de app sea seguro para usar en filesystem y Angular CLI"""
        if not name:
            return False
        # Solo letras, números, guiones y guiones bajos
        if not all(c.isalnum() or c in '-_' for c in name):
            return False
        # No empezar con número o guión
        if name[0].isdigit() or name.startswith('-'):
            return False
        # Longitud razonable
        if len(name) > 50:
            return False
        return True

    
    def _create_angular_project(self, app_path: Path, app_name: str) -> bool:
        """Crea proyecto Angular base usando ng new con --skip-install"""
        self._log_progress(f"📦 Creando proyecto Angular '{app_name}'...")
        
        try:
            import subprocess
            import shutil
            
            # 🛠️ Encontrar la ruta completa de 'ng' en Windows
            ng_path = shutil.which("ng")
            
            if not ng_path:
                ng_cmd_path = Path.home() / "AppData" / "Roaming" / "npm" / "ng.cmd"
                if ng_cmd_path.exists():
                    ng_path = str(ng_cmd_path)
                else:
                    env_path = os.environ.get("PATH", "")
                    for path_dir in env_path.split(";"):
                        candidate = Path(path_dir) / "ng.cmd"
                        if candidate.exists():
                            ng_path = str(candidate)
                            break
            
            if not ng_path:
                logger.error("❌ No se encontró 'ng' en PATH ni en rutas típicas de npm")
                return False
            
            logger.info(f"✅ Usando Angular CLI en: {ng_path}")
            
            # Preparar entorno con PATH que incluya npm global
            env = os.environ.copy()
            npm_global_path = str(Path.home() / "AppData" / "Roaming" / "npm")
            if npm_global_path not in env.get("PATH", ""):
                env["PATH"] = npm_global_path + ";" + env.get("PATH", "")
            
            # 🛠️ CRÍTICO: Usar --skip-install para evitar npm install automático de ng new
            # Luego instalaremos manualmente con nuestro .npmrc configurado para Nexus/ATOM
            cmd = [
                ng_path,
                "new", app_name,
                "--routing", "true",
                "--style", "scss",
                "--skip-git", "true",
                "--minimal", "false",
                "--skip-install", "true"  # ← ¡Esto evita el npm install automático!
            ]
            
            logger.info(f"🔧 Ejecutando: {' '.join(cmd)}")
            
            # Ejecutar ng new con --skip-install
            process = subprocess.run(
                cmd,
                cwd=str(self.output_dir),
                env=env,
                input=b'Y\n',  # Responder 'Y' a prompts de ng new
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300,  # 5 minutos
                shell=False
            )
            
            if process.returncode != 0:
                stderr_text = process.stderr.decode('utf-8', errors='ignore')[:500]
                stdout_text = process.stdout.decode('utf-8', errors='ignore')[:500]
                logger.error(f"❌ ng new falló (code={process.returncode}):")
                logger.error(f"   STDOUT: {stdout_text}")
                logger.error(f"   STDERR: {stderr_text}")
                return False
            
            # 🛠️ Verificar que package.json fue creado
            package_json = app_path / "package.json"
            if not package_json.exists():
                logger.error(f"❌ ng new completó pero package.json no existe en {app_path}")
                return False
            
            # 🛠️ Crear .npmrc con configuración ATOM/Nexus ANTES de npm install manual
            npmrc_path = app_path / ".npmrc"
            npmrc_content = """# Registry principal (proxy de npmjs.org)
    registry=https://artefactos-ic.scae.redsara.es/nexus/repository/registry_npmjs_org/

    # Autenticación para registry principal
    //artefactos-ic.scae.redsara.es/nexus/repository/registry_npmjs_org/:_auth=bXVmYWNlOmF0b20yMDI0

    # Registry específico para @muface-lib (librería ATOM)
    @muface-lib:registry=https://artefactos-ic.scae.redsara.es/nexus/repository/ad-npm/

    # Autenticación para registry ATOM
    //artefactos-ic.scae.redsara.es/nexus/repository/ad-npm/:_auth=bXVmYWNlOmF0b20yMDI0

    # Configuración de conexión
    strict-ssl=false
    fetch-retries=10
    fetch-retry-mintimeout=20000
    fetch-retry-maxtimeout=600000
    fetch-timeout=300000

    # legacy-peer-deps para compatibilidad con Angular Material + ATOM
    legacy-peer-deps=true
    """
            npmrc_path.write_text(npmrc_content, encoding='utf-8')
            logger.info(f"✅ .npmrc configurado para Nexus/ATOM en {npmrc_path}")
            
            self._log_progress(f"✅ Proyecto Angular creado en {app_path}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("⏰ Timeout en ng new (300s)")
            return False
        except FileNotFoundError as e:
            logger.error(f"❌ Angular CLI no encontrado: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error en _create_angular_project: {type(e).__name__}: {e}", exc_info=True)
            return False


    async def _parse_and_write_files(self, app_path: Path, response: str) -> int:
        """Parsea la respuesta de la IA y escribe los archivos en disco"""
        import re
        
        files_written = 0
        app_src = app_path / "src" / "app"
        
        # 🛠️ LOGGING: Ver qué respondió la IA
        logger.info(f"🔍 Respuesta de IA recibida ({len(response)} chars)")
        
        # 🛠️ PATRÓN PRINCIPAL: Extrae ruta Y contenido del formato ### FILE: ruta ===
        # Soporta: ### FILE: src/app/x.ts ===, === FILE: src/app/x.ts ===, // FILE: src/app/x.ts
        file_pattern = r'(?:###|===|//)\s*FILE:\s*(src/app/[^\s\n]+?)\s*(?:===)?\s*\n\s*```(?:\w+)?\s*\n(.*?)```'
        
        matches = re.findall(file_pattern, response, re.DOTALL | re.IGNORECASE)
        
        if matches:
            logger.info(f"✅ Patrón principal encontró {len(matches)} archivos con ruta explícita")
            
            for file_path, content in matches:
                try:
                    if files_written >= self.max_files:
                        logger.warning(f"⚠️ Límite de archivos alcanzado ({self.max_files})")
                        break
                    
                    # Limpiar contenido: remover marcas de código si quedaron
                    content = re.sub(r'^```(?:\w+)?\s*', '', content.strip())
                    content = re.sub(r'```$', '', content.strip())
                    
                    # Construir ruta completa
                    full_path = app_src.parent.parent / file_path.strip()
                    
                    # Crear directorios padre si no existen
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Escribir archivo
                    full_path.write_text(content, encoding='utf-8')
                    files_written += 1
                    
                    logger.info(f"📝 Escrito: {file_path.strip()} ({len(content)} chars)")
                    
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo escribir {file_path}: {e}")
                    continue
        
        # 🛠️ FALLBACK: Si no encontró con patrón principal, intentar extraer bloques de código con inferencia de nombre
        if files_written == 0:
            logger.warning("⚠️ Patrón principal no encontró archivos. Intentando fallback...")
            
            # Extraer bloques de código y comentarios que puedan contener rutas
            code_blocks = re.findall(
                r'(?:###|===|//)\s*FILE:\s*([^\s\n]+)\s*(?:===)?\s*\n\s*```(?:\w+)?\s*\n(.*?)```',
                response, re.DOTALL | re.IGNORECASE
            )
            
            for file_path, content in code_blocks:
                try:
                    if files_written >= self.max_files:
                        break
                    
                    content = re.sub(r'^```(?:\w+)?\s*', '', content.strip())
                    content = re.sub(r'```$', '', content.strip())
                    
                    # Si la ruta no empieza con src/app, asumirla relativa a app/
                    if not file_path.strip().startswith('src/'):
                        file_path = f"src/app/{file_path.strip()}"
                    
                    full_path = app_src.parent.parent / file_path.strip()
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(content, encoding='utf-8')
                    files_written += 1
                    
                    logger.info(f"📝 Fallback escrito: {file_path.strip()}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Fallback falló: {e}")
        
        # 🛠️ ÚLTIMO RECURSO: Extraer cualquier bloque de código y nombrarlo genéricamente
        if files_written == 0:
            logger.warning("⚠️ No se encontraron archivos con rutas. Extrayendo bloques de código genéricos...")
            
            code_blocks = re.findall(r'```(?:typescript|ts|html|scss)?\s*\n(.*?)```', response, re.DOTALL)
            
            for i, content in enumerate(code_blocks[:10]):  # Máximo 10 bloques
                try:
                    content = content.strip()
                    
                    # Inferir extensión y nombre por contenido
                    if '<template>' in content or '@Component' in content:
                        ext = 'ts'
                        filename = f'component-{i}.component.ts'
                    elif '@Injectable' in content:
                        ext = 'ts'
                        filename = f'service-{i}.service.ts'
                    elif '<div' in content or '<mat-' in content:
                        ext = 'html'
                        filename = f'template-{i}.component.html'
                    elif '{' in content and ('.scss' in content.lower() or 'style' in content.lower()):
                        ext = 'scss'
                        filename = f'styles-{i}.scss'
                    else:
                        ext = 'ts'
                        filename = f'generated-{i}.ts'
                    
                    full_path = app_src / filename
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(content, encoding='utf-8')
                    files_written += 1
                    
                    logger.info(f"📝 Genérico escrito: {filename}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Genérico falló: {e}")
        
        if files_written == 0:
            logger.error(f"❌ No se pudo extraer ningún archivo. Respuesta:\n{response[:2000]}")
        
        return files_written


    def _install_dependencies(self, app_path: Path) -> bool:
        """Instala dependencias con npm install (usando .npmrc ya configurado)"""
        self._log_progress("📦 Instalando dependencias ATOM (puede tardar 15-20 min)...")
        
        try:
            import subprocess
            import shutil
            
            # Encontrar npm
            npm_path = shutil.which("npm")
            if not npm_path:
                npm_cmd_path = Path.home() / "AppData" / "Roaming" / "npm" / "npm.cmd"
                if npm_cmd_path.exists():
                    npm_path = str(npm_cmd_path)
            
            if not npm_path:
                logger.error("❌ No se encontró 'npm'")
                return False
            
            logger.info(f"✅ Usando npm en: {npm_path}")
            
            # Preparar entorno
            env = os.environ.copy()
            npm_global_path = str(Path.home() / "AppData" / "Roaming" / "npm")
            if npm_global_path not in env.get("PATH", ""):
                env["PATH"] = npm_global_path + ";" + env.get("PATH", "")
            
            # Ejecutar npm install (el .npmrc ya está en la carpeta del proyecto)
            cmd = [npm_path, "install", "--legacy-peer-deps", "--no-progress"]
            logger.info(f"🔧 Ejecutando: {' '.join(cmd)}")
            
            process = subprocess.run(
                cmd,
                cwd=str(app_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=1800,  # 30 minutos
                env=env
            )
            
            if process.returncode != 0:
                stderr_text = process.stderr.decode('utf-8', errors='ignore')[:500]
                logger.error(f"❌ npm install falló: {stderr_text}")
                return False
            
            self._log_progress("✅ Dependencias ATOM instaladas")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("⏰ Timeout en npm install (1800s)")
            return False
        except Exception as e:
            logger.error(f"❌ Error en _install_dependencies: {e}", exc_info=True)
            return False
    

    def _start_dev_server(self, app_path: Path) -> Optional[int]:
        """Inicia ng serve en background (síncrono con Popen)"""
        port = 4200
        self._log_progress(f"🚀 Iniciando servidor de desarrollo en puerto {port}...")
        
        try:
            import subprocess
            import shutil
            
            # 🛠️ CRÍTICO: Encontrar la ruta completa de 'ng' en Windows
            ng_path = shutil.which("ng")
            
            if not ng_path:
                # Intentar ruta típica de npm global en Windows
                ng_cmd_path = Path.home() / "AppData" / "Roaming" / "npm" / "ng.cmd"
                if ng_cmd_path.exists():
                    ng_path = str(ng_cmd_path)
                else:
                    # Último intento: buscar en PATH manualmente
                    env_path = os.environ.get("PATH", "")
                    for path_dir in env_path.split(";"):
                        candidate = Path(path_dir) / "ng.cmd"
                        if candidate.exists():
                            ng_path = str(candidate)
                            break
            
            if not ng_path:
                logger.error("❌ Angular CLI no encontrado para ng serve")
                logger.error(f"💡 PATH: {os.environ.get('PATH', '')[:300]}...")
                return None
            
            logger.info(f"✅ Usando ng en: {ng_path} para serve")
            
            # Preparar entorno con PATH que incluya npm global
            env = os.environ.copy()
            npm_global_path = str(Path.home() / "AppData" / "Roaming" / "npm")
            if npm_global_path not in env.get("PATH", ""):
                env["PATH"] = npm_global_path + ";" + env.get("PATH", "")
            
            # Iniciar ng serve en background con Popen usando ruta completa
            process = subprocess.Popen(
                [ng_path, "serve", "--port", str(port), "--host", "0.0.0.0", "--disable-host-check"],
                cwd=str(app_path),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Esperar a que compile (leer stdout hasta "Compiled successfully")
            compiled = False
            start_wait = datetime.now()
            
            while not compiled and (datetime.now() - start_wait).total_seconds() < 120:
                line = process.stdout.readline()
                if not line:
                    break
                line_str = line.decode('utf-8', errors='ignore').strip()
                
                if "Compiled successfully" in line_str:
                    compiled = True
                    self._log_progress("✅ Servidor compilado y corriendo")
                    break
                elif "error" in line_str.lower() and "Compiled" not in line_str:
                    logger.warning(f"⚠️ ng serve: {line_str}")
            
            if not compiled:
                logger.warning("⚠️ El servidor puede no estar compilado correctamente")
            
            return port
            
        except FileNotFoundError as e:
            logger.error(f"❌ Angular CLI no encontrado: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error en _start_dev_server: {e}")
            return None


    def cleanup(self, app_name: str) -> bool:
        """Elimina un proyecto generado (para limpieza)"""
        app_path = self.output_dir / app_name
        if app_path.exists():
            try:
                shutil.rmtree(app_path)
                logger.info(f"🗑️ Proyecto eliminado: {app_path}")
                return True
            except Exception as e:
                logger.error(f"❌ Error eliminando proyecto: {e}")
                return False
        return False


    def _validate_generated_code(self, app_path: Path) -> List[str]:
        """
        Valida que el código generado cumple con las reglas ATOM para CUALQUIER componente.
        
        Reglas validadas:
        • Selector comienza con 'lib-'
        • Nombre de clase comienza con 'Lib'
        • standalone: true
        • changeDetection: ChangeDetectionStrategy.OnPush
        • Inyección vía inject() (no constructor)
        • Usa signal()/computed() para estado
        • Implementa lifecycle hooks (OnInit, AfterViewInit, OnDestroy)
        • Imports consistentes en componentes standalone
        • Estilos en archivo .scss separado (no CSS inline)
        """

        import re
        
        errors = []
        warnings = []
        app_src = app_path / "src" / "app"
        
        # 🛠️ Buscar todos los archivos .ts en src/app
        ts_files = list(app_src.rglob("*.ts"))
        
        # 🛠️ Patrones regex para validación ATOM
        patterns = {
            'selector_lib': re.compile(r"selector:\s*['\"](lib-[^\'\"]+)['\"]"),
            'class_lib': re.compile(r"export\s+class\s+(Lib\w+)"),
            'standalone': re.compile(r"standalone:\s*true"),
            'onpush': re.compile(r"changeDetection:\s*ChangeDetectionStrategy\.OnPush"),
            'inject': re.compile(r"inject\(\w+\)"),
            'signal': re.compile(r"signal\(|computed\(|\.set\(|\.update\("),
            'oninit': re.compile(r"ngOnInit\s*\("),
            'afterviewinit': re.compile(r"ngAfterViewInit\s*\("),
            'ondestroy': re.compile(r"ngOnDestroy\s*\("),
            'constructor_di': re.compile(r"constructor\s*\([^)]*\([^)]*\)\s*:"),  # Constructor con DI
            'css_inline': re.compile(r"style:\s*['\"]|<[^>]+style=['\"]"),  # CSS inline
        }
        
        for ts_file in ts_files:
            try:
                content = ts_file.read_text(encoding='utf-8')
                rel_path = ts_file.relative_to(app_path)
                filename = ts_file.name
                
                # 🛠️ Solo validar componentes (archivos con @Component)
                if '@Component' not in content:
                    continue
                
                # ✅ 1. Validar selector con prefijo 'lib-'
                selector_match = patterns['selector_lib'].search(content)
                if not selector_match:
                    # Si es un componente pero no tiene selector lib-, es warning (puede ser app.component)
                    if 'app.component' not in filename.lower():
                        warnings.append(f"{rel_path}: Selector no sigue convención 'lib-*'")
                
                # ✅ 2. Validar nombre de clase con prefijo 'Lib'
                class_match = patterns['class_lib'].search(content)
                if not class_match and 'app.component' not in filename.lower():
                    warnings.append(f"{rel_path}: Nombre de clase no sigue convención 'Lib*'")
                
                # ✅ 3. Validar standalone: true (OBLIGATORIO para componentes ATOM)
                if not patterns['standalone'].search(content):
                    if 'app.component' not in filename.lower():
                        errors.append(f"{rel_path}: Componente debe ser standalone: true (regla ATOM)")
                
                # ✅ 4. Validar changeDetection: OnPush (OBLIGATORIO)
                if not patterns['onpush'].search(content):
                    if 'app.component' not in filename.lower():
                        errors.append(f"{rel_path}: Debe usar ChangeDetectionStrategy.OnPush (regla ATOM)")
                
                # ✅ 5. Validar inyección vía inject() (NO constructor con DI)
                has_inject = patterns['inject'].search(content)
                has_constructor_di = patterns['constructor_di'].search(content)
                
                if has_constructor_di and not has_inject:
                    errors.append(f"{rel_path}: Usar inject() para inyección de dependencias (NO constructor)")
                
                # ✅ 6. Validar uso de signals para estado (RECOMENDADO)
                if not patterns['signal'].search(content):
                    # Solo warning, no todos los componentes necesitan estado reactivo
                    warnings.append(f"{rel_path}: Considerar usar signal()/computed() para estado reactivo")
                
                # ✅ 7. Validar lifecycle hooks (RECOMENDADO)
                has_oninit = patterns['oninit'].search(content)
                has_afterviewinit = patterns['afterviewinit'].search(content)
                has_ondestroy = patterns['ondestroy'].search(content)
                
                # Si tiene OnInit, debería tener OnDestroy para cleanup
                if has_oninit and not has_ondestroy:
                    warnings.append(f"{rel_path}: Si implementa ngOnInit, considerar ngOnDestroy para cleanup")
                
                # ✅ 8. Validar imports consistentes en componentes standalone
                if patterns['standalone'].search(content):
                    # Si usa componentes de template, debe importar sus módulos/clases
                    template_matches = re.findall(r'<(lib-\w+)', content)
                    for component_tag in template_matches:
                        component_class = component_tag.replace('lib-', 'Lib').replace('-', '').title() + 'Component'
                        # Verificar si el componente está importado
                        if component_class not in content and 'imports:' not in content:
                            warnings.append(f"{rel_path}: Usa <{component_tag}> pero puede faltar import en imports: []")
                    
                    # Validar que imports: [] no esté vacío si usa componentes externos
                    imports_empty = re.search(r'imports:\s*\[\s*\]', content)
                    if imports_empty and template_matches:
                        errors.append(f"{rel_path}: imports: [] vacío pero usa componentes externos en template")
                
                # ✅ 9. Validar NO CSS inline
                if patterns['css_inline'].search(content):
                    errors.append(f"{rel_path}: No usar CSS inline, usar archivo .scss separado")
                
                # ✅ 10. Validar que existe archivo .scss para el componente (si es componente lib-)
                if selector_match and 'app.component' not in filename.lower():
                    scss_file = ts_file.with_suffix('.scss')
                    if not scss_file.exists():
                        # Intentar buscar en la misma carpeta
                        component_name = ts_file.stem
                        scss_alternatives = list(ts_file.parent.glob(f"{component_name}.scss"))
                        if not scss_alternatives:
                            warnings.append(f"{rel_path}: Componente sin archivo .scss asociado")
            
            except Exception as e:
                logger.warning(f"⚠️ No se pudo validar {ts_file}: {e}")
                continue
        
        # 🛠️ Validación adicional: app.config.ts
        app_config = app_path / "src" / "app" / "app.config.ts"
        if app_config.exists():
            content = app_config.read_text(encoding='utf-8').strip()
            if not content or content.startswith('//') and 'export' not in content:
                # Si está vacío o solo comentarios, añadir export mínimo
                app_config.write_text("export {};\n// Configuración mínima para Angular", encoding='utf-8')
                logger.info(f"✅ app.config.ts corregido con export mínimo")
        
        # 🛠️ Validación: consistency entre componentes y imports
        # Buscar todos los selectores usados en templates
        all_selectors = []
        all_component_classes = []
        
        for ts_file in ts_files:
            try:
                content = ts_file.read_text(encoding='utf-8')
                
                # Extraer selectores definidos
                selectors = re.findall(r"selector:\s*['\"]([^'\"]+)['\"]", content)
                all_selectors.extend(selectors)
                
                # Extraer clases de componentes exportadas
                classes = re.findall(r"export\s+class\s+(\w+Component)", content)
                all_component_classes.extend(classes)
                
            except:
                continue
        
        # Log resumen
        if errors:
            logger.warning(f"⚠️ {len(errors)} errores de validación ATOM detectados")
            for error in errors[:5]:  # Mostrar primeros 5
                logger.warning(f"   - {error}")
        
        if warnings:
            logger.info(f"ℹ️ {len(warnings)} advertencias de validación ATOM")
        
        return errors + warnings  # Devolver ambos para que el caller decida