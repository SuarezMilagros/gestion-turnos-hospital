import sqlite3
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

class GestionTurnos:
    def __init__(self, db_name: str = "hospital_turnos.db"):
        """Inicializa la conexión a la base de datos"""
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.conectar()
        self.crear_tablas()
    
    def conectar(self):
        """Establece la conexión con la base de datos"""
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            print(f"✓ Conexión exitosa a {self.db_name}")
        except sqlite3.Error as e:
            print(f"✗ Error al conectar: {e}")
    
    def crear_tablas(self):
        """Crea las tablas necesarias si no existen"""
        try:
            # Tabla de Pacientes
            self.cursor.execute('''
                CREATE DATABASE turnos_hospital;
                USE turnos_hospital;
                CREATE TABLE IF NOT EXISTS pacientes (
                    id_paciente INTEGER PRIMARY KEY NOT NULL AUTOINCREMENT,
                    nombre VARCHAR(50) NOT NULL,
                    apellido VARCHAR(50) NOT NULL,
                    dni VARCHAR(20) UNIQUE NOT NULL,
                    fecha_nacimiento DATE NOT NULL,
                    genero VARCHAR(10),
                    telefono VARCHAR(50),
                    domicilio VARCHAR(20)
                )
            ''')
            
            # Tabla de Médicos
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS medicos (
                    id_medico INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre VARCHAR(50) NOT NULL,
                    apellido VARCHAR(50) NOT NULL,
                    especialidad VARCHAR(50) NOT NULL,
                    telefono VARCHAR(50) NOT NULL
                )
            ''')
            
            # Tabla de Turnos
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS turnos (
                    id_turno INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha DATE NOT NULL,
                    horario TIME NOT NULL,
                    id_paciente INT NOT NULL,
                    id_medico INT NOT NULL,
                    id_consultorio INT NOT NULL,
                    FOREIGN KEY (id_paciente) REFERENCES pacientes(id_paciente),
                    FOREIGN KEY (id_medico) REFERENCES medicos(id_medico),
                )
            ''')
            
            self.conn.commit()
            print("✓ Tablas creadas correctamente")
        except sqlite3.Error as e:
            print(f"✗ Error al crear tablas: {e}")
    
    # ==================== PACIENTES ====================
    
    def registrar_paciente(self, nombre: str, apellido: str, dni: str, 
                          fecha_nacimiento: str = None, telefono: str = None, 
                          email: str = None, direccion: str = None) -> Optional[int]:
        """Registra un nuevo paciente"""
        try:
            self.cursor.execute('''
                INSERT INTO pacientes (id_paciente, nombre, apellido, dni, fecha_nacimiento, genero, telefono, domicilio)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (nombre, apellido, dni, fecha_nacimiento, telefono, email, direccion))
            self.conn.commit()
            print(f"✓ Paciente {nombre} {apellido} registrado con ID: {self.cursor.lastrowid}")
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            print(f"✗ Error: Ya existe un paciente con DNI {dni}")
            return None
        except sqlite3.Error as e:
            print(f"✗ Error al registrar paciente: {e}")
            return None
    
    def buscar_paciente_por_dni(self, dni: str) -> Optional[Tuple]:
        """Busca un paciente por su DNI"""
        try:
            self.cursor.execute('SELECT * FROM pacientes WHERE dni = ?', (dni,))
            paciente = self.cursor.fetchone()
            return paciente
        except sqlite3.Error as e:
            print(f"✗ Error al buscar paciente: {e}")
            return None
    
    def listar_pacientes(self) -> List[Tuple]:
        """Lista todos los pacientes"""
        try:
            self.cursor.execute('SELECT * FROM pacientes ORDER BY apellido, nombre')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"✗ Error al listar pacientes: {e}")
            return []
    
    # ==================== MÉDICOS ====================
    
    def registrar_medico(self, nombre: str, apellido: str, especialidad: str, 
                        matricula: str, telefono: str = None, email: str = None) -> Optional[int]:
        """Registra un nuevo médico"""
        try:
            self.cursor.execute('''
                INSERT INTO medicos (nombre, apellido, especialidad, matricula, telefono, email)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nombre, apellido, especialidad, matricula, telefono, email))
            self.conn.commit()
            print(f"✓ Médico {nombre} {apellido} ({especialidad}) registrado con ID: {self.cursor.lastrowid}")
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            print(f"✗ Error: Ya existe un médico con matrícula {matricula}")
            return None
        except sqlite3.Error as e:
            print(f"✗ Error al registrar médico: {e}")
            return None
    
    def listar_medicos(self, especialidad: str = None) -> List[Tuple]:
        """Lista todos los médicos, opcionalmente filtrados por especialidad"""
        try:
            if especialidad:
                self.cursor.execute('SELECT * FROM medicos WHERE especialidad = ? ORDER BY apellido, nombre', (especialidad,))
            else:
                self.cursor.execute('SELECT * FROM medicos ORDER BY especialidad, apellido, nombre')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"✗ Error al listar médicos: {e}")
            return []
    
    # ==================== TURNOS ====================
    
    def crear_turno(self, paciente_id: int, medico_id: int, fecha_hora: str, 
                   duracion: int = 30, motivo_consulta: str = None) -> Optional[int]:
        """Crea un nuevo turno"""
        try:
            # Verificar disponibilidad
            if not self.verificar_disponibilidad(medico_id, fecha_hora, duracion):
                print("✗ El médico no está disponible en ese horario")
                return None
            
            self.cursor.execute('''
                INSERT INTO turnos (paciente_id, medico_id, fecha_hora, duracion, motivo_consulta)
                VALUES (?, ?, ?, ?, ?)
            ''', (paciente_id, medico_id, fecha_hora, duracion, motivo_consulta))
            self.conn.commit()
            print(f"✓ Turno creado con ID: {self.cursor.lastrowid}")
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"✗ Error al crear turno: {e}")
            return None
    
    def verificar_disponibilidad(self, medico_id: int, fecha_hora: str, duracion: int = 30) -> bool:
        """Verifica si el médico está disponible en el horario solicitado"""
        try:
            # Convertir fecha_hora a datetime
            dt = datetime.strptime(fecha_hora, '%Y-%m-%d %H:%M')
            dt_fin = dt + timedelta(minutes=duracion)
            
            self.cursor.execute('''
                SELECT COUNT(*) FROM turnos 
                WHERE medico_id = ? 
                AND estado IN ('pendiente', 'confirmado')
                AND (
                    (datetime(fecha_hora) < datetime(?) AND datetime(fecha_hora, '+' || duracion || ' minutes') > datetime(?))
                    OR
                    (datetime(fecha_hora) >= datetime(?) AND datetime(fecha_hora) < datetime(?))
                )
            ''', (medico_id, dt_fin.strftime('%Y-%m-%d %H:%M'), dt.strftime('%Y-%m-%d %H:%M'),
                  dt.strftime('%Y-%m-%d %H:%M'), dt_fin.strftime('%Y-%m-%d %H:%M')))
            
            count = self.cursor.fetchone()[0]
            return count == 0
        except Exception as e:
            print(f"✗ Error al verificar disponibilidad: {e}")
            return False
    
    def listar_turnos_por_fecha(self, fecha: str) -> List[Tuple]:
        """Lista todos los turnos de una fecha específica"""
        try:
            self.cursor.execute('''
                SELECT t.id, p.nombre, p.apellido, m.nombre, m.apellido, m.especialidad,
                       t.fecha_hora, t.duracion, t.estado, t.motivo_consulta
                FROM turnos t
                JOIN pacientes p ON t.paciente_id = p.id
                JOIN medicos m ON t.medico_id = m.id
                WHERE DATE(t.fecha_hora) = ?
                ORDER BY t.fecha_hora
            ''', (fecha,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"✗ Error al listar turnos: {e}")
            return []
    
    def listar_turnos_paciente(self, paciente_id: int) -> List[Tuple]:
        """Lista todos los turnos de un paciente"""
        try:
            self.cursor.execute('''
                SELECT t.id, m.nombre, m.apellido, m.especialidad,
                       t.fecha_hora, t.duracion, t.estado, t.motivo_consulta
                FROM turnos t
                JOIN medicos m ON t.medico_id = m.id
                WHERE t.paciente_id = ?
                ORDER BY t.fecha_hora DESC
            ''', (paciente_id,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"✗ Error al listar turnos del paciente: {e}")
            return []
    
    def actualizar_estado_turno(self, turno_id: int, nuevo_estado: str, observaciones: str = None) -> bool:
        """Actualiza el estado de un turno"""
        estados_validos = ['pendiente', 'confirmado', 'cancelado', 'completado']
        if nuevo_estado not in estados_validos:
            print(f"✗ Estado inválido. Use uno de: {estados_validos}")
            return False
        
        try:
            if observaciones:
                self.cursor.execute('''
                    UPDATE turnos SET estado = ?, observaciones = ? WHERE id = ?
                ''', (nuevo_estado, observaciones, turno_id))
            else:
                self.cursor.execute('''
                    UPDATE turnos SET estado = ? WHERE id = ?
                ''', (nuevo_estado, turno_id))
            
            self.conn.commit()
            if self.cursor.rowcount > 0:
                print(f"✓ Estado del turno actualizado a: {nuevo_estado}")
                return True
            else:
                print("✗ No se encontró el turno especificado")
                return False
        except sqlite3.Error as e:
            print(f"✗ Error al actualizar estado: {e}")
            return False
    
    # ==================== UTILIDADES ====================
    
    def cerrar_conexion(self):
        """Cierra la conexión con la base de datos"""
        if self.conn:
            self.conn.close()
            print("✓ Conexión cerrada")
    
    def __del__(self):
        """Destructor para asegurar el cierre de la conexión"""
        self.cerrar_conexion()


# ==================== EJEMPLO DE USO ====================

if __name__ == "__main__":
    # Crear instancia del sistema
    sistema = GestionTurnos()
    
    print("\n" + "="*50)
    print("EJEMPLO DE USO DEL SISTEMA")
    print("="*50 + "\n")
    
    # Registrar pacientes
    print("1. REGISTRANDO PACIENTES")
    print("-" * 50)
    paciente1_id = sistema.registrar_paciente(
        "Juan", "Pérez", "12345678", "1980-05-15", 
        "1145678901", "juan.perez@email.com", "Av. Corrientes 1234"
    )
    paciente2_id = sistema.registrar_paciente(
        "María", "González", "87654321", "1992-08-20", 
        "1156789012", "maria.gonzalez@email.com"
    )
    paciente3_id = sistema.registrar_paciente(
        "Milagros", "Suarez", "2432423", "200-14-05",
        "2424232423", "suarezmilagros@email.com", "Av. Corrientes 1324"
    )
    
    # Registrar médicos
    print("\n2. REGISTRANDO MÉDICOS")
    print("-" * 50)
    medico1_id = sistema.registrar_medico(
        "Carlos", "Rodríguez", "Cardiología", "MN12345", 
        "1167890123", "dr.rodriguez@hospital.com"
    )
    medico2_id = sistema.registrar_medico(
        "Ana", "Martínez", "Traumatología", "MN67890", 
        "1178901234", "dra.martinez@hospital.com"
    )
    
    # Crear turnos
    print("\n3. CREANDO TURNOS")
    print("-" * 50)
    if paciente1_id and medico1_id:
        sistema.crear_turno(
            paciente1_id, medico1_id, 
            "2025-11-20 10:00", 30, 
            "Control rutinario"
        )
    
    if paciente2_id and medico2_id:
        sistema.crear_turno(
            paciente2_id, medico2_id, 
            "2025-11-20 11:00", 45, 
            "Dolor de rodilla"
        )
    
    # Listar turnos
    print("\n4. TURNOS DEL DÍA 2025-11-20")
    print("-" * 50)
    turnos = sistema.listar_turnos_por_fecha("2025-11-20")
    for turno in turnos:
        print(f"ID: {turno[0]} | Paciente: {turno[1]} {turno[2]} | "
              f"Médico: {turno[3]} {turno[4]} ({turno[5]}) | "
              f"Hora: {turno[6]} | Estado: {turno[8]}")
    
    # Actualizar estado de turno
    print("\n5. ACTUALIZANDO ESTADO DE TURNO")
    print("-" * 50)
    sistema.actualizar_estado_turno(1, "confirmado", "Paciente confirmó por teléfono")
    
    # Buscar paciente
    print("\n6. BUSCAR PACIENTE POR DNI")
    print("-" * 50)
    paciente = sistema.buscar_paciente_por_dni("2432423")
    if paciente:
        print(f"Encontrado: {paciente[1]} {paciente[2]} - DNI: {paciente[3]}")
    
    print("\n" + "="*50)
    print("FIN DEL EJEMPLO")
    print("="*50 + "\n")
    
    # Cerrar conexión
    sistema.cerrar_conexion()