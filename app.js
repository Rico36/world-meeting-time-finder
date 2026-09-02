const cities = [
  ['New York','United States','America/New_York','US','US-NY'],['Los Angeles','United States','America/Los_Angeles','US','US-CA'],['Chicago','United States','America/Chicago','US','US-IL'],['San Juan','Puerto Rico','America/Puerto_Rico','PR',null],['Toronto','Canada','America/Toronto','CA','CA-ON'],['Vancouver','Canada','America/Vancouver','CA','CA-BC'],['Mexico City','Mexico','America/Mexico_City','MX','MX-CMX'],['São Paulo','Brazil','America/Sao_Paulo','BR','BR-SP'],['Buenos Aires','Argentina','America/Argentina/Buenos_Aires','AR','AR-C'],
  ['London','United Kingdom','Europe/London','GB','GB-ENG'],['Dublin','Ireland','Europe/Dublin','IE',null],['Paris','France','Europe/Paris','FR','FR-IDF'],['Berlin','Germany','Europe/Berlin','DE','DE-BE'],['Madrid','Spain','Europe/Madrid','ES','ES-MD'],['Lisbon','Portugal','Europe/Lisbon','PT','PT-11'],['Rome','Italy','Europe/Rome','IT','IT-RM'],['Amsterdam','Netherlands','Europe/Amsterdam','NL','NL-NH'],['Zurich','Switzerland','Europe/Zurich','CH','CH-ZH'],['Stockholm','Sweden','Europe/Stockholm','SE','SE-AB'],['Warsaw','Poland','Europe/Warsaw','PL','PL-14'],['Athens','Greece','Europe/Athens','GR','GR-I'],
  ['Cairo','Egypt','Africa/Cairo','EG','EG-C'],['Johannesburg','South Africa','Africa/Johannesburg','ZA','ZA-GP'],['Nairobi','Kenya','Africa/Nairobi','KE','KE-30'],['Dubai','United Arab Emirates','Asia/Dubai','AE','AE-DU'],['Istanbul','Türkiye','Europe/Istanbul','TR','TR-34'],['Mumbai','India','Asia/Kolkata','IN','IN-MH'],['Delhi','India','Asia/Kolkata','IN','IN-DL'],['Bangkok','Thailand','Asia/Bangkok','TH','TH-10'],['Singapore','Singapore','Asia/Singapore','SG',null],['Hong Kong','Hong Kong','Asia/Hong_Kong','HK',null],['Shanghai','China','Asia/Shanghai','CN','CN-SH'],['Beijing','China','Asia/Shanghai','CN','CN-BJ'],['Tokyo','Japan','Asia/Tokyo','JP','JP-13'],['Seoul','South Korea','Asia/Seoul','KR','KR-11'],
  ['Perth','Australia','Australia/Perth','AU','AU-WA'],['Sydney','Australia','Australia/Sydney','AU','AU-NSW'],['Melbourne','Australia','Australia/Melbourne','AU','AU-VIC'],['Auckland','New Zealand','Pacific/Auckland','NZ','NZ-AUK'],['Honolulu','United States','Pacific/Honolulu','US','US-HI']
].map(([name,country,zone,countryCode,subdivision]) => ({name,country,zone,countryCode,subdivision}));

const copy = {
  en:{language:'Language',advertisement:'Advertisement',eyebrow:'Free world meeting time finder',headline:'Find the best meeting time across time zones.',subhead:'Add two or more cities, choose a date and meeting length, and instantly see the most convenient hours for everyone.',plannerTitle:'Plan a meeting',startCity:'Where are you?',addCity:'Add another city',cityPlaceholder:'Type any city or country…',add:'Add',meetingDay:'Meeting day',duration:'Duration',autoUpdate:'Results update automatically',bestOverlap:'Best overlap',bestCompromise:'Best compromise',compromiseHint:'This is the closest match to normal working hours. Try a nearby day or adjust the time to compare alternatives.',copy:'Copy',share:'Share',adjustTime:'Adjust meeting time',adjustHint:'Drag to explore, or move in 30-minute steps.',workingHours:'Normal working hours',selectedMeeting:'Selected meeting',legendHelp:'Green shows when a city is normally at work; the darker band is your chosen meeting.',simpleTitle:'Simple by design',simpleCopy:'No account required. Dates and times stay in your browser. Holiday checks use country-level public calendar data.',footer:'A friendly world meeting time finder.',selectCity:'Choose a specific city from the suggestions.',minimumCities:'Add at least two cities to compare.',holiday:'Public holiday',weekend:'Weekend',copied:'Copied!',yourTimeZone:'Your time zone',searching:'Searching places…',noMatches:'No matching places found.'},
  es:{language:'Idioma',advertisement:'Publicidad',eyebrow:'Buscador de horarios mundiales',headline:'Encuentra una buena hora para todos.',subhead:'Compara ciudades, elige un día y encuentra las horas que funcionan sin calcular zonas horarias.',plannerTitle:'Planificar una reunión',addCity:'Añadir otra ciudad',cityPlaceholder:'Buscar ciudad o país…',add:'Añadir',meetingDay:'Día de reunión',duration:'Duración',autoUpdate:'Los resultados se actualizan automáticamente',bestOverlap:'Mejor coincidencia',bestCompromise:'Mejor alternativa',compromiseHint:'Esta es la opción más cercana al horario laboral normal. Prueba otro día o ajusta la hora para comparar alternativas.',copy:'Copiar',share:'Compartir',adjustTime:'Ajustar hora',adjustHint:'Arrastra para explorar o avanza en intervalos de 30 minutos.',workingHours:'Horario laboral normal',selectedMeeting:'Reunión seleccionada',legendHelp:'El verde muestra el horario laboral; la franja oscura es la reunión elegida.',simpleTitle:'Simple por diseño',simpleCopy:'No requiere cuenta. Las fechas y horas permanecen en tu navegador.',footer:'Un buscador de horarios mundiales amigable.',selectCity:'Elige una ciudad de la lista.',minimumCities:'Conserva al menos dos ciudades.',holiday:'Día festivo',weekend:'Fin de semana',copied:'¡Copiado!'},
  fr:{language:'Langue',advertisement:'Publicité',eyebrow:'Outil de réunion mondiale',headline:'Trouvez une bonne heure pour tout le monde.',subhead:'Comparez les villes, choisissez un jour et trouvez les heures compatibles sans calcul de fuseaux.',plannerTitle:'Planifier une réunion',addCity:'Ajouter une ville',cityPlaceholder:'Rechercher une ville ou un pays…',add:'Ajouter',meetingDay:'Jour de réunion',duration:'Durée',autoUpdate:'Les résultats se mettent à jour automatiquement',bestOverlap:'Meilleur créneau',bestCompromise:'Meilleur compromis',compromiseHint:'C’est l’option la plus proche des heures de travail habituelles. Essayez un autre jour ou ajustez l’heure.',copy:'Copier',share:'Partager',adjustTime:'Ajuster l’heure',adjustHint:'Faites glisser ou avancez par pas de 30 minutes.',workingHours:'Heures de travail normales',selectedMeeting:'Réunion sélectionnée',legendHelp:'Le vert indique les heures de travail; la bande foncée est votre réunion.',simpleTitle:'Simple par conception',simpleCopy:'Aucun compte requis. Les dates et heures restent dans votre navigateur.',footer:'Un outil convivial pour les réunions mondiales.',selectCity:'Choisissez une ville dans la liste.',minimumCities:'Gardez au moins deux villes.',holiday:'Jour férié',weekend:'Week-end',copied:'Copié !'},
  de:{language:'Sprache',advertisement:'Anzeige',eyebrow:'Weltweite Terminplanung',headline:'Finde eine gute Zeit für alle.',subhead:'Vergleiche Städte, wähle einen Tag und finde passende Zeiten ohne Zeitzonenrechnen.',plannerTitle:'Meeting planen',addCity:'Weitere Stadt hinzufügen',cityPlaceholder:'Stadt oder Land suchen…',add:'Hinzufügen',meetingDay:'Besprechungstag',duration:'Dauer',autoUpdate:'Ergebnisse werden automatisch aktualisiert',bestOverlap:'Beste Überschneidung',bestCompromise:'Bester Kompromiss',compromiseHint:'Dies ist die beste Annäherung an normale Arbeitszeiten. Probiere einen anderen Tag oder passe die Uhrzeit an.',copy:'Kopieren',share:'Teilen',adjustTime:'Zeit anpassen',adjustHint:'Ziehe den Regler oder gehe in 30-Minuten-Schritten.',workingHours:'Normale Arbeitszeit',selectedMeeting:'Ausgewähltes Meeting',legendHelp:'Grün zeigt die Arbeitszeit; der dunkle Bereich ist das Meeting.',simpleTitle:'Bewusst einfach',simpleCopy:'Kein Konto nötig. Datum und Uhrzeit bleiben in deinem Browser.',footer:'Ein freundlicher weltweiter Terminplaner.',selectCity:'Wähle eine Stadt aus der Liste.',minimumCities:'Mindestens zwei Städte behalten.',holiday:'Feiertag',weekend:'Wochenende',copied:'Kopiert!'},
  pt:{language:'Idioma',advertisement:'Publicidade',eyebrow:'Horário mundial de reuniões',headline:'Encontre um bom horário para todos.',subhead:'Compare cidades, escolha um dia e encontre horários compatíveis sem calcular fusos.',plannerTitle:'Planejar reunião',addCity:'Adicionar outra cidade',cityPlaceholder:'Buscar cidade ou país…',add:'Adicionar',meetingDay:'Dia da reunião',duration:'Duração',autoUpdate:'Os resultados são atualizados automaticamente',bestOverlap:'Melhor sobreposição',bestCompromise:'Melhor alternativa',compromiseHint:'Esta é a opção mais próxima do horário normal de trabalho. Tente outro dia ou ajuste o horário para comparar.',copy:'Copiar',share:'Compartilhar',adjustTime:'Ajustar horário',adjustHint:'Arraste para explorar ou avance em passos de 30 minutos.',workingHours:'Horário normal de trabalho',selectedMeeting:'Reunião selecionada',legendHelp:'O verde mostra o horário de trabalho; a faixa escura é a reunião escolhida.',simpleTitle:'Simples por design',simpleCopy:'Sem necessidade de conta. Datas e horários ficam no seu navegador.',footer:'Um localizador amigável de horários mundiais.',selectCity:'Escolha uma cidade da lista.',minimumCities:'Mantenha pelo menos duas cidades.',holiday:'Feriado',weekend:'Fim de semana',copied:'Copiado!'}
};

const pageCopy = {
  en:{headline:'Find the best meeting time across time zones',subhead:'Compare cities, working hours, dates and holidays to find a convenient international meeting time—free.',howEyebrow:'How it works',howTitle:'Plan a meeting across time zones in seconds',step1Title:'Add each city.',step1Copy:'Search for the locations where participants will join.',step2Title:'Choose the meeting.',step2Copy:'Set the date and how long the conversation should last.',step3Title:'Compare common hours.',step3Copy:'Review local times, normal working hours, weekends and holiday notices.',guidesEyebrow:'Helpful guides',guidesTitle:'Make international scheduling easier',guideConverterTitle:'Meeting time-zone converter',guideConverterCopy:'Understand local times and convert a proposed meeting for every participant.',guidePlannerTitle:'International meeting planner',guidePlannerCopy:'Use a practical checklist for fair, workable meetings across countries.',guideDstTitle:'Daylight saving and holidays',guideDstCopy:'Avoid the date changes and public holidays that commonly disrupt global meetings.',faqEyebrow:'Frequently asked questions',faqTitle:'Meeting time-zone questions',faq1Question:'Does Common Hours account for daylight saving time?',faq1Answer:'Yes. Times are calculated for the selected meeting date using each city’s time zone, including applicable daylight-saving changes.',faq2Question:'Are public holidays excluded from the results?',faq2Answer:'No. Holidays are displayed as notices so you can make the final decision rather than having possible meeting times removed automatically.',faq3Question:'What does the green area mean?',faq3Answer:'Green represents normal weekday working hours for each city. The darker band shows the meeting time you are currently considering.',faq4Question:'Do I need an account?',faq4Answer:'No. Common Hours is free to use and does not require registration. Your selected cities and preferences stay in your browser.',navHow:'How it works',navGuides:'Guides',navFaq:'FAQ',navPrivacy:'Privacy'},
  es:{headline:'Encuentra la mejor hora de reunión entre zonas horarias',subhead:'Compara ciudades, horarios laborales, fechas y festivos para encontrar gratis una hora conveniente para una reunión internacional.',howEyebrow:'Cómo funciona',howTitle:'Planifica una reunión entre zonas horarias en segundos',step1Title:'Añade cada ciudad.',step1Copy:'Busca los lugares desde donde participará cada persona.',step2Title:'Elige la reunión.',step2Copy:'Define la fecha y la duración de la conversación.',step3Title:'Compara las horas comunes.',step3Copy:'Revisa horas locales, horarios laborales, fines de semana y avisos de festivos.',guidesEyebrow:'Guías útiles',guidesTitle:'Haz más sencilla la planificación internacional',guideConverterTitle:'Conversor de zonas horarias para reuniones',guideConverterCopy:'Comprende las horas locales y convierte una propuesta para cada participante.',guidePlannerTitle:'Planificador de reuniones internacionales',guidePlannerCopy:'Sigue una lista práctica para organizar reuniones justas entre países.',guideDstTitle:'Horario de verano y festivos',guideDstCopy:'Evita los cambios de fecha y festivos que suelen afectar las reuniones globales.',faqEyebrow:'Preguntas frecuentes',faqTitle:'Preguntas sobre reuniones y zonas horarias',faq1Question:'¿Common Hours contempla el horario de verano?',faq1Answer:'Sí. Las horas se calculan para la fecha elegida con la zona horaria de cada ciudad y sus cambios de horario aplicables.',faq2Question:'¿Se excluyen los festivos de los resultados?',faq2Answer:'No. Los festivos aparecen como avisos para que tú tomes la decisión final.',faq3Question:'¿Qué significa el área verde?',faq3Answer:'El verde representa el horario laboral normal de lunes a viernes. La franja más oscura indica la reunión elegida.',faq4Question:'¿Necesito una cuenta?',faq4Answer:'No. Common Hours es gratis y no exige registro. Las ciudades y preferencias permanecen en tu navegador.',navHow:'Cómo funciona',navGuides:'Guías',navFaq:'Preguntas',navPrivacy:'Privacidad'},
  fr:{headline:'Trouvez la meilleure heure de réunion entre fuseaux horaires',subhead:'Comparez les villes, heures de travail, dates et jours fériés pour trouver gratuitement une heure de réunion internationale pratique.',howEyebrow:'Fonctionnement',howTitle:'Planifiez une réunion entre fuseaux horaires en quelques secondes',step1Title:'Ajoutez chaque ville.',step1Copy:'Recherchez les lieux depuis lesquels les participants se connecteront.',step2Title:'Choisissez la réunion.',step2Copy:'Indiquez la date et la durée de la conversation.',step3Title:'Comparez les heures communes.',step3Copy:'Vérifiez les heures locales, heures de travail, week-ends et jours fériés.',guidesEyebrow:'Guides utiles',guidesTitle:'Simplifiez la planification internationale',guideConverterTitle:'Convertisseur de fuseaux horaires',guideConverterCopy:'Comprenez les heures locales et convertissez une proposition pour chaque participant.',guidePlannerTitle:'Planificateur de réunion internationale',guidePlannerCopy:'Suivez une liste pratique pour organiser des réunions équitables entre pays.',guideDstTitle:'Heure d’été et jours fériés',guideDstCopy:'Évitez les changements de date et jours fériés qui perturbent les réunions mondiales.',faqEyebrow:'Questions fréquentes',faqTitle:'Questions sur les réunions et fuseaux horaires',faq1Question:'Common Hours tient-il compte de l’heure d’été ?',faq1Answer:'Oui. Les heures sont calculées pour la date choisie selon le fuseau de chaque ville et les changements d’heure applicables.',faq2Question:'Les jours fériés sont-ils exclus des résultats ?',faq2Answer:'Non. Ils sont affichés comme avertissements afin que vous puissiez prendre la décision finale.',faq3Question:'Que signifie la zone verte ?',faq3Answer:'Le vert représente les heures de travail habituelles en semaine. La bande plus foncée indique la réunion choisie.',faq4Question:'Ai-je besoin d’un compte ?',faq4Answer:'Non. Common Hours est gratuit et sans inscription. Vos villes et préférences restent dans votre navigateur.',navHow:'Fonctionnement',navGuides:'Guides',navFaq:'FAQ',navPrivacy:'Confidentialité'},
  de:{headline:'Finde die beste Meetingzeit über Zeitzonen hinweg',subhead:'Vergleiche Städte, Arbeitszeiten, Daten und Feiertage, um kostenlos eine passende internationale Meetingzeit zu finden.',howEyebrow:'So funktioniert es',howTitle:'Plane ein Meeting über Zeitzonen hinweg in Sekunden',step1Title:'Füge jede Stadt hinzu.',step1Copy:'Suche die Orte, von denen die Teilnehmenden teilnehmen.',step2Title:'Wähle das Meeting.',step2Copy:'Lege Datum und Gesprächsdauer fest.',step3Title:'Vergleiche gemeinsame Zeiten.',step3Copy:'Prüfe Ortszeiten, Arbeitszeiten, Wochenenden und Feiertagshinweise.',guidesEyebrow:'Hilfreiche Leitfäden',guidesTitle:'Internationale Terminplanung leicht gemacht',guideConverterTitle:'Zeitzonen-Umrechner für Meetings',guideConverterCopy:'Verstehe Ortszeiten und rechne einen Vorschlag für alle Teilnehmenden um.',guidePlannerTitle:'Internationaler Meetingplaner',guidePlannerCopy:'Nutze eine praktische Checkliste für faire Meetings zwischen Ländern.',guideDstTitle:'Sommerzeit und Feiertage',guideDstCopy:'Vermeide Datumswechsel und Feiertage, die globale Meetings oft stören.',faqEyebrow:'Häufige Fragen',faqTitle:'Fragen zu Meetings und Zeitzonen',faq1Question:'Berücksichtigt Common Hours die Sommerzeit?',faq1Answer:'Ja. Die Zeiten werden für das gewählte Datum anhand der Zeitzone jeder Stadt und der geltenden Zeitumstellung berechnet.',faq2Question:'Werden Feiertage aus den Ergebnissen entfernt?',faq2Answer:'Nein. Feiertage erscheinen als Hinweise, damit du die endgültige Entscheidung treffen kannst.',faq3Question:'Was bedeutet der grüne Bereich?',faq3Answer:'Grün zeigt die üblichen Arbeitszeiten an Werktagen. Das dunklere Band zeigt das gewählte Meeting.',faq4Question:'Brauche ich ein Konto?',faq4Answer:'Nein. Common Hours ist kostenlos und erfordert keine Registrierung. Städte und Einstellungen bleiben im Browser.',navHow:'So funktioniert es',navGuides:'Leitfäden',navFaq:'FAQ',navPrivacy:'Datenschutz'},
  pt:{headline:'Encontre o melhor horário de reunião entre fusos horários',subhead:'Compare cidades, horários de trabalho, datas e feriados para encontrar gratuitamente um horário conveniente para uma reunião internacional.',howEyebrow:'Como funciona',howTitle:'Planeje uma reunião entre fusos horários em segundos',step1Title:'Adicione cada cidade.',step1Copy:'Pesquise os locais de onde os participantes entrarão.',step2Title:'Escolha a reunião.',step2Copy:'Defina a data e quanto tempo a conversa deve durar.',step3Title:'Compare horários em comum.',step3Copy:'Veja horários locais, expediente normal, fins de semana e avisos de feriados.',guidesEyebrow:'Guias úteis',guidesTitle:'Facilite o agendamento internacional',guideConverterTitle:'Conversor de fusos para reuniões',guideConverterCopy:'Entenda os horários locais e converta uma proposta para cada participante.',guidePlannerTitle:'Planejador de reuniões internacionais',guidePlannerCopy:'Use uma lista prática para reuniões justas e viáveis entre países.',guideDstTitle:'Horário de verão e feriados',guideDstCopy:'Evite mudanças de data e feriados que costumam afetar reuniões globais.',faqEyebrow:'Perguntas frequentes',faqTitle:'Perguntas sobre reuniões e fusos horários',faq1Question:'O Common Hours considera o horário de verão?',faq1Answer:'Sim. Os horários são calculados para a data escolhida usando o fuso de cada cidade e as mudanças aplicáveis.',faq2Question:'Os feriados são excluídos dos resultados?',faq2Answer:'Não. Eles aparecem como avisos para que você tome a decisão final.',faq3Question:'O que significa a área verde?',faq3Answer:'O verde representa o expediente normal nos dias úteis. A faixa mais escura mostra a reunião escolhida.',faq4Question:'Preciso de uma conta?',faq4Answer:'Não. O Common Hours é gratuito e não exige cadastro. Cidades e preferências ficam no seu navegador.',navHow:'Como funciona',navGuides:'Guias',navFaq:'Perguntas',navPrivacy:'Privacidade'}
};

const positioningCopy = {
  en:{eyebrow:'Holiday-aware international meeting planner',headline:'Find a meeting time that works—and isn’t a holiday there.',subhead:'Compare local working hours and public holidays across countries before scheduling your international meeting.',guideDstTitle:'International public holidays and meeting planning',guideDstCopy:'Check holidays, date changes and daylight-saving shifts before you schedule across countries.',holidayCheck:'Holiday check by location',workingDay:'Working day',checkingHolidays:'Checking local holidays…',holidayUnavailable:'Holiday status unavailable'},
  es:{eyebrow:'Planificador internacional con festivos',headline:'Encuentra una hora que funcione y que allí no sea festivo.',subhead:'Compara horarios laborales y festivos entre países antes de programar tu reunión internacional.',guideDstTitle:'Festivos internacionales y planificación de reuniones',guideDstCopy:'Comprueba festivos, cambios de fecha y horario antes de programar entre países.',holidayCheck:'Comprobación de festivos por ubicación',workingDay:'Día laborable',checkingHolidays:'Comprobando festivos locales…',holidayUnavailable:'Estado de festivo no disponible'},
  fr:{eyebrow:'Planificateur international avec jours fériés',headline:'Trouvez une heure qui convient sans tomber sur un jour férié.',subhead:'Comparez les heures de travail et jours fériés entre pays avant de planifier votre réunion internationale.',guideDstTitle:'Jours fériés internationaux et planification',guideDstCopy:'Vérifiez jours fériés, changements de date et d’heure avant de planifier entre pays.',holidayCheck:'Vérification des jours fériés par lieu',workingDay:'Jour ouvré',checkingHolidays:'Vérification des jours fériés…',holidayUnavailable:'Statut du jour férié indisponible'},
  de:{eyebrow:'Internationaler Planer mit Feiertagsprüfung',headline:'Finde eine Meetingzeit, die passt—und dort kein Feiertag ist.',subhead:'Vergleiche Arbeitszeiten und Feiertage verschiedener Länder, bevor du dein internationales Meeting planst.',guideDstTitle:'Internationale Feiertage und Meetingplanung',guideDstCopy:'Prüfe Feiertage, Datumswechsel und Zeitumstellungen vor der länderübergreifenden Planung.',holidayCheck:'Feiertagsprüfung nach Ort',workingDay:'Arbeitstag',checkingHolidays:'Lokale Feiertage werden geprüft…',holidayUnavailable:'Feiertagsstatus nicht verfügbar'},
  pt:{eyebrow:'Planejador internacional com feriados',headline:'Encontre um horário que funcione e não seja feriado por lá.',subhead:'Compare horários de trabalho e feriados entre países antes de marcar sua reunião internacional.',guideDstTitle:'Feriados internacionais e planejamento de reuniões',guideDstCopy:'Confira feriados, mudanças de data e de horário antes de agendar entre países.',holidayCheck:'Verificação de feriados por local',workingDay:'Dia útil',checkingHolidays:'Verificando feriados locais…',holidayUnavailable:'Status de feriado indisponível'}
};

const qualityCopy = {
  en:{methodEyebrow:'How holiday checking works',methodTitle:'Useful warnings, with honest limits',methodIntro:'Common Hours checks the meeting’s local date in every selected city against public-calendar information. When a nationwide holiday is found, it appears beside that city so the organizer can confirm availability before sending an invitation.',methodCoverageTitle:'What the check covers',methodCoverageCopy:'The tool looks for nationwide public holidays and known local calendar entries. India’s three fixed national holidays—Republic Day, Independence Day and Gandhi Jayanti—also have built-in coverage when the external calendar cannot provide results.',methodLimitsTitle:'What no calendar can know',methodLimitsCopy:'Regional observances, substitute days, company shutdowns, school breaks and personal leave can differ. If coverage is unavailable, the site says so instead of incorrectly calling the date a normal working day.',methodUseTitle:'How to use a warning',methodUseCopy:'Holiday notices are not automatic exclusions. Confirm the observance with the local participant, then keep the proposed time, choose a nearby day or adjust the meeting. The people attending always make the final decision.'},
  es:{methodEyebrow:'Cómo se comprueban los festivos',methodTitle:'Avisos útiles con límites claros',methodIntro:'Common Hours comprueba la fecha local de la reunión en cada ciudad con información de calendarios públicos. Si encuentra un festivo nacional, lo muestra para confirmar la disponibilidad antes de invitar.',methodCoverageTitle:'Qué cubre',methodCoverageCopy:'Busca festivos nacionales y entradas conocidas de calendarios locales. También incluye los tres festivos nacionales fijos de India cuando la fuente externa no responde.',methodLimitsTitle:'Lo que ningún calendario conoce',methodLimitsCopy:'Las celebraciones regionales, días sustitutos, cierres empresariales y permisos personales varían. Si no hay datos, el sitio lo indica en lugar de asumir un día laborable.',methodUseTitle:'Cómo usar el aviso',methodUseCopy:'Un aviso no excluye automáticamente la fecha. Confírmalo con el participante local y decide si mantener la hora, elegir otro día o ajustarla.'},
  fr:{methodEyebrow:'Fonctionnement du contrôle des jours fériés',methodTitle:'Des avertissements utiles aux limites claires',methodIntro:'Common Hours vérifie la date locale dans chaque ville à partir de calendriers publics. Un jour férié national apparaît afin de confirmer la disponibilité avant l’invitation.',methodCoverageTitle:'Ce qui est couvert',methodCoverageCopy:'L’outil recherche les jours fériés nationaux et certaines données locales. Les trois dates nationales fixes de l’Inde sont aussi intégrées quand la source externe ne répond pas.',methodLimitsTitle:'Ce qu’un calendrier ignore',methodLimitsCopy:'Observances régionales, jours de remplacement, fermetures d’entreprise et congés personnels varient. Si les données manquent, le site le dit au lieu de supposer un jour ouvré.',methodUseTitle:'Utiliser un avertissement',methodUseCopy:'Un avertissement n’exclut pas automatiquement la date. Confirmez avec la personne locale, puis gardez l’heure, changez de jour ou ajustez la réunion.'},
  de:{methodEyebrow:'So funktioniert die Feiertagsprüfung',methodTitle:'Nützliche Hinweise mit klaren Grenzen',methodIntro:'Common Hours prüft das lokale Meetingdatum jeder Stadt anhand öffentlicher Kalender. Ein nationaler Feiertag wird angezeigt, damit die Verfügbarkeit vor der Einladung bestätigt werden kann.',methodCoverageTitle:'Was geprüft wird',methodCoverageCopy:'Das Tool sucht nationale Feiertage und bekannte lokale Kalendereinträge. Indiens drei feste nationale Feiertage sind auch integriert, wenn die externe Quelle keine Daten liefert.',methodLimitsTitle:'Was kein Kalender wissen kann',methodLimitsCopy:'Regionale Regeln, Ersatztage, Betriebsferien und persönliche Abwesenheiten unterscheiden sich. Fehlen Daten, meldet die Seite das statt fälschlich Arbeitstag anzuzeigen.',methodUseTitle:'Hinweise richtig nutzen',methodUseCopy:'Ein Hinweis schließt das Datum nicht automatisch aus. Kläre ihn mit der Person vor Ort und entscheide dann über Uhrzeit oder Nachbartag.'},
  pt:{methodEyebrow:'Como funciona a verificação de feriados',methodTitle:'Alertas úteis com limites claros',methodIntro:'O Common Hours confere a data local da reunião em cada cidade usando calendários públicos. Um feriado nacional aparece para que a disponibilidade seja confirmada antes do convite.',methodCoverageTitle:'O que é coberto',methodCoverageCopy:'A ferramenta busca feriados nacionais e registros locais conhecidos. Os três feriados nacionais fixos da Índia também estão integrados quando a fonte externa não responde.',methodLimitsTitle:'O que nenhum calendário sabe',methodLimitsCopy:'Observâncias regionais, dias substitutos, fechamentos de empresas e folgas pessoais variam. Se não houver dados, o site informa em vez de presumir um dia útil.',methodUseTitle:'Como usar o alerta',methodUseCopy:'Um alerta não exclui a data automaticamente. Confirme com o participante local e decida se mantém o horário, escolhe outro dia ou ajusta a reunião.'}
};

const builtInNationalHolidays = {
  IN:{'01-26':'Republic Day','08-15':'Independence Day','10-02':'Gandhi Jayanti'}
};

const state = { language:'en', selected:[], date:'', duration:60, slot:20, holidays:new Map(), suggestions:[], restoredFromUrl:false, holidayCheckId:0 };
const els = Object.fromEntries(['language','city-list','city-search','city-search-label','city-suggestions','city-error','add-city','meeting-date','duration','results','result-label','results-title','meeting-summary','compromise-note','selected-day','time-slider','timeline','holiday-notices','copy-result','share-result','previous-day','next-day','earlier','later','theme-toggle'].map(id => [id.replaceAll('-','_'), document.getElementById(id)]));

function t(key){ return qualityCopy[state.language]?.[key] || positioningCopy[state.language]?.[key] || pageCopy[state.language]?.[key] || copy[state.language]?.[key] || qualityCopy.en[key] || positioningCopy.en[key] || pageCopy.en[key] || copy.en[key] || key; }
function track(event, detail={}){ window.dataLayer?.push({event, ...detail}); window.dispatchEvent(new CustomEvent('commonhours:analytics',{detail:{event,...detail}})); }
function localParts(date, zone){ return Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit',weekday:'short',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(date).filter(p=>p.type!=='literal').map(p=>[p.type,p.value])); }
function offsetAt(date, zone){ const p=localParts(date,zone); return Date.UTC(+p.year,+p.month-1,+p.day,+p.hour,+p.minute)-date.getTime(); }
function zonedMidnight(dateText, zone){ const [y,m,d]=dateText.split('-').map(Number); const guess=new Date(Date.UTC(y,m-1,d,0,0)); return new Date(guess.getTime()-offsetAt(guess,zone)); }
function formatTime(date, zone){ return new Intl.DateTimeFormat(state.language,{timeZone:zone,hour:'numeric',minute:'2-digit'}).format(date); }
function formatDay(date, zone){ return new Intl.DateTimeFormat(state.language,{timeZone:zone,weekday:'short',month:'short',day:'numeric'}).format(date); }
function isoLocal(date, zone){ const p=localParts(date,zone); return `${p.year}-${p.month}-${p.day}`; }
function slotDate(slot){ const start=zonedMidnight(state.date,state.selected[0].zone); return new Date(start.getTime()+slot*30*60000); }
function isWorking(date, city, duration=state.duration){ const p=localParts(date,city.zone); const minutes=+p.hour*60 + +p.minute; return !['Sat','Sun'].includes(p.weekday) && minutes>=540 && minutes+duration<=1020; }

function renderCities(){
  const now=new Date();
  els.city_list.innerHTML=state.selected.map((city,index)=>`<div class="city-row"><div class="city-name"><strong>${city.detected?t('yourTimeZone'):city.name}</strong><span>${city.country?`${city.country} · `:''}${city.zone}</span></div><div class="city-clock"><strong>${formatTime(now,city.zone)}</strong><span>${index===0?'Your reference':'Local time now'}</span></div><button class="remove-city" type="button" data-remove="${index}" aria-label="Remove ${city.name}">×</button></div>`).join('');
  els.city_search_label.textContent=state.selected.length?t('addCity'):t('startCity');
}
function setLanguage(lang){ state.language=copy[lang]?lang:'en'; document.documentElement.lang=state.language; els.language.value=state.language; document.querySelectorAll('[data-i18n]').forEach(el=>{el.textContent=t(el.dataset.i18n)}); document.querySelectorAll('[data-i18n-placeholder]').forEach(el=>{el.placeholder=t(el.dataset.i18nPlaceholder)}); renderCities(); if(state.selected.length>=2) renderResults(); localStorage.setItem('commonHoursLanguage',state.language); }
function applyTheme(theme){ document.documentElement.dataset.theme=theme; localStorage.setItem('commonHoursTheme',theme); }

function saveCities(){ localStorage.setItem('commonHoursCitiesV2',JSON.stringify(state.selected)); }
function meetingUrl(){
  const url=new URL(location.href); url.search=''; url.hash='';
  state.selected.forEach(city=>url.searchParams.append('city',[city.name,city.zone,city.countryCode||'',city.subdivision||'',city.country||''].join('|')));
  url.searchParams.set('date',state.date); url.searchParams.set('duration',String(state.duration)); url.searchParams.set('slot',String(state.slot));
  if(state.language!=='en') url.searchParams.set('lang',state.language);
  return url;
}
function updateMeetingUrl(){ if(state.selected.length>=2) history.replaceState(null,'',meetingUrl()); }
function restoreFromUrl(){
  const params=new URLSearchParams(location.search); const encoded=params.getAll('city');
  if(encoded.length<2) return false;
  const restored=encoded.slice(0,5).map(value=>{ const [name,zone,countryCode,subdivision,country]=value.split('|'); return {name,zone,countryCode:countryCode||null,subdivision:subdivision||null,country:country||''}; }).filter(city=>city.name&&city.zone);
  if(restored.length<2) return false;
  state.selected=restored;
  const date=params.get('date'); if(/^\d{4}-\d{2}-\d{2}$/.test(date||'')) state.date=date;
  const duration=Number(params.get('duration')); if([30,45,60,90,120].includes(duration)) state.duration=duration;
  const slot=Number(params.get('slot')); if(Number.isInteger(slot)&&slot>=0&&slot<=47) state.slot=slot;
  const lang=params.get('lang'); if(copy[lang]) state.language=lang;
  state.restoredFromUrl=true; saveCities(); return true;
}
function shareText(){ return `${els.result_label.textContent}: ${els.results_title.textContent} — ${els.meeting_summary.textContent}\n\n${meetingUrl().href}`; }
function addSelectedCity(city){
  if(state.selected.some(item=>item.name===city.name && item.zone===city.zone)){ els.city_error.textContent='Already added.'; return; }
  if(state.selected.length>=5){ els.city_error.textContent='Maximum 5 cities.'; return; }
  state.selected.push(city); saveCities(); els.city_search.value=''; els.city_error.textContent=''; els.city_suggestions.hidden=true; renderCities();
  if(state.selected.length>=2) calculate(); else els.results.hidden=true;
  track('city_added',{city:city.name,country:city.countryCode||''});
}

function renderSuggestions(items,status=''){
  els.city_suggestions.replaceChildren();
  if(status){ const line=document.createElement('div'); line.className='city-suggestions-status'; line.textContent=status; els.city_suggestions.append(line); }
  items.forEach((city,index)=>{
    const button=document.createElement('button'); button.type='button'; button.className='city-suggestion'; button.role='option'; button.dataset.suggestion=String(index);
    const name=document.createElement('strong'); name.textContent=city.name;
    const detail=document.createElement('span'); detail.textContent=[city.admin,city.country,city.zone].filter(Boolean).join(' · ');
    button.append(name,detail); els.city_suggestions.append(button);
  });
  els.city_suggestions.hidden=!status && items.length===0;
}

let searchTimer; let searchController;
async function searchPlaces(query){
  const normalized=query.trim();
  if(normalized.length<2){ state.suggestions=[]; renderSuggestions([]); return; }
  const local=cities.filter(city=>`${city.name} ${city.country}`.toLowerCase().includes(normalized.toLowerCase())).slice(0,5).map(city=>({...city,admin:''}));
  state.suggestions=local; renderSuggestions(local,t('searching'));
  searchController?.abort(); searchController=new AbortController();
  try{
    const response=await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(normalized)}&count=8&language=${state.language}&format=json`,{signal:searchController.signal});
    if(!response.ok) throw new Error('Search unavailable');
    const data=await response.json();
    const remote=(data.results||[]).filter(place=>place.timezone).map(place=>({name:place.name,country:place.country||'',admin:place.admin1||'',zone:place.timezone,countryCode:place.country_code||null,subdivision:null}));
    const combined=[...local,...remote].filter((city,index,array)=>array.findIndex(item=>item.name===city.name&&item.zone===city.zone)===index).slice(0,8);
    state.suggestions=combined; renderSuggestions(combined,combined.length?'':t('noMatches'));
  }catch(error){ if(error.name!=='AbortError'){ state.suggestions=local; renderSuggestions(local,local.length?'':t('noMatches')); } }
}

function restoreOrDetectReference(){
  if(restoreFromUrl()) return;
  try{
    const saved=JSON.parse(localStorage.getItem('commonHoursCitiesV2')||'[]');
    if(Array.isArray(saved)&&saved.length){ state.selected=saved.filter(city=>city?.zone&&city?.name&&!city.detected).slice(0,5); if(state.selected.length)return; }
  }catch{}
}

function findBestSlot(){
  const needed=Math.ceil(state.duration/30);
  let best={slot:20,score:-1,perfect:false};
  for(let slot=0;slot<=48-needed;slot++){
    let score=0; let perfect=true;
    for(const city of state.selected){
      for(let part=0;part<needed;part++){
        const good=isWorking(slotDate(slot+part),city,30);
        score+=good?1:0; perfect&&=good;
      }
    }
    if(perfect) return {slot,score,perfect:true};
    if(score>best.score) best={slot,score,perfect:false};
  }
  return best;
}
function slotIsPerfect(){
  const needed=Math.ceil(state.duration/30);
  return state.selected.every(city=>Array.from({length:needed},(_,part)=>isWorking(slotDate(state.slot+part),city,30)).every(Boolean));
}

async function holidayFor(city,date){
  if(!city.countryCode) return false;
  const localDate=isoLocal(date,city.zone); const year=localDate.slice(0,4); const key=`${city.countryCode}-${year}`;
  const fixedHoliday=builtInNationalHolidays[city.countryCode]?.[localDate.slice(5)];
  if(fixedHoliday) return {name:fixedHoliday,nationalHoliday:true,builtIn:true};
  if(!state.holidays.has(key)){
    try{
      const response=await fetch(`https://nagerholidays.com/api/v4/Holidays/${city.countryCode}/${year}`);
      if(!response.ok) throw new Error('Holiday data unavailable');
      state.holidays.set(key,await response.json());
    }catch{ state.holidays.set(key,false); }
  }
  const holidays=state.holidays.get(key);
  if(holidays===false) return false;
  return holidays.find(h=>h.date===localDate && (h.nationalHoliday || !h.subdivisionCodes?.length || h.subdivisionCodes.includes(city.subdivision))) || null;
}

function renderResults(isCompromise=!slotIsPerfect()){
  if(state.selected.length<2){ els.results.hidden=true; return; }
  els.results.hidden=false;
  const start=slotDate(state.slot); const end=new Date(start.getTime()+state.duration*60000);
  els.result_label.textContent=t(isCompromise?'bestCompromise':'bestOverlap');
  els.results_title.textContent=`${formatTime(start,state.selected[0].zone)}–${formatTime(end,state.selected[0].zone)} ${state.selected[0].name}`;
  els.meeting_summary.textContent=state.selected.map(c=>`${formatTime(start,c.zone)} ${c.name}`).join(' · ');
  els.compromise_note.hidden=!isCompromise; els.compromise_note.textContent=isCompromise?t('compromiseHint'):'';
  els.selected_day.textContent=formatDay(start,state.selected[0].zone);
  els.time_slider.value=state.slot;
  const width=Math.max(2,(state.duration/1440)*100); const left=(state.slot/48)*100;
  els.timeline.innerHTML=state.selected.map(city=>{
    const slots=Array.from({length:48},(_,slot)=>`<span class="slot ${isWorking(slotDate(slot),city,30)?'working':''}"></span>`).join('');
    return `<div class="timeline-row"><div class="timeline-city"><strong>${city.name}</strong><span>${formatDay(start,city.zone)} · ${formatTime(start,city.zone)}</span></div><div class="timeline-track" data-track><div class="slot-grid">${slots}</div><span class="meeting-band" style="left:${left}%;width:${width}%"></span></div></div>`;
  }).join('');
  document.querySelectorAll('.slot-grid').forEach(grid=>{ grid.style.display='grid'; grid.style.gridTemplateColumns='repeat(48,1fr)'; grid.style.position='absolute'; grid.style.inset='0'; });
  updateMeetingUrl();
  checkHolidays(start);
}

async function checkHolidays(start){
  const checkId=++state.holidayCheckId;
  els.holiday_notices.innerHTML=`<div class="holiday-notice status-loading">◌ ${t('checkingHolidays')}</div>`;
  const notices=[];
  for(const city of state.selected){
    const parts=localParts(start,city.zone);
    const holiday=await holidayFor(city,start);
    if(holiday) notices.push({kind:'warning',icon:'⚑',text:`${city.name}: ${t('holiday')} — ${holiday.name}`});
    else if(['Sat','Sun'].includes(parts.weekday)) notices.push({kind:'warning',icon:'●',text:`${city.name}: ${t('weekend')}`});
    else if(holiday===false) notices.push({kind:'muted',icon:'○',text:`${city.name}: ${t('holidayUnavailable')}`});
    else notices.push({kind:'ok',icon:'✓',text:`${city.name}: ${t('workingDay')}`});
  }
  if(checkId!==state.holidayCheckId) return;
  els.holiday_notices.innerHTML=notices.map(n=>`<div class="holiday-notice status-${n.kind}">${n.icon} ${n.text}</div>`).join('');
}

function calculate(){ if(state.selected.length<2){ els.city_error.textContent=t('minimumCities'); els.results.hidden=true; return; } els.city_error.textContent=''; const best=findBestSlot(); state.slot=best.slot; renderResults(!best.perfect); track('overlap_calculated',{cities:state.selected.length,duration:state.duration}); }
function shiftDay(amount){ const d=new Date(`${state.date}T12:00:00Z`); d.setUTCDate(d.getUTCDate()+amount); state.date=d.toISOString().slice(0,10); els.meeting_date.value=state.date; calculate(); }
function shiftTime(amount){ state.slot=Math.max(0,Math.min(47,state.slot+amount)); renderResults(); track('time_adjusted',{slot:state.slot}); }

els.city_search.addEventListener('input',()=>{ clearTimeout(searchTimer); searchTimer=setTimeout(()=>searchPlaces(els.city_search.value),220); });
els.city_search.addEventListener('focus',()=>{ if(state.suggestions.length) renderSuggestions(state.suggestions); });
els.city_suggestions.addEventListener('click',event=>{ const button=event.target.closest('[data-suggestion]'); if(button) addSelectedCity(state.suggestions[Number(button.dataset.suggestion)]); });
els.add_city.addEventListener('click',()=>{ if(state.suggestions.length) addSelectedCity(state.suggestions[0]); else { els.city_error.textContent=t('selectCity'); searchPlaces(els.city_search.value); } });
els.city_list.addEventListener('click',event=>{ const button=event.target.closest('[data-remove]'); if(!button)return; state.selected.splice(Number(button.dataset.remove),1); saveCities(); renderCities(); if(state.selected.length>=2) calculate(); else els.results.hidden=true; });
els.meeting_date.addEventListener('change',()=>{state.date=els.meeting_date.value;calculate();});
els.duration.addEventListener('change',()=>{state.duration=Number(els.duration.value);calculate();track('duration_changed',{duration:state.duration});});
els.time_slider.addEventListener('input',()=>{state.slot=Number(els.time_slider.value);renderResults();});
els.earlier.addEventListener('click',()=>shiftTime(-1)); els.later.addEventListener('click',()=>shiftTime(1));
els.previous_day.addEventListener('click',()=>shiftDay(-1)); els.next_day.addEventListener('click',()=>shiftDay(1));
els.language.addEventListener('change',()=>setLanguage(els.language.value));
els.theme_toggle.addEventListener('click',()=>applyTheme(document.documentElement.dataset.theme==='dark'?'light':'dark'));
els.city_search.addEventListener('keydown',event=>{ if(event.key==='Enter'){ event.preventDefault(); els.add_city.click(); } });
document.addEventListener('click',event=>{ if(!event.target.closest('.city-add-row')) els.city_suggestions.hidden=true; });
els.timeline.addEventListener('click',event=>{ const trackEl=event.target.closest('[data-track]'); if(!trackEl)return; const box=trackEl.getBoundingClientRect(); state.slot=Math.max(0,Math.min(47,Math.round(((event.clientX-box.left)/box.width)*48))); renderResults(); });
els.copy_result.addEventListener('click',async()=>{await navigator.clipboard.writeText(shareText()); els.copy_result.textContent=t('copied'); setTimeout(()=>els.copy_result.textContent=t('copy'),1200); track('result_copied');});
els.share_result.addEventListener('click',async()=>{const url=meetingUrl().href; const text=`${els.result_label.textContent}: ${els.results_title.textContent} — ${els.meeting_summary.textContent}`; if(navigator.share) await navigator.share({title:'Common Hours',text,url}); else await navigator.clipboard.writeText(`${text}\n\n${url}`); track('result_shared');});

const browserLanguage=(navigator.language||'en').slice(0,2); state.language=localStorage.getItem('commonHoursLanguage') || (copy[browserLanguage]?browserLanguage:'en');
state.date=new Date().toISOString().slice(0,10); restoreOrDetectReference(); els.meeting_date.value=state.date; els.duration.value=String(state.duration); applyTheme(localStorage.getItem('commonHoursTheme') || (matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light')); setLanguage(state.language); if(state.selected.length>=2){ if(state.restoredFromUrl) renderResults(); else calculate(); } else els.city_search.focus();
