import { Injectable } from '@angular/core';
import { Firestore, collection, collectionData, doc, docData, addDoc, updateDoc, deleteDoc, query, where } from '@angular/fire/firestore';
import { Observable } from 'rxjs';
import { 
  Expediente, 
  Titular, 
  Organismo, 
  Titulacion, 
  Ciudad, 
  Actividad 
} from '../models';

@Injectable({
  providedIn: 'root'
})
export class FirestoreService {
  constructor(private firestore: Firestore) {}

  // ========== EXPEDIENTES ==========
  getExpedientes(): Observable<Expediente[]> {
    const expedientesRef = collection(this.firestore, 'expedientes');
    return collectionData(expedientesRef, { idField: 'id' }) as Observable<Expediente[]>;
  }

  getExpedienteById(id: string): Observable<Expediente> {
    const expedienteRef = doc(this.firestore, 'expedientes', id);
    return docData(expedienteRef, { idField: 'id' }) as Observable<Expediente>;
  }

  addExpediente(expediente: Expediente): Promise<any> {
    const expedientesRef = collection(this.firestore, 'expedientes');
    return addDoc(expedientesRef, expediente);
  }

  updateExpediente(id: string, expediente: Partial<Expediente>): Promise<void> {
    const expedienteRef = doc(this.firestore, 'expedientes', id);
    return updateDoc(expedienteRef, expediente);
  }

  deleteExpediente(id: string): Promise<void> {
    const expedienteRef = doc(this.firestore, 'expedientes', id);
    return deleteDoc(expedienteRef);
  }

  // ========== TITULARES ==========
  getTitulares(): Observable<Titular[]> {
    const titularesRef = collection(this.firestore, 'titulares');
    return collectionData(titularesRef, { idField: 'id' }) as Observable<Titular[]>;
  }

  getTitularById(id: string): Observable<Titular> {
    const titularRef = doc(this.firestore, 'titulares', id);
    return docData(titularRef, { idField: 'id' }) as Observable<Titular>;
  }

  addTitular(titular: Titular): Promise<any> {
    const titularesRef = collection(this.firestore, 'titulares');
    return addDoc(titularesRef, titular);
  }

  updateTitular(id: string, titular: Partial<Titular>): Promise<void> {
    const titularRef = doc(this.firestore, 'titulares', id);
    return updateDoc(titularRef, titular);
  }

  deleteTitular(id: string): Promise<void> {
    const titularRef = doc(this.firestore, 'titulares', id);
    return deleteDoc(titularRef);
  }

  // ========== ORGANISMOS ==========
  getOrganismos(): Observable<Organismo[]> {
    const organismosRef = collection(this.firestore, 'organismos');
    return collectionData(organismosRef, { idField: 'id' }) as Observable<Organismo[]>;
  }

  addOrganismo(organismo: Organismo): Promise<any> {
    const organismosRef = collection(this.firestore, 'organismos');
    return addDoc(organismosRef, organismo);
  }

  // ========== TITULACIONES ==========
  getTitulaciones(): Observable<Titulacion[]> {
    const titulacionesRef = collection(this.firestore, 'titulaciones');
    return collectionData(titulacionesRef, { idField: 'id' }) as Observable<Titulacion[]>;
  }

  addTitulacion(titulacion: Titulacion): Promise<any> {
    const titulacionesRef = collection(this.firestore, 'titulaciones');
    return addDoc(titulacionesRef, titulacion);
  }

  // ========== CIUDADES ==========
  getCiudades(): Observable<Ciudad[]> {
    const ciudadesRef = collection(this.firestore, 'ciudades');
    return collectionData(ciudadesRef, { idField: 'id' }) as Observable<Ciudad[]>;
  }

  addCiudad(ciudad: Ciudad): Promise<any> {
    const ciudadesRef = collection(this.firestore, 'ciudades');
    return addDoc(ciudadesRef, ciudad);
  }

  // ========== ACTIVIDAD ==========
  getActividad(): Observable<Actividad[]> {
    const actividadRef = collection(this.firestore, 'actividad');
    return collectionData(actividadRef, { idField: 'id' }) as Observable<Actividad[]>;
  }

  addActividad(actividad: Actividad): Promise<any> {
    const actividadRef = collection(this.firestore, 'actividad');
    return addDoc(actividadRef, actividad);
  }

  // ========== ESTADÍSTICAS ==========
  getExpedientesCount(): Observable<Expediente[]> {
    return this.getExpedientes();
  }

  getTitularesCount(): Observable<Titular[]> {
    return this.getTitulares();
  }

  async seedTestData(): Promise<void> {
    const titulares: Titular[] = [
      { nombre: 'MARTÍNEZ', apellidos: 'ROBERTO', dni: '12345678A', email: 'roberto.martinez@muface.es', telefono: '600123456', status: 'Activo', provincia: 'Madrid' },
      { nombre: 'LÓPEZ', apellidos: 'ELENA', dni: '87654321B', email: 'elena.lopez@muface.es', telefono: '600654321', status: 'Jubilado', provincia: 'Barcelona' },
      { nombre: 'GÓMEZ', apellidos: 'JAVIER', dni: '45678901C', email: 'javier.gomez@muface.es', telefono: '600789012', status: 'Baja', provincia: 'Sevilla' },
      { nombre: 'FERNÁNDEZ', apellidos: 'ANA', dni: '23456789D', email: 'ana.fernandez@muface.es', telefono: '600890123', status: 'Activo', provincia: 'Valencia' },
    ];

    const ciudades: Ciudad[] = [
      { nombre: 'Madrid', region: 'Comunidad de Madrid', codigo_postal: '28001' },
      { nombre: 'Barcelona', region: 'Cataluña', codigo_postal: '08001' },
      { nombre: 'Sevilla', region: 'Andalucía', codigo_postal: '41001' },
    ];

    const organismos: Organismo[] = [
      { nombre: 'Instituto Nacional de la Seguridad Social', ciudad: 'Madrid', region: 'Comunidad de Madrid' },
      { nombre: 'Oficina MUFACE Cataluña', ciudad: 'Barcelona', region: 'Cataluña' },
    ];

    const expedientes: Expediente[] = [
      { numero: 'EXP-2024-001', estado: 'Activo', titular_id: '12345678A', organismo_id: '1', ciudad_id: '1', fecha_creacion: new Date('2024-03-12'), fecha_actualizacion: new Date('2024-03-14') },
      { numero: 'EXP-2024-042', estado: 'Pendiente', titular_id: '87654321B', organismo_id: '1', ciudad_id: '2', fecha_creacion: new Date('2024-03-10'), fecha_actualizacion: new Date('2024-03-11') },
      { numero: 'EXP-2024-089', estado: 'Resuelto', titular_id: '45678901C', organismo_id: '2', ciudad_id: '3', fecha_creacion: new Date('2024-03-08'), fecha_actualizacion: new Date('2024-03-20') },
    ];

    const actividad: Actividad[] = [
      { tipo: 'creacion', descripcion: 'Creado expediente EXP-2024-001', fecha: new Date(), usuario: 'admin' },
      { tipo: 'actualizacion', descripcion: 'Titular 87654321B actualizado', fecha: new Date(), usuario: 'admin' },
    ];

    for (const t of titulares) { await this.addTitular(t); }
    for (const c of ciudades) { await this.addCiudad(c); }
    for (const o of organismos) { await this.addOrganismo(o); }
    for (const e of expedientes) { await this.addExpediente(e); }
    for (const a of actividad) { await this.addActividad(a); }
  }
}
