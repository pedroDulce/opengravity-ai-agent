export interface Expediente {
  id?: string;
  numero: string;
  estado: 'Activo' | 'Pendiente' | 'Resuelto';
  titular_id: string;
  organismo_id: string;
  ciudad_id: string;
  fecha_creacion: Date;
  fecha_actualizacion: Date;
}

export interface Titular {
  id?: string;
  nombre: string;
  apellidos: string;
  dni: string;
  email: string;
  telefono: string;
  status?: 'Activo' | 'Jubilado' | 'Baja';
  provincia?: string;
}

export interface Organismo {
  id?: string;
  nombre: string;
  ciudad: string;
  region: string;
}

export interface Titulacion {
  id?: string;
  nombre: string;
  tipo: string;
  requisitos: string;
}

export interface Ciudad {
  id?: string;
  nombre: string;
  region: string;
  codigo_postal: string;
}

export interface Actividad {
  id?: string;
  tipo: 'creacion' | 'actualizacion' | 'aprobacion' | 'eliminacion';
  descripcion: string;
  fecha: Date;
  usuario: string;
}
