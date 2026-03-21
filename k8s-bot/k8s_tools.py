# k8s_tools.py
# Herramientas seguras que el Agente de Kubernetes puede ejecutar

from kubernetes import client, config
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar configuración
load_dotenv()
K8S_NAMESPACE = os.getenv("K8S_NAMESPACE", "atom")
K8S_CONFIG_PATH = os.getenv("K8S_CONFIG_PATH", "./dev-atom-kubeconfig")

def cargar_k8s_config():
    """Carga la configuración de Kubernetes"""
    config_path = os.path.join(Path(__file__).parent, K8S_CONFIG_PATH)
    config.load_kube_config(config_file=config_path)
    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    return v1, apps_v1

# ===========================================
# 📊 HERRAMIENTAS DE LECTURA (Seguras, sin confirmación)
# ===========================================

def get_pods(namespace=None, label_selector=None):
    """Obtiene lista de pods CON recursos"""
    v1, _ = cargar_k8s_config()
    ns = namespace or K8S_NAMESPACE
    pods = v1.list_namespaced_pod(namespace=ns, label_selector=label_selector)
    
    result = []
    for pod in pods.items:
        # Extraer recursos de los contenedores
        recursos = []
        for container in pod.spec.containers:
            resources = container.resources or {}
            requests = resources.get("requests", {})
            limits = resources.get("limits", {})
            recursos.append({
                "name": container.name,
                "cpu_request": requests.get("cpu", "N/A"),
                "memory_request": requests.get("memory", "N/A"),
                "cpu_limit": limits.get("cpu", "N/A"),
                "memory_limit": limits.get("memory", "N/A")
            })
        
        result.append({
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": pod.status.phase,
            "ip": pod.status.pod_ip,
            "node": pod.spec.node_name,
            "restarts": sum(cs.restart_count for cs in (pod.status.container_statuses or [])),
            "age": str(pod.metadata.creation_timestamp).split("+")[0] if pod.metadata.creation_timestamp else "N/A",
            "recursos": recursos
        })
    return result

# ===========================================
# 🌐 HERRAMIENTAS PARA CONTOUR/HTTPPROXY
# ===========================================

def get_httpproxies(namespace=None):
    """Obtiene reglas de enrutamiento HTTPProxy (Contour/Project Contour)"""
    try:
        from kubernetes import dynamic
        from kubernetes.client import api_client
        
        v1, _ = cargar_k8s_config()
        ns = namespace or K8S_NAMESPACE
        
        dyn_client = dynamic.DynamicClient(
            api_client.ApiClient(configuration=v1.api_client.configuration)
        )
        
        httpproxy_resource = dyn_client.resources.get(
            api_version='projectcontour.io/v1',
            kind='HTTPProxy'
        )
        
        proxies = httpproxy_resource.get(namespace=ns)
        
        result = []
        for proxy in proxies.items:
            # Extraer información de enrutamiento
            routes = []
            if hasattr(proxy, 'spec') and hasattr(proxy.spec, 'routes'):
                for route in (proxy.spec.routes or []):
                    routes.append({
                        "conditions": [c.get("prefix") for c in (route.get("conditions") or []) if c.get("prefix")],
                        "services": [f"{s.get('name')}:{s.get('port')}" for s in (route.get("services") or [])],
                        "timeout": route.get("timeoutPolicy", {}).get("timeout", "default")
                    })
            
            # Extraer virtualhost si existe
            virtualhost = None
            if hasattr(proxy, 'spec') and hasattr(proxy.spec, 'virtualhost'):
                vh = proxy.spec.virtualhost
                virtualhost = getattr(vh, 'fqdn', None) if hasattr(vh, 'fqdn') else None
            
            result.append({
                "name": proxy.metadata.name,
                "namespace": proxy.metadata.namespace,
                "virtualhost": virtualhost,
                "routes": routes,
                "status": getattr(getattr(proxy, 'status', None), 'currentStatus', 'Unknown'),
                "description": getattr(getattr(proxy, 'spec', None), 'description', ''),
                "age": str(proxy.metadata.creation_timestamp).split("+")[0] if proxy.metadata.creation_timestamp else "N/A"
            })
        
        return result
        
    except Exception as e:
        error_str = str(e)
        # 👇 Detectar error 403 y devolver mensaje estructurado
        if "403" in error_str or "Forbidden" in error_str:
            return {
                "error": "403 Forbidden: Sin permisos para listar HTTPProxy",
                "hint": "Pide al equipo de plataforma permisos para 'httpproxies.projectcontour.io' o usa 'get_ingresses' como alternativa"
            }
        return {
            "error": f"No se pudieron consultar HTTPProxies: {error_str[:200]}",
            "hint": "Verifica que Contour está instalado y los CRDs están registrados"
        }        
    

def get_ingresses(namespace=None):
    """
    Obtiene reglas de enrutamiento Ingress (Kubernetes nativo)
    Alternativa si no usas Contour
    """
    from kubernetes.client import networking_v1
    
    v1, _ = cargar_k8s_config()
    ns = namespace or K8S_NAMESPACE
    net_v1 = networking_v1.NetworkingV1Api(v1.api_client)
    
    ingresses = net_v1.list_namespaced_ingress(namespace=ns)
    
    result = []
    for ing in ingresses.items:
        rules = []
        if ing.spec and ing.spec.rules:
            for rule in ing.spec.rules:
                host = rule.host or "*"
                paths = []
                if rule.http and rule.http.paths:
                    for path in rule.http.paths:
                        paths.append({
                            "path": path.path,
                            "pathType": path.path_type,
                            "service": f"{path.backend.service.name}:{path.backend.service.port.number}"
                        })
                rules.append({"host": host, "paths": paths})
        
        result.append({
            "name": ing.metadata.name,
            "namespace": ing.metadata.namespace,
            "host": ing.spec.rules[0].host if ing.spec.rules and ing.spec.rules[0].host else "*",
            "rules": rules,
            "tls": [t.hosts for t in ing.spec.tls] if ing.spec.tls else [],
            "age": str(ing.metadata.creation_timestamp).split("+")[0] if ing.metadata.creation_timestamp else "N/A"
        })
    
    return result

def get_services(namespace=None):
    """Obtiene lista de servicios y sus endpoints"""
    v1, _ = cargar_k8s_config()
    ns = namespace or K8S_NAMESPACE
    services = v1.list_namespaced_service(namespace=ns)
    
    result = []
    for svc in services.items:
        endpoints = []
        if svc.spec.ports:
            for port in svc.spec.ports:
                endpoints.append(f"{port.port}/{port.protocol}")
        
        result.append({
            "name": svc.metadata.name,
            "namespace": svc.metadata.namespace,
            "type": svc.spec.type,
            "cluster_ip": svc.spec.cluster_ip,
            "external_ip": svc.status.load_balancer.ingress[0].ip if svc.status.load_balancer.ingress else "N/A",
            "ports": ", ".join(endpoints) if endpoints else "N/A"
        })
    
    return result

def get_deployments(namespace=None):
    """Obtiene lista de deployments"""
    _, apps_v1 = cargar_k8s_config()
    ns = namespace or K8S_NAMESPACE
    deployments = apps_v1.list_namespaced_deployment(namespace=ns)
    
    return [{
        "name": dep.metadata.name,
        "namespace": dep.metadata.namespace,
        "ready": f"{dep.status.ready_replicas or 0}/{dep.spec.replicas or 0}",
        "available": dep.status.available_replicas or 0,
        "image": dep.spec.template.spec.containers[0].image if dep.spec.template.spec.containers else "N/A"
    } for dep in deployments.items]

def get_events(namespace=None, limit=10):
    """Obtiene eventos recientes"""
    v1, _ = cargar_k8s_config()
    ns = namespace or K8S_NAMESPACE
    events = v1.list_namespaced_event(namespace=ns, limit=limit)
    
    return [{
        "type": event.type,
        "reason": event.reason,
        "message": event.message[:200],
        "object": f"{event.involvedObject.kind}/{event.involvedObject.name}",
        "time": str(event.last_timestamp or event.event_time).split("+")[0]
    } for event in events.items]

def get_pod_logs(pod_name, namespace=None, lines=100, previous=False):
    """Obtiene logs de un pod"""
    v1, _ = cargar_k8s_config()
    ns = namespace or K8S_NAMESPACE
    
    logs = v1.read_namespaced_pod_log(
        name=pod_name,
        namespace=ns,
        tail_lines=lines,
        previous=previous
    )
    return logs[:4000]  # Limitar longitud

def describe_pod(pod_name, namespace=None):
    """Describe un pod en detalle"""
    v1, _ = cargar_k8s_config()
    ns = namespace or K8S_NAMESPACE
    pod = v1.read_namespaced_pod(name=pod_name, namespace=ns)
    
    return {
        "name": pod.metadata.name,
        "namespace": pod.metadata.namespace,
        "phase": pod.status.phase,
        "ip": pod.status.pod_ip,
        "node": pod.spec.node_name,
        "containers": [c.name for c in pod.spec.containers],
        "restarts": sum(cs.restart_count for cs in (pod.status.container_statuses or []))
    }

def get_nodes():
    """Obtiene lista de nodos"""
    v1, _ = cargar_k8s_config()
    nodes = v1.list_node()
    
    return [{
        "name": node.metadata.name,
        "status": "Ready" if any(c.type == "Ready" and c.status == "True" for c in node.status.conditions) else "NotReady",
        "pods": node.status.allocatable.get("pods", "N/A"),
        "cpu": node.status.allocatable.get("cpu", "N/A"),
        "memory": node.status.allocatable.get("memory", "N/A")
    } for node in nodes.items]

def get_namespaces():
    """Obtiene lista de namespaces"""
    v1, _ = cargar_k8s_config()
    namespaces = v1.list_namespace()
    
    return [{
        "name": ns.metadata.name,
        "status": ns.status.phase,
        "age": str(ns.metadata.creation_timestamp).split("+")[0] if ns.metadata.creation_timestamp else "N/A"
    } for ns in namespaces.items]

# ===========================================
# ⚠️ HERRAMIENTAS DE ESCRITURA (Requieren confirmación)
# ===========================================

def restart_pod(pod_name, namespace=None):
    """Elimina un pod para que Kubernetes lo recreé"""
    v1, _ = cargar_k8s_config()
    ns = namespace or K8S_NAMESPACE
    v1.delete_namespaced_pod(name=pod_name, namespace=ns)
    return f"Pod {pod_name} eliminado. Kubernetes lo recreará automáticamente."

def scale_deployment(deployment_name, replicas, namespace=None):
    """Escala un deployment"""
    _, apps_v1 = cargar_k8s_config()
    ns = namespace or K8S_NAMESPACE
    apps_v1.patch_namespaced_deployment_scale(
        name=deployment_name,
        namespace=ns,
        body={"spec": {"replicas": replicas}}
    )
    return f"Deployment {deployment_name} escalado a {replicas} réplicas."

# ===========================================
# 📋 REGISTRO DE HERRAMIENTAS DISPONIBLES
# ===========================================

TOOLS_REGISTRY = {
    "get_pods": {
        "description": "Obtiene lista de pods en un namespace",
        "parameters": ["namespace", "label_selector"],
        "requires_confirmation": False,
        "function": get_pods
    },
    "get_services": {
        "description": "Obtiene servicios y sus endpoints",
        "parameters": ["namespace"],
        "requires_confirmation": False,
        "function": get_services
    },
    "get_deployments": {
        "description": "Obtiene lista de deployments",
        "parameters": ["namespace"],
        "requires_confirmation": False,
        "function": get_deployments
    },
    "get_events": {
        "description": "Obtiene eventos recientes del clúster",
        "parameters": ["namespace", "limit"],
        "requires_confirmation": False,
        "function": get_events
    },
    "get_pod_logs": {
        "description": "Obtiene logs de un pod específico",
        "parameters": ["pod_name", "namespace", "lines", "previous"],
        "requires_confirmation": False,
        "function": get_pod_logs
    },
    "describe_pod": {
        "description": "Describe un pod en detalle",
        "parameters": ["pod_name", "namespace"],
        "requires_confirmation": False,
        "function": describe_pod
    },
    "get_nodes": {
        "description": "Obtiene lista de nodos del clúster",
        "parameters": [],
        "requires_confirmation": False,
        "function": get_nodes
    },
    "get_namespaces": {
        "description": "Obtiene lista de namespaces",
        "parameters": [],
        "requires_confirmation": False,
        "function": get_namespaces
    },
    "restart_pod": {
        "description": "Reinicia un pod (lo elimina para que se recreé)",
        "parameters": ["pod_name", "namespace"],
        "requires_confirmation": True,
        "function": restart_pod
    },
    "scale_deployment": {
        "description": "Escala un deployment a N réplicas",
        "parameters": ["deployment_name", "replicas", "namespace"],
        "requires_confirmation": True,
        "function": scale_deployment
    },
    "get_httpproxies": {
        "description": "Obtiene reglas de enrutamiento HTTPProxy (Contour/Project Contour)",
        "parameters": ["namespace"],
        "requires_confirmation": False,
        "function": get_httpproxies
    },
    "get_ingresses": {
        "description": "Obtiene reglas de enrutamiento Ingress (Kubernetes nativo)",
        "parameters": ["namespace"],
        "requires_confirmation": False,
        "function": get_ingresses
    },
}

def get_tools_description():
    """Devuelve descripción de herramientas para el LLM"""
    desc = "HERRAMIENTAS DISPONIBLES:\n\n"
    for name, info in TOOLS_REGISTRY.items():
        desc += f"• `{name}`: {info['description']}\n"
        if info['parameters']:
            desc += f"  Parámetros: {', '.join(info['parameters'])}\n"
        desc += f"  ¿Requiere confirmación? {'✅ SÍ' if info['requires_confirmation'] else '❌ NO'}\n\n"
    return desc

