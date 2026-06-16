"""Curated travel-destination dataset for Feature 4 (auto-embedding).

Chosen for the demo because each description is semantically distinct, so a
natural-language query produces obviously-different, defensible rankings.
Documents store PLAIN TEXT only — Atlas generates the embeddings automatically
from the `description` field at index time.
"""
from __future__ import annotations

DESTINATIONS: list[dict] = [
    {
        "name": "Kyoto",
        "country": "Japan",
        "region": "Kansai",
        "best_season": "Spring & Autumn",
        "tags": ["temples", "gardens", "tradition", "tea"],
        "description": "A serene former imperial capital of wooden temples, raked Zen gardens, "
        "geisha districts, and tea houses. Cherry blossoms in spring and fiery maple leaves in "
        "autumn frame centuries-old shrines and quiet bamboo groves.",
    },
    {
        "name": "Reykjavík & the Golden Circle",
        "country": "Iceland",
        "region": "Capital Region",
        "best_season": "Summer for midnight sun, Winter for auroras",
        "tags": ["volcanoes", "geothermal", "northern lights", "waterfalls"],
        "description": "A rugged land of erupting geysers, thundering waterfalls, black-sand "
        "coasts, and steaming geothermal lagoons. In winter the northern lights ripple over "
        "lava fields; in summer the sun barely sets.",
    },
    {
        "name": "Santorini",
        "country": "Greece",
        "region": "Cyclades",
        "best_season": "Late Spring & Early Autumn",
        "tags": ["islands", "sunsets", "romance", "caldera"],
        "description": "Whitewashed cliff-top villages with blue-domed churches tumble toward a "
        "sapphire caldera. Famous for spectacular sunsets, volcanic beaches, and crisp Assyrtiko "
        "wine, it is a quintessential romantic island escape.",
    },
    {
        "name": "Serengeti National Park",
        "country": "Tanzania",
        "region": "East Africa",
        "best_season": "June to October (dry season)",
        "tags": ["safari", "wildlife", "migration", "savanna"],
        "description": "Endless golden savanna where millions of wildebeest and zebra thunder "
        "across the plains in the Great Migration, trailed by lions, cheetahs, and crocodiles. "
        "The ultimate big-game safari wilderness.",
    },
    {
        "name": "Banff & Lake Louise",
        "country": "Canada",
        "region": "Canadian Rockies",
        "best_season": "Summer for hiking, Winter for skiing",
        "tags": ["mountains", "lakes", "hiking", "skiing"],
        "description": "Turquoise glacial lakes mirror snow-capped peaks in this alpine national "
        "park. Hike larch valleys and glaciers in summer, then carve world-class powder slopes in "
        "winter, all amid grizzly-country wilderness.",
    },
    {
        "name": "Marrakech",
        "country": "Morocco",
        "region": "North Africa",
        "best_season": "Spring & Autumn",
        "tags": ["souks", "markets", "desert gateway", "culture"],
        "description": "A sensory whirl of labyrinthine souks, spice-scented medinas, and snake "
        "charmers in the Jemaa el-Fnaa square. Ornate riads and palaces give way to the Atlas "
        "Mountains and the gateway to the Sahara.",
    },
    {
        "name": "Bora Bora",
        "country": "French Polynesia",
        "region": "South Pacific",
        "best_season": "May to October (dry season)",
        "tags": ["overwater bungalows", "lagoon", "snorkeling", "luxury"],
        "description": "A turquoise lagoon ringed by coral reefs and a dramatic volcanic peak. "
        "Overwater bungalows perch above warm shallows teeming with rays and reef sharks — a "
        "secluded, luxurious tropical-island honeymoon idyll.",
    },
    {
        "name": "Machu Picchu",
        "country": "Peru",
        "region": "Andes",
        "best_season": "May to September (dry season)",
        "tags": ["ruins", "trekking", "history", "mountains"],
        "description": "A lost Inca citadel of terraced stone perched on a misty Andean ridge. "
        "Reached by the multi-day Inca Trail past cloud forests and ruins, it rewards trekkers "
        "with one of the world's most breathtaking archaeological vistas.",
    },
    {
        "name": "Venice",
        "country": "Italy",
        "region": "Veneto",
        "best_season": "Spring & Autumn",
        "tags": ["canals", "art", "romance", "history"],
        "description": "A dreamlike city built on water, where gondolas glide down canals beneath "
        "Gothic palaces and Byzantine basilicas. Labyrinthine alleys, masked carnivals, and "
        "Renaissance art make it endlessly romantic.",
    },
    {
        "name": "Queenstown",
        "country": "New Zealand",
        "region": "South Island",
        "best_season": "Year-round (adventure varies by season)",
        "tags": ["adventure", "bungee", "lakes", "mountains"],
        "description": "The adrenaline capital of the world, cradled between Lake Wakatipu and "
        "the jagged Remarkables. Bungee jumping, jet boating, skydiving, and skiing draw thrill "
        "seekers to its dramatic alpine playground.",
    },
    {
        "name": "Petra",
        "country": "Jordan",
        "region": "Middle East",
        "best_season": "Spring & Autumn",
        "tags": ["ruins", "desert", "history", "canyon"],
        "description": "A rose-red city carved into sandstone cliffs, hidden at the end of a "
        "narrow canyon. Ancient Nabataean tombs and temples glow at dawn in this archaeological "
        "wonder ringed by desert.",
    },
    {
        "name": "Maldives Atolls",
        "country": "Maldives",
        "region": "Indian Ocean",
        "best_season": "November to April (dry season)",
        "tags": ["beaches", "diving", "luxury", "coral"],
        "description": "Scattered coral atolls of powder-white sand and impossibly clear lagoons. "
        "World-class diving and snorkeling reveal manta rays and whale sharks, while private "
        "island resorts define barefoot tropical luxury.",
    },
    {
        "name": "Patagonia — Torres del Paine",
        "country": "Chile",
        "region": "Patagonia",
        "best_season": "November to March (Southern summer)",
        "tags": ["trekking", "glaciers", "wilderness", "mountains"],
        "description": "A remote wilderness of granite spires, electric-blue glaciers, and "
        "wind-scoured steppe roamed by guanacos and pumas. The legendary W and O treks pass "
        "turquoise lakes beneath the soaring Paine towers.",
    },
    {
        "name": "Dubrovnik",
        "country": "Croatia",
        "region": "Dalmatia",
        "best_season": "Late Spring & Early Autumn",
        "tags": ["walled city", "coast", "history", "adriatic"],
        "description": "A honey-stone medieval walled city jutting into the Adriatic, its marble "
        "streets and baroque churches encircled by mighty ramparts. Swim in hidden coves below "
        "the cliffs of this gleaming coastal fortress.",
    },
    {
        "name": "Cappadocia",
        "country": "Turkey",
        "region": "Central Anatolia",
        "best_season": "Spring & Autumn",
        "tags": ["hot air balloons", "caves", "rock formations", "history"],
        "description": "A surreal moonscape of fairy-chimney rock spires and cave dwellings carved "
        "over millennia. At dawn hundreds of hot-air balloons drift over the valleys and "
        "underground cities of this otherworldly region.",
    },
    {
        "name": "Kerala Backwaters",
        "country": "India",
        "region": "South India",
        "best_season": "September to March",
        "tags": ["backwaters", "houseboats", "tropical", "relaxation"],
        "description": "A tranquil web of palm-fringed lagoons and canals threaded by traditional "
        "houseboats. Glide past emerald paddy fields and fishing villages in this lush, languid "
        "tropical waterland.",
    },
    {
        "name": "Swiss Alps — Zermatt",
        "country": "Switzerland",
        "region": "Valais",
        "best_season": "Winter for skiing, Summer for hiking",
        "tags": ["skiing", "mountains", "matterhorn", "alpine"],
        "description": "A car-free alpine village beneath the iconic pyramid of the Matterhorn. "
        "Glacier skiing, cogwheel railways, and flower-strewn summer trails define this pristine, "
        "chocolate-box Swiss mountain retreat.",
    },
    {
        "name": "New York City",
        "country": "United States",
        "region": "Northeast",
        "best_season": "Spring & Autumn",
        "tags": ["city", "skyline", "culture", "nightlife"],
        "description": "A relentless, electric metropolis of soaring skyscrapers, Broadway "
        "theaters, world-class museums, and endless cuisine. From Central Park to neon-lit Times "
        "Square, it is the quintessential big-city energy trip.",
    },
    {
        "name": "Galápagos Islands",
        "country": "Ecuador",
        "region": "Pacific",
        "best_season": "Year-round",
        "tags": ["wildlife", "islands", "diving", "nature"],
        "description": "A living laboratory of evolution where giant tortoises, marine iguanas, "
        "and blue-footed boobies show no fear of humans. Volcanic islands and rich waters offer "
        "extraordinary wildlife encounters and diving.",
    },
    {
        "name": "Prague",
        "country": "Czech Republic",
        "region": "Bohemia",
        "best_season": "Spring & Autumn",
        "tags": ["old town", "castles", "history", "architecture"],
        "description": "A fairy-tale city of spires, a medieval astronomical clock, and a hilltop "
        "castle above the Vltava. Cobbled lanes, Gothic and baroque facades, and cozy beer halls "
        "make its old town enchanting.",
    },
]
