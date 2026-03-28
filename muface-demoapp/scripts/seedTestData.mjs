import { initializeApp } from 'firebase/app';
import { getFirestore, collection, addDoc } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: 'AIzaSyCdYyUkT5QANoJOS9Y2ka8pK3D8wgfV_Q8',
  authDomain: 'muface-app-demo.firebaseapp.com',
  projectId: 'muface-app-demo',
  storageBucket: 'muface-app-demo.appspot.com',
  messagingSenderId: '1067527701568',
  appId: '1:1067527701568:web:234949c1f2a8240ae7d06d',
  measurementId: 'G-7V6F2L32NM'
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

const titulares = [
  { nombre: 'MARTÍNEZ', apellidos: 'ROBERTO', dni: '12345678A', email: 'roberto.martinez@muface.es', telefono: '600123456', status: 'Activo', provincia: 'Madrid' },
  { nombre: 'LÓPEZ', apellidos: 'ELENA', dni: '87654321B', email: 'elena.lopez@muface.es', telefono: '600654321', status: 'Jubilado', provincia: 'Barcelona' },
  { nombre: 'GÓMEZ', apellidos: 'JAVIER', dni: '45678901C', email: 'javier.gomez@muface.es', telefono: '600789012', status: 'Baja', provincia: 'Sevilla' },
  { nombre: 'FERNÁNDEZ', apellidos: 'ANA', dni: '23456789D', email: 'ana.fernandez@muface.es', telefono: '600890123', status: 'Activo', provincia: 'Valencia' }
];

const ciudades = [
  { nombre: 'Madrid', region: 'Comunidad de Madrid', codigo_postal: '28001' },
  { nombre: 'Barcelona', region: 'Cataluña', codigo_postal: '08001' },
  { nombre: 'Sevilla', region: 'Andalucía', codigo_postal: '41001' }
];

const organismos = [
  { nombre: 'Instituto Nacional de la Seguridad Social', ciudad: 'Madrid', region: 'Comunidad de Madrid' },
  { nombre: 'Oficina MUFACE Cataluña', ciudad: 'Barcelona', region: 'Cataluña' }
];

const expedientes = [
  { numero: 'EXP-2024-001', estado: 'Activo', titular_id: '12345678A', organismo_id: '1', ciudad_id: '1', fecha_creacion: new Date('2024-03-12'), fecha_actualizacion: new Date('2024-03-14') },
  { numero: 'EXP-2024-042', estado: 'Pendiente', titular_id: '87654321B', organismo_id: '1', ciudad_id: '2', fecha_creacion: new Date('2024-03-10'), fecha_actualizacion: new Date('2024-03-11') },
  { numero: 'EXP-2024-089', estado: 'Resuelto', titular_id: '45678901C', organismo_id: '2', ciudad_id: '3', fecha_creacion: new Date('2024-03-08'), fecha_actualizacion: new Date('2024-03-20') }
];

const actividad = [
  { tipo: 'creacion', descripcion: 'Creado expediente EXP-2024-001', fecha: new Date(), usuario: 'admin' },
  { tipo: 'actualizacion', descripcion: 'Titular 87654321B actualizado', fecha: new Date(), usuario: 'admin' }
];

async function seed() {
  try {
    for (const t of titulares) {
      await addDoc(collection(db, 'titulares'), t);
    }
    for (const c of ciudades) {
      await addDoc(collection(db, 'ciudades'), c);
    }
    for (const o of organismos) {
      await addDoc(collection(db, 'organismos'), o);
    }
    for (const e of expedientes) {
      await addDoc(collection(db, 'expedientes'), e);
    }
    for (const a of actividad) {
      await addDoc(collection(db, 'actividad'), a);
    }
    console.log('seedTestData: datos cargados OK');
    process.exit(0);
  } catch (err) {
    console.error('seedTestData error', err);
    process.exit(1);
  }
}

seed();
