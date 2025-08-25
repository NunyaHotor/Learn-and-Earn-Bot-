import random

# --- African Countries Data ---
AFRICAN_COUNTRIES = [
    {"name": "Algeria", "website": "http://www.el-mouradia.dz", "bio": "A North African country with a Mediterranean coastline and a Saharan desert interior."},
    {"name": "Angola", "website": "http://www.governo.gov.ao/", "bio": "A Southern African nation whose varied terrain encompasses tropical Atlantic beaches, a labyrinthine system of rivers and Sub-Saharan desert."},
    {"name": "Benin", "website": "https://www.gouv.bj/", "bio": "A French-speaking West African nation, is a birthplace of the vodun (or “voodoo”) religion."},
    {"name": "Botswana", "website": "http://www.gov.bw/", "bio": "A landlocked country in Southern Africa, has a landscape defined by the Kalahari Desert and the Okavango Delta."},
    {"name": "Burkina Faso", "website": "https://www.gouvernement.gov.bf/", "bio": "A landlocked country in West Africa, it covers an area of around 274,200 square kilometres."},
    {"name": "Burundi", "website": "https://presidence.gov.bi/", "bio": "A landlocked country in the Great Rift Valley where the African Great Lakes region and East Africa converge."},
    {"name": "Cabo Verde", "website": "https://www.governo.cv/", "bio": "An island country in the central Atlantic Ocean."},
    {"name": "Cameroon", "website": "https://www.prc.cm/en", "bio": "A country in West Africa, on the Gulf of Guinea."},
    {"name": "Central African Republic", "website": "http://www.gouv.cf/", "bio": "A landlocked country in Central Africa."},
    {"name": "Chad", "website": "", "bio": "A landlocked country at the crossroads of North and Central Africa."},
    {"name": "Comoros", "website": "http://www.beit-salam.km", "bio": "An island country in the Indian Ocean, at the northern end of the Mozambique Channel off the eastern coast of Africa."},
    {"name": "Congo, Democratic Republic of the", "website": "http://www.presidence.cd/", "bio": "A country in Central Africa, it is the second-largest country in Africa by area and the 11th-largest in the world."},
    {"name": "Congo, Republic of the", "website": "https://www.gouvernement.cg/", "bio": "A country located in the western part of Central Africa."},
    {"name": "Côte d'Ivoire", "website": "http://www.gouv.ci/", "bio": "A West African country with beach resorts, rainforests and a French-colonial legacy."},
    {"name": "Djibouti", "website": "https://www.presidence.dj/", "bio": "A country in the Horn of Africa, bordered by Somalia to the south, Ethiopia to the southwest, Eritrea to the north, and the Red Sea and the Gulf of Aden to the east."},
    {"name": "Egypt", "website": "http://www.presidency.eg/en/", "bio": "A transcontinental country spanning the northeast corner of Africa and southwest corner of Asia via a land bridge formed by the Sinai Peninsula."},
    {"name": "Equatorial Guinea", "website": "https://www.guineaecuatorialpress.com/index.php", "bio": "A Central African country comprising the Rio Muni mainland and 5 volcanic offshore islands."},
    {"name": "Eritrea", "website": "https://shabait.com/", "bio": "A northeast African country on the Red Sea coast. It shares borders with Ethiopia, Sudan and Djibouti."},
    {"name": "Eswatini (formerly Swaziland)", "website": "http://www.gov.sz/", "bio": "A small, landlocked monarchy in southern Africa, known for its wilderness reserves and festivals showcasing traditional Swazi culture."},
    {"name": "Ethiopia", "website": "https://www.pmo.gov.et/en/", "bio": "A rugged, landlocked country split by the Great Rift Valley. With archaeological finds dating back more than 3 million years, it’s a place of ancient culture."},
    {"name": "Gabon", "website": "http://www.gouvernement.ga/", "bio": "A country along the Atlantic coast of Central Africa. It has significant areas of protected parkland."},
    {"name": "Gambia", "website": "https://www.statehouse.gm/", "bio": "A small West African country, bounded by Senegal, with a narrow Atlantic coastline."},
    {"name": "Ghana", "website": "https://www.ghana.gov.gh/", "bio": "A country in West Africa, situated on the coast of the Gulf of Guinea."},
    {"name": "Guinea", "website": "https://www.presidence.gov.gn/", "bio": "A country in West Africa, bordered on the west by the Atlantic Ocean."},
    {"name": "Guinea-Bissau", "website": "http://www.gov.gw/", "bio": "A tropical country on West Africa’s Atlantic coast that’s known for national parks and wildlife."},
    {"name": "Kenya", "website": "https://www.president.go.ke/", "bio": "A country in East Africa with coastline on the Indian Ocean. It encompasses savannah, lakelands, the dramatic Great Rift Valley and mountain highlands."},
    {"name": "Lesotho", "website": "http://www.gov.ls/", "bio": "A high-altitude, landlocked kingdom encircled by South Africa, is crisscrossed by a network of rivers and mountain ranges including the 3,482m-high peak of Thabana Ntlenyana."},
    {"name": "Liberia", "website": "http://www.emansion.gov.lr/", "bio": "A country on the West African coast. It is bordered by Sierra Leone to its west, Guinea to its north and Côte d'Ivoire to its east."},
    {"name": "Libya", "website": "", "bio": "A country in the Maghreb region in North Africa, bordered by the Mediterranean Sea to the north, Egypt to the east, Sudan to the southeast, Chad to the south, Niger to the southwest, Algeria to the west, and Tunisia to the northwest."},
    {"name": "Madagascar", "website": "http.www.presidence.gov.mg/", "bio": "A huge island nation off the southeast coast of Africa."},
    {"name": "Malawi", "website": "https://www.malawi.gov.mw/", "bio": "A landlocked country in southeastern Africa, is defined by its topography of highlands split by the Great Rift Valley and enormous Lake Malawi."},
    {"name": "Mali", "website": "https://www.primature.ml/", "bio": "A landlocked country in West Africa, a region geologically identified with the West Africa Craton."},
    {"name": "Mauritania", "website": "http://www.presidence.mr/", "bio": "A country in Northwest Africa. It is the eleventh largest sovereign state in Africa and is bordered by the Atlantic Ocean to the west, Western Sahara to the north and northwest, Algeria to the northeast, Mali to the east and southeast, and Senegal to the southwest."},
    {"name": "Mauritius", "website": "https://www.govmu.org", "bio": "An island nation in the Indian Ocean, is known for its beaches, lagoons and reefs."},
    {"name": "Morocco", "website": "https://www.maroc.ma/en/", "bio": "A North African country bordering the Atlantic Ocean and Mediterranean Sea, is distinguished by its Berber, Arabian and European cultural influences."},
    {"name": "Mozambique", "website": "http://www.portaldogoverno.gov.mz/", "bio": "A southern African nation whose long Indian Ocean coastline is dotted with popular beaches like Tofo, as well as offshore marine parks."},
    {"name": "Namibia", "website": "http://www.gov.na/", "bio": "A country in southwest Africa, is distinguished by the Namib Desert along its Atlantic Ocean coast."},
    {"name": "Niger", "website": "http://www.presidence.ne/", "bio": "A landlocked country in West Africa named after the Niger River."},
    {"name": "Nigeria", "website": "https://www.nigeria.gov.ng/", "bio": "An African country on the Gulf of Guinea, has many natural landmarks and wildlife reserves."},
    {"name": "Rwanda", "website": "https://www.gov.rw/", "bio": "A landlocked country in the Great Rift Valley where the African Great Lakes region and East Africa converge."},
    {"name": "Sao Tome and Principe", "website": "http://www.gov.st/", "bio": "An African island nation close to the equator, is part of a volcano chain featuring striking rock and coral formations, tropical rainforests and beaches."},
    {"name": "Senegal", "website": "http://www.sec.gouv.sn/", "bio": "A country on Africa’s west coast with a rich French colonial heritage and many natural attractions."},
    {"name": "Seychelles", "website": "http://www.gov.sc/", "bio": "An archipelago of 115 islands in the Indian Ocean, off East Africa. It's home to numerous beaches, coral reefs and nature reserves, as well as rare animals such as giant Aldabra tortoises."},
    {"name": "Sierra Leone", "website": "https://www.statehouse.gov.sl/", "bio": "A country in West Africa, on the Atlantic Ocean. It’s known for the white-sand beaches lining the Freetown Peninsula."},
    {"name": "Somalia", "website": "https://www.somaligov.so/", "bio": "A country in the Horn of Africa. It is bordered by Ethiopia to the west, Djibouti to the northwest, the Gulf of Aden to the north, the Indian Ocean to the east, and Kenya to the southwest."},
    {"name": "South Africa", "website": "https://www.gov.za/", "bio": "A country on the southernmost tip of the African continent, marked by several distinct ecosystems."},
    {"name": "South Sudan", "website": "http://www.goss-online.org/", "bio": "A landlocked country in East-Central Africa."},
    {"name": "Sudan", "website": "", "bio": "A country in Northeast Africa. It is bordered by Egypt to the north, the Red Sea to the northeast, Eritrea to the east, Ethiopia to the southeast, South Sudan to the south, the Central African Republic to the southwest, Chad to the west and Libya to the northwest."},
    {"name": "Tanzania", "website": "http://www.tanzania.go.tz/", "bio": "An East African country known for its vast wilderness areas. They include the plains of Serengeti National Park, a safari mecca populated by the “big five” game (elephant, lion, leopard, buffalo, rhino), and Kilimanjaro National Park, home to Africa’s highest mountain."},
    {"name": "Togo", "website": "https://www.gouvernement.tg/", "bio": "A West African nation on the Gulf of Guinea, is known for its palm-lined beaches and hilltop villages."},
    {"name": "Tunisia", "website": "http://www.tunisie.gov.tn/", "bio": "A North African country bordering the Mediterranean Sea and Sahara Desert."},
    {"name": "Uganda", "website": "https://www.statehouse.go.ug/", "bio": "A landlocked country in East Africa whose diverse landscape encompasses the snow-capped Rwenzori Mountains and immense Lake Victoria."},
    {"name": "Zambia", "website": "https://www.statehouse.gov.zm/", "bio": "A landlocked country in southern Africa, features rugged terrain and diverse wildlife, with many parks and safari areas."},
    {"name": "Zimbabwe", "website": "http://www.zim.gov.zw/", "bio": "A landlocked country in southern Africa known for its dramatic landscape and diverse wildlife, much of it within parks, reserves and safari areas."}
]

# --- Unified Quiz Data ---
ALL_QUIZZES = [
    # General
    {"q": "Who was Ghana's first president?", "a": "Kwame Nkrumah", "choices": ["Kwame Nkrumah", "Rawlings", "Mahama", "Busia"]},
    {"q": "When did Ghana gain independence?", "a": "1957", "choices": ["1945", "1957", "1960", "1966"]},
    {"q": "What is the capital of Ghana?", "a": "Accra", "choices": ["Kumasi", "Tamale", "Accra", "Ho"]},
    {"q": "Which region is Lake Volta in?", "a": "Volta", "choices": ["Ashanti", "Volta", "Northern", "Bono"]},
    {"q": "Who led the 1948 Accra Riots?", "a": "The Big Six", "choices": ["Yaa Asantewaa", "The Big Six", "Danquah", "Rawlings"]},
    {"q": "What is the largest country in Africa by land area?", "a": "Algeria", "choices": ["Nigeria", "Algeria", "Egypt", "South Africa"]},
    {"q": "Which African country has the most pyramids?", "a": "Sudan", "choices": ["Egypt", "Sudan", "Ethiopia", "Libya"]},
    {"q": "What is the official language of Angola?", "a": "Portuguese", "choices": ["French", "Portuguese", "English", "Spanish"]},
    {"q": "Which African river is the longest?", "a": "Nile", "choices": ["Congo", "Niger", "Zambezi", "Nile"]},
    {"q": "Which African country is known as the Rainbow Nation?", "a": "South Africa", "choices": ["Ghana", "South Africa", "Kenya", "Tanzania"]},
    {"q": "Which African island nation lies off the southeast coast of Africa?", "a": "Madagascar", "choices": ["Seychelles", "Mauritius", "Madagascar", "Comoros"]},
    {"q": "What is the largest desert in Africa?", "a": "Sahara", "choices": ["Namib", "Sahara", "Kalahari", "Gobi"]},
    {"q": "Which African country was never colonized?", "a": "Ethiopia", "choices": ["Ghana", "Liberia", "Ethiopia", "Morocco"]},
    {"q": "Which African country produces the most cocoa?", "a": "Côte d'Ivoire", "choices": ["Ghana", "Nigeria", "Cameroon", "Côte d'Ivoire"]},
    {"q": "What is the currency of Nigeria?", "a": "Naira", "choices": ["Cedi", "Shilling", "Rand", "Naira"]},
    {"q": "Who was the Ethiopian emperor who defeated Italy at Adwa in 1896?", "a": "Menelik II", "choices": ["Haile Selassie", "Menelik II", "Tewodros II", "Yohannes IV"]},
    {"q": "Which ancient African kingdom was known for its gold trade?", "a": "Mali Empire", "choices": ["Songhai", "Mali Empire", "Ghana Empire", "Kanem"]},
    {"q": "Who was the first woman to win a Nobel Peace Prize from Africa?", "a": "Wangari Maathai", "choices": ["Ellen Johnson Sirleaf", "Wangari Maathai", "Leymah Gbowee", "Tawakkol Karman"]},
    {"q": "Which African city is known as the 'Mother City'?", "a": "Cape Town", "choices": ["Lagos", "Cairo", "Cape Town", "Nairobi"]},
    {"q": "What was the ancient name of Ethiopia?", "a": "Abyssinia", "choices": ["Nubia", "Kush", "Abyssinia", "Axum"]},
    {"q": "Which African leader coined the term 'African Socialism'?", "a": "Julius Nyerere", "choices": ["Kwame Nkrumah", "Julius Nyerere", "Kenneth Kaunda", "Jomo Kenyatta"]},
    {"q": "The Great Rift Valley runs through which part of Africa?", "a": "East Africa", "choices": ["West Africa", "North Africa", "East Africa", "Central Africa"]},
    {"q": "Which African country was formerly known as Southern Rhodesia?", "a": "Zimbabwe", "choices": ["Zambia", "Zimbabwe", "Botswana", "Malawi"]},
    {"q": "Who was known as the 'Father of African Nationalism'?", "a": "Marcus Garvey", "choices": ["W.E.B. Du Bois", "Marcus Garvey", "Kwame Nkrumah", "Nelson Mandela"]},
    {"q": "Which African queen fought against Roman expansion?", "a": "Queen Nzinga", "choices": ["Queen Nefertiti", "Queen Nzinga", "Queen Candace", "Queen Amina"]},
    {"q": "What is the highest mountain in Africa?", "a": "Mount Kilimanjaro", "choices": ["Mount Kenya", "Mount Kilimanjaro", "Ras Dashen", "Mount Elgon"]},
    {"q": "Which African empire controlled the salt and gold trade routes?", "a": "Songhai Empire", "choices": ["Mali Empire", "Ghana Empire", "Songhai Empire", "Kanem Empire"]},
    {"q": "Who was the last Pharaoh of Egypt?", "a": "Cleopatra VII", "choices": ["Nefertiti", "Hatshepsut", "Cleopatra VII", "Ankhesenamun"]},
    {"q": "Which African country has the most official languages?", "a": "South Africa", "choices": ["Nigeria", "South Africa", "Kenya", "Tanzania"]},
    {"q": "What was the original name of Ghana before independence?", "a": "Gold Coast", "choices": ["Gold Coast", "Ivory Coast", "Slave Coast", "Grain Coast"]},
    {"q": "Which African kingdom was famous for its terracotta sculptures?", "a": "Nok", "choices": ["Benin", "Nok", "Ife", "Oyo"]},
    {"q": "Who wrote the novel 'Things Fall Apart'?", "a": "Chinua Achebe", "choices": ["Wole Soyinka", "Chinua Achebe", "Ngugi wa Thiong'o", "Ama Ata Aidoo"]},
    {"q": "Which lake is shared by Kenya, Tanzania, and Uganda?", "a": "Lake Victoria", "choices": ["Lake Tanganyika", "Lake Victoria", "Lake Malawi", "Lake Chad"]},
    {"q": "What does 'Ubuntu' mean in African philosophy?", "a": "I am because we are", "choices": ["Unity in diversity", "I am because we are", "Strength in numbers", "Peace and harmony"]},
    {"q": "Which African country was the first to gain independence?", "a": "Libya", "choices": ["Ghana", "Nigeria", "Libya", "Morocco"]},
    {"q": "Who was the founder of the Kingdom of Zulu?", "a": "Shaka Zulu", "choices": ["Shaka Zulu", "Cetshwayo", "Dingane", "Mpande"]},
    {"q": "Which African country is landlocked and bordered by 7 countries?", "a": "Chad", "choices": ["Mali", "Niger", "Chad", "Burkina Faso"]},
    {"q": "What is the largest lake in Africa?", "a": "Lake Victoria", "choices": ["Lake Tanganyika", "Lake Victoria", "Lake Malawi", "Lake Chad"]},
    {"q": "Which African country has both Atlantic and Indian Ocean coastlines?", "a": "South Africa", "choices": ["Somalia", "South Africa", "Morocco", "Egypt"]},
    {"q": "What is the lowest point in Africa?", "a": "Lake Assal", "choices": ["Dead Sea", "Lake Assal", "Qattara Depression", "Danakil Depression"]},
    {"q": "Which African mountain range is located in Morocco?", "a": "Atlas Mountains", "choices": ["Atlas Mountains", "Drakensberg", "Ethiopian Highlands", "Ahaggar Mountains"]},
    {"q": "What is the currency of Kenya?", "a": "Shilling", "choices": ["Rand", "Shilling", "Birr", "Dinar"]},
    {"q": "Which African country uses the Franc CFA?", "a": "Senegal", "choices": ["Ghana", "Nigeria", "Senegal", "Ethiopia"]},
    {"q": "What is the currency of Egypt?", "a": "Pound", "choices": ["Dinar", "Dirham", "Pound", "Birr"]},
    {"q": "Which currency is used in Morocco?", "a": "Dirham", "choices": ["Dinar", "Dirham", "Franc", "Pound"]},
    {"q": "What is the currency of Ethiopia?", "a": "Birr", "choices": ["Birr", "Shilling", "Rand", "Naira"]},
    {"q": "Which African country is the largest producer of diamonds?", "a": "Botswana", "choices": ["South Africa", "Botswana", "Angola", "Congo"]},
    {"q": "What is Africa's largest stock exchange?", "a": "Johannesburg Stock Exchange", "choices": ["Nigerian Stock Exchange", "Johannesburg Stock Exchange", "Egyptian Exchange", "Nairobi Securities Exchange"]},
    {"q": "Which African country exports the most oil?", "a": "Nigeria", "choices": ["Angola", "Nigeria", "Algeria", "Libya"]},
    {"q": "What is the main export of Zambia?", "a": "Copper", "choices": ["Gold", "Copper", "Cobalt", "Zinc"]},
    {"q": "Which country is famous for the city of Livingstone?", "a": "Zambia", "choices": ["Zambia", "Zimbabwe", "Botswana", "South Africa"]},
    
    # Additional 65 African-related quizzes
    # History
    {"q": "Which ancient African kingdom built the pyramids of Meroë?", "a": "Kingdom of Kush", "choices": ["Ancient Egypt", "Kingdom of Kush", "Axum", "Carthage"]},
    {"q": "In which year did the Battle of Adwa take place?", "a": "1896", "choices": ["1885", "1896", "1900", "1914"]},
    {"q": "Who was the founder of the Mali Empire?", "a": "Sundiata Keita", "choices": ["Mansa Musa", "Sundiata Keita", "Askia Muhammad", "Sonni Ali"]},
    {"q": "Which African leader was known as the 'Lion King'?", "a": "Haile Selassie", "choices": ["Haile Selassie", "Idi Amin", "Mobutu Sese Seko", "Robert Mugabe"]},
    {"q": "What was the name of the trade route that connected West Africa to North Africa?", "a": "Trans-Saharan trade route", "choices": ["Silk Road", "Trans-Saharan trade route", "Indian Ocean trade", "Red Sea trade"]},
    {"q": "Which African country was formerly known as Abyssinia?", "a": "Ethiopia", "choices": ["Eritrea", "Ethiopia", "Somalia", "Sudan"]},
    {"q": "Who was the first president of independent Kenya?", "a": "Jomo Kenyatta", "choices": ["Jomo Kenyatta", "Daniel arap Moi", "Mwai Kibaki", "Uhuru Kenyatta"]},
    {"q": "Which empire was ruled by Mansa Musa?", "a": "Mali Empire", "choices": ["Songhai Empire", "Mali Empire", "Ghana Empire", "Kanem-Bornu"]},
    {"q": "In which country is the ancient city of Timbuktu located?", "a": "Mali", "choices": ["Niger", "Mali", "Burkina Faso", "Senegal"]},
    {"q": "Which African queen led resistance against French colonialism in Madagascar?", "a": "Ranavalona III", "choices": ["Ranavalona III", "Nzinga Mbande", "Amina of Zaria", "Yaa Asantewaa"]},
    
    # Culture
    {"q": "What is the traditional cloth of Ghana called?", "a": "Kente", "choices": ["Ankara", "Kente", "Aso Oke", "Kitenge"]},
    {"q": "Which African country is famous for its Great Sphinx?", "a": "Egypt", "choices": ["Sudan", "Egypt", "Libya", "Tunisia"]},
    {"q": "What is the traditional dance of the Zulu people called?", "a": "Indlamu", "choices": ["Kpanlogo", "Indlamu", "Agbekor", "Ewe"]},
    {"q": "Which African ethnic group is known for their elaborate wooden masks?", "a": "Dogon", "choices": ["Dogon", "Yoruba", "Ashanti", "Zulu"]},
    {"q": "What is the traditional instrument of the West African griots?", "a": "Kora", "choices": ["Balafon", "Kora", "Djembe", "Talking drum"]},
    {"q": "Which African country is home to the Maasai people?", "a": "Kenya", "choices": ["Tanzania", "Kenya", "Uganda", "Rwanda"]},
    {"q": "What is the traditional beer of South Africa called?", "a": "Umqombothi", "choices": ["Sorghum beer", "Umqombothi", "Palm wine", "Tej"]},
    {"q": "Which African country is famous for its rock-hewn churches?", "a": "Ethiopia", "choices": ["Eritrea", "Ethiopia", "Sudan", "Somalia"]},
    {"q": "What is the traditional greeting in Swahili?", "a": "Jambo", "choices": ["Sannu", "Jambo", "Molo", "Sawubona"]},
    {"q": "Which African people are known for their distinctive lip plates?", "a": "Mursi", "choices": ["Himba", "Mursi", "Tuareg", "Berber"]},
    
    # Religion
    {"q": "What is the dominant religion in North Africa?", "a": "Islam", "choices": ["Christianity", "Islam", "Traditional African religions", "Judaism"]},
    {"q": "Which African country has the largest Muslim population?", "a": "Nigeria", "choices": ["Egypt", "Nigeria", "Algeria", "Morocco"]},
    {"q": "What percentage of Africans identify as Christian?", "a": "49%", "choices": ["30%", "49%", "65%", "80%"]},
    {"q": "Which African country was the first to adopt Christianity as state religion?", "a": "Ethiopia", "choices": ["Egypt", "Ethiopia", "Sudan", "Eritrea"]},
    {"q": "What is the largest church building in Africa?", "a": "Basilica of Our Lady of Peace", "choices": ["St. Peter's Basilica", "Basilica of Our Lady of Peace", "National Cathedral Ghana", "Christ the King Cathedral"]},
    {"q": "Which African country has the most churches per capita?", "a": "Rwanda", "choices": ["Ghana", "Nigeria", "Rwanda", "South Africa"]},
    {"q": "What is the traditional religion of the Yoruba people?", "a": "Ifá", "choices": ["Voodoo", "Ifá", "Santería", "Candomblé"]},
    {"q": "Which African country is home to the Mourides brotherhood?", "a": "Senegal", "choices": ["Mali", "Senegal", "Nigeria", "Morocco"]},
    {"q": "What is the holy city of the Ethiopian Orthodox Church?", "a": "Axum", "choices": ["Lalibela", "Axum", "Gondar", "Addis Ababa"]},
    {"q": "Which African country has the oldest mosque in Sub-Saharan Africa?", "a": "Nigeria", "choices": ["Ghana", "Nigeria", "Senegal", "Sudan"]},
    
    # Commerce
    {"q": "What is the largest market in West Africa?", "a": "Kejetia Market", "choices": ["Makola Market", "Kejetia Market", "Onitsha Market", "Kano Market"]},
    {"q": "Which African country is the world's largest producer of cocoa?", "a": "Côte d'Ivoire", "choices": ["Ghana", "Nigeria", "Cameroon", "Côte d'Ivoire"]},
    {"q": "What is the main export of Ghana?", "a": "Gold", "choices": ["Oil", "Gold", "Cocoa", "Timber"]},
    {"q": "Which African country has the largest economy by GDP?", "a": "Nigeria", "choices": ["South Africa", "Egypt", "Nigeria", "Algeria"]},
    {"q": "What is the busiest port in Africa?", "a": "Port of Durban", "choices": ["Port of Lagos", "Port of Durban", "Port of Mombasa", "Port of Alexandria"]},
    {"q": "Which African country is the largest producer of platinum?", "a": "South Africa", "choices": ["Zimbabwe", "South Africa", "Botswana", "Zambia"]},
    {"q": "What is the main agricultural export of Kenya?", "a": "Tea", "choices": ["Coffee", "Tea", "Flowers", "Tobacco"]},
    {"q": "Which African country has the most developed banking sector?", "a": "South Africa", "choices": ["Nigeria", "Kenya", "South Africa", "Egypt"]},
    {"q": "What is the currency of Morocco?", "a": "Dirham", "choices": ["Dinar", "Dirham", "Franc", "Pound"]},
    {"q": "Which African country is the largest producer of coffee?", "a": "Ethiopia", "choices": ["Kenya", "Uganda", "Ethiopia", "Rwanda"]},
    
    # Business
    {"q": "Who is Africa's richest person according to Forbes 2023?", "a": "Aliko Dangote", "choices": ["Nassef Sawiris", "Aliko Dangote", "Mike Adenuga", "Nicky Oppenheimer"]},
    {"q": "Which African country has the highest mobile money penetration?", "a": "Kenya", "choices": ["Ghana", "Nigeria", "Kenya", "South Africa"]},
    {"q": "What is the largest telecommunications company in Africa?", "a": "MTN Group", "choices": ["Vodacom", "MTN Group", "Airtel Africa", "Orange"]},
    {"q": "Which African stock exchange was the first to list Bitcoin?", "a": "Nigerian Stock Exchange", "choices": ["Johannesburg Stock Exchange", "Nigerian Stock Exchange", "Egyptian Exchange", "Nairobi Securities Exchange"]},
    {"q": "What is the largest fintech company in Africa by valuation?", "a": "Flutterwave", "choices": ["Paystack", "Flutterwave", "Chipper Cash", "Wave"]},
    {"q": "Which African country has the most unicorns?", "a": "Nigeria", "choices": ["South Africa", "Kenya", "Nigeria", "Egypt"]},
    {"q": "What is the largest e-commerce platform in Africa?", "a": "Jumia", "choices": ["Konga", "Jumia", "Takealot", "Kilimall"]},
    {"q": "Which African country has the highest GDP per capita?", "a": "Seychelles", "choices": ["Mauritius", "Seychelles", "Botswana", "South Africa"]},
    {"q": "What is the largest construction company in Africa?", "a": "Arab Contractors", "choices": ["Julius Berger", "Arab Contractors", "WBHO", "Stefanutti Stocks"]},
    {"q": "Which African country has the most developed startup ecosystem?", "a": "Nigeria", "choices": ["South Africa", "Kenya", "Nigeria", "Egypt"]},
    
    # Additional History
    {"q": "Which African kingdom was known for its obelisks?", "a": "Kingdom of Axum", "choices": ["Kingdom of Kush", "Kingdom of Axum", "Mali Empire", "Songhai Empire"]},
    {"q": "Who was the last emperor of Ethiopia?", "a": "Haile Selassie", "choices": ["Menelik II", "Haile Selassie", "Tewodros II", "Yohannes IV"]},
    {"q": "Which African country was the first to gain independence from colonial rule?", "a": "Liberia", "choices": ["Ghana", "Liberia", "Ethiopia", "Egypt"]},
    {"q": "What was the name of the empire that ruled much of North Africa from 909-1171?", "a": "Fatimid Caliphate", "choices": ["Umayyad Caliphate", "Fatimid Caliphate", "Abbasid Caliphate", "Ottoman Empire"]},
    {"q": "Which African leader was known as the 'Black Napoleon'?", "a": "Toussaint Louverture", "choices": ["Shaka Zulu", "Toussaint Louverture", "Samori Ture", "Yaa Asantewaa"]},
    
    # Additional Culture
    {"q": "What is the traditional dish of Ethiopia?", "a": "Injera with wat", "choices": ["Jollof rice", "Injera with wat", "Fufu and soup", "Couscous"]},
    {"q": "Which African country is known for its blue men?", "a": "Tuareg of Mali/Niger", "choices": ["Berbers of Morocco", "Tuareg of Mali/Niger", "Fulani of Nigeria", "Maasai of Kenya"]},
    {"q": "What is the traditional wrestling sport of Senegal called?", "a": "Laamb", "choices": ["Dambe", "Laamb", "Nguni stick fighting", "Engolo"]},
    {"q": "Which African country has the most UNESCO World Heritage sites?", "a": "South Africa", "choices": ["Egypt", "Morocco", "South Africa", "Ethiopia"]},
    {"q": "What is the traditional hairstyle of married Zulu women?", "a": "Isicholo", "choices": ["Bantu knots", "Isicholo", "Fulani braids", "Ethiopian cornrows"]},
    
    # Additional Commerce
    {"q": "Which African country has the largest gold reserves?", "a": "South Africa", "choices": ["Ghana", "South Africa", "Sudan", "Mali"]},
    {"q": "What is the main export of Botswana?", "a": "Diamonds", "choices": ["Gold", "Copper", "Diamonds", "Platinum"]},
    {"q": "Which African country is the largest producer of uranium?", "a": "Niger", "choices": ["Namibia", "Niger", "South Africa", "Malawi"]},
    {"q": "What is the largest shopping mall in Africa?", "a": "Mall of Africa", "choices": ["Sandton City", "Mall of Africa", "Two Rivers Mall", "Gateway Theatre of Shopping"]},
    {"q": "Which African country has the most billionaires?", "a": "South Africa", "choices": ["Nigeria", "Egypt", "South Africa", "Morocco"]}
]

player_progress = {}
user_question_pools = {}

def init_player_progress(user_id):
    if user_id not in player_progress:
        player_progress[user_id] = {
            'current_streak': 0,
            'best_streak': 0,
            'total_correct': 0,
            'total_questions': 0,
            'questions_until_bonus': 10,
            'skips_used': 0,
            'games_paused': 0
        }

def update_player_progress(user_id, is_correct):
    init_player_progress(user_id)
    progress = player_progress[user_id]
    progress['total_questions'] += 1
    if is_correct:
        progress['current_streak'] += 1
        progress['total_correct'] += 1
        progress['questions_until_bonus'] -= 1
        if progress['questions_until_bonus'] == 0:
            progress['questions_until_bonus'] = 10
            progress['current_streak'] = 0
            return True
    else:
        progress['current_streak'] = 0
        progress['questions_until_bonus'] = 10
    progress['best_streak'] = max(progress['best_streak'], progress['current_streak'])
    return False

def get_random_question(user_id):
    if user_id not in user_question_pools:
        user_question_pools[user_id] = []
    
    used_questions = user_question_pools[user_id]
    available_questions = [q for q in ALL_QUIZZES if q['q'] not in used_questions]
    
    if not available_questions:
        user_question_pools[user_id] = []
        available_questions = ALL_QUIZZES
        
    selected_quiz = random.choice(available_questions)
    user_question_pools[user_id].append(selected_quiz['q'])
    return selected_quiz
