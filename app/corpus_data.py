"""Hand-written building blocks for the SYNTHETIC cold-start corpus (see corpus.py).

Entry format:  "text|urgency|subtype"  (urgency: l/m/h/c  = low/medium/high/critical, subtype only for requests: g/i/c)
These are NOT real citizen texts. They exist so the model works on day one; real feedback from officials replaces them.
"""

SITUATIONS: dict[str, dict[str, list[str]]] = {
    "atencion_ciudadano": {
        "venues": ["la ventanilla de atención al ciudadano", "la oficina de radicación", "el punto de atención", "la línea de atención"],
        "requests": [
            "información sobre los horarios y requisitos para radicar un trámite|m|i",
            "que me indiquen el estado de mi solicitud radicada hace dos semanas|m|i",
            "la dirección de la oficina donde puedo presentar mis documentos|l|i",
            "que me orienten sobre a qué dependencia debo dirigir mi caso|m|g",
            "un turno prioritario para atender mi trámite pendiente|m|g",
            "que me confirmen si recibieron los documentos que envié por correo|m|i",
        ],
        "failures": [
            "la página web no permite radicar mi solicitud desde hace varios días",
            "nadie contesta la línea de atención al ciudadano",
            "radiqué un documento hace un mes y no me han dado respuesta",
            "me enviaron de una oficina a otra sin resolver mi caso",
            "el sistema de turnos no funciona y pasamos horas de pie",
        ],
        "suggestions": [
            "habiliten una opción de citas por internet para evitar filas",
            "pongan una cartelera con los requisitos de cada trámite en la entrada",
            "envíen mensajes de texto cuando haya cambios en el estado de la solicitud",
            "amplíen el horario de atención al público los sábados",
        ],
        "irregularities": [
            "en la ventanilla le dan prioridad a ciertas personas que conocen a los funcionarios",
            "un tramitador cobra por conseguir turnos en la oficina de atención",
            "se pierden radicados de manera sospechosa en la oficina de correspondencia",
        ],
    },
    "salud": {
        "venues": ["el hospital local", "la secretaría de salud", "el puesto de salud del barrio", "la IPS asignada", "la EPS"],
        "requests": [
            "la copia de mi historia clínica del hospital|l|i",
            "que me asignen una cita con medicina general en el puesto de salud|m|g",
            "información sobre las jornadas de vacunación de este mes|l|i",
            "que autoricen los medicamentos formulados para mi tratamiento|h|g",
            "un concepto sobre si mi afiliación al régimen subsidiado sigue vigente|m|c",
            "que me informen cómo afiliar a mi hijo recién nacido al sistema de salud|m|g",
            "el traslado urgente de mi padre a una clínica con unidad de cuidados intensivos|c|g",
        ],
        "failures": [
            "llevo tres meses esperando una cita con el especialista y no me la asignan",
            "la EPS no entrega los medicamentos de mi mamá, que es adulta mayor y diabética",
            "en el hospital no hay médicos de turno en urgencias por las noches",
            "me negaron la atención por no tener el carné actualizado",
            "la ambulancia tardó más de dos horas en llegar a la vereda y el paciente empeoró",
            "no han entregado los resultados de los exámenes que me hicieron hace un mes",
        ],
        "suggestions": [
            "amplíen el horario del puesto de salud para que los trabajadores podamos ir",
            "pongan citas por WhatsApp para no madrugar a hacer fila",
            "organicen brigadas de salud en las veredas apartadas",
            "tengan un módulo de información en el hospital para orientar a los pacientes",
        ],
        "irregularities": [
            "en el hospital cobran por debajo de la mesa para dar citas más rápido",
            "un funcionario de la secretaría de salud vende los cupos de las brigadas de vacunación",
            "las EPS están entregando medicamentos vencidos a pacientes crónicos",
            "una clínica factura servicios que nunca prestó a pacientes del régimen subsidiado",
        ],
    },
    "movilidad": {
        "venues": ["la secretaría de movilidad", "el punto de atención de tránsito", "la sede de tránsito", "el patio de vehículos"],
        "requests": [
            "información sobre cómo pagar y consultar un comparendo|l|i",
            "la copia de la resolución con la que me impusieron una fotomulta|m|i",
            "que me indiquen los requisitos para renovar la licencia de conducción|l|i",
            "la revisión de un semáforo dañado en la esquina de mi casa|m|g",
            "un concepto sobre si mi vehículo está exento del pico y placa|m|c",
            "el levantamiento de la inmovilización de mi vehículo en el patio|h|g",
        ],
        "failures": [
            "me llegó una fotomulta por una infracción que nunca cometí",
            "llevo meses esperando el traspaso de mi vehículo y el trámite no avanza",
            "el semáforo de la avenida lleva una semana dañado y hay trancones y choques",
            "el bus de la ruta de mi barrio pasa cada hora y llega repleto",
            "me cobraron dos veces la matrícula del vehículo",
            "no hay señalización en la curva donde ya han ocurrido varios accidentes",
        ],
        "suggestions": [
            "instalen reductores de velocidad frente al colegio del sector",
            "habiliten un carril exclusivo para bicicletas en la avenida principal",
            "pongan una aplicación para ver en tiempo real la ubicación de los buses",
            "amplíen las rutas de transporte público hacia las veredas",
        ],
        "irregularities": [
            "agentes de tránsito piden dinero para no inmovilizar vehículos",
            "en la sede de tránsito hay tramitadores que cobran por agilizar traspasos",
            "los parqueaderos autorizados cobran tarifas ilegales por los vehículos inmovilizados",
            "un contratista de semaforización instaló equipos que nunca funcionaron y cobró la obra completa",
        ],
    },
    "hacienda": {
        "venues": ["la secretaría de hacienda", "la oficina de impuestos", "la ventanilla de recaudo", "la tesorería"],
        "requests": [
            "el paz y salvo del impuesto predial de mi casa|m|i",
            "la devolución del dinero que pagué por duplicado en el impuesto vehicular|m|g",
            "información sobre las fechas y descuentos del pago del impuesto predial|l|i",
            "que me aclaren si debo declarar el impuesto de industria y comercio de mi tienda|m|c",
            "un acuerdo de pago para las cuotas atrasadas de valorización|m|g",
            "el levantamiento del embargo de mi cuenta por un cobro coactivo ya pagado|h|g",
        ],
        "failures": [
            "me cobraron dos veces el impuesto predial y el banco no devuelve el dinero",
            "la factura del impuesto llegó con un avalúo que no corresponde a mi casa",
            "el sistema no reconoce mi pago y me siguen enviando cobros coactivos",
            "me embargaron la cuenta por una deuda que ya había cancelado",
            "la liquidación de industria y comercio tiene un valor muy superior al que declaré",
        ],
        "suggestions": [
            "permitan pagar el impuesto predial en cuotas sin intereses",
            "envíen la factura por correo electrónico y no solo en papel",
            "den descuentos a quienes paguen antes de la fecha límite",
            "publiquen una guía sencilla para entender la factura del impuesto",
        ],
        "irregularities": [
            "un funcionario de cobro coactivo ofrece borrar deudas a cambio de dinero",
            "se están dejando de cobrar impuestos a grandes empresas mientras se persigue a los pequeños propietarios",
            "en la tesorería hay recibos de pago que desaparecen para cobrar de nuevo",
        ],
    },
    "infraestructura": {
        "venues": ["la secretaría de obras públicas", "la oficina de infraestructura", "la interventoría de la obra"],
        "requests": [
            "el arreglo del hueco que hay frente a mi casa|m|g",
            "información sobre el cronograma de pavimentación de mi barrio|l|i",
            "la copia del contrato de la obra del puente de la vereda|m|i",
            "que instalen alumbrado público en el parque donde juegan los niños|m|g",
            "la reparación urgente del andén que se hundió y ya hubo caídas|h|g",
            "la limpieza de la alcantarilla que se desborda cada vez que llueve|m|g",
        ],
        "failures": [
            "el hueco de la vía principal lleva meses sin arreglarse y ya dañó varios vehículos",
            "la obra de la calle quedó abandonada y los escombros bloquean el paso",
            "las lámparas del alumbrado público llevan dos semanas apagadas y hay robos",
            "el puente peatonal está en mal estado y la comunidad teme que se caiga",
            "el contratista dejó la vía a medio pavimentar desde el año pasado",
            "un poste inclinado está a punto de caer sobre la calle|c",
        ],
        "suggestions": [
            "pavimenten primero las vías por donde pasa el transporte escolar",
            "pongan una línea para reportar huecos desde el celular",
            "hagan mantenimiento preventivo de las vías antes de la temporada de lluvias",
            "publiquen en carteles el avance de cada obra para que la comunidad la vigile",
        ],
        "irregularities": [
            "el contratista de la obra de la avenida usa material de mala calidad y la interventoría no dice nada",
            "se pagó la totalidad de una obra que solo está ejecutada en un treinta por ciento",
            "el contrato de mantenimiento vial se adjudicó a dedo a una empresa de un familiar del funcionario",
        ],
    },
    "educacion": {
        "venues": ["la secretaría de educación", "el colegio público del sector", "la rectoría", "la oficina de matrículas"],
        "requests": [
            "un cupo escolar para mi hijo de siete años en el colegio del barrio|h|g",
            "el certificado de estudios de mi hija del año pasado|l|i",
            "información sobre el programa de alimentación escolar y cómo inscribirme|l|i",
            "que me expliquen los requisitos para acceder a una beca universitaria|m|g",
            "el traslado de mi hijo a otro colegio por problemas de acoso escolar|h|g",
            "un concepto sobre si el colegio puede negar la matrícula por deuda de pensión|m|c",
        ],
        "failures": [
            "el restaurante escolar no entrega los almuerzos completos a los niños",
            "el transporte escolar de la vereda no ha funcionado en todo el mes",
            "mi hijo lleva dos meses sin profesor de matemáticas en el colegio",
            "el colegio no entregó los certificados que necesito para inscribirme a la universidad",
            "las aulas tienen goteras y los estudiantes se mojan cuando llueve",
        ],
        "suggestions": [
            "abran más cupos en el colegio del barrio para evitar viajes largos",
            "incluyan clases de inglés y tecnología desde primaria",
            "mejoren la conectividad a internet en las escuelas rurales",
            "hagan jornadas de orientación vocacional para los estudiantes de once",
        ],
        "irregularities": [
            "en el colegio venden los cupos escolares por dinero",
            "el rector se queda con parte del dinero de la alimentación escolar",
            "un docente acosa a las estudiantes y las directivas no han hecho nada",
            "el contratista del restaurante escolar entrega menos raciones de las que cobra",
        ],
    },
    "ambiente": {
        "venues": ["la secretaría de ambiente", "la autoridad ambiental", "la oficina de gestión ambiental"],
        "requests": [
            "la poda de un árbol enorme que amenaza con caer sobre las casas|h|g",
            "información sobre los permisos ambientales de la empresa vecina|m|i",
            "que midan el ruido de la fábrica que opera frente a mi casa|m|g",
            "el concepto técnico sobre la tala de árboles en el parque del barrio|m|c",
            "que revisen la contaminación de la quebrada que cruza mi vereda|m|g",
            "la copia de la licencia ambiental del proyecto minero cercano|m|i",
        ],
        "failures": [
            "la fábrica del barrio emite humo negro todas las noches y nadie lo controla",
            "arrojan basura y escombros a la quebrada y el olor es insoportable",
            "talaron los árboles del parque sin avisar a la comunidad",
            "el ruido de la planta industrial no nos deja dormir desde hace meses",
            "hay maltrato a perros callejeros y la entidad no responde a las llamadas",
        ],
        "suggestions": [
            "siembren árboles nativos en las orillas de la quebrada",
            "pongan canecas de reciclaje en los parques del sector",
            "hagan campañas de adopción de mascotas y esterilización gratuita",
            "creen un punto limpio para recibir escombros y electrodomésticos",
        ],
        "irregularities": [
            "una empresa vierte residuos químicos al río durante la noche para evitar controles",
            "se están talando árboles en zona protegida con permisos presuntamente falsos",
            "un funcionario ambiental recibe dinero para no sancionar a una curtiembre",
        ],
    },
    "planeacion": {
        "venues": ["la oficina de planeación", "la curaduría urbana", "la secretaría de planeación"],
        "requests": [
            "el certificado de estratificación de mi vivienda|l|i",
            "información sobre los requisitos de la licencia de construcción|l|i",
            "un concepto sobre el uso del suelo permitido en mi lote|m|c",
            "que revisen la construcción ilegal que está levantando mi vecino|m|g",
            "la corrección del estrato de mi casa que quedó mal clasificado|m|g",
            "que me aclaren si puedo ampliar mi casa en segundo piso|m|c",
        ],
        "failures": [
            "llevo seis meses esperando la licencia de construcción y no avanza el trámite",
            "invadieron el andén con una construcción y no dejan pasar a los peatones",
            "el estrato de mi casa está mal y pago tarifas de servicios más altas",
            "los vendedores ocuparon todo el espacio público del parque",
            "construyeron un edificio sin licencia y la oficina no ha hecho nada pese a mis quejas",
        ],
        "suggestions": [
            "publiquen un mapa digital con el uso del suelo de cada predio",
            "reduzcan los tiempos de la licencia de construcción con trámite en línea",
            "recuperen el espacio público ocupado por parqueaderos informales",
            "hagan jornadas de socialización del plan de ordenamiento territorial",
        ],
        "irregularities": [
            "una constructora edifica con más pisos de los permitidos y el funcionario firma las licencias a cambio de dinero",
            "se entregan licencias de construcción en zonas de riesgo presuntamente por favores políticos",
            "hay loteadores ilegales que venden predios en zona de protección con complicidad de funcionarios",
        ],
    },
    "servicios_publicos": {
        "venues": ["la empresa de acueducto", "la empresa de energía", "la empresa de aseo", "la oficina de servicios públicos"],
        "requests": [
            "la reconexión del servicio de agua en mi vivienda|h|g",
            "la copia de mi factura de energía de los últimos seis meses|l|i",
            "información sobre las rutas y horarios de recolección de basuras|l|i",
            "que revisen el medidor de agua porque marca un consumo exagerado|m|g",
            "un concepto sobre si pueden cortarme el servicio mientras reclamo la factura|m|c",
            "la instalación del servicio de gas natural en mi barrio|m|g",
        ],
        "failures": [
            "llevamos tres días sin agua en el barrio y no han dicho cuándo la restablecen",
            "la factura de energía llegó con un valor tres veces mayor al habitual",
            "el camión de la basura no pasa hace dos semanas y se acumulan los residuos",
            "me cortaron el servicio de agua aunque estoy al día en los pagos",
            "hay apagones todos los días en la vereda y se dañan los electrodomésticos",
            "la presión del agua es tan baja que no sube al segundo piso",
        ],
        "suggestions": [
            "avisen con anticipación por mensaje de texto los cortes programados",
            "instalen puntos de recolección de aceite usado y reciclables",
            "permitan pagar las facturas por aplicación móvil",
            "hagan mantenimiento a las tuberías antes de que revienten",
        ],
        "irregularities": [
            "un técnico de la empresa de energía cobra por reconectar el servicio sin factura",
            "hay conexiones fraudulentas de agua que el personal de la empresa conoce y permite",
            "la empresa de aseo cobra por rutas que no recorre",
        ],
    },
    "seguridad": {
        "venues": ["la inspección de policía", "la estación de policía", "la comisaría", "la secretaría de seguridad"],
        "requests": [
            "que aumenten las rondas de patrullaje en mi barrio por las noches|m|g",
            "información sobre cómo solicitar cámaras de seguridad comunitarias|l|i",
            "que verifiquen el bar que funciona sin permiso y con música a todo volumen|m|g",
            "una medida de protección porque mi vecino me amenaza|h|g",
            "un concepto sobre el horario permitido para venta de licor en mi zona|m|c",
            "que atiendan la riña constante que ocurre en la esquina de mi casa|m|g",
        ],
        "failures": [
            "hay atracos todos los días en el paradero y no hay presencia de la policía",
            "llamé al cuadrante tres veces por una riña y nunca llegaron",
            "el bar del barrio hace ruido hasta las cuatro de la madrugada y no pasa nada",
            "la inspección de policía no ha resuelto mi caso de perturbación a la posesión hace un año",
            "venden drogas frente al colegio y las denuncias no tienen respuesta",
        ],
        "suggestions": [
            "instalen cámaras de vigilancia en los parques y paraderos",
            "creen frentes de seguridad con apoyo de la policía en cada barrio",
            "mejoren la iluminación de los callejones donde ocurren los robos",
            "hagan talleres de convivencia para los vecinos y los comerciantes",
        ],
        "irregularities": [
            "un agente de policía recibe dinero del dueño de un bar para permitir que funcione fuera de horario",
            "hay una banda de microtráfico que opera con la protección de uniformados",
            "en la inspección de policía le piden dinero a los vecinos para tramitar sus querellas",
        ],
    },
    "control_interno": {
        "venues": ["la alcaldía", "la secretaría general", "la oficina de contratación", "la dependencia"],
        "requests": [
            "el estado de la investigación disciplinaria que radiqué contra un funcionario|m|i",
            "la copia del expediente del proceso de contratación de la obra|m|i",
            "que me informen quién es el responsable de la dependencia donde ocurrieron los hechos|m|g",
            "un concepto sobre si un servidor puede contratar con la entidad siendo familiar del secretario|m|c",
            "que me certifiquen si el funcionario tiene sanciones disciplinarias vigentes|m|i",
        ],
        "failures": [
            "el proceso disciplinario que inicié lleva un año sin ninguna actuación",
            "la oficina de control interno no ha respondido mi solicitud de investigación",
            "mi queja contra un servidor fue archivada sin explicarme las razones",
            "no me entregan copia de las actuaciones de mi propio caso disciplinario",
        ],
        "suggestions": [
            "publiquen los contratos y sus soportes en la página web de la entidad",
            "habiliten un canal anónimo y seguro para denunciar a servidores públicos",
            "rotén a los funcionarios que llevan años en las áreas de contratación",
            "hagan rendición de cuentas abierta con la comunidad cada semestre",
        ],
        "irregularities": [
            "el secretario adjudicó un contrato millonario a la empresa de su cuñado",
            "un funcionario de contratación pide un porcentaje a cambio de adjudicar licitaciones",
            "hay nepotismo: varios familiares del alcalde fueron nombrados sin concurso",
            "se hicieron pagos por obras que nunca se ejecutaron, hay presunto peculado",
            "un servidor público me pidió dinero para entregarme un certificado que es gratuito",
        ],
    },
    "desarrollo_social": {
        "venues": ["la oficina de desarrollo social", "la comisaría de familia", "el punto de atención a víctimas", "la oficina del Sisbén"],
        "requests": [
            "la inclusión de mi madre de ochenta años en el programa Colombia Mayor|h|g",
            "información sobre cómo encuestarme en el Sisbén|l|i",
            "la ayuda humanitaria para mi familia desplazada por la violencia|c|g",
            "que me expliquen cómo acceder al subsidio de vivienda|m|g",
            "una medida de protección por violencia intrafamiliar|c|g",
            "el certificado de discapacidad de mi hijo para acceder a los beneficios|m|i",
        ],
        "failures": [
            "llevo seis meses sin recibir el subsidio del adulto mayor que me aprobaron",
            "el Sisbén me clasificó en un grupo que no corresponde a mi situación",
            "la comisaría de familia no ha atendido mi denuncia de violencia intrafamiliar|c",
            "no han entregado el mercado de ayuda humanitaria a las familias de la vereda",
            "mi nombre desapareció de la lista de beneficiarios de Familias en Acción",
        ],
        "suggestions": [
            "hagan jornadas del Sisbén en las veredas para que los campesinos no viajen",
            "creen un comedor comunitario para los adultos mayores del barrio",
            "den cursos de formación para madres cabeza de hogar",
            "pongan un puesto móvil de atención a víctimas en los barrios periféricos",
        ],
        "irregularities": [
            "un funcionario cobra dinero para incluir personas en los listados de subsidios",
            "los mercados de ayuda humanitaria se entregan a personas que no los necesitan por amistad",
            "en el programa de adulto mayor aparecen personas fallecidas cobrando el subsidio",
        ],
    },
}

# Quejas are about the conduct of a public servant, independent of the dependency.
QUEJA_SERVANTS = ["el funcionario", "la funcionaria", "el servidor público", "la servidora que me atendió", "el vigilante de la entrada", "el coordinador", "la persona de la ventanilla"]
QUEJA_CONDUCTS = [
    ("me atendió con groserías y sin ningún respeto", "m"),
    ("se negó a recibir mis documentos sin darme una explicación", "m"),
    ("me hizo esperar cuatro horas y luego me dijo que volviera otro día", "m"),
    ("me gritó delante de todos cuando pregunté por mi trámite", "m"),
    ("no quiso darme su nombre ni su cargo", "m"),
    ("me trató de manera humillante por mi condición", "h"),
    ("se burló de mi situación y no quiso orientarme", "m"),
    ("rechazó atender a mi madre, que tiene ochenta y dos años, y la dejó esperando de pie", "h"),
    ("fue indolente con mi hijo menor de edad y no quiso ayudarnos", "h"),
    ("me dio información equivocada y por eso perdí el plazo del trámite", "m"),
    ("estuvo hablando por celular y no me prestó atención", "m"),
    ("fue prepotente y me dijo que no tenía por qué atenderme", "m"),
]

OPENINGS = ["", "", "Buenos días.", "Cordial saludo.", "Respetados señores:", "Señores de la Alcaldía:", "Buenas tardes,", "Estimados funcionarios:", "A quien corresponda:", "Hola, buenas.", "Buen día."]
CLOSINGS = ["", "", "", "Agradezco su pronta respuesta.", "Quedo atento a su respuesta.", "Gracias por su atención.", "Cordialmente,", "Muchas gracias.", "Espero una respuesta dentro de los términos de ley."]

PETITION_WRAPPERS = [
    "Solicito {x}.", "Me permito solicitar {x}.", "En ejercicio del derecho de petición (artículo 23 de la Constitución) solicito {x}.",
    "Quisiera solicitar {x}.", "Respetuosamente solicito {x}.", "Necesito {x}.", "Por medio de la presente solicito {x}.", "Les ruego {x}.",
]
RECLAMO_WRAPPERS = [
    "Presento un reclamo porque {x}.", "Reclamo porque {x}.", "Quiero reclamar: {x}.", "Exijo una solución, pues {x}.",
    "Mi reclamo es el siguiente: {x}.", "{X}. Exijo que se resuelva esta situación.", "No puedo más con esto: {x}.", "{X}, por favor corrijan este mal servicio.",
]
SUGGESTION_WRAPPERS = [
    "Sugiero que {x}.", "Propongo que {x}.", "Sería bueno que {x}.", "Me gustaría sugerir que {x}.", "Recomiendo que {x}.",
    "Tengo una idea para mejorar el servicio: que {x}.", "Sería conveniente que {x}.", "Una sugerencia: que {x}.",
]
DENUNCIA_WRAPPERS = [
    "Denuncio que {x}.", "Quiero denunciar que {x}.", "Presento denuncia: {x}.", "Pongo en conocimiento de las autoridades que {x}.",
    "Denuncio presuntas irregularidades: {x}.", "Hago esta denuncia porque {x}.", "Presuntamente {x}.",
]
QUEJA_WRAPPERS = [
    "Presento queja contra {s} de {v} porque {c}.", "Quiero poner una queja: {s} de {v} {c}.", "Queja por mala atención en {v}: {s} {c}.",
    "Mi queja es contra {s} ({v}), que {c}.", "En {v}, {s} {c}. Presento esta queja formal.",
]

URGENCY_CUES = {
    "c": ["Es una emergencia, hay riesgo para la vida de personas.", "Por favor actúen ya: hay peligro de muerte.", "Hay niños en riesgo inminente.", "Esto no da espera, es peligro inminente."],
    "h": ["Es urgente.", "Mi madre es adulta mayor y no puede esperar.", "Hay una persona con discapacidad afectada.", "Ya se venció el término legal para responder.", "Llevo meses esperando y está en juego un derecho fundamental.", "Necesito una respuesta con urgencia.", "Si no se resuelve interpondré una tutela."],
    "l": ["No es urgente, cuando puedan.", "Sin afán.", "Es una idea a futuro.", "Cuando tengan tiempo."],
    "m": ["", "", ""],
}

BARRIOS = ["San José", "La Esperanza", "El Prado", "Santa Ana", "Villa del Sol", "Los Alpes", "El Carmen", "La Floresta", "Bellavista", "San Fernando", "Ciudad Jardín", "Las Palmas", "El Recreo", "La Candelaria"]
CITIES = ["Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga", "Pereira", "Manizales", "Ibagué", "Neiva", "Pasto", "Tunja", "Montería"]
NAMES = ["Carlos Pérez", "María Rodríguez", "Luis Gómez", "Ana Martínez", "Jorge Ramírez", "Claudia Torres", "Andrés Castro", "Laura Herrera"]
