# dashboard.py - Dashboard Profesional Kubernetes
# 📊 Visualización interactiva del estado del clúster

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from kubernetes import client, config
import os
from pathlib import Path
from dotenv import load_dotenv
import time

# ===========================================
# 🛡️ PARCHE SSL PARA ENTORNO CORPORATIVO
# ===========================================
import ssl
import urllib3
import warnings

# Desactivar verificación SSL (solo para desarrollo en VDI)
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", message=".*Unverified HTTPS request.*")
# ===========================================

# ==========================
# CONFIGURACIÓN DE PÁGINA
# ==========================
st.set_page_config(
    page_title="K8s Dashboard - dev-atom",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================
# CARGAR CONFIGURACIÓN
# ==========================
# Cargar .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Configurar Kubernetes
K8S_NAMESPACE = os.getenv("K8S_NAMESPACE", "atom")
K8S_CONFIG_PATH = os.getenv("K8S_CONFIG_PATH", "./dev-atom-kubeconfig")
K8S_CONTEXT = os.getenv("K8S_CONTEXT", "dev-atom")

# ==========================
# ESTILOS CSS PERSONALIZADOS
# ==========================
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #1f77b4 0%, #2ca02c 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .status-running {
        color: #28a745;
        font-weight: bold;
    }
    .status-pending {
        color: #ffc107;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================
# CONEXIÓN A KUBERNETES
# ==========================
@st.cache_resource
def conectar_k8s():
    """Conecta a Kubernetes con cacheo"""
    try:
        config_path = os.path.join(BASE_DIR, K8S_CONFIG_PATH)
        config.load_kube_config(config_file=config_path, context=K8S_CONTEXT)
        v1 = client.CoreV1Api()
        apps_v1 = client.AppsV1Api()
        return v1, apps_v1
    except Exception as e:
        st.error(f"❌ Error conectando a Kubernetes: {str(e)}")
        return None, None

# ==========================
# OBTENER DATOS DEL CLÚSTER
# ==========================
@st.cache_data(ttl=30)  # Cache por 30 segundos
def obtener_datos_cluster(namespace):
    """Obtiene todos los datos del clúster"""
    v1, apps_v1 = conectar_k8s()
    
    if not v1:
        return None
    
    try:
        # Pods
        pods = v1.list_namespaced_pod(namespace=namespace)
        pods_data = []
        for pod in pods.items:
            containers_ready = 0
            containers_total = len(pod.status.container_statuses or [])
            for cs in (pod.status.container_statuses or []):
                if cs.ready:
                    containers_ready += 1
            
            pods_data.append({
                "Nombre": pod.metadata.name,
                "Namespace": pod.metadata.namespace,
                "Estado": pod.status.phase,
                "IP": pod.status.pod_ip or "N/A",
                "Node": pod.spec.node_name or "N/A",
                "Containers": f"{containers_ready}/{containers_total}",
                "Reinicios": sum(cs.restart_count for cs in (pod.status.container_statuses or [])),
                "Edad": str(pod.metadata.creation_timestamp).split("+")[0] if pod.metadata.creation_timestamp else "N/A"
            })
        
        # Deployments
        deployments = apps_v1.list_namespaced_deployment(namespace=namespace)
        deployments_data = []
        for dep in deployments.items:
            deployments_data.append({
                "Nombre": dep.metadata.name,
                "Disponibles": dep.status.available_replicas or 0,
                "Listos": dep.status.ready_replicas or 0,
                "Deseados": dep.spec.replicas or 0
            })
        
        # Services
        services = v1.list_namespaced_service(namespace=namespace)
        services_data = []
        for svc in services.items:
            services_data.append({
                "Nombre": svc.metadata.name,
                "Tipo": svc.spec.type,
                "Cluster IP": svc.spec.cluster_ip,
                "Puertos": ", ".join([f"{p.port}/{p.protocol}" for p in svc.spec.ports]) if svc.spec.ports else "N/A"
            })
        
        return {
            "pods": pd.DataFrame(pods_data),
            "deployments": pd.DataFrame(deployments_data),
            "services": pd.DataFrame(services_data)
        }
    
    except Exception as e:
        st.error(f"❌ Error obteniendo datos: {str(e)}")
        return None

# ==========================
# HEADER
# ==========================
st.markdown('<h1 class="main-header">🚀 Kubernetes Dashboard</h1>', unsafe_allow_html=True)
st.markdown(f"**Namespace:** `{K8S_NAMESPACE}` | **Contexto:** `{K8S_CONTEXT}`")
st.markdown("---")

# ==========================
# SIDEBAR
# ==========================
with st.sidebar:
    st.header("🎛️ Controles")
    
    # Auto-refresh
    auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=False)
    
    # Filtros
    st.subheader("🔍 Filtros")
    
    if st.button("🔄 Actualizar ahora"):
        st.cache_data.clear()
    
    st.markdown("---")
    st.markdown("### ℹ️ Información")
    st.markdown("""
    - **Actualización:** Cada 30s (si está activado)
    - **Fuente:** Kubernetes API
    - **Métricas:** Tiempo real
    """)

# ==========================
# CARGAR DATOS
# ==========================
datos = obtener_datos_cluster(K8S_NAMESPACE)

if not datos:
    st.warning("⏳ Esperando datos del clúster...")
    st.stop()

pods_df = datos["pods"]
deployments_df = datos["deployments"]
services_df = datos["services"]

# ==========================
# MÉTRICAS PRINCIPALES
# ==========================
st.subheader("📊 Métricas del Clúster")

col1, col2, col3, col4 = st.columns(4)

total_pods = len(pods_df)
pods_running = len(pods_df[pods_df["Estado"] == "Running"])
pods_pending = len(pods_df[pods_df["Estado"] == "Pending"])
pods_error = total_pods - pods_running - pods_pending

total_deployments = len(deployments_df)
total_services = len(services_df)
total_restarts = pods_df["Reinicios"].sum()

with col1:
    st.metric(
        label="📦 Total Pods",
        value=total_pods,
        delta=f"{pods_running} running",
        delta_color="normal"
    )

with col2:
    st.metric(
        label="🚀 Deployments",
        value=total_deployments,
        delta=f"{total_services} servicios",
        delta_color="normal"
    )

with col3:
    st.metric(
        label="✅ Salud",
        value=f"{round((pods_running/total_pods*100) if total_pods > 0 else 0, 1)}%",
        delta=f"{pods_error} con errores",
        delta_color="inverse" if pods_error > 0 else "normal"
    )

with col4:
    st.metric(
        label="🔄 Reinicios Totales",
        value=total_restarts,
        delta="Acumulado",
        delta_color="inverse" if total_restarts > 10 else "normal"
    )

st.markdown("---")

# ==========================
# GRÁFICOS
# ==========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Pods por Estado")
    
    estado_counts = pods_df["Estado"].value_counts().reset_index()
    estado_counts.columns = ["Estado", "Cantidad"]
    
    fig_pie = px.pie(
        estado_counts,
        values="Cantidad",
        names="Estado",
        color_discrete_sequence=px.colors.qualitative.Set2,
        hole=0.4
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(height=300, showlegend=True)
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    st.subheader("📈 Pods por Node")
    
    node_counts = pods_df["Node"].value_counts().reset_index()
    node_counts.columns = ["Node", "Pods"]
    
    fig_bar = px.bar(
        node_counts,
        x="Node",
        y="Pods",
        color="Pods",
        color_continuous_scale="Viridis"
    )
    fig_bar.update_layout(height=300, showlegend=False, xaxis_title="Node", yaxis_title="Número de Pods")
    st.plotly_chart(fig_bar, use_container_width=True)

# ==========================
# TABLA DE PODS
# ==========================
st.subheader("📋 Lista de Pods")

# Filtros en la tabla
col1, col2 = st.columns(2)
with col1:
    filtro_estado = st.multiselect(
        "Filtrar por estado",
        options=pods_df["Estado"].unique(),
        default=pods_df["Estado"].unique()
    )

with col2:
    busqueda = st.text_input("🔍 Buscar pod", "")

# Aplicar filtros
pods_filtrados = pods_df[pods_df["Estado"].isin(filtro_estado)]
if busqueda:
    pods_filtrados = pods_filtrados[
        pods_filtrados["Nombre"].str.contains(busqueda, case=False, na=False)
    ]

# Mostrar tabla con estilo
st.dataframe(
    pods_filtrados,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Nombre": st.column_config.TextColumn("Nombre", width="medium"),
        "Estado": st.column_config.TextColumn("Estado", width="small"),
        "IP": st.column_config.TextColumn("IP", width="small"),
        "Node": st.column_config.TextColumn("Node", width="medium"),
        "Containers": st.column_config.TextColumn("Containers", width="small"),
        "Reinicios": st.column_config.NumberColumn("Reinicios", width="small"),
        "Edad": st.column_config.TextColumn("Edad", width="medium")
    }
)

# ==========================
# DEPLOYMENTS Y SERVICIOS
# ==========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🚀 Deployments")
    st.dataframe(
        deployments_df,
        use_container_width=True,
        hide_index=True
    )

with col2:
    st.subheader("🌐 Servicios")
    st.dataframe(
        services_df,
        use_container_width=True,
        hide_index=True
    )

# ==========================
# FOOTER
# ==========================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; padding: 1rem;'>
        <p>🤖 K8s Dashboard | Actualizado automáticamente cada 30 segundos</p>
        <p>Namespace: <code>atom</code> | Contexto: <code>dev-atom</code></p>
    </div>
    """,
    unsafe_allow_html=True
)

# ==========================
# AUTO-REFRESH
# ==========================
if auto_refresh:
    time.sleep(30)
    st.rerun()