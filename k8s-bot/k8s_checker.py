from kubernetes import client, config
from kubernetes.client.rest import ApiException
import os

def cargar_k8s():
    """Carga la configuración de Kubernetes"""
    contexto = os.getenv("K8S_CONTEXT", "dev-atom")
    config_path = os.getenv("K8S_CONFIG_PATH")
    
    try:
        # Si hay una ruta específica, úsala. Si no, usa la por defecto.
        if config_path:
            # Convertir ruta relativa a absoluta
            if not os.path.isabs(config_path):
                config_path = os.path.join(os.path.dirname(__file__), config_path)
            
            print(f"📁 Usando kubeconfig: {config_path}")
            config.load_kube_config(config_file=config_path, context=contexto)
        else:
            print(f"📁 Usando kubeconfig por defecto (~/.kube/config)")
            config.load_kube_config(context=contexto)
        
        v1 = client.CoreV1Api()
        print(f"✅ Conectado al contexto: {contexto}")
        return v1
    except Exception as e:
        print(f"❌ Error conectando a K8s: {e}")
        return None

def obtener_estado_pods(v1):
    """Obtiene el estado de todos los pods"""
    if not v1:
        return "❌ Error: No hay conexión con Kubernetes."
    
    try:
        pods = v1.list_pod_for_all_namespaces(watch=False)
        reporte = []
        problemas = []
        
        for pod in pods.items:
            nombre = pod.metadata.name
            namespace = pod.metadata.namespace
            estado = pod.status.phase
            
            linea = f"📦 `{namespace}/{nombre}`: {estado}"
            reporte.append(linea)
            
            if estado != "Running":
                problemas.append(f"⚠️ **ALERTA**: `{namespace}/{nombre}` está en **{estado}**")
        
        resumen = f"📊 **Total Pods:** {len(reporte)}\n\n"
        
        if problemas:
            resumen += "🚨 **PROBLEMAS DETECTADOS:**\n" + "\n".join(problemas)
        else:
            resumen += "✅ **Todos los pods están Running**"
        
        if len(reporte) > 0:
            resumen += "\n\n--- 📋 Detalle (primeros 20) ---\n"
            resumen += "\n".join(reporte[:20])
            if len(reporte) > 20:
                resumen += f"\n... y {len(reporte) - 20} más."
        
        return resumen

    except ApiException as e:
        return f"❌ Error consultando K8s: {e.reason}"

def obtener_estado_pods(v1):
    """Obtiene el estado de todos los pods"""
    if not v1:
        return "❌ Error: No hay conexión con Kubernetes."
    
    try:
        pods = v1.list_pod_for_all_namespaces(watch=False)
        reporte = []
        problemas = []
        
        for pod in pods.items:
            nombre = pod.metadata.name
            namespace = pod.metadata.namespace
            estado = pod.status.phase
            
            linea = f"📦 `{namespace}/{nombre}`: {estado}"
            reporte.append(linea)
            
            if estado != "Running":
                problemas.append(f"⚠️ **ALERTA**: `{namespace}/{nombre}` está en **{estado}**")
        
        resumen = f"📊 **Total Pods:** {len(reporte)}\n\n"
        
        if problemas:
            resumen += "🚨 **PROBLEMAS DETECTADOS:**\n" + "\n".join(problemas)
        else:
            resumen += "✅ **Todos los pods están Running**"
        
        # Añadir primeros 20 pods como detalle
        if len(reporte) > 0:
            resumen += "\n\n--- 📋 Detalle (primeros 20) ---\n"
            resumen += "\n".join(reporte[:20])
            if len(reporte) > 20:
                resumen += f"\n... y {len(reporte) - 20} más."
        
        return resumen

    except ApiException as e:
        return f"❌ Error consultando K8s: {e.reason}"