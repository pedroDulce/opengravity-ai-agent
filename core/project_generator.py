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
            if not await self._create_angular_project(app_path, app_name):
                result["errors"].append("Error creando proyecto Angular")
                return result

            # Paso 2: Generar código desde API spec o descripción
            if api_spec or description:
                if not await self._generate_app_code(app_path, api_spec, description):
                    # ✅ CORRECTO:
                    result["errors"].append("Error generando código de la app")
                    return result

            # Paso 3: Instalar dependencias adicionales si es necesario
            if not await self._install_dependencies(app_path):
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

    async def _create_angular_project(self, app_path: Path, app_name: str) -> bool:
        """Crea proyecto Angular base usando ng new"""
        self._log_progress(f"📦 Creando proyecto Angular '{app_name}'...")

        try:
            # Comando ng new con opciones corporativas
            cmd = [
                "ng", "new", app_name,
                "--routing", "true",
                "--style", "scss",
                "--skip-git", "true",  # No inicializar git automáticamente
                "--minimal", "false"
            ]

            # Ejecutar en el directorio de salida
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.output_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                # Responder automáticamente a prompts de ng new
                stdin=asyncio.subprocess.PIPE
            )

            # Enviar 'Y' para confirmar CSS y otras preguntas
            process.stdin.write(b'Y\n')
            await process.stdin.drain()

            # Esperar con timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300  # 5 minutos para ng new
            )

            if process.returncode != 0:
                logger.error(f"❌ ng new falló: {stderr.decode()}")
                return False

            self._log_progress(f"✅ Proyecto Angular creado en {app_path}")
            return True

        except asyncio.TimeoutError:
            logger.error("⏰ Timeout en ng new")
            return False
        except FileNotFoundError:
            logger.error("❌ Angular CLI no encontrado. Ejecuta: npm install -g @angular/cli")
            return False
        except Exception as e:
            logger.error(f"❌ Error en _create_angular_project: {e}")
            return False

    async def _generate_app_code(self, app_path: Path, api_spec: Optional[str],
                                  description: Optional[str]) -> bool:
        """Genera componentes, servicios y código de la app usando la IA"""
        self._log_progress("🧠 Generando código de la aplicación...")

        try:
            # Importar aquí para evitar circular imports
            from core.llm_client import LLMClient
            from core.context_manager import ContextManager

            client = LLMClient()
            ctx_manager = ContextManager()

            # Obtener contexto corporativo Angular
            angular_context = ctx_manager.get_context(
                "angular component service module routing",
                category="angular-guidelines",
                max_tokens=2000
            )

            # Construir prompt para generar estructura de archivos
            prompt = f"""Eres un arquitecto Angular experto. Tu tarea es generar la estructura completa de archivos para una aplicación Angular.

{'ESPECIFICACIÓN API:' if api_spec else 'DESCRIPCIÓN DE LA APP:'}
{api_spec[:4000] if api_spec else description}

{angular_context if angular_context else ''}

INSTRUCCIONES:
1. Genera la lista COMPLETA de archivos que debe tener la aplicación
2. Para CADA archivo, proporciona:
   - Ruta relativa desde src/app/
   - Contenido completo del archivo en TypeScript/HTML/SCSS
3. Sigue las convenciones corporativas del contexto

FORMATO DE RESPUESTA (ESTRICTO):
Usa este formato exacto para cada archivo:

=== FILE: src/app/path/to/file.ts ===
```typescript
// contenido del archivo
```

=== FILE: src/app/path/to/file.html ===
```html
<!-- contenido del archivo -->
```

=== FILE: src/app/path/to/file.scss ===
```scss
// contenido del archivo
```

Genera como mínimo:
- app.module.ts con imports necesarios
- app-routing.module.ts con rutas básicas
- Un componente principal (ej: pet-list, store-home)
- Un servicio para consumir la API
- Interfaces TypeScript para los modelos de la API

NO incluyas explicaciones, solo los archivos en el formato especificado."""

            response = await asyncio.to_thread(client.generate, prompt, timeout=180)

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

    async def _install_dependencies(self, app_path: Path) -> bool:
        """Instala dependencias adicionales si son necesarias"""
        self._log_progress("📦 Instalando dependencias...")

        try:
            # Ejecutar npm install
            process = await asyncio.create_subprocess_exec(
                "npm", "install",
                cwd=str(app_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=600  # 10 minutos para npm install
            )

            if process.returncode != 0:
                logger.error(f"❌ npm install falló: {stderr.decode()[:500]}")
                return False

            self._log_progress("✅ Dependencias instaladas")
            return True

        except asyncio.TimeoutError:
            logger.error("⏰ Timeout en npm install")
            return False
        except FileNotFoundError:
            logger.error("❌ npm no encontrado. Asegúrate de tener Node.js instalado")
            return False
        except Exception as e:
            logger.error(f"❌ Error en _install_dependencies: {e}")
            return False

    async def _start_dev_server(self, app_path: Path) -> Optional[int]:
        """Inicia ng serve y devuelve el puerto donde está corriendo"""
        port = 4200
        self._log_progress(f"🚀 Iniciando servidor de desarrollo en puerto {port}...")

        try:
            # Ejecutar ng serve en background
            process = await asyncio.create_subprocess_exec(
                "ng", "serve",
                "--port", str(port),
                "--host", "0.0.0.0",
                "--disable-host-check",
                cwd=str(app_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            # Esperar a que el servidor esté listo (buscar "Compiled successfully")
            compiled = False
            start_wait = datetime.now()

            while not compiled and (datetime.now() - start_wait).total_seconds() < 120:
                line = await process.stdout.readline()
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