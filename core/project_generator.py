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
                    # ✅ CORRECTO:
                    result["errors"].append("Error generando código de la app")
                    return result

            # ✅ CORRECTO (sin await, es método síncrono):
            if not self._install_dependencies(app_path):            
                result["errors"].append("Error instalando dependencias")
                return result

            # Paso 4: Iniciar servidor de desarrollo
            port = await self._start_dev_server(app_path)
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
        """Crea proyecto Angular base usando ng new (versión corregida para Windows)"""
        self._log_progress(f"📦 Creando proyecto Angular '{app_name}'...")
        
        try:
            import subprocess
            import shutil
            
            # 🛠️ CRÍTICO: Encontrar la ruta completa de 'ng' en Windows
            # Primero intentar con shutil.which (busca en PATH)
            ng_path = shutil.which("ng")
            
            # Si no lo encuentra, usar ruta típica de npm global en Windows
            if not ng_path:
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
                logger.error("❌ No se encontró 'ng' en PATH ni en rutas típicas de npm")
                logger.error(f"💡 PATH actual: {os.environ.get('PATH', '')[:200]}...")
                return False
            
            logger.info(f"✅ Usando Angular CLI en: {ng_path}")
            
            # Preparar entorno con PATH que incluya npm global
            env = os.environ.copy()
            npm_global_path = str(Path.home() / "AppData" / "Roaming" / "npm")
            if npm_global_path not in env.get("PATH", ""):
                env["PATH"] = npm_global_path + ";" + env.get("PATH", "")
            
            # Comando ng new con ruta completa al ejecutable
            cmd = [
                ng_path,  # ← Usar ruta completa en lugar de solo "ng"
                "new", app_name,
                "--routing", "true",
                "--style", "scss",
                "--skip-git", "true",
                "--minimal", "false"
            ]
            
            # Ejecutar con subprocess.run (síncrono para evitar NotImplementedError)
            process = subprocess.run(
                cmd,
                cwd=str(self.output_dir),
                env=env,
                input=b'Y\n',  # Responder 'Y' a prompts de ng new
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300,  # 5 minutos timeout
                shell=False   # ← Importante: False para seguridad
            )
            
            # Logging mejorado para debug
            if process.returncode != 0:
                stderr_text = process.stderr.decode('utf-8', errors='ignore')[:500]
                stdout_text = process.stdout.decode('utf-8', errors='ignore')[:500]
                logger.error(f"❌ ng new falló (code={process.returncode}):")
                logger.error(f"   STDOUT: {stdout_text}")
                logger.error(f"   STDERR: {stderr_text}")
                return False
            
            self._log_progress(f"✅ Proyecto Angular creado en {app_path}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("⏰ Timeout en ng new (300s)")
            return False
        except FileNotFoundError as e:
            logger.error(f"❌ Angular CLI no encontrado: {e}")
            logger.error("💡 Verifica: ng version")
            return False
        except Exception as e:
            logger.error(f"❌ Error en _create_angular_project: {type(e).__name__}: {e}", exc_info=True)
            return False

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
    1. TODOS los componentes deben seguir el patrón ATOM:
    - Selector con prefijo "lib-"
    - Clase con prefijo "Lib"
    - standalone: true
    - changeDetection: ChangeDetectionStrategy.OnPush
    - Inyección de servicios vía inject()
    - Usar signal()/computed() para estado
    - Implementar OnInit, AfterViewInit, OnDestroy

    2. ESTILOS:
    - En styles.scss global: @use '@angular/material' as mat; @use '@muface-lib/muface-lib/estilos/m3-theme' as muf-theme;
    - En componentes: estilos acotados con :host, sin CSS inline

    3. DTOs:
    - Usar tipos genéricos <T> en clases base
    - Inputs encapsulados en objeto de estructura

    {'ESPECIFICACIÓN API:' if api_spec else 'DESCRIPCIÓN DE LA APP:'}
    {api_spec[:4000] if api_spec else description}

    {angular_context if angular_context else ''}

    TU TAREA: Generar la estructura completa de archivos para una aplicación Angular.

    FORMATO DE RESPUESTA (ESTRICTO):
    === FILE: src/app/path/to/file.ts ===
    ```typescript
    <!-- contenido del archivo -->
    Genera como mínimo:

    app.module.ts o componentes standalone con routing
    Un componente principal
    Un servicio para consumir la API
    Interfaces TypeScript para los modelos

    NO incluyas explicaciones, solo los archivos en el formato especificado."""
            # ✅ CORRECTO: Usar asyncio.wait_for para manejar el timeout
            response = await asyncio.wait_for(
                asyncio.to_thread(client.generate, prompt),
                timeout=180  # 3 minutos para generación de código
            )
    
            # Parsear respuesta y escribir archivos
            files_written = await self._parse_and_write_files(app_path, response)
            
            if files_written == 0:
                logger.warning("⚠️ No se generaron archivos desde la respuesta de la IA")
                return False
            
            self._log_progress(f"✅ {files_written} archivos generados")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en _generate_app_code: {e}", exc_info=True)
            return False

    async def _parse_and_write_files(self, app_path: Path, response: str) -> int:
        """Parsea la respuesta de la IA y escribe los archivos en disco"""
        import re

        files_written = 0
        app_src = app_path / "src" / "app"

        # Patrón para extraer archivos: === FILE: ruta === ```lenguaje contenido ```
        file_pattern = r'=== FILE: (src/app/[^\s]+) ===\s*```(?:\w+)?\s*(.*?)```'

        matches = re.findall(file_pattern, response, re.DOTALL)

        for file_path, content in matches:
            try:
                # Validar que no excedemos límite de archivos
                if files_written >= self.max_files:
                    logger.warning(f"⚠️ Límite de archivos alcanzado ({self.max_files})")
                    break

                # Construir ruta completa
                full_path = app_src.parent.parent / file_path  # Desde src/

                # Crear directorios padre si no existen
                full_path.parent.mkdir(parents=True, exist_ok=True)

                # Escribir archivo
                full_path.write_text(content.strip(), encoding='utf-8')
                files_written += 1

                logger.debug(f"📝 Escrito: {file_path}")

            except Exception as e:
                logger.warning(f"⚠️ No se pudo escribir {file_path}: {e}")
                continue

        return files_written

    def _install_dependencies(self, app_path: Path) -> bool:
        """Instala dependencias con npm install (síncrono)"""
        self._log_progress("📦 Instalando dependencias (puede tardar 15-20 min)...")
        
        try:
            import subprocess
            import shutil
            
            # 🛠️ CRÍTICO: Encontrar la ruta completa de 'npm' en Windows
            npm_path = shutil.which("npm")
            
            if not npm_path:
                # Intentar ruta típica de npm global en Windows
                npm_cmd_path = Path.home() / "AppData" / "Roaming" / "npm" / "npm.cmd"
                if npm_cmd_path.exists():
                    npm_path = str(npm_cmd_path)
                else:
                    # Último intento: buscar en PATH manualmente
                    env_path = os.environ.get("PATH", "")
                    for path_dir in env_path.split(";"):
                        candidate = Path(path_dir) / "npm.cmd"
                        if candidate.exists():
                            npm_path = str(candidate)
                            break
            
            if not npm_path:
                logger.error("❌ No se encontró 'npm' en PATH ni en rutas típicas")
                logger.error(f"💡 PATH actual: {os.environ.get('PATH', '')[:300]}...")
                return False
            
            logger.info(f"✅ Usando npm en: {npm_path}")
            
            # Preparar entorno con PATH que incluya npm global
            env = os.environ.copy()
            npm_global_path = str(Path.home() / "AppData" / "Roaming" / "npm")
            if npm_global_path not in env.get("PATH", ""):
                env["PATH"] = npm_global_path + ";" + env.get("PATH", "")
            
            # Crear .npmrc temporal para usar registry público (evita error 504 de Nexus)
            npmrc_path = app_path / ".npmrc"
            original_npmrc = None
            
            if npmrc_path.exists():
                original_npmrc = npmrc_path.read_text(encoding='utf-8')
            
            npmrc_content = """registry=https://registry.npmjs.org/
    strict-ssl=false
    fetch-retries=10
    fetch-retry-mintimeout=20000
    fetch-retry-maxtimeout=600000
    """
            npmrc_path.write_text(npmrc_content, encoding='utf-8')
            
            # Ejecutar npm install con ruta completa al ejecutable
            process = subprocess.run(
                [npm_path, "install"],  # Usamos ruta completa, no solo "npm"
                #[npm_path, "install --legacy-peer-deps --verbose --strict-ssl=false --registry=https://artefactos-ic.scae.redsara.es/nexus/repository/registry_npmjs_org/ --//artefactos-ic.scae.redsara.es/nexus/repository/registry_npmjs_org/:_auth=bXVmYWNlOmF0b20yMDI0 --@muface-lib:registry=https://artefactos-ic.scae.redsara.es/nexus/repository/ad-npm/ --//artefactos-ic.scae.redsara.es/nexus/repository/ad-npm/:_auth=bXVmYWNlOmF0b20yMDI0"],
                cwd=str(app_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=1800,  # 30 minutos para proxy corporativo
                env=env
            )
            
            # Restaurar .npmrc original si existía
            if original_npmrc is not None:
                npmrc_path.write_text(original_npmrc, encoding='utf-8')
            else:
                npmrc_path.unlink(missing_ok=True)
            
            if process.returncode != 0:
                stderr_text = process.stderr.decode('utf-8', errors='ignore')[:500]
                logger.error(f"❌ npm install falló: {stderr_text}")
                return False
            
            self._log_progress("✅ Dependencias instaladas")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("⏰ Timeout en npm install (1800s)")
            return False
        except FileNotFoundError as e:
            logger.error(f"❌ npm no encontrado: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error en _install_dependencies: {e}", exc_info=True)
            return False

    
            
    def _start_dev_server(self, app_path: Path) -> Optional[int]:
        """Inicia ng serve en background (síncrono con Popen)"""
        port = 4200
        self._log_progress(f"🚀 Iniciando servidor en puerto {port}...")
        
        try:
            import subprocess
            
            # Preparar entorno
            env = os.environ.copy()
            npm_global_path = Path.home() / "AppData" / "Roaming" / "npm"
            if str(npm_global_path) not in env.get("PATH", ""):
                env["PATH"] = str(npm_global_path) + ";" + env.get("PATH", "")
            
            # Iniciar ng serve en background con Popen
            process = subprocess.Popen(
                ["ng", "serve", "--port", str(port), "--host", "0.0.0.0", "--disable-host-check"],
                cwd=str(app_path),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0  # Windows: sin ventana console
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
            
        except FileNotFoundError:
            logger.error("❌ Angular CLI no encontrado para ng serve")
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