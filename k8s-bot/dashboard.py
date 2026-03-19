import streamlit as st
import pandas as pd
from kubernetes import client, config

# Configurar página
st.set_page_config(page_title="K8s Dashboard", layout="wide")
st.title("📊 Estado del Clúster dev-atom")

# Cargar K8s
try:
    config.load_kube_config(context="dev-atom")
    v1 = client.CoreV1Api()
except Exception as e:
    st.error(f"No se pudo conectar a K8s: {e}")
    st.stop()

# Obtener datos
@st.cache_data(ttl=60) # Cachear por 60 segundos
def get_pod_data():
    pods = v1.list_pod_for_all_namespaces(watch=False)
    data = []
    for pod in pods.items:
        data.append({
            "Nombre": pod.metadata.name,
            "Namespace": pod.metadata.namespace,
            "Estado": pod.status.phase,
            "IP": pod.status.pod_ip,
            "Node": pod.spec.node_name
        })
    return pd.DataFrame(data)

df = get_pod_data()

# Sidebar para filtros
st.sidebar.header("Filtros")
namespace_filter = st.sidebar.multiselect("Namespace", options=df["Namespace"].unique(), default=df["Namespace"].unique())
status_filter = st.sidebar.multiselect("Estado", options=df["Estado"].unique(), default=df["Estado"].unique())

# Filtrar DF
df_selection = df.query("Namespace == @namespace_filter & Estado == @status_filter")

# Métricas
st.metric("Total Pods", len(df))
st.metric("Pods No-Running", len(df[df["Estado"] != "Running"]))

# Tabla interactiva
st.dataframe(df_selection, use_container_width=True)

# Gráfico simple
st.bar_chart(df_selection.groupby("Estado").size())