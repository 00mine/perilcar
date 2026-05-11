// Database comuni italiani — ~1800 comuni principali — offline
// Formato: {n: nome, p: provincia, c: cap}
var COMUNI_DB = [
  {n:"Agrigento",p:"AG",c:"92100"},
  {n:"Canicattì",p:"AG",c:"92024"},
  {n:"Favara",p:"AG",c:"92026"},
  {n:"Licata",p:"AG",c:"92027"},
  {n:"Sciacca",p:"AG",c:"92019"},
  {n:"Porto Empedocle",p:"AG",c:"92014"},
  {n:"Ribera",p:"AG",c:"92016"},
  {n:"Campobello di Licata",p:"AG",c:"92023"},
  {n:"Palma di Montechiaro",p:"AG",c:"92020"},
  {n:"Ravanusa",p:"AG",c:"92029"},
  {n:"Menfi",p:"AG",c:"92013"},
  {n:"Aragona",p:"AG",c:"92021"},
  {n:"Alessandria",p:"AL",c:"15100"},
  {n:"Casale Monferrato",p:"AL",c:"15033"},
  {n:"Novi Ligure",p:"AL",c:"15067"},
  {n:"Tortona",p:"AL",c:"15057"},
  {n:"Acqui Terme",p:"AL",c:"15011"},
  {n:"Valenza",p:"AL",c:"15048"},
  {n:"Ovada",p:"AL",c:"15076"},
  {n:"Asti",p:"AT",c:"14100"},
  {n:"Canelli",p:"AT",c:"14053"},
  {n:"Ancona",p:"AN",c:"60100"},
  {n:"Senigallia",p:"AN",c:"60019"},
  {n:"Fabriano",p:"AN",c:"60044"},
  {n:"Jesi",p:"AN",c:"60035"},
  {n:"Chiaravalle",p:"AN",c:"60033"},
  {n:"Falconara Marittima",p:"AN",c:"60015"},
  {n:"Osimo",p:"AN",c:"60027"},
  {n:"Castelfidardo",p:"AN",c:"60022"},
  {n:"Aosta",p:"AO",c:"11100"},
  {n:"Châtillon",p:"AO",c:"11024"},
  {n:"Saint-Vincent",p:"AO",c:"11027"},
  {n:"Arezzo",p:"AR",c:"52100"},
  {n:"Cortona",p:"AR",c:"52044"},
  {n:"Sansepolcro",p:"AR",c:"52037"},
  {n:"Montevarchi",p:"AR",c:"52025"},
  {n:"San Giovanni Valdarno",p:"AR",c:"52027"},
  {n:"Cavriglia",p:"AR",c:"52022"},
  {n:"Ascoli Piceno",p:"AP",c:"63100"},
  {n:"San Benedetto del Tronto",p:"AP",c:"63074"},
  {n:"Grottammare",p:"AP",c:"63066"},
  {n:"Monteprandone",p:"AP",c:"63076"},
  {n:"Asti",p:"AT",c:"14100"},
  {n:"Canelli",p:"AT",c:"14053"},
  {n:"Nizza Monferrato",p:"AT",c:"14049"},
  {n:"Avellino",p:"AV",c:"83100"},
  {n:"Ariano Irpino",p:"AV",c:"83031"},
  {n:"Atripalda",p:"AV",c:"83042"},
  {n:"Mercato San Severino",p:"SA",c:"84085"},
  {n:"Solofra",p:"AV",c:"83029"},
  {n:"Montoro",p:"AV",c:"83025"},
  {n:"Cervinara",p:"AV",c:"83012"},
  {n:"Mugnano del Cardinale",p:"AV",c:"83027"},
  {n:"Nola",p:"NA",c:"80035"},
  {n:"Baiano",p:"AV",c:"83022"},
  {n:"Sperone",p:"AV",c:"83020"},
  {n:"Bari",p:"BA",c:"70100"},
  {n:"Altamura",p:"BA",c:"70022"},
  {n:"Molfetta",p:"BA",c:"70056"},
  {n:"Corato",p:"BA",c:"70033"},
  {n:"Bitonto",p:"BA",c:"70032"},
  {n:"Modugno",p:"BA",c:"70026"},
  {n:"Gravina in Puglia",p:"BA",c:"70024"},
  {n:"Taranto",p:"TA",c:"74100"},
  {n:"Gioia del Colle",p:"BA",c:"70023"},
  {n:"Ruvo di Puglia",p:"BA",c:"70037"},
  {n:"Terlizzi",p:"BA",c:"70038"},
  {n:"Triggiano",p:"BA",c:"70019"},
  {n:"Casamassima",p:"BA",c:"70010"},
  {n:"Capurso",p:"BA",c:"70010"},
  {n:"Acquaviva delle Fonti",p:"BA",c:"70021"},
  {n:"Palo del Colle",p:"BA",c:"70027"},
  {n:"Bitritto",p:"BA",c:"70020"},
  {n:"Grumo Appula",p:"BA",c:"70025"},
  {n:"Cassano delle Murge",p:"BA",c:"70020"},
  {n:"Monopoli",p:"BA",c:"70043"},
  {n:"Conversano",p:"BA",c:"70014"},
  {n:"Polignano a Mare",p:"BA",c:"70044"},
  {n:"Putignano",p:"BA",c:"70017"},
  {n:"Andria",p:"BT",c:"76123"},
  {n:"Barletta",p:"BT",c:"76121"},
  {n:"Trani",p:"BT",c:"76125"},
  {n:"Canosa di Puglia",p:"BT",c:"76012"},
  {n:"Margherita di Savoia",p:"BT",c:"76016"},
  {n:"San Ferdinando di Puglia",p:"BT",c:"76017"},
  {n:"Spinazzola",p:"BT",c:"76014"},
  {n:"Belluno",p:"BL",c:"32100"},
  {n:"Feltre",p:"BL",c:"32032"},
  {n:"Sedico",p:"BL",c:"32036"},
  {n:"Benevento",p:"BN",c:"82100"},
  {n:"Sant\'Agata de\' Goti",p:"BN",c:"82019"},
  {n:"Montesarchio",p:"BN",c:"82016"},
  {n:"Airola",p:"BN",c:"82011"},
  {n:"Telese Terme",p:"BN",c:"82037"},
  {n:"Ceppaloni",p:"BN",c:"82010"},
  {n:"San Giorgio del Sannio",p:"BN",c:"82018"},
  {n:"Bergamo",p:"BG",c:"24100"},
  {n:"Treviglio",p:"BG",c:"24047"},
  {n:"Romano di Lombardia",p:"BG",c:"24058"},
  {n:"Seriate",p:"BG",c:"24068"},
  {n:"Dalmine",p:"BG",c:"24044"},
  {n:"Caravaggio",p:"BG",c:"24043"},
  {n:"Clusone",p:"BG",c:"24023"},
  {n:"Alzano Lombardo",p:"BG",c:"24022"},
  {n:"Ponte San Pietro",p:"BG",c:"24036"},
  {n:"Stezzano",p:"BG",c:"24040"},
  {n:"Osio Sotto",p:"BG",c:"24046"},
  {n:"Grassobbio",p:"BG",c:"24050"},
  {n:"Biella",p:"BI",c:"13900"},
  {n:"Cossato",p:"BI",c:"13836"},
  {n:"Vigliano Biellese",p:"BI",c:"13856"},
  {n:"Bologna",p:"BO",c:"40100"},
  {n:"Imola",p:"BO",c:"40026"},
  {n:"Casalecchio di Reno",p:"BO",c:"40033"},
  {n:"San Lazzaro di Savena",p:"BO",c:"40068"},
  {n:"Castel Maggiore",p:"BO",c:"40013"},
  {n:"Pianoro",p:"BO",c:"40065"},
  {n:"Zola Predosa",p:"BO",c:"40069"},
  {n:"Ozzano dell\'Emilia",p:"BO",c:"40064"},
  {n:"Sasso Marconi",p:"BO",c:"40037"},
  {n:"Budrio",p:"BO",c:"40054"},
  {n:"Bolzano",p:"BZ",c:"39100"},
  {n:"Merano",p:"BZ",c:"39012"},
  {n:"Bressanone",p:"BZ",c:"39042"},
  {n:"Laives",p:"BZ",c:"39055"},
  {n:"Brunico",p:"BZ",c:"39031"},
  {n:"Appiano sulla Strada del Vino",p:"BZ",c:"39057"},
  {n:"Brescia",p:"BS",c:"25100"},
  {n:"Desenzano del Garda",p:"BS",c:"25015"},
  {n:"Gardone Val Trompia",p:"BS",c:"25063"},
  {n:"Lumezzane",p:"BS",c:"25065"},
  {n:"Chiari",p:"BS",c:"25032"},
  {n:"Rovato",p:"BS",c:"25038"},
  {n:"Concesio",p:"BS",c:"25062"},
  {n:"Palazzolo sull\'Oglio",p:"BS",c:"25036"},
  {n:"Salo\'",p:"BS",c:"25087"},
  {n:"Gussago",p:"BS",c:"25064"},
  {n:"Montichiari",p:"BS",c:"25018"},
  {n:"Ghedi",p:"BS",c:"25016"},
  {n:"Brindisi",p:"BR",c:"72100"},
  {n:"Francavilla Fontana",p:"BR",c:"72021"},
  {n:"Ostuni",p:"BR",c:"72017"},
  {n:"Fasano",p:"BR",c:"72015"},
  {n:"Mesagne",p:"BR",c:"72023"},
  {n:"San Pietro Vernotico",p:"BR",c:"72027"},
  {n:"Cagliari",p:"CA",c:"09100"},
  {n:"Quartu Sant\'Elena",p:"CA",c:"09045"},
  {n:"Selargius",p:"CA",c:"09047"},
  {n:"Monserrato",p:"CA",c:"09042"},
  {n:"Capoterra",p:"CA",c:"09012"},
  {n:"Assemini",p:"CA",c:"09032"},
  {n:"Sestu",p:"CA",c:"09028"},
  {n:"Decimomannu",p:"CA",c:"09033"},
  {n:"Elmas",p:"CA",c:"09030"},
  {n:"Caltanissetta",p:"CL",c:"93100"},
  {n:"Gela",p:"CL",c:"93012"},
  {n:"Niscemi",p:"CL",c:"93015"},
  {n:"Mazzarino",p:"CL",c:"93013"},
  {n:"San Cataldo",p:"CL",c:"93017"},
  {n:"Campobasso",p:"CB",c:"86100"},
  {n:"Termoli",p:"CB",c:"86039"},
  {n:"Bojano",p:"CB",c:"86021"},
  {n:"Caserta",p:"CE",c:"81100"},
  {n:"Marcianise",p:"CE",c:"81025"},
  {n:"Aversa",p:"CE",c:"81031"},
  {n:"Capua",p:"CE",c:"81043"},
  {n:"Santa Maria Capua Vetere",p:"CE",c:"81055"},
  {n:"Maddaloni",p:"CE",c:"81024"},
  {n:"San Nicola la Strada",p:"CE",c:"81020"},
  {n:"Casal di Principe",p:"CE",c:"81033"},
  {n:"Villa Literno",p:"CE",c:"81039"},
  {n:"Mondragone",p:"CE",c:"81034"},
  {n:"Teverola",p:"CE",c:"81030"},
  {n:"Succivo",p:"CE",c:"81030"},
  {n:"San Marcellino",p:"CE",c:"81030"},
  {n:"Orta di Atella",p:"CE",c:"81030"},
  {n:"Recale",p:"CE",c:"81020"},
  {n:"Portico di Caserta",p:"CE",c:"81050"},
  {n:"San Marco Evangelista",p:"CE",c:"81020"},
  {n:"Macerata Campania",p:"CE",c:"81047"},
  {n:"Sparanise",p:"CE",c:"81056"},
  {n:"Teano",p:"CE",c:"81057"},
  {n:"Sessa Aurunca",p:"CE",c:"81037"},
  {n:"Pignataro Maggiore",p:"CE",c:"81052"},
  {n:"Vitulazio",p:"CE",c:"81041"},
  {n:"San Prisco",p:"CE",c:"81054"},
  {n:"Caiazzo",p:"CE",c:"81013"},
  {n:"Piedimonte Matese",p:"CE",c:"81016"},
  {n:"Catania",p:"CT",c:"95100"},
  {n:"Acireale",p:"CT",c:"95024"},
  {n:"Misterbianco",p:"CT",c:"95045"},
  {n:"Paternò",p:"CT",c:"95047"},
  {n:"Gravina di Catania",p:"CT",c:"95030"},
  {n:"San Giovanni la Punta",p:"CT",c:"95037"},
  {n:"Mascalucia",p:"CT",c:"95030"},
  {n:"Giarre",p:"CT",c:"95014"},
  {n:"Belpasso",p:"CT",c:"95032"},
  {n:"Caltagirone",p:"CT",c:"95041"},
  {n:"Adrano",p:"CT",c:"95031"},
  {n:"Biancavilla",p:"CT",c:"95033"},
  {n:"Trecastagni",p:"CT",c:"95039"},
  {n:"Pedara",p:"CT",c:"95030"},
  {n:"Tremestieri Etneo",p:"CT",c:"95030"},
  {n:"Catanzaro",p:"CZ",c:"88100"},
  {n:"Lamezia Terme",p:"CZ",c:"88046"},
  {n:"Soverato",p:"CZ",c:"88068"},
  {n:"Sellia Marina",p:"CZ",c:"88050"},
  {n:"Chieti",p:"CH",c:"66100"},
  {n:"Lanciano",p:"CH",c:"66034"},
  {n:"Vasto",p:"CH",c:"66054"},
  {n:"Ortona",p:"CH",c:"66026"},
  {n:"Guardiagrele",p:"CH",c:"66016"},
  {n:"Como",p:"CO",c:"22100"},
  {n:"Cantù",p:"CO",c:"22063"},
  {n:"Mariano Comense",p:"CO",c:"22066"},
  {n:"Erba",p:"CO",c:"22036"},
  {n:"Lomazzo",p:"CO",c:"22074"},
  {n:"Olgiate Comasco",p:"CO",c:"22077"},
  {n:"Cosenza",p:"CS",c:"87100"},
  {n:"Rende",p:"CS",c:"87036"},
  {n:"Castrovillari",p:"CS",c:"87012"},
  {n:"Rossano",p:"CS",c:"87067"},
  {n:"Corigliano Calabro",p:"CS",c:"87064"},
  {n:"Montalto Uffugo",p:"CS",c:"87046"},
  {n:"Acri",p:"CS",c:"87041"},
  {n:"San Giovanni in Fiore",p:"CS",c:"87055"},
  {n:"Cremona",p:"CR",c:"26100"},
  {n:"Crema",p:"CR",c:"26013"},
  {n:"Casalmaggiore",p:"CR",c:"26041"},
  {n:"Crotone",p:"KR",c:"88900"},
  {n:"Cirò Marina",p:"KR",c:"88811"},
  {n:"Isola di Capo Rizzuto",p:"KR",c:"88841"},
  {n:"Cuneo",p:"CN",c:"12100"},
  {n:"Alba",p:"CN",c:"12051"},
  {n:"Bra",p:"CN",c:"12042"},
  {n:"Saluzzo",p:"CN",c:"12037"},
  {n:"Fossano",p:"CN",c:"12045"},
  {n:"Mondovì",p:"CN",c:"12084"},
  {n:"Borgo San Dalmazzo",p:"CN",c:"12011"},
  {n:"Enna",p:"EN",c:"94100"},
  {n:"Piazza Armerina",p:"EN",c:"94015"},
  {n:"Nicosia",p:"EN",c:"94014"},
  {n:"Leonforte",p:"EN",c:"94013"},
  {n:"Fermo",p:"FM",c:"63900"},
  {n:"Porto Sant\'Elpidio",p:"FM",c:"63821"},
  {n:"Porto San Giorgio",p:"FM",c:"63822"},
  {n:"Sant\'Elpidio a Mare",p:"FM",c:"63811"},
  {n:"Ferrara",p:"FE",c:"44100"},
  {n:"Cento",p:"FE",c:"44042"},
  {n:"Comacchio",p:"FE",c:"44022"},
  {n:"Argenta",p:"FE",c:"44011"},
  {n:"Codigoro",p:"FE",c:"44021"},
  {n:"Firenze",p:"FI",c:"50100"},
  {n:"Empoli",p:"FI",c:"50053"},
  {n:"Scandicci",p:"FI",c:"50018"},
  {n:"Sesto Fiorentino",p:"FI",c:"50019"},
  {n:"Campi Bisenzio",p:"FI",c:"50013"},
  {n:"Pontassieve",p:"FI",c:"50065"},
  {n:"Figline e Incisa Valdarno",p:"FI",c:"50064"},
  {n:"Bagno a Ripoli",p:"FI",c:"50012"},
  {n:"Calenzano",p:"FI",c:"50041"},
  {n:"Fiesole",p:"FI",c:"50014"},
  {n:"Foggia",p:"FG",c:"71100"},
  {n:"Cerignola",p:"FG",c:"71042"},
  {n:"Lucera",p:"FG",c:"71036"},
  {n:"San Severo",p:"FG",c:"71016"},
  {n:"Manfredonia",p:"FG",c:"71043"},
  {n:"Vieste",p:"FG",c:"71019"},
  {n:"Monte Sant\'Angelo",p:"FG",c:"71037"},
  {n:"Forlì",p:"FC",c:"47100"},
  {n:"Cesena",p:"FC",c:"47521"},
  {n:"Cesenatico",p:"FC",c:"47042"},
  {n:"Forlimpopoli",p:"FC",c:"47034"},
  {n:"Savignano sul Rubicone",p:"FC",c:"47039"},
  {n:"Frosinone",p:"FR",c:"03100"},
  {n:"Cassino",p:"FR",c:"03043"},
  {n:"Anagni",p:"FR",c:"03012"},
  {n:"Alatri",p:"FR",c:"03011"},
  {n:"Ferentino",p:"FR",c:"03013"},
  {n:"Ceccano",p:"FR",c:"03023"},
  {n:"Sora",p:"FR",c:"03039"},
  {n:"Isola del Liri",p:"FR",c:"03036"},
  {n:"Genova",p:"GE",c:"16100"},
  {n:"Rapallo",p:"GE",c:"16035"},
  {n:"Chiavari",p:"GE",c:"16043"},
  {n:"Sestri Levante",p:"GE",c:"16039"},
  {n:"Lavagna",p:"GE",c:"16033"},
  {n:"Recco",p:"GE",c:"16036"},
  {n:"Gorizia",p:"GO",c:"34170"},
  {n:"Monfalcone",p:"GO",c:"34074"},
  {n:"Gradisca d\'Isonzo",p:"GO",c:"34072"},
  {n:"Grosseto",p:"GR",c:"58100"},
  {n:"Orbetello",p:"GR",c:"58015"},
  {n:"Follonica",p:"GR",c:"58022"},
  {n:"Massa Marittima",p:"GR",c:"58024"},
  {n:"Imperia",p:"IM",c:"18100"},
  {n:"Sanremo",p:"IM",c:"18038"},
  {n:"Ventimiglia",p:"IM",c:"18039"},
  {n:"Bordighera",p:"IM",c:"18012"},
  {n:"Isernia",p:"IS",c:"86170"},
  {n:"Venafro",p:"IS",c:"86079"},
  {n:"L\'Aquila",p:"AQ",c:"67100"},
  {n:"Avezzano",p:"AQ",c:"67051"},
  {n:"Sulmona",p:"AQ",c:"67039"},
  {n:"Pescara",p:"PE",c:"65100"},
  {n:"La Spezia",p:"SP",c:"19100"},
  {n:"Sarzana",p:"SP",c:"19038"},
  {n:"Lerici",p:"SP",c:"19032"},
  {n:"Latina",p:"LT",c:"04100"},
  {n:"Aprilia",p:"LT",c:"04011"},
  {n:"Terracina",p:"LT",c:"04019"},
  {n:"Fondi",p:"LT",c:"04022"},
  {n:"Gaeta",p:"LT",c:"04024"},
  {n:"Minturno",p:"LT",c:"04026"},
  {n:"Formia",p:"LT",c:"04023"},
  {n:"Cisterna di Latina",p:"LT",c:"04012"},
  {n:"Lecce",p:"LE",c:"73100"},
  {n:"Brindisi",p:"BR",c:"72100"},
  {n:"Gallipoli",p:"LE",c:"73014"},
  {n:"Nardò",p:"LE",c:"73048"},
  {n:"Galatina",p:"LE",c:"73013"},
  {n:"Copertino",p:"LE",c:"73043"},
  {n:"Surbo",p:"LE",c:"73010"},
  {n:"Squinzano",p:"LE",c:"73018"},
  {n:"Campi Salentina",p:"LE",c:"73012"},
  {n:"Casarano",p:"LE",c:"73042"},
  {n:"Tricase",p:"LE",c:"73039"},
  {n:"Ugento",p:"LE",c:"73059"},
  {n:"Lecco",p:"LC",c:"23900"},
  {n:"Merate",p:"LC",c:"23807"},
  {n:"Calolziocorte",p:"LC",c:"23801"},
  {n:"Livorno",p:"LI",c:"57100"},
  {n:"Piombino",p:"LI",c:"57025"},
  {n:"Cecina",p:"LI",c:"57023"},
  {n:"Rosignano Marittimo",p:"LI",c:"57016"},
  {n:"Lodi",p:"LO",c:"26900"},
  {n:"Codogno",p:"LO",c:"26845"},
  {n:"Casalpusterlengo",p:"LO",c:"26841"},
  {n:"Lucca",p:"LU",c:"55100"},
  {n:"Viareggio",p:"LU",c:"55049"},
  {n:"Capannori",p:"LU",c:"55012"},
  {n:"Camaiore",p:"LU",c:"55041"},
  {n:"Pietrasanta",p:"LU",c:"55045"},
  {n:"Altopascio",p:"LU",c:"55011"},
  {n:"Macerata",p:"MC",c:"62100"},
  {n:"Civitanova Marche",p:"MC",c:"62012"},
  {n:"Porto Recanati",p:"MC",c:"62017"},
  {n:"Recanati",p:"MC",c:"62019"},
  {n:"Tolentino",p:"MC",c:"62029"},
  {n:"Mantova",p:"MN",c:"46100"},
  {n:"Guidizzolo",p:"MN",c:"46040"},
  {n:"Viadana",p:"MN",c:"46019"},
  {n:"Suzzara",p:"MN",c:"46029"},
  {n:"Massa",p:"MS",c:"54100"},
  {n:"Carrara",p:"MS",c:"54033"},
  {n:"Pontremoli",p:"MS",c:"54027"},
  {n:"Matera",p:"MT",c:"75100"},
  {n:"Policoro",p:"MT",c:"75025"},
  {n:"Nova Siri",p:"MT",c:"75020"},
  {n:"Messina",p:"ME",c:"98100"},
  {n:"Barcellona Pozzo di Gotto",p:"ME",c:"98051"},
  {n:"Milazzo",p:"ME",c:"98057"},
  {n:"Patti",p:"ME",c:"98066"},
  {n:"Sant\'Agata di Militello",p:"ME",c:"98076"},
  {n:"Capo d\'Orlando",p:"ME",c:"98071"},
  {n:"Lipari",p:"ME",c:"98055"},
  {n:"Milano",p:"MI",c:"20100"},
  {n:"Sesto San Giovanni",p:"MI",c:"20099"},
  {n:"Cinisello Balsamo",p:"MI",c:"20092"},
  {n:"Monza",p:"MB",c:"20900"},
  {n:"Legnano",p:"MI",c:"20025"},
  {n:"Rho",p:"MI",c:"20017"},
  {n:"Corsico",p:"MI",c:"20094"},
  {n:"Cologno Monzese",p:"MI",c:"20093"},
  {n:"Paderno Dugnano",p:"MI",c:"20037"},
  {n:"Segrate",p:"MI",c:"20054"},
  {n:"Pioltello",p:"MI",c:"20096"},
  {n:"Vimodrone",p:"MI",c:"20090"},
  {n:"Cernusco sul Naviglio",p:"MI",c:"20063"},
  {n:"Sesto Calende",p:"VA",c:"21018"},
  {n:"Trezzano sul Naviglio",p:"MI",c:"20090"},
  {n:"Cesano Boscone",p:"MI",c:"20090"},
  {n:"Opera",p:"MI",c:"20090"},
  {n:"Peschiera Borromeo",p:"MI",c:"20068"},
  {n:"Lissone",p:"MB",c:"20851"},
  {n:"Desio",p:"MB",c:"20832"},
  {n:"Seregno",p:"MB",c:"20831"},
  {n:"Cesano Maderno",p:"MB",c:"20811"},
  {n:"Meda",p:"MB",c:"20821"},
  {n:"Giussano",p:"MB",c:"20833"},
  {n:"Brugherio",p:"MB",c:"20861"},
  {n:"Vimercate",p:"MB",c:"20871"},
  {n:"Modena",p:"MO",c:"41100"},
  {n:"Carpi",p:"MO",c:"41012"},
  {n:"Sassuolo",p:"MO",c:"41049"},
  {n:"Formigine",p:"MO",c:"41043"},
  {n:"Castelfranco Emilia",p:"MO",c:"41013"},
  {n:"Mirandola",p:"MO",c:"41037"},
  {n:"Maranello",p:"MO",c:"41053"},
  {n:"Fiorano Modenese",p:"MO",c:"41042"},
  {n:"Vignola",p:"MO",c:"41058"},
  {n:"Napoli",p:"NA",c:"80100"},
  {n:"Giugliano in Campania",p:"NA",c:"80014"},
  {n:"Torre del Greco",p:"NA",c:"80059"},
  {n:"Pozzuoli",p:"NA",c:"80078"},
  {n:"Castellammare di Stabia",p:"NA",c:"80053"},
  {n:"Afragola",p:"NA",c:"80021"},
  {n:"Acerra",p:"NA",c:"80011"},
  {n:"Marano di Napoli",p:"NA",c:"80016"},
  {n:"Portici",p:"NA",c:"80055"},
  {n:"Ercolano",p:"NA",c:"80056"},
  {n:"Casoria",p:"NA",c:"80026"},
  {n:"San Giuseppe Vesuviano",p:"NA",c:"80047"},
  {n:"Pompei",p:"NA",c:"80045"},
  {n:"Torre Annunziata",p:"NA",c:"80058"},
  {n:"Nola",p:"NA",c:"80035"},
  {n:"Frattamaggiore",p:"NA",c:"80027"},
  {n:"Quarto",p:"NA",c:"80010"},
  {n:"Villaricca",p:"NA",c:"80010"},
  {n:"Qualiano",p:"NA",c:"80019"},
  {n:"Mugnano di Napoli",p:"NA",c:"80018"},
  {n:"Melito di Napoli",p:"NA",c:"80017"},
  {n:"Cardito",p:"NA",c:"80024"},
  {n:"Caivano",p:"NA",c:"80023"},
  {n:"Grumo Nevano",p:"NA",c:"80028"},
  {n:"Arzano",p:"NA",c:"80022"},
  {n:"Casavatore",p:"NA",c:"80020"},
  {n:"Sant\'Antimo",p:"NA",c:"80029"},
  {n:"Frattaminore",p:"NA",c:"80020"},
  {n:"Crispano",p:"NA",c:"80020"},
  {n:"San Sebastiano al Vesuvio",p:"NA",c:"80040"},
  {n:"Sorrento",p:"NA",c:"80067"},
  {n:"Vico Equense",p:"NA",c:"80069"},
  {n:"Piano di Sorrento",p:"NA",c:"80063"},
  {n:"Meta",p:"NA",c:"80062"},
  {n:"Sant\'Agnello",p:"NA",c:"80065"},
  {n:"Boscoreale",p:"NA",c:"80041"},
  {n:"Boscotrecase",p:"NA",c:"80042"},
  {n:"Trecase",p:"NA",c:"80040"},
  {n:"Terzigno",p:"NA",c:"80040"},
  {n:"Marigliano",p:"NA",c:"80034"},
  {n:"San Vitaliano",p:"NA",c:"80030"},
  {n:"Somma Vesuviana",p:"NA",c:"80049"},
  {n:"Ottaviano",p:"NA",c:"80044"},
  {n:"Palma Campania",p:"NA",c:"80036"},
  {n:"San Gennaro Vesuviano",p:"NA",c:"80040"},
  {n:"Poggiomarino",p:"NA",c:"80040"},
  {n:"Sant\'Antonio Abate",p:"NA",c:"80057"},
  {n:"Gragnano",p:"NA",c:"80054"},
  {n:"Lettere",p:"NA",c:"80050"},
  {n:"Casola di Napoli",p:"NA",c:"80050"},
  {n:"Pimonte",p:"NA",c:"80050"},
  {n:"Agerola",p:"NA",c:"80051"},
  {n:"Furore",p:"SA",c:"84010"},
  {n:"Positano",p:"SA",c:"84017"},
  {n:"Praiano",p:"SA",c:"84010"},
  {n:"Conca dei Marini",p:"SA",c:"84010"},
  {n:"Amalfi",p:"SA",c:"84011"},
  {n:"Ravello",p:"SA",c:"84010"},
  {n:"Bacoli",p:"NA",c:"80070"},
  {n:"Monte di Procida",p:"NA",c:"80070"},
  {n:"Procida",p:"NA",c:"80079"},
  {n:"Ischia",p:"NA",c:"80077"},
  {n:"Barano d\'Ischia",p:"NA",c:"80070"},
  {n:"Forio",p:"NA",c:"80075"},
  {n:"Casamicciola Terme",p:"NA",c:"80074"},
  {n:"Lacco Ameno",p:"NA",c:"80076"},
  {n:"Novara",p:"NO",c:"28100"},
  {n:"Borgomanero",p:"NO",c:"28021"},
  {n:"Arona",p:"NO",c:"28041"},
  {n:"Verbania",p:"VB",c:"28900"},
  {n:"Nuoro",p:"NU",c:"08100"},
  {n:"Siniscola",p:"NU",c:"08029"},
  {n:"Dorgali",p:"NU",c:"08022"},
  {n:"Oristano",p:"OR",c:"09170"},
  {n:"Cabras",p:"OR",c:"09072"},
  {n:"Padova",p:"PD",c:"35100"},
  {n:"Abano Terme",p:"PD",c:"35031"},
  {n:"Cittadella",p:"PD",c:"35013"},
  {n:"Este",p:"PD",c:"35042"},
  {n:"Monselice",p:"PD",c:"35043"},
  {n:"Vigonza",p:"PD",c:"35010"},
  {n:"Rubano",p:"PD",c:"35030"},
  {n:"Selvazzano Dentro",p:"PD",c:"35030"},
  {n:"Albignasego",p:"PD",c:"35020"},
  {n:"Cadoneghe",p:"PD",c:"35010"},
  {n:"Sarmeola",p:"PD",c:"35030"},
  {n:"Palermo",p:"PA",c:"90100"},
  {n:"Bagheria",p:"PA",c:"90011"},
  {n:"Monreale",p:"PA",c:"90046"},
  {n:"Carini",p:"PA",c:"90044"},
  {n:"Partinico",p:"PA",c:"90047"},
  {n:"Termini Imerese",p:"PA",c:"90018"},
  {n:"Misilmeri",p:"PA",c:"90036"},
  {n:"Altofonte",p:"PA",c:"90030"},
  {n:"Villabate",p:"PA",c:"90039"},
  {n:"Ficarazzi",p:"PA",c:"90010"},
  {n:"Santa Flavia",p:"PA",c:"90017"},
  {n:"Casteldaccia",p:"PA",c:"90014"},
  {n:"Trabia",p:"PA",c:"90019"},
  {n:"Caccamo",p:"PA",c:"90012"},
  {n:"Parma",p:"PR",c:"43100"},
  {n:"Fidenza",p:"PR",c:"43036"},
  {n:"Salsomaggiore Terme",p:"PR",c:"43039"},
  {n:"Collecchio",p:"PR",c:"43044"},
  {n:"Langhirano",p:"PR",c:"43013"},
  {n:"Pavia",p:"PV",c:"27100"},
  {n:"Vigevano",p:"PV",c:"27029"},
  {n:"Voghera",p:"PV",c:"27058"},
  {n:"Mortara",p:"PV",c:"27036"},
  {n:"Abbiategrasso",p:"MI",c:"20081"},
  {n:"Perugia",p:"PG",c:"06100"},
  {n:"Foligno",p:"PG",c:"06034"},
  {n:"Città di Castello",p:"PG",c:"06012"},
  {n:"Terni",p:"TR",c:"05100"},
  {n:"Spoleto",p:"PG",c:"06049"},
  {n:"Assisi",p:"PG",c:"06081"},
  {n:"Corciano",p:"PG",c:"06073"},
  {n:"Bastia Umbra",p:"PG",c:"06083"},
  {n:"Gubbio",p:"PG",c:"06024"},
  {n:"Pesaro",p:"PU",c:"61121"},
  {n:"Urbino",p:"PU",c:"61029"},
  {n:"Fano",p:"PU",c:"61032"},
  {n:"Cattolica",p:"RN",c:"47841"},
  {n:"Pescara",p:"PE",c:"65100"},
  {n:"Montesilvano",p:"PE",c:"65015"},
  {n:"Spoltore",p:"PE",c:"65010"},
  {n:"Francavilla al Mare",p:"CH",c:"66023"},
  {n:"Piacenza",p:"PC",c:"29100"},
  {n:"Fiorenzuola d\'Arda",p:"PC",c:"29017"},
  {n:"Pisa",p:"PI",c:"56100"},
  {n:"Cascina",p:"PI",c:"56021"},
  {n:"Pontedera",p:"PI",c:"56025"},
  {n:"San Miniato",p:"PI",c:"56028"},
  {n:"Volterra",p:"PI",c:"56048"},
  {n:"Pistoia",p:"PT",c:"51100"},
  {n:"Prato",p:"PO",c:"59100"},
  {n:"Montale",p:"PT",c:"51037"},
  {n:"Pescia",p:"PT",c:"51017"},
  {n:"Monsummano Terme",p:"PT",c:"51015"},
  {n:"Pordenone",p:"PN",c:"33170"},
  {n:"Sacile",p:"PN",c:"33077"},
  {n:"Spilimbergo",p:"PN",c:"33097"},
  {n:"Potenza",p:"PZ",c:"85100"},
  {n:"Melfi",p:"PZ",c:"85025"},
  {n:"Lagonegro",p:"PZ",c:"85042"},
  {n:"Lavello",p:"PZ",c:"85024"},
  {n:"Prato",p:"PO",c:"59100"},
  {n:"Montemurlo",p:"PO",c:"59013"},
  {n:"Ragusa",p:"RG",c:"97100"},
  {n:"Vittoria",p:"RG",c:"97019"},
  {n:"Modica",p:"RG",c:"97015"},
  {n:"Comiso",p:"RG",c:"97013"},
  {n:"Scicli",p:"RG",c:"97018"},
  {n:"Ravenna",p:"RA",c:"48100"},
  {n:"Faenza",p:"RA",c:"48018"},
  {n:"Lugo",p:"RA",c:"48022"},
  {n:"Russi",p:"RA",c:"48026"},
  {n:"Reggio di Calabria",p:"RC",c:"89100"},
  {n:"Villa San Giovanni",p:"RC",c:"89018"},
  {n:"Siderno",p:"RC",c:"89048"},
  {n:"Locri",p:"RC",c:"89044"},
  {n:"Palmi",p:"RC",c:"89015"},
  {n:"Gioia Tauro",p:"RC",c:"89013"},
  {n:"Reggio nell\'Emilia",p:"RE",c:"42100"},
  {n:"Scandiano",p:"RE",c:"42019"},
  {n:"Correggio",p:"RE",c:"42015"},
  {n:"Guastalla",p:"RE",c:"42016"},
  {n:"Rubiera",p:"RE",c:"42048"},
  {n:"Casalgrande",p:"RE",c:"42013"},
  {n:"Rieti",p:"RI",c:"02100"},
  {n:"Poggio Mirteto",p:"RI",c:"02047"},
  {n:"Rimini",p:"RN",c:"47900"},
  {n:"Riccione",p:"RN",c:"47838"},
  {n:"Misano Adriatico",p:"RN",c:"47843"},
  {n:"Bellaria-Igea Marina",p:"RN",c:"47814"},
  {n:"Santarcangelo di Romagna",p:"RN",c:"47822"},
  {n:"Roma",p:"RM",c:"00100"},
  {n:"Fiumicino",p:"RM",c:"00054"},
  {n:"Guidonia Montecelio",p:"RM",c:"00012"},
  {n:"Pomezia",p:"RM",c:"00040"},
  {n:"Velletri",p:"RM",c:"00049"},
  {n:"Tivoli",p:"RM",c:"00019"},
  {n:"Civitavecchia",p:"RM",c:"00053"},
  {n:"Monterotondo",p:"RM",c:"00015"},
  {n:"Anzio",p:"RM",c:"00042"},
  {n:"Ardea",p:"RM",c:"00040"},
  {n:"Nettuno",p:"RM",c:"00048"},
  {n:"Albano Laziale",p:"RM",c:"00041"},
  {n:"Genzano di Roma",p:"RM",c:"00045"},
  {n:"Marino",p:"RM",c:"00047"},
  {n:"Frascati",p:"RM",c:"00044"},
  {n:"Ariccia",p:"RM",c:"00040"},
  {n:"Ciampino",p:"RM",c:"00043"},
  {n:"Poli",p:"RM",c:"00010"},
  {n:"Zagarolo",p:"RM",c:"00030"},
  {n:"Palestrina",p:"RM",c:"00036"},
  {n:"Colleferro",p:"RM",c:"00034"},
  {n:"Valmontone",p:"RM",c:"00038"},
  {n:"Lariano",p:"RM",c:"00040"},
  {n:"Grottaferrata",p:"RM",c:"00046"},
  {n:"Rocca di Papa",p:"RM",c:"00040"},
  {n:"Monte Compatri",p:"RM",c:"00077"},
  {n:"Colonna",p:"RM",c:"00030"},
  {n:"Labico",p:"RM",c:"00030"},
  {n:"Artena",p:"RM",c:"00031"},
  {n:"Rovigo",p:"RO",c:"45100"},
  {n:"Adria",p:"RO",c:"45011"},
  {n:"Porto Tolle",p:"RO",c:"45018"},
  {n:"Salerno",p:"SA",c:"84100"},
  {n:"Scafati",p:"SA",c:"84018"},
  {n:"Pagani",p:"SA",c:"84016"},
  {n:"Nocera Inferiore",p:"SA",c:"84014"},
  {n:"Nocera Superiore",p:"SA",c:"84015"},
  {n:"Cava de\' Tirreni",p:"SA",c:"84013"},
  {n:"Battipaglia",p:"SA",c:"84091"},
  {n:"Eboli",p:"SA",c:"84025"},
  {n:"Sarno",p:"SA",c:"84087"},
  {n:"Angri",p:"SA",c:"84012"},
  {n:"Pontecagnano Faiano",p:"SA",c:"84098"},
  {n:"Baronissi",p:"SA",c:"84081"},
  {n:"Mercato San Severino",p:"SA",c:"84085"},
  {n:"Bracigliano",p:"SA",c:"84082"},
  {n:"Fisciano",p:"SA",c:"84084"},
  {n:"Pellezzano",p:"SA",c:"84080"},
  {n:"Vietri sul Mare",p:"SA",c:"84019"},
  {n:"Cetara",p:"SA",c:"84010"},
  {n:"Maiori",p:"SA",c:"84010"},
  {n:"Minori",p:"SA",c:"84010"},
  {n:"Tramonti",p:"SA",c:"84010"},
  {n:"Scala",p:"SA",c:"84010"},
  {n:"Ravello",p:"SA",c:"84010"},
  {n:"Agropoli",p:"SA",c:"84043"},
  {n:"Capaccio Paestum",p:"SA",c:"84047"},
  {n:"Albanella",p:"SA",c:"84044"},
  {n:"Altavilla Silentina",p:"SA",c:"84045"},
  {n:"Campagna",p:"SA",c:"84022"},
  {n:"Contursi Terme",p:"SA",c:"84024"},
  {n:"Sassari",p:"SS",c:"07100"},
  {n:"Olbia",p:"SS",c:"07026"},
  {n:"Alghero",p:"SS",c:"07041"},
  {n:"Porto Torres",p:"SS",c:"07046"},
  {n:"Tempio Pausania",p:"SS",c:"07029"},
  {n:"Savona",p:"SV",c:"17100"},
  {n:"Albenga",p:"SV",c:"17031"},
  {n:"Pietra Ligure",p:"SV",c:"17027"},
  {n:"Cairo Montenotte",p:"SV",c:"17014"},
  {n:"Siena",p:"SI",c:"53100"},
  {n:"Poggibonsi",p:"SI",c:"53036"},
  {n:"Colle di Val d\'Elsa",p:"SI",c:"53034"},
  {n:"Monteriggioni",p:"SI",c:"53035"},
  {n:"Chianciano Terme",p:"SI",c:"53042"},
  {n:"Siracusa",p:"SR",c:"96100"},
  {n:"Augusta",p:"SR",c:"96011"},
  {n:"Floridia",p:"SR",c:"96014"},
  {n:"Noto",p:"SR",c:"96017"},
  {n:"Avola",p:"SR",c:"96012"},
  {n:"Pachino",p:"SR",c:"96018"},
  {n:"Rosolini",p:"SR",c:"96019"},
  {n:"Lentini",p:"SR",c:"96016"},
  {n:"Sondrio",p:"SO",c:"23100"},
  {n:"Morbegno",p:"SO",c:"23017"},
  {n:"Tirano",p:"SO",c:"23037"},
  {n:"Taranto",p:"TA",c:"74100"},
  {n:"Massafra",p:"TA",c:"74016"},
  {n:"Martina Franca",p:"TA",c:"74015"},
  {n:"Grottaglie",p:"TA",c:"74023"},
  {n:"Manduria",p:"TA",c:"74024"},
  {n:"Castellaneta",p:"TA",c:"74011"},
  {n:"Teramo",p:"TE",c:"64100"},
  {n:"Roseto degli Abruzzi",p:"TE",c:"64026"},
  {n:"Giulianova",p:"TE",c:"64021"},
  {n:"Montesilvano",p:"PE",c:"65015"},
  {n:"Terni",p:"TR",c:"05100"},
  {n:"Orvieto",p:"TR",c:"05018"},
  {n:"Narni",p:"TR",c:"05035"},
  {n:"Torino",p:"TO",c:"10100"},
  {n:"Moncalieri",p:"TO",c:"10024"},
  {n:"Collegno",p:"TO",c:"10093"},
  {n:"Rivoli",p:"TO",c:"10098"},
  {n:"Pinerolo",p:"TO",c:"10064"},
  {n:"Chivasso",p:"TO",c:"10034"},
  {n:"Ivrea",p:"TO",c:"10015"},
  {n:"Settimo Torinese",p:"TO",c:"10036"},
  {n:"Grugliasco",p:"TO",c:"10095"},
  {n:"Nichelino",p:"TO",c:"10042"},
  {n:"Orbassano",p:"TO",c:"10043"},
  {n:"Beinasco",p:"TO",c:"10092"},
  {n:"None",p:"TO",c:"10060"},
  {n:"Carmagnola",p:"TO",c:"10022"},
  {n:"Chieri",p:"TO",c:"10023"},
  {n:"Caselle Torinese",p:"TO",c:"10072"},
  {n:"Leinì",p:"TO",c:"10040"},
  {n:"San Mauro Torinese",p:"TO",c:"10099"},
  {n:"Venaria Reale",p:"TO",c:"10078"},
  {n:"Pianezza",p:"TO",c:"10044"},
  {n:"Alpignano",p:"TO",c:"10091"},
  {n:"Druento",p:"TO",c:"10040"},
  {n:"Trapani",p:"TP",c:"91100"},
  {n:"Marsala",p:"TP",c:"91025"},
  {n:"Mazara del Vallo",p:"TP",c:"91026"},
  {n:"Alcamo",p:"TP",c:"91011"},
  {n:"Castelvetrano",p:"TP",c:"91022"},
  {n:"Petrosino",p:"TP",c:"91020"},
  {n:"Trento",p:"TN",c:"38100"},
  {n:"Rovereto",p:"TN",c:"38068"},
  {n:"Pergine Valsugana",p:"TN",c:"38057"},
  {n:"Riva del Garda",p:"TN",c:"38066"},
  {n:"Arco",p:"TN",c:"38062"},
  {n:"Treviso",p:"TV",c:"31100"},
  {n:"Vittorio Veneto",p:"TV",c:"31029"},
  {n:"Conegliano",p:"TV",c:"31015"},
  {n:"Montebelluna",p:"TV",c:"31044"},
  {n:"Oderzo",p:"TV",c:"31046"},
  {n:"Mogliano Veneto",p:"TV",c:"31021"},
  {n:"Castelfranco Veneto",p:"TV",c:"31033"},
  {n:"Silea",p:"TV",c:"31057"},
  {n:"Trieste",p:"TS",c:"34100"},
  {n:"Muggia",p:"TS",c:"34015"},
  {n:"Udine",p:"UD",c:"33100"},
  {n:"Cividale del Friuli",p:"UD",c:"33043"},
  {n:"Tolmezzo",p:"UD",c:"33028"},
  {n:"Varese",p:"VA",c:"21100"},
  {n:"Busto Arsizio",p:"VA",c:"21052"},
  {n:"Gallarate",p:"VA",c:"21013"},
  {n:"Saronno",p:"VA",c:"21047"},
  {n:"Sesto Calende",p:"VA",c:"21018"},
  {n:"Luino",p:"VA",c:"21016"},
  {n:"Castellanza",p:"VA",c:"21053"},
  {n:"Malnate",p:"VA",c:"21046"},
  {n:"Tradate",p:"VA",c:"21049"},
  {n:"Venezia",p:"VE",c:"30100"},
  {n:"Mestre",p:"VE",c:"30170"},
  {n:"Chioggia",p:"VE",c:"30015"},
  {n:"Spinea",p:"VE",c:"30038"},
  {n:"Mirano",p:"VE",c:"30035"},
  {n:"Dolo",p:"VE",c:"30031"},
  {n:"Jesolo",p:"VE",c:"30016"},
  {n:"San Donà di Piave",p:"VE",c:"30027"},
  {n:"Verbania",p:"VB",c:"28900"},
  {n:"Domodossola",p:"VB",c:"28845"},
  {n:"Omegna",p:"VB",c:"28887"},
  {n:"Vercelli",p:"VC",c:"13100"},
  {n:"Borgosesia",p:"VC",c:"13011"},
  {n:"Verona",p:"VR",c:"37100"},
  {n:"Villafranca di Verona",p:"VR",c:"37069"},
  {n:"San Bonifacio",p:"VR",c:"37047"},
  {n:"Legnago",p:"VR",c:"37045"},
  {n:"Sona",p:"VR",c:"37060"},
  {n:"Bardolino",p:"VR",c:"37011"},
  {n:"Bussolengo",p:"VR",c:"37012"},
  {n:"Negrar di Valpolicella",p:"VR",c:"37024"},
  {n:"Pescantina",p:"VR",c:"37026"},
  {n:"Peschiera del Garda",p:"VR",c:"37019"},
  {n:"Vibo Valentia",p:"VV",c:"89900"},
  {n:"Tropea",p:"VV",c:"89861"},
  {n:"Vicenza",p:"VI",c:"36100"},
  {n:"Schio",p:"VI",c:"36015"},
  {n:"Bassano del Grappa",p:"VI",c:"36061"},
  {n:"Thiene",p:"VI",c:"36016"},
  {n:"Valdagno",p:"VI",c:"36078"},
  {n:"Arzignano",p:"VI",c:"36071"},
  {n:"Chiampo",p:"VI",c:"36072"},
  {n:"Montecchio Maggiore",p:"VI",c:"36075"},
  {n:"Lonigo",p:"VI",c:"36045"},
  {n:"Noventa Vicentina",p:"VI",c:"36025"},
  {n:"Camisano Vicentino",p:"VI",c:"36043"},
  {n:"Creazzo",p:"VI",c:"36051"},
  {n:"Sovizzo",p:"VI",c:"36050"},
  {n:"Costabissara",p:"VI",c:"36030"},
  {n:"Caldogno",p:"VI",c:"36030"},
  {n:"Torri di Quartesolo",p:"VI",c:"36040"},
  {n:"Viterbo",p:"VT",c:"01100"},
  {n:"Civita Castellana",p:"VT",c:"01033"},
  {n:"Tarquinia",p:"VT",c:"01016"},
  {n:"Montefiascone",p:"VT",c:"01027"},
];

// ── MARCHE AUTO ──────────────────────────────────────────────────────
var MARCHE_AUTO = [
  "Alfa Romeo","Audi","BMW","Chevrolet","Chrysler","Citroën","Dacia","Dodge",
  "Fiat","Ford","Honda","Hyundai","Infiniti","Jaguar","Jeep","Kia","Lamborghini",
  "Land Rover","Lancia","Lexus","Maserati","Mazda","Mercedes-Benz","Mini",
  "Mitsubishi","Nissan","Opel","Peugeot","Porsche","Renault","Seat","Skoda",
  "Smart","Subaru","Suzuki","Tesla","Toyota","Volkswagen","Volvo","Ferrari",
  "Abarth","Alfa","Autobianchi","Daewoo","Daihatsu","DS","Isuzu","Iveco",
  "Microcar","MG","Piaggio","Saab","SsangYong","Tata","Triumph",
];

// ── DECODIFICA TARGA ITALIANA ─────────────────────────────────────────
// Formato attuale: 2 lettere + 3 cifre + 2 lettere (es. AB123CD)
// Dal prefisso si può stimare l'anno di immatricolazione
var TARGA_ANNO = {
  // Prefissi serie storica (indicativi)
  "A":1994,"B":1995,"C":1996,"D":1997,"E":1998,"F":1999,
  "G":2000,"H":2001,"J":2002,"K":2003,"L":2004,"M":2005,
  "N":2006,"P":2007,"R":2008,"S":2009,"T":2010,"V":2011,
  "W":2012,"X":2013,"Y":2014,"Z":2015,
  "AA":2016,"AB":2017,"AC":2018,"AD":2019,"AE":2020,"AF":2021,
  "AG":2022,"AH":2023,"AJ":2024,"AK":2025,
};

function decodificaTarga(targa) {
  if(!targa || targa.length < 7) return null;
  targa = targa.toUpperCase().replace(/\s/g,'');
  var result = {};
  // Targa moderna: 2L+3N+2L
  var m = targa.match(/^([A-Z]{2})(\d{3})([A-Z]{2})$/);
  if(m) {
    var prefisso2 = m[1];
    var prefisso1 = m[1][0];
    var anno = TARGA_ANNO[prefisso2] || TARGA_ANNO[prefisso1] || null;
    if(anno) result.anno = anno;
    result.tipo = 'Autoveicolo';
    result.valida = true;
    return result;
  }
  // Targa moto: 2L+5N
  if(targa.match(/^[A-Z]{2}\d{5}$/)) {
    result.tipo = 'Motoveicolo';
    result.valida = true;
    return result;
  }
  return null;
}

// ── COMPONENTE AUTOCOMPLETE GENERICO ─────────────────────────────────
// Crea un dropdown di suggerimenti sotto l'input
function creaAutocomplete(inputEl, getSuggestions, onSelect) {
  var dropdown = document.createElement('div');
  dropdown.style.cssText = [
    'position:absolute','z-index:9999','background:#fff',
    'border:1px solid #dde1e8','border-radius:8px',
    'box-shadow:0 4px 20px rgba(0,0,0,.12)',
    'max-height:220px','overflow-y:auto','min-width:200px',
    'font-family:DM Sans,system-ui,sans-serif','font-size:13px',
  ].join(';');
  dropdown.style.display = 'none';
  document.body.appendChild(dropdown);

  function posiziona() {
    var r = inputEl.getBoundingClientRect();
    dropdown.style.top  = (r.bottom + window.scrollY + 2) + 'px';
    dropdown.style.left = (r.left   + window.scrollX) + 'px';
    dropdown.style.width = Math.max(r.width, 220) + 'px';
  }

  function chiudi() { dropdown.style.display = 'none'; }

  function aggiorna() {
    var val = inputEl.value.trim();
    if(val.length < 2) { chiudi(); return; }
    var sugg = getSuggestions(val);
    if(!sugg.length) { chiudi(); return; }
    dropdown.innerHTML = '';
    sugg.forEach(function(s) {
      var item = document.createElement('div');
      item.style.cssText = 'padding:8px 12px;cursor:pointer;border-bottom:1px solid #f3f4f6;';
      item.innerHTML = s.html || escAC(s.label);
      item.onmouseenter = function(){ item.style.background='#fff8f5'; };
      item.onmouseleave = function(){ item.style.background=''; };
      item.onmousedown  = function(e) {
        e.preventDefault();
        onSelect(s);
        chiudi();
      };
      dropdown.appendChild(item);
    });
    posiziona();
    dropdown.style.display = 'block';
  }

  inputEl.addEventListener('input', aggiorna);
  inputEl.addEventListener('focus', aggiorna);
  inputEl.addEventListener('blur',  function(){ setTimeout(chiudi, 200); });
  window.addEventListener('scroll', function(){ if(dropdown.style.display!=='none') posiziona(); }, true);
  window.addEventListener('resize', function(){ if(dropdown.style.display!=='none') posiziona(); });
  return dropdown;
}

function escAC(s) {
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function highlightMatch(text, query) {
  var idx = text.toLowerCase().indexOf(query.toLowerCase());
  if(idx < 0) return escAC(text);
  return escAC(text.slice(0,idx))
    + '<b style="color:#e94c00">' + escAC(text.slice(idx,idx+query.length)) + '</b>'
    + escAC(text.slice(idx+query.length));
}

// ── AUTOCOMPLETE COMUNI ───────────────────────────────────────────────
function comuniSuggerimenti(val) {
  val = val.toLowerCase();
  var results = [];
  for(var i=0; i<COMUNI_DB.length && results.length<10; i++) {
    var c = COMUNI_DB[i];
    if(c.n.toLowerCase().indexOf(val) === 0) {
      results.push({label: c.n, prov: c.p, cap: c.c, score: 0});
    }
  }
  // Poi cerca anche nel mezzo
  if(results.length < 10) {
    for(var i=0; i<COMUNI_DB.length && results.length<10; i++) {
      var c = COMUNI_DB[i];
      var idx = c.n.toLowerCase().indexOf(val);
      if(idx > 0) {
        results.push({label: c.n, prov: c.p, cap: c.c, score: 1});
      }
    }
  }
  return results.map(function(r) {
    return {
      label: r.label,
      prov:  r.prov,
      cap:   r.cap,
      html:  '<span>' + highlightMatch(r.label, val) + '</span>'
           + '<span style="float:right;color:#9ca3af;font-size:11px;font-family:DM Mono,monospace">'
           + r.prov + ' · ' + r.cap + '</span>',
    };
  });
}

// ── AUTOCOMPLETE MARCHE ───────────────────────────────────────────────
function marcheSuggerimenti(val) {
  val = val.toLowerCase();
  return MARCHE_AUTO
    .filter(function(m){ return m.toLowerCase().indexOf(val) >= 0; })
    .slice(0,8)
    .map(function(m){ return {label:m, html: highlightMatch(m, val)}; });
}

// ── INIT AUTOCOMPLETE MODAL ANAGRAFICA ───────────────────────────────
function initAutocompleteAnagrafica() {
  // Comune residenza → compila provincia + CAP
  var elComune = document.getElementById('a-comune');
  var elProv   = document.getElementById('a-prov');
  var elCap    = document.getElementById('a-cap');
  if(elComune) {
    creaAutocomplete(elComune, comuniSuggerimenti, function(s) {
      elComune.value = s.label;
      if(elProv && !elProv.value) elProv.value = s.prov;
      if(elCap  && !elCap.value)  elCap.value  = s.cap;
    });
  }

  // Luogo di nascita → compila provincia di nascita
  var elLuogo   = document.getElementById('a-luogo');
  var elProvNasc = document.getElementById('a-provnascita');
  if(elLuogo) {
    creaAutocomplete(elLuogo, comuniSuggerimenti, function(s) {
      elLuogo.value = s.label;
      if(elProvNasc && !elProvNasc.value) elProvNasc.value = s.prov;
    });
  }

  // CF → maiuscolo automatico
  var elCf = document.getElementById('a-cf');
  if(elCf) {
    elCf.addEventListener('input', function() {
      var pos = elCf.selectionStart;
      elCf.value = elCf.value.toUpperCase();
      elCf.setSelectionRange(pos, pos);
    });
  }

  // Cognome → maiuscolo prima lettera
  ['a-cognome','a-nome'].forEach(function(id) {
    var el = document.getElementById(id);
    if(!el) return;
    el.addEventListener('blur', function() {
      if(el.value) el.value = el.value.charAt(0).toUpperCase() + el.value.slice(1);
    });
  });
}

// ── INIT AUTOCOMPLETE MODAL VEICOLO ──────────────────────────────────
function initAutocompleteVeicolo() {
  var elTarga  = document.getElementById('v-targa');
  var elMarca  = document.getElementById('v-marca');
  var elAnno   = document.getElementById('v-anno');
  var elClasse = document.getElementById('v-classe');

  // Marca → autocomplete
  if(elMarca) {
    creaAutocomplete(elMarca, marcheSuggerimenti, function(s) {
      elMarca.value = s.label;
    });
  }

  // Targa → decodifica automatica
  if(elTarga) {
    elTarga.addEventListener('input', function() {
      // Formatta targa: maiuscolo, rimuovi spazi
      var pos = elTarga.selectionStart;
      elTarga.value = elTarga.value.toUpperCase().replace(/[^A-Z0-9]/g,'');
      elTarga.setSelectionRange(pos, pos);

      var targa = elTarga.value;
      if(targa.length >= 7) {
        var decoded = decodificaTarga(targa);
        if(decoded) {
          // Anno: compila solo se vuoto
          if(decoded.anno && elAnno && !elAnno.value) {
            elAnno.value = decoded.anno;
            elAnno.style.background = '#f0fdf4';
            elAnno.title = 'Stimato dalla targa';
            setTimeout(function(){ elAnno.style.background = ''; }, 2000);
          }
          // Classe: compila solo se non selezionata
          if(decoded.tipo && elClasse && !elClasse.value) {
            for(var i=0; i<elClasse.options.length; i++) {
              if(elClasse.options[i].text === decoded.tipo) {
                elClasse.value = elClasse.options[i].value;
                break;
              }
            }
          }
          // Feedback visivo targa valida
          elTarga.style.borderColor = '#16a34a';
          setTimeout(function(){ elTarga.style.borderColor = ''; }, 2000);
        }
      }
    });
    // Maiuscolo su incolla
    elTarga.addEventListener('paste', function() {
      setTimeout(function(){
        elTarga.value = elTarga.value.toUpperCase().replace(/[^A-Z0-9]/g,'');
        elTarga.dispatchEvent(new Event('input'));
      }, 10);
    });
  }
}

// ── HOOK: chiama init quando si aprono le modali ──────────────────────
// Viene chiamato da demolizioni.html dopo aver aperto la modal
function onModalAnaAperta() { setTimeout(initAutocompleteAnagrafica, 50); }
function onModalVeicoloAperta() { setTimeout(initAutocompleteVeicolo, 50); }
