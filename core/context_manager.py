# core/context_manager.py
"""
Gestor de contexto corporativo para OpenGravity.
Permite cargar, indexar y recuperar documentación de referencia para mejorar las respuestas de la IA.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Gestiona la base de conocimiento corporativa para inyectar contexto en los prompts de IA.
    """
    
    def __init__(self, knowledge_path: Optional[str] = None):
        """
        Inicializa el gestor de contexto.
        
        Args:
            knowledge_path: Ruta a la carpeta knowledge/ (por defecto: ./knowledge)
        """
        # Usar ruta absoluta desde la raíz del proyecto
        base_dir = Path(__file__).resolve().parent.parent
        self.knowledge_path = Path(knowledge_path or base_dir / "knowledge").resolve()
        self._cache: Dict[str, str] = {}
        self._index: Dict[str, List[Path]] = {
            "angular-guidelines": [],
            "api-contracts": [],
            "atom-guidelines": [],
            "examples": [],
            "general": []
        }
        
        if self.knowledge_path.exists():
            self._build_index()
            logger.info(f"✅ ContextManager inicializado: {len(self._cache)} documentos cargados")
        else:
            logger.warning(f"⚠️ Carpeta knowledge no encontrada: {self.knowledge_path}")
    

    def _build_index(self):
        """Indexa todos los documentos en la carpeta knowledge/"""
        if not self.knowledge_path.exists():
            return
        
        for category in self._index.keys():
            category_path = self.knowledge_path / category
            if category_path.exists():
                for file in category_path.rglob("*"):
                    if file.suffix in [".md", ".ts", ".json", ".yaml", ".yml", ".txt"]:
                        if file.name.startswith("."):
                            continue
                        self._index[category].append(file)
                        try:
                            content = file.read_text(encoding="utf-8")
                            self._cache[str(file)] = content
                            logger.debug(f"📄 Cargado: {file.relative_to(self.knowledge_path)}")
                        except Exception as e:
                            logger.warning(f"⚠️ No se pudo cargar {file}: {e}")

    # core/context_manager.py - Reemplazar TODO el método get_context:

    def get_context(self, query: str, category: Optional[str] = None, 
                    max_tokens: int = 3000) -> str:
        """
        Recupera contexto relevante para una consulta BUSCANDO EN EL CONTENIDO de los documentos.
        Prioriza documentos ATOM cuando la query menciona componentes, lib-, material, etc.
        
        Args:
            query: La consulta del usuario (para búsqueda por palabras clave)
            category: Filtrar por categoría (angular-guidelines, atom-guidelines, api-contracts, examples, general)
            max_tokens: Límite aproximado de tokens para el contexto devuelto
            
        Returns:
            String con el contexto formateado para inyectar en el prompt
        """
        relevant_docs = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # 🔍 Detectar si la query menciona conceptos ATOM
        is_atom_query = any(kw in query_lower for kw in [
            "component", "lib-", "atom", "material", "standalone", 
            "onpush", "inject", "signal", "computed", "m3-theme", "muface"
        ])
        
        # Categorías a buscar
        categories_to_search = [category] if category else list(self._index.keys())
        
        for cat in categories_to_search:
            for file_path in self._index.get(cat, []):
                content = self._cache.get(str(file_path), "")
                content_lower = content.lower()
                
                # ✅ Búsqueda REAL en el contenido del archivo
                score = 0
                
                # Palabras clave de la query en el contenido
                for word in query_words:
                    if len(word) > 3:  # Ignorar palabras muy cortas
                        if word in content_lower:
                            score += content_lower.count(word) * 2  # Doble peso por coincidencia
                
                # Bonus por coincidencia en nombre de archivo
                if any(word in file_path.name.lower() for word in query_words):
                    score += 10
                
                # 🎯 Bonus CRÍTICO: Si es query ATOM y el documento es de atom-guidelines
                if is_atom_query and cat == "atom-guidelines":
                    score += 50  # Prioridad máxima para guías ATOM
                
                # Bonus por categoría específica solicitada
                if category and cat == category:
                    score += 5
                
                # Si hay coincidencias, añadir a relevantes
                if score > 0:
                    relevant_docs.append((file_path, content, score, cat))
        
        # 🎯 Si es query ATOM y no hay resultados, forzar inclusión de guías ATOM
        if is_atom_query and not relevant_docs:
            for file_path in self._index.get("atom-guidelines", []):
                content = self._cache.get(str(file_path), "")
                if content:
                    relevant_docs.append((file_path, content, 100, "atom-guidelines"))  # Score máximo
        
        # Ordenar por relevancia (score más alto primero)
        relevant_docs.sort(key=lambda x: x[2], reverse=True)
        
        # Si aún no hay resultados, fallback a angular-guidelines y examples
        if not relevant_docs:
            for file_path in self._index.get("angular-guidelines", [])[:2]:
                content = self._cache.get(str(file_path), "")
                if content:
                    relevant_docs.append((file_path, content, 1, "angular-guidelines"))
            for file_path in self._index.get("examples", [])[:2]:
                content = self._cache.get(str(file_path), "")
                if content:
                    relevant_docs.append((file_path, content, 1, "examples"))
        
        # Formatear contexto para el prompt
        context_parts = []
        total_chars = 0
        max_chars = max_tokens * 4  # Aprox: 1 token ≈ 4 chars
        
        for file_path, content, score, cat in relevant_docs:
            rel_path = file_path.relative_to(self.knowledge_path)
            header = f"\n\n--- 📄 {rel_path} [{cat}] (relevancia: {score}) ---\n"
            
            if total_chars + len(header) + len(content) > max_chars:
                # Truncar contenido si excede el límite
                remaining = max_chars - total_chars - len(header)
                if remaining > 100:
                    context_parts.append(header)
                    context_parts.append(content[:remaining])
                break
            
            context_parts.append(header)
            context_parts.append(content)
            total_chars += len(header) + len(content)
        
        if not context_parts:
            return "⚠️ No se encontró contexto relevante en la base de conocimiento."
        
        # 🎯 Instrucción final FORZANDO uso de contexto ATOM si está presente
        atom_instruction = ""
        if is_atom_query and any(cat == "atom-guidelines" for _, _, _, cat in relevant_docs):
            atom_instruction = """
    🔴 INSTRUCCIÓN CRÍTICA - COMPONENTES ATOM:
    El código generado DEBE seguir EXACTAMENTE las reglas ATOM:
    • Selector con prefijo "lib-", clase con prefijo "Lib"
    • standalone: true, changeDetection: ChangeDetectionStrategy.OnPush
    • Inyección vía inject(), estado con signal()/computed()
    • Estilos en .scss separado, tema M3 con @muface-lib
    • Lifecycle hooks: OnInit, AfterViewInit, OnDestroy
    """
        
        return "\n".join([
            "📚 CONTEXTO CORPORATIVO DISPONIBLE:",
            "El siguiente material de referencia debe guiar tu respuesta:",
            *context_parts,
            atom_instruction,
            "\n\n🎯 INSTRUCCIÓN: Usa este contexto para generar código que siga EXACTAMENTE las convenciones corporativas mostradas arriba."
        ])

    def reload(self):
        """Recarga todos los documentos desde disco"""
        self._cache.clear()
        for key in self._index:
            self._index[key] = []
        self._build_index()
        logger.info("🔄 ContextManager recargado")
    
    def list_documents(self) -> Dict[str, List[str]]:
        """Lista todos los documentos indexados por categoría"""
        result = {}
        for category, files in self._index.items():
            result[category] = [
                str(f.relative_to(self.knowledge_path)) for f in files
            ]
        return result
    
    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Búsqueda avanzada que devuelve resultados estructurados.
        
        Args:
            query: Término de búsqueda
            max_results: Máximo de resultados a devolver
            
        Returns:
            Lista de dicts con: {file, category, score, preview}
        """
        results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for category, files in self._index.items():
            for file_path in files:
                content = self._cache.get(str(file_path), "")
                content_lower = content.lower()
                
                score = 0
                for word in query_words:
                    if len(word) > 3:
                        if word in content_lower:
                            score += content_lower.count(word)
                
                if score > 0:
                    # Crear preview del contenido
                    preview_start = content_lower.find(query_lower.split()[0]) if query_words else 0
                    preview_start = max(0, preview_start - 50)
                    preview_end = min(len(content), preview_start + 200)
                    preview = content[preview_start:preview_end].replace('\n', ' ').strip()
                    if len(preview) >= 200:
                        preview += "..."
                    
                    results.append({
                        "file": str(file_path.relative_to(self.knowledge_path)),
                        "category": category,
                        "score": score,
                        "preview": preview
                    })
        
        # Ordenar por score y limitar resultados
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:max_results]