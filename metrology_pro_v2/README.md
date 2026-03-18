# Metrology Pro v2.0

**Sistema de calibración y verificación metrológica conforme a ISO 10360-2 / VDI/VDE 2617**

Aplicación web local para gestión completa de calibraciones de máquinas de medición
por coordenadas (CMM) y máquinas herramienta. Funciona de forma independiente en
Windows y Linux sin necesidad de conexión a internet.

---

## Características

- **Gestión de calibraciones**: Registro de sesiones con datos del equipo, operador y
  condiciones ambientales (temperatura, humedad).
- **Carga de datos CSV**: Importación de mediciones con validación automática. Soporta
  múltiples ejes (X, Y, Z), dirección (forward/backward) y ciclos de repetición.
- **Informe ISO 10360-2**: Cálculo automático de:
  - Error de indicación (E_UNI) — rango de error unidireccional
  - Error medio y sistemático
  - Repetibilidad (desviación estándar agrupada)
  - Histéresis (diferencia forward/backward)
  - Incertidumbre expandida U (k=2, nivel de confianza ~95%)
  - Verificación MPE (error máximo permisible del fabricante)
- **Historial**: Consulta y filtrado de todas las calibraciones.
- **Análisis de deriva**: Evolución temporal del error por máquina y eje con
  gráficas SVG interactivas.
- **Interfaz profesional**: Dashboard con panel de estado, gráficos y tablas.

---

## Requisitos

- **Python 3.10 o superior**
- Navegador web moderno (Chrome, Firefox, Edge, Safari)
- No requiere conexión a internet (las dependencias se instalan una sola vez)

---

## Instalación y ejecución

### Windows

1. Descarga e instala Python desde https://www.python.org/downloads/
   (marca "Add Python to PATH" durante la instalación)
2. Descomprime el archivo del proyecto
3. Haz doble clic en `start.bat`
4. El navegador se abrirá automáticamente en http://127.0.0.1:8000

### Linux

```bash
# Instala Python si no lo tienes
sudo apt install python3 python3-pip   # Debian/Ubuntu
sudo dnf install python3 python3-pip   # Fedora/RHEL

# Da permisos al launcher y ejecútalo
chmod +x start.sh
./start.sh
```

### Manual (cualquier sistema)

```bash
pip install -r requirements.txt
python run.py
```

---

## Formato del archivo CSV

El CSV debe contener las columnas `nominal` y `measured` (valores en milímetros).
Las demás columnas son opcionales:

| Columna   | Obligatoria | Descripción                            | Valores           |
|-----------|:-----------:|----------------------------------------|--------------------|
| nominal   | Sí          | Valor nominal del patrón (mm)          | Numérico           |
| measured  | Sí          | Valor medido por la máquina (mm)       | Numérico           |
| axis      | No          | Eje de medición                        | X, Y, Z            |
| direction | No          | Sentido del desplazamiento             | forward, backward  |
| run       | No          | Número de ciclo/repetición             | 1, 2, 3…           |

**Ejemplo:**

```csv
nominal,measured,axis,direction,run
0,0.0012,X,forward,1
50,50.0034,X,forward,1
100,100.0018,X,forward,1
150,150.0045,X,forward,1
200,200.0028,X,forward,1
0,0.0008,X,backward,1
50,50.0029,X,backward,1
100,100.0015,X,backward,1
150,150.0040,X,backward,1
200,200.0022,X,backward,1
```

---

## Flujo de trabajo

1. **Crear calibración** → Registra máquina, operador y condiciones
2. **Cargar datos** → Sube el CSV de mediciones vinculado a la calibración
3. **Generar informe** → Obtén los resultados ISO con gráficas
4. **Historial** → Consulta calibraciones anteriores
5. **Deriva** → Analiza la evolución temporal del error

---

## API REST

La documentación interactiva de la API está disponible en:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

---

## Estructura del proyecto

```
metrology_pro/
├── run.py              # Lanzador multiplataforma
├── start.bat           # Lanzador Windows
├── start.sh            # Lanzador Linux/macOS
├── requirements.txt    # Dependencias Python
├── README.md           # Este archivo
├── app/
│   ├── main.py         # Aplicación FastAPI
│   ├── db.py           # Gestión de base de datos SQLite
│   ├── models.py       # Modelos Pydantic (validación)
│   ├── iso.py          # Motor de cálculos ISO 10360-2
│   ├── routers/
│   │   ├── calibration.py  # CRUD de calibraciones
│   │   ├── upload.py       # Carga de datos CSV
│   │   ├── report.py       # Generación de informes
│   │   ├── history.py      # Historial
│   │   └── analysis.py     # Análisis de deriva
│   └── static/
│       └── index.html      # Interfaz web (SPA)
└── metrology_pro.db        # Base de datos (se crea automáticamente)
```

---

## Normas de referencia

- **ISO 10360-2:2009** — Máquinas de medición por coordenadas. Verificación de longitudes.
- **VDI/VDE 2617** — Exactitud de máquinas de medición por coordenadas.
- **GUM (JCGM 100:2008)** — Guía para la expresión de la incertidumbre de medida.

---

## Licencia

Uso interno / personal. Adaptar según necesidades.
