# core/context_manager.py
"""
Gestor de contexto corporativo para OpenGravity.
Permite cargar, indexar y recuperar documentación de referencia para mejorar las respuestas de la IA.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Gestiona la base de conocimiento corporativa para inyectar contexto en los prompts de IA.
    
    Características:
    - Carga documentos Markdown/TS de la carpeta knowledge/
    - Indexa por categorías (angular-guidelines, api-contracts, examples)
    - Recupera contexto relevante según la consulta del usuario
    - Limita el contexto para no exceder límites de tokens del LLM
    """
    
    def __init__(self, knowledge_path: Optional[str] = None):
        """
        Inicializa el gestor de contexto.
        
        Args:
            knowledge_path: Ruta a la carpeta knowledge/ (por defecto: ./knowledge)
        """
        self.knowledge_path = Path(knowledge_path or "knowledge").resolve()
        self._cache: Dict[str, str] = {}
        self._index: Dict[str, List[Path]] = {
            "angular-guidelines": [],
            "api-contracts": [],
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
                    if file.suffix in [".md", ".ts", ".json", ".yaml", ".yml"]:
                        self._index[category].append(file)
                        # Cargar contenido en caché
                        try:
                            content = file.read_text(encoding="utf-8")
                            self._cache[str(file)] = content
                            logger.debug(f"📄 Cargado: {file.relative_to(self.knowledge_path)}")
                        except Exception as e:
                            logger.warning(f"⚠️ No se pudo cargar {file}: {e}")
    
    def get_context(self, query: str, category: Optional[str] = None, 
                    max_tokens: int = 3000) -> str:
        """
        Recupera contexto relevante para una consulta.
        
        Args:
            query: La consulta del usuario (para búsqueda semántica simple)
            category: Filtrar por categoría (angular-guidelines, api-contracts, examples, general)
            max_tokens: Límite aproximado de tokens para el contexto devuelto
            
        Returns:
            String con el contexto formateado para inyectar en el prompt
        """
        relevant_docs = []
        query_lower = query.lower()
        
        # Filtrar por categoría si se especifica
        categories_to_search = [category] if category else list(self._index.keys())
        
        for cat in categories_to_search:
            for file_path in self._index.get(cat, []):
                content = self._cache.get(str(file_path), "")
                
                # Búsqueda simple por palabras clave (puede mejorarse con embeddings)
                if any(keyword in query_lower for keyword in 
                      ["angular", "component", "service", "module", "typescript"]):
                    if cat == "angular-guidelines" or cat == "examples":
                        relevant_docs.append((file_path, content))
                
                elif any(keyword in query_lower for keyword in 
                        ["api", "endpoint", "swagger", "openapi", "http", "rest"]):
                    if cat == "api-contracts" or cat == "examples":
                        relevant_docs.append((file_path, content))
                
                elif any(keyword in query_lower for keyword in 
                        ["test", "spec", "jest", "jasmine", "karma"]):
                    if cat == "examples":
                        relevant_docs.append((file_path, content))
        
        # Si no hay resultados, devolver documentos generales
        if not relevant_docs:
            for cat in ["angular-guidelines", "examples"]:
                for file_path in self._index.get(cat, [])[:3]:  # Máximo 3 docs por defecto
                    content = self._cache.get(str(file_path), "")
                    relevant_docs.append((file_path, content))
        
        # Formatear contexto para el prompt
        context_parts = []
        total_chars = 0
        
        for file_path, content in relevant_docs:
            rel_path = file_path.relative_to(self.knowledge_path)
            header = f"\n\n--- 📄 {rel_path} ---\n"
            
            if total_chars + len(header) + len(content) > max_tokens * 4:  # Aprox: 1 token ≈ 4 chars
                break
            
            context_parts.append(header)
            context_parts.append(content[:max_tokens//2])  # Limitar contenido por doc
            total_chars += len(header) + len(content)
        
        if not context_parts:
            return "⚠️ No se encontró contexto relevante en la base de conocimiento."
        
        return "\n".join([
            "📚 CONTEXTO CORPORATIVO DISPONIBLE:",
            "El siguiente material de referencia debe guiar tu respuesta:",
            *context_parts,
            "\n\n🎯 INSTRUCCIÓN: Usa este contexto para generar código que siga EXACTAMENTE las convenciones corporativas mostradas arriba."
        ])
    
    def reload(self):
        """Recarga todos los documentos desde disco (útil después de actualizar la knowledge base)"""
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