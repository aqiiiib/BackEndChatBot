# This file represents the "Knowledge Base" (Tier 3) of the architecture.
# It acts as the "brain memory" storing all data the chatbot needs to answer queries.
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Static Information Storage
    # Stores fixed responses (like greetings, FAQs, farewells) that don't change often.
    c.execute("""
        CREATE TABLE IF NOT EXISTS static_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intent TEXT NOT NULL,
            keywords TEXT NOT NULL,
            response TEXT NOT NULL
        )
    """)

    # Dynamic Information Storage
    # Stores travel packages which can be updated, added or removed over time.
    c.execute("""
        CREATE TABLE IF NOT EXISTS packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            destination TEXT NOT NULL,
            duration TEXT NOT NULL,
            price_usd REAL NOT NULL,
            description TEXT NOT NULL,
            highlights TEXT NOT NULL
        )
    """)

    # Machine Learning / Self-Learning Feature (Part 1)
    # When the bot doesn't understand a query, it saves it here.
    c.execute("""
        CREATE TABLE IF NOT EXISTS unknown_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            answered INTEGER DEFAULT 0,
            answer TEXT
        )
    """)

    # Machine Learning / Self-Learning Feature (Part 2)
    # Once the admin provides an answer for an unknown query, it's stored here so the bot Learns it forever.
    c.execute("""
        CREATE TABLE IF NOT EXISTS learned_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger_phrase TEXT NOT NULL,
            response TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    seed_data()


def seed_data():
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM static_responses")
    if c.fetchone()[0] > 0:
        conn.close()
        return

    static = [
        ("greeting", "hi,hello,hey,greetings,good morning,good afternoon,good evening,howdy",
         "Hello! Welcome to Sri Lanka Travel Assistant. I can help you explore amazing destinations, find travel packages, and plan your perfect trip to Sri Lanka. What would you like to know?"),

        ("farewell", "bye,goodbye,see you,take care,farewell,cya,later",
         "Goodbye! Thank you for choosing Sri Lanka Travel. We hope to see you on the island soon! Have a wonderful journey."),

        ("thanks", "thanks,thank you,thank,appreciate,cheers,ty",
         "You're most welcome! Feel free to ask if you need any more help planning your Sri Lanka adventure."),

        ("about", "who are you,what are you,tell me about yourself,what can you do,help",
         "I'm your Sri Lanka Travel Assistant — an AI-powered chatbot here to help you discover the beauty of Sri Lanka. I can tell you about travel packages, popular destinations, best times to visit, visa requirements, local cuisine, and much more. Just ask away!"),

        ("visa", "visa,visa requirements,do i need a visa,entry,passport,etv,eta",
         "Most visitors to Sri Lanka require an Electronic Travel Authorization (ETA). You can apply online at eta.gov.lk. The fee is around USD 35 for most nationalities, and it's valid for 30 days (extendable). Citizens of the Maldives and Singapore may be eligible for free ETA. Always check the official site for your specific nationality."),

        ("weather", "weather,climate,best time,when to visit,season,rain,monsoon,temperature",
         "Sri Lanka has two main seasons due to monsoons. The west and south coasts (Colombo, Galle) are best from December to March. The east coast (Trincomalee, Arugam Bay) is best from April to September. The hill country (Kandy, Ella) is generally pleasant year-round. Overall, December to March is the most popular time to visit."),

        ("currency", "currency,money,exchange,rupee,lkr,usd,cost,budget,expensive,cheap",
         "The Sri Lankan Rupee (LKR) is the local currency. As of 2024, approximately 1 USD = 300 LKR. Sri Lanka is budget-friendly — a mid-range meal costs around 500-1500 LKR, and guesthouses start from 2000 LKR/night. ATMs are widely available in cities. Inform your bank before travel."),

        ("food", "food,eat,cuisine,dish,restaurant,rice,curry,kottu,hoppers,seafood",
         "Sri Lankan cuisine is rich and flavorful! Must-tries include: Rice & Curry (the staple), Kottu Roti (chopped roti stir-fry), Hoppers (bowl-shaped pancakes), Fresh Seafood (especially in coastal areas), and Pol Sambol (coconut relish). Street food is safe and delicious. Don't miss a traditional rice and curry banana leaf meal!"),

        ("transport", "transport,travel,bus,train,tuk tuk,taxi,car,hire,getting around,how to get",
         "Getting around Sri Lanka: Trains are scenic and affordable (Kandy-Ella route is world-famous). Buses cover most routes cheaply. Tuk-tuks are perfect for short distances — always negotiate the fare. Private car hire with a driver is popular for tours (around USD 50-70/day). Ride-hailing apps like PickMe are available in cities."),

        ("destinations", "destinations,places,where to go,must see,attractions,famous,popular,top places,visit",
         "Top destinations in Sri Lanka: Sigiriya (ancient rock fortress), Kandy (cultural capital, Temple of the Tooth), Ella (misty hills, Nine Arch Bridge), Galle (Dutch colonial fort town), Mirissa & Unawatuna (beaches), Yala National Park (leopards & wildlife), Trincomalee (east coast beaches), Nuwara Eliya (tea country). Each offers a unique experience!"),

        ("accommodation", "hotel,stay,accommodation,guesthouse,resort,airbnb,where to stay,lodge,hostel",
         "Sri Lanka has accommodation for every budget. Luxury resorts in Colombo and coastal areas start from USD 100+/night. Mid-range hotels and boutique guesthouses cost USD 25-60/night. Budget guesthouses and hostels are available from USD 10-20/night. Booking.com and Agoda are popular platforms. We also recommend local guesthouses for authentic experiences!"),
    ]

    c.executemany(
        "INSERT INTO static_responses (intent, keywords, response) VALUES (?, ?, ?)", static
    )

    packages = [
        ("Classic Sri Lanka", "Colombo, Kandy, Nuwara Eliya, Ella, Galle",
         "8 Days / 7 Nights", 850.00,
         "The most popular island circuit covering cultural highlights, scenic hill country, and beautiful beaches.",
         "Sigiriya Rock, Temple of the Tooth, Tea Plantation Tour, Ella Nine Arch Bridge, Galle Fort"),

        ("Beach & Surf Paradise", "Mirissa, Unawatuna, Hikkaduwa, Arugam Bay",
         "6 Days / 5 Nights", 620.00,
         "Perfect for beach lovers and surfers. Explore Sri Lanka's finest coastlines, go whale watching, and surf world-class waves.",
         "Whale Watching in Mirissa, Surfing at Arugam Bay, Snorkeling, Beach Hopping, Sunset Cruises"),

        ("Cultural Triangle", "Colombo, Anuradhapura, Polonnaruwa, Sigiriya, Kandy",
         "5 Days / 4 Nights", 550.00,
         "Immerse yourself in ancient civilizations. Visit UNESCO World Heritage Sites and centuries-old Buddhist temples.",
         "Ancient City of Anuradhapura, Polonnaruwa Ruins, Sigiriya Rock Fortress, Dambulla Cave Temple, Kandy Perahera"),

        ("Wildlife Safari Adventure", "Yala, Udawalawe, Wilpattu, Minneriya",
         "7 Days / 6 Nights", 780.00,
         "Experience Sri Lanka's incredible wildlife. Spot leopards, elephants, and hundreds of bird species in their natural habitat.",
         "Yala Leopard Safari, Udawalawe Elephant Gathering, Wilpattu Jungle, Bird Watching, Nature Walks"),

        ("Honeymoon Special", "Colombo, Kandy, Nuwara Eliya, Bentota",
         "9 Days / 8 Nights", 1200.00,
         "A romantic journey through scenic highlands and pristine beaches. Luxury resorts, couple spa treatments, and private dining.",
         "Luxury Resort Stay, Private Beach Dinners, Couple Spa, Scenic Train Ride, Sunset Boat Cruise"),

        ("Budget Backpacker", "Colombo, Kandy, Ella, Mirissa",
         "7 Days / 6 Nights", 320.00,
         "See the best of Sri Lanka on a budget. Hostels, local food, public transport, and unforgettable experiences.",
         "Hostel Network, Local Street Food, Public Train Travel, Hiking in Ella, Budget Beach Stays"),
    ]

    c.executemany(
        "INSERT INTO packages (name, destination, duration, price_usd, description, highlights) VALUES (?,?,?,?,?,?)",
        packages
    )

    conn.commit()
    conn.close()


def get_all_static_responses():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT intent, keywords, response FROM static_responses")
    rows = c.fetchall()
    conn.close()
    return rows


def get_all_packages():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM packages")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_packages(keyword):
    conn = get_connection()
    c = conn.cursor()
    kw = f"%{keyword}%"
    c.execute("""
        SELECT * FROM packages
        WHERE name LIKE ? OR destination LIKE ? OR description LIKE ? OR highlights LIKE ?
    """, (kw, kw, kw, kw))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_unknown_query(user_input):
    conn = get_connection()
    c = conn.cursor()
    # Avoid duplicates
    c.execute("SELECT id FROM unknown_queries WHERE user_input = ? AND answered = 0", (user_input,))
    if not c.fetchone():
        c.execute("INSERT INTO unknown_queries (user_input) VALUES (?)", (user_input,))
        conn.commit()
    conn.close()


def get_learned_response(trigger):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT response FROM learned_responses WHERE LOWER(trigger_phrase) = LOWER(?)", (trigger,))
    row = c.fetchone()
    conn.close()
    return row["response"] if row else None


def add_learned_response(trigger, response):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO learned_responses (trigger_phrase, response) VALUES (?, ?)", (trigger, response))
    # Also mark matching unknown queries as answered
    c.execute("UPDATE unknown_queries SET answered = 1, answer = ? WHERE LOWER(user_input) = LOWER(?)",
              (response, trigger))
    conn.commit()
    conn.close()


def get_unanswered_queries():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, user_input, timestamp FROM unknown_queries WHERE answered = 0 ORDER BY timestamp DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]
