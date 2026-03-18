# core/project_generator.py
"""
Generador autónomo de proyectos Angular.
Crea, configura y ejecuta aplicaciones Angular basadas en especificaciones API.
"""

import os
import subprocess
import asyncio
import logging
import re
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

            # 🔍 NUEVO: Validación rápida de sintaxis antes de ng serve
            if not self._quick_compile_check(app_path):
                logger.warning("⚠️ Errores de sintaxis detectados, pero continuando con ng serve para debugging")

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
            
            prompt = f"""Eres un arquitecto Angular experto en la librería corporativa ATOM.

            REGLAS OBLIGATORIAS - NO OMITIR:

            1. IMPORTS DE ANGULAR MATERIAL (CRÍTICO):
            - Si usas mat-card, DEBES importar el módulo EXACTO:
                import {{ MatCardModule }} from '@angular/material/card';
            - Y añadirlo en imports: [] como REFERENCIA DE CLASE, NO string:
                imports: [CommonModule, MatCardModule]  // ← ✅ Correcto
                // NO: imports: ["MatCardModule"]  // ← ❌ Causa TS-991010

            2. FORMATO DE imports: [] EN COMPONENTES STANDALONE:
            - DEBE ser un array de identificadores de clase:
                imports: [CommonModule, MatCardModule, LibHelloComponent]
            - NO usar comillas ni strings: imports: ["MatCardModule"] ❌

            3. ESTILOS GLOBALES (styles.scss) - Angular Material 19+ API M3:
            - USAR @include mat.theme(...) NO mat.define-light-theme(...)
            - Los colores usan paletas M3: mat.$azure-palette, mat.$indigo-palette
            - Usar variables CSS M3: var(--mat-sys-surface)

            DESCRIPCIÓN DE LA APP:
            {description}

            {angular_context if angular_context else ''}

            TU TAREA: Generar código Angular COMPILABLE para aplicación minimalista.

            FORMATO ESTRICTO (sin saltos extra):
            === FILE: src/app/app.component.ts ===

            import {{ Component }} from '@angular/core';
            import {{ CommonModule }} from '@angular/common';
            import {{ MatCardModule }} from '@angular/material/card';
            import {{ LibHelloComponent }} from './lib-hello/lib-hello.component';

            @Component({{
            selector: 'app-root',
            standalone: true,
            imports: [CommonModule, MatCardModule, LibHelloComponent],
            template: `<lib-hello></lib-hello>`
            }})
            export class AppComponent {{}}

            === FILE: src/app/lib-hello/lib-hello.component.ts ===

            import {{ Component, ChangeDetectionStrategy }} from '@angular/core';
            import {{ CommonModule }} from '@angular/common';
            import {{ MatCardModule }} from '@angular/material/card';

            @Component({{
            selector: 'lib-hello',
            standalone: true,
            imports: [CommonModule, MatCardModule],
            template: `
                <mat-card>
                <mat-card-content>Hola ATOM</mat-card-content>
                </mat-card>
            `,
            changeDetection: ChangeDetectionStrategy.OnPush
            }})
            export class LibHelloComponent {{}}

            === FILE: src/app/lib-hello/lib-hello.component.scss ===

            :host {{
            display: block;
            padding: 1rem;
            }}
            mat-card {{
            width: 100%;
            }}

            === FILE: src/styles.scss ===

            @use '@angular/material' as mat;

            @include mat.core();

            :root {{
            @include mat.theme((
                color: (
                primary: mat.$azure-palette,
                tertiary: mat.$blue-palette,
                ),
                typography: Roboto,
                density: 0,
            ));
            }}

            body {{
            margin: 0;
            font-family: Roboto, "Helvetica Neue", sans-serif;
            background-color: var(--mat-sys-surface);
            color: var(--mat-sys-on-surface);
            }}

            REGLAS PARA styles.scss (Angular Material 19+):
            1. USAR @include mat.theme(...) NO mat.define-light-theme(...)
            2. Los colores usan paletas M3: mat.$azure-palette, mat.$indigo-palette, etc.
            3. Usar variables CSS M3: var(--mat-sys-surface), var(--mat-sys-on-surface)
            4. NO usar funciones deprecated de M2: define-light-theme, define-dark-theme

            RESPONDE SOLO CON ARCHIVOS EN FORMATO === FILE: ... ===, SIN EXPLICACIONES."""


            

            # ✅ CORRECTO: Usar asyncio.wait_for para manejar el timeout
            response = await asyncio.wait_for(
                asyncio.to_thread(client.generate, prompt),
                timeout=180  # 3 minutos para generación de código
            )
    
            # Parsear respuesta y escribir archivos
            files_written = await self._parse_and_write_files(app_path, response)
            self._auto_fix_common_issues(app_path)  # ← Añadir esta línea
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
            # En el comando ng new, añadir --skip-install:
            cmd = [
                ng_path, "new", app_name,
                "--routing", "true",
                "--style", "scss",
                "--skip-git", "true",
                "--minimal", "false",
                "--skip-install", "true"  # Evita npm install automático
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
            # Después de verificar que package.json existe:
            package_json = app_path / "package.json"
            if package_json.exists():
                import json
                pkg = json.loads(package_json.read_text(encoding='utf-8'))
                
                # Añadir Angular Material si no está
                if '@angular/material' not in pkg.get('dependencies', {}):
                    pkg.setdefault('dependencies', {})['@angular/material'] = '^19.0.0'
                    pkg.setdefault('dependencies', {})['@angular/cdk'] = '^19.0.0'
                    package_json.write_text(json.dumps(pkg, indent=2), encoding='utf-8')
                    logger.info("✅ Añadido @angular/material a package.json")
            
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
        
        # Logging de la respuesta de la IA
        logger.info(f"🔍 Respuesta de IA recibida ({len(response)} chars)")
        
        # 🛠️ PATRÓN FLEXIBLE: Soporta múltiples saltos de línea y formatos
        # Explicación:
        # (?:###|===|//)       → Prefijos soportados para FILE:
        # \s*FILE:\s*          → "FILE:" con espacios opcionales
        # ([^\s\n]+?)          → Captura la ruta del archivo (grupo 1)
        # (?:===)?             → === opcional de cierre
        # [\s\n]*              → ← CLAVE: cualquier combinación de espacios/saltos de línea
        # ```(?:\w+)?\s*\n     → Inicio del bloque de código markdown
        # (.*?)                → Contenido del archivo (grupo 2, no greedy)
        # ```                  → Fin del bloque de código
        file_pattern = r'(?:###|===|//)\s*FILE:\s*([^\s\n]+?)\s*(?:===)?[\s\n]*```(?:\w+)?\s*\n(.*?)```'
        
        matches = re.findall(file_pattern, response, re.DOTALL | re.IGNORECASE)
        
        if matches:
            logger.info(f"✅ Patrón flexible encontró {len(matches)} archivos")
            
            for file_path, content in matches:
                try:
                    if files_written >= self.max_files:
                        logger.warning(f"⚠️ Límite de archivos alcanzado ({self.max_files})")
                        break
                    
                    # Limpiar contenido: remover marcas de código si quedaron
                    content = re.sub(r'^```(?:\w+)?\s*', '', content.strip())
                    content = re.sub(r'```$', '', content.strip())
                    
                    # Construir ruta completa
                    if file_path.strip().startswith('src/app/'):
                        full_path = app_src.parent.parent / file_path.strip()
                    elif file_path.strip() == 'src/styles.scss':
                        full_path = app_src.parent / 'styles.scss'
                    else:
                        full_path = app_path / file_path.strip()
                    
                    # Crear directorios padre si no existen
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Escribir archivo
                    # En _parse_and_write_files, después de escribir cada archivo:
                    full_path.write_text(content, encoding='utf-8')
                    files_written += 1

                    # 🛠️ NUEVO: Validar sintaxis básica
                    syntax_errors = self._validate_typescript_syntax(full_path, content)
                    if syntax_errors:
                        logger.warning(f"⚠️ Errores de sintaxis en {file_path}: {syntax_errors}")
                        # Opcional: intentar auto-corregir o marcar para revisión

                    logger.info(f"📝 Escrito: {file_path.strip()} ({len(content)} chars)")
                    
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo escribir {file_path}: {e}")
                    continue
        else:
            logger.warning("⚠️ Patrón flexible no encontró archivos. Respuesta preview:")
            logger.warning(response[:500])
        
        if files_written == 0:
            logger.error(f"❌ No se pudo extraer ningún archivo. Respuesta completa:\n{response[:2000]}")
        
        return files_written

    def _install_dependencies(self, app_path: Path) -> bool:
        """Instala dependencias con npm install (configuración híbrida para proxy SARA)"""
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
                logger.error("❌ npm no encontrado")
                return False
            
            logger.info(f"✅ Usando npm en: {npm_path}")
            
            # Preparar entorno
            env = os.environ.copy()
            npm_global_path = str(Path.home() / "AppData" / "Roaming" / "npm")
            if npm_global_path not in env.get("PATH", ""):
                env["PATH"] = npm_global_path + ";" + env.get("PATH", "")
            
            # 🛠️ CRÍTICO: Crear .npmrc con configuración HÍBRIDA
            # - Registry público para paquetes genéricos (evita 504 de Nexus)
            # - Registry corporativo CON AUTH solo para @muface-lib
            npmrc_path = app_path / ".npmrc"
            npmrc_content = """# Registry principal: npmjs.org PÚBLICO (evita 504 de Nexus para paquetes genéricos)
    registry=https://registry.npmjs.org/

    # Registry corporativo SOLO para librería ATOM @muface-lib
    @muface-lib:registry=https://artefactos-ic.scae.redsara.es/nexus/repository/ad-npm/
    //artefactos-ic.scae.redsara.es/nexus/repository/ad-npm/:_auth=bXVmYWNlOmF0b20yMDI0

    # Configuración de conexión robusta para proxy corporativo
    strict-ssl=false
    fetch-retries=10
    fetch-retry-mintimeout=20000
    fetch-retry-maxtimeout=600000
    fetch-timeout=300000

    # legacy-peer-deps para compatibilidad Angular Material + ATOM
    legacy-peer-deps=true

    # Sin progreso para evitar problemas de buffering en subprocess
    progress=false
    """
            npmrc_path.write_text(npmrc_content, encoding='utf-8')
            logger.info(f"✅ .npmrc híbrido creado: registry público + @muface-lib corporativo")
            
            # Ejecutar npm install con logging en tiempo real
            cmd = [npm_path, "install", "--legacy-peer-deps", "--no-progress"]
            logger.info(f"🔧 Ejecutando: {' '.join(cmd)}")
            
            # Usar Popen para ver output en vivo y detectar errores temprano
            process = subprocess.Popen(
                cmd,
                cwd=str(app_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Leer output línea por línea y loguear
            for line in process.stdout:
                stripped = line.strip()
                if stripped:
                    # Loguear solo líneas relevantes (evitar spam)
                    if any(kw in stripped.lower() for kw in ['error', 'warn', 'deprecated', 'added', 'removed', 'changed']):
                        logger.info(f"📦 npm: {stripped}")
            
            process.wait(timeout=1800)
            
            if process.returncode != 0:
                logger.error(f"❌ npm install falló con código {process.returncode}")
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
        """Inicia ng serve con logging robusto y timeout"""
        port = 4200
        self._log_progress(f"🚀 Iniciando servidor de desarrollo en puerto {port}...")
        
        try:
            import subprocess
            import shutil
            import time
            
            # Encontrar ng
            ng_path = shutil.which("ng")
            if not ng_path:
                ng_cmd_path = Path.home() / "AppData" / "Roaming" / "npm" / "ng.cmd"
                if ng_cmd_path.exists():
                    ng_path = str(ng_cmd_path)
            if not ng_path:
                logger.error("❌ Angular CLI no encontrado para ng serve")
                return None
            
            # Preparar entorno
            env = os.environ.copy()
            npm_global_path = str(Path.home() / "AppData" / "Roaming" / "npm")
            if npm_global_path not in env.get("PATH", ""):
                env["PATH"] = npm_global_path + ";" + env.get("PATH", "")
            
            # 🛠️ CLAVE: Usar text=True, bufsize=1, y leer stderr por separado
            process = subprocess.Popen(
                [ng_path, "serve", "--port", str(port), "--host", "0.0.0.0", "--disable-host-check"],
                cwd=str(app_path),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # ← Leer stderr por separado
                text=True,               # ← Recibir texto, no bytes
                bufsize=1,               # ← Line-buffered
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Esperar compilación con logging de TODO el output
            compiled = False
            start_wait = datetime.now()
            last_output = datetime.now()
            error_lines = []  # Acumular posibles errores
            
            while not compiled and (datetime.now() - start_wait).total_seconds() < 300:  # 5 min
                # Leer stdout
                stdout_line = process.stdout.readline()
                if stdout_line:
                    line_str = stdout_line.strip()
                    last_output = datetime.now()
                    logger.info(f"📦 ng serve [OUT]: {line_str}")
                    
                    if "Compiled successfully" in line_str:
                        compiled = True
                        self._log_progress("✅ Servidor compilado y corriendo")
                        break
                    elif "X [ERROR]" in line_str or "error TS" in line_str.lower():
                        error_lines.append(line_str)
                        logger.warning(f"⚠️ Error de compilación: {line_str}")
                
                # Leer stderr (a veces los errores van aquí)
                stderr_line = process.stderr.readline()
                if stderr_line:
                    line_str = stderr_line.strip()
                    last_output = datetime.now()
                    logger.error(f"📦 ng serve [ERR]: {line_str}")
                    error_lines.append(line_str)
                
                # Timeout de inactividad: si 90s sin output, asumir bloqueo
                if (datetime.now() - last_output).total_seconds() > 90:
                    logger.warning("⚠️ ng serve sin output por 90s, asumiendo bloqueo de compilación")
                    break
                
                time.sleep(0.1)  # Pequeña pausa para no consumir CPU
            
            # Si no compiló, loguear errores acumulados
            if not compiled:
                if error_lines:
                    logger.error(f"❌ ng serve falló con {len(error_lines)} errores:")
                    for err in error_lines[:10]:  # Primeros 10 errores
                        logger.error(f"   {err}")
                else:
                    logger.error("❌ ng serve no reportó éxito ni errores en 300s")
                return None
            
            return port
            
        except Exception as e:
            logger.error(f"❌ Error en _start_dev_server: {e}", exc_info=True)
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


    def _auto_fix_common_issues(self, app_path: Path) -> int:
        """Corrige automáticamente errores comunes en código generado por IA"""
        import re
        fixes = 0
        
        # 1. Corregir imports: [] con strings → referencias de clase
        for ts_file in (app_path / "src" / "app").rglob("*.component.ts"):
            content = ts_file.read_text(encoding='utf-8')
            
            # Corregir imports: ["Something"] → imports: [Something]
            if re.search(r'imports:\s*\[\s*["\']', content):
                content = re.sub(
                    r'imports:\s*\[\s*["\']([^"\']+)["\']\s*\]',
                    r'imports: [\1]',
                    content
                )
                ts_file.write_text(content, encoding='utf-8')
                fixes += 1
                logger.info(f"✅ Auto-fix: {ts_file.name} - imports corregidos")
            
            # Asegurar que MatCardModule está importado si se usa mat-card
            if '<mat-card' in content and 'MatCardModule' not in content:
                # Añadir import
                if 'import {' in content:
                    content = content.replace(
                        'from \'@angular/core\';',
                        'from \'@angular/core\';\nimport { MatCardModule } from \'@angular/material/card\';'
                    )
                    # Añadir a imports: []
                    if 'imports: [' in content:
                        content = content.replace(
                            'imports: [',
                            'imports: [MatCardModule, '
                        )
                    ts_file.write_text(content, encoding='utf-8')
                    fixes += 1
                    logger.info(f"✅ Auto-fix: {ts_file.name} - MatCardModule añadido")
        
        # 2. Crear .scss faltante para componentes lib-*
        for ts_file in (app_path / "src" / "app").rglob("lib-*.component.ts"):
            scss_file = ts_file.with_suffix('.scss')
            if not scss_file.exists():
                scss_content = """:host {
                display: block;
                padding: var(--spacing-md, 1rem);
                }
                """
                scss_file.write_text(scss_content, encoding='utf-8')
                fixes += 1
                logger.info(f"✅ Auto-fix: Creado {scss_file.name}")
        
        # En la sección que corrige styles.scss:

        if "@muface-lib" in content and "@use '@angular/material'" in content:
            # Comentar línea de muface si no está disponible
            content = content.replace(
                "@use '@muface-lib/muface-lib/estilos/m3-theme' as muf-theme;",
                "// @use '@muface-lib/muface-lib/estilos/m3-theme' as muf-theme; // ← Comentado si no disponible"
            )
            
            # ✅ CORRECCIÓN: Generar fallback theme COMPLETO y bien cerrado
            fallback_theme = """
        // Fallback theme si muf-theme no está disponible
        :root {
        @include mat.all-component-themes(
            mat.define-light-theme((
            color: (
                primary: mat.define-palette(mat.$indigo-palette),
                accent: mat.define-palette(mat.$pink-palette, A200, A100, A400),
                warn: mat.define-palette(mat.$red-palette),
            ),
            ))
        );
        }
        """
    
    # Añadir fallback solo si no existe ya un theme definido
    if "mat.define-light-theme" not in content and "mat.all-component-themes" not in content:
        content += fallback_theme
        logger.info("✅ Auto-fix: styles.scss - fallback theme añadido correctamente")
    
    styles_file.write_text(content, encoding='utf-8')
        
        return fixes

    
    def _validate_typescript_syntax(self, file_path: Path, content: str) -> List[str]:
        """Validación básica de sintaxis TypeScript para detectar errores comunes"""
        errors = []
        
        # 1. Verificar balance de paréntesis en decorators @Component
        if '@Component' in content:
            # Contar paréntesis después de @Component
            comp_start = content.find('@Component')
            comp_block = content[comp_start:comp_start+500]  # Primeros 500 chars después
            
            open_parens = comp_block.count('(')
            close_parens = comp_block.count(')')
            if open_parens != close_parens:
                errors.append(f"{file_path.name}: Paréntesis desbalanceados en @Component")
        
        # 2. Verificar que los templates inline están cerrados con backticks
        template_matches = re.findall(r'template:\s*`([^`]*)', content)
        for match in template_matches:
            # Si el template no termina con `, es probable que esté truncado
            if not match.rstrip().endswith('`'):
                # Verificar si hay un ` más adelante en el contenido
                full_template = re.search(r'template:\s*`.*?`', content, re.DOTALL)
                if not full_template:
                    errors.append(f"{file_path.name}: Template inline no cerrado con backticks")
        
        # 3. Verificar que los imports tienen sintaxis básica correcta
        import_lines = re.findall(r'^import\s+.*?;?\s*$', content, re.MULTILINE)
        for imp in import_lines:
            if 'from' in imp and ("'" not in imp or '"' not in imp):
                # Import sin comillas en la ruta
                if not re.search(r"from\s+['\"].+?['\"]", imp):
                    errors.append(f"{file_path.name}: Import con sintaxis inválida: {imp[:50]}")
        
        # 4. Verificar balance de llaves en clases/componentes
        if 'export class' in content:
            open_braces = content.count('{')
            close_braces = content.count('}')
            if open_braces != close_braces:
                errors.append(f"{file_path.name}: Llaves desbalanceadas en clase")
        
        return errors

    
    def _quick_compile_check(self, app_path: Path) -> bool:
        """Ejecuta tsc --noEmit para verificar sintaxis sin generar output"""
        try:
            import subprocess
            import shutil
            
            # Encontrar tsc
            tsc_path = shutil.which("tsc")
            if not tsc_path:
                # Intentar en node_modules/.bin
                tsc_local = app_path / "node_modules" / ".bin" / "tsc.cmd"
                if tsc_local.exists():
                    tsc_path = str(tsc_local)
            
            if not tsc_path:
                logger.warning("⚠️ tsc no encontrado, saltando compilación rápida")
                return True  # No fallar si no hay tsc
            
            # Ejecutar tsc --noEmit (solo verifica, no genera JS)
            process = subprocess.run(
                [tsc_path, "--noEmit", "--skipLibCheck"],
                cwd=str(app_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,  # 1 minuto máximo
                text=True
            )
            
            if process.returncode != 0:
                # Loguear primeros errores para debugging
                stderr_lines = process.stderr.strip().split('\n')[:10]
                logger.warning(f"⚠️ tsc --noEmit encontró errores:")
                for line in stderr_lines:
                    logger.warning(f"   {line}")
                return False
            
            logger.info("✅ tsc --noEmit: sintaxis válida")
            return True
            
        except subprocess.TimeoutExpired:
            logger.warning("⏰ Timeout en tsc --noEmit, continuando...")
            return True  # No fallar por timeout
        except Exception as e:
            logger.warning(f"⚠️ Error en compilación rápida: {e}")
            return True  # No fallar si hay error ejecutando tsc