"""Hand-written evaluation set (NOT generated from the synthetic templates).

Each row: (text, type, dependency, urgency).  Written by hand in the register real citizens use
(informal, typos, long-winded, partial info) to measure generalisation beyond the cold-start corpus.
It is small (see len(REALISTIC)); treat the resulting numbers as indicative, not as a benchmark.
"""

REALISTIC: list[tuple[str, str, str, str]] = [
    ("Buenas tardes, llevo tres semanas esperando que arreglen el hueco que hay frente a mi casa en la calle 45 con carrera 12, ya se me dañó una llanta y pueden ocurrir accidentes.", "reclamo", "infraestructura", "high"),
    ("Solicito respetuosamente copia del contrato de obra número 2345 de 2024 celebrado para la construcción del parque del barrio Santa Lucía.", "peticion", "infraestructura", "low"),
    ("Hace una semana no llega el agua a mi barrio y tengo un bebé de meses, necesito que la empresa de acueducto atienda esto ya.", "reclamo", "servicios_publicos", "critical"),
    ("Quiero poner una queja contra el funcionario de la ventanilla 3 que me trató muy mal y se rió cuando le pregunté por mi trámite.", "queja", "atencion_ciudadano", "medium"),
    ("Me gustaría proponer que instalen más canecas de reciclaje en el parque principal, hay mucha basura los fines de semana.", "sugerencia", "ambiente", "low"),
    ("Denuncio que un funcionario de la oficina de tránsito me pidió 200 mil pesos para agilizar el trámite de mi licencia.", "denuncia", "control_interno", "high"),
    ("Mi papá tiene 80 años y lleva dos meses esperando una cita con el especialista en cardiología, la EPS dice que la secretaría no ha autorizado.", "reclamo", "salud", "high"),
    ("Por favor me informan cuál es el procedimiento y los requisitos para solicitar una licencia de construcción para una casa de dos pisos.", "peticion", "planeacion", "low"),
    ("Pagué el impuesto predial en enero y todavía me aparece como deudor, necesito el paz y salvo urgente porque tengo escritura el viernes.", "reclamo", "hacienda", "high"),
    ("Hay un árbol enorme a punto de caerse sobre la vivienda de mi vecina en la carrera 7 con 20, está inclinado y con las lluvias puede caer en cualquier momento.", "reclamo", "ambiente", "critical"),
    ("Quisiera consultar si es posible que la alcaldía considere una ciclorruta en la avenida principal, sería de gran ayuda para los estudiantes.", "sugerencia", "movilidad", "low"),
    ("El semáforo de la esquina de la 30 con 5 lleva días dañado y casi atropellan a un niño ayer, por favor envíen a alguien.", "reclamo", "movilidad", "critical"),
    ("Solicito se me informe el estado de mi solicitud de subsidio de arriendo radicada hace dos meses, nadie me da razón.", "peticion", "desarrollo_social", "medium"),
    ("Mi hijo no ha podido ser matriculado en ningún colegio público del sector y las clases ya empezaron, necesito un cupo.", "peticion", "educacion", "high"),
    ("En el barrio hay venta de drogas todas las noches en la esquina del parque y la policía no hace nada, tengo miedo por mis hijos.", "denuncia", "seguridad", "high"),
    ("El profesor de matemáticas del colegio distrital acosa a las estudiantes, varias niñas me lo han contado. Esto es grave.", "denuncia", "educacion", "critical"),
    ("Agradezco que me expliquen cómo puedo pagar el impuesto de vehículos en cuotas porque no cuento con todo el dinero.", "peticion", "hacienda", "low"),
    ("Una fuga de gas en el edificio de la calle 10 #5-20 huele muy fuerte desde esta mañana, la gente está asustada.", "reclamo", "servicios_publicos", "critical"),
    ("La atención en el punto de atención al ciudadano es pésima, hacen fila por horas y los funcionarios solo hablan por celular.", "queja", "atencion_ciudadano", "medium"),
    ("Pido que me certifiquen que mi predio no está en zona de riesgo, lo necesito para un crédito de vivienda.", "peticion", "planeacion", "medium"),
    ("Quiero denunciar que la constructora vecina está botando escombros al río y contaminando el agua, ya hay peces muertos.", "denuncia", "ambiente", "high"),
    ("Les escribo para felicitarlos por el nuevo parque, solo sugiero que pongan más bancas y luz en la noche.", "sugerencia", "infraestructura", "low"),
    ("Mi factura de agua llegó por $1.850.000 cuando normalmente pago 60 mil, es un error evidente y solicito revisión.", "reclamo", "servicios_publicos", "medium"),
    ("Deseo saber cuáles son los horarios y los documentos para inscribirme en el programa de adulto mayor.", "peticion", "desarrollo_social", "low"),
    ("Nos tienen sin ambulancia en el centro de salud de la vereda desde hace un mes, una señora casi muere ayer esperando traslado.", "queja", "salud", "critical"),
    ("Quisiera una copia de los estudios técnicos con los que se aprobó el cambio de uso del suelo en el sector de La Floresta.", "peticion", "planeacion", "low"),
    ("Me multaron por un comparendo que no es mío, la placa que aparece es ABC123 y mi carro es otro. Pido que lo anulen.", "reclamo", "movilidad", "medium"),
    ("Señores, el ruido de un bar en el barrio no nos deja dormir, ya van seis meses y nadie viene a controlar el volumen.", "queja", "seguridad", "medium"),
    ("Propongo que se habilite una app para pedir citas en los centros de salud y así evitar las filas desde las 4 de la mañana.", "sugerencia", "salud", "low"),
    ("Denuncio posible nepotismo: la secretaria contrató a su hermano sin concurso y sin cumplir los requisitos del cargo.", "denuncia", "control_interno", "medium"),
]
