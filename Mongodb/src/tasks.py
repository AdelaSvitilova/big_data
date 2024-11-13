import random
from datetime import datetime, timedelta
import pymongo


def top_5(collection):
    # Top 5 nejprodávanějších produktů na základě počtu prodaných kusů
    pipeline = [
        {"$group": {"_id":"$product_name", "total_sales":{"$sum":"$quantity"}}},
        {"$sort": {"total_sales": -1 }},
        {"$limit": 5}
    ]

    print("Top 5 nejprodávanějších produktů:")
    for result in collection.aggregate(pipeline):
        print(result)

def avg_price(collection):
    # Seskupní dat podle kategorie (category) a vypočet průměrné ceny produktů v každé kategorii
    pipeline = [
        {"$group": {"_id":"$category", "average_price":{"$avg":"$price"}}}
    ]

    print("Průměrná cena produktů v každé kategorii:")
    for result in collection.aggregate(pipeline):
        print(result)

def total_sales_in_time(collection):
    # Trend podle regionů: Prodeje v průběhu času
    # výběr dat za poslední rok
    # výpočet celkových prodejů(hodnot) v jednotlivých regionech po měsících
    start_date = datetime.now() - timedelta(days=365)
    pipeline = [
        {
            "$match": {
                "order_date": {"$gte": start_date}
            }
        },
        {
            "$group": {
                "_id": {
                    "region": "$customer_region",
                    "month": {"$dateToString": {"format": "%Y-%m", "date": "$order_date"}}
                },
                "total_sales": {
                    "$sum": {"$multiply": ["$price", "$quantity"]}
                }
            }
        },
        {
            "$sort": {
                "_id.region": 1,
                "_id.month": 1
            }
        }
    ]

    print("Prodeje v průběhu času:")
    for result in collection.aggregate(pipeline):
        print(result)

def highest_sales_in_month(collection):
    # Zjištění, ve kterém měsíci byl celkový objem prodejů (součet price krát quantity) nejvyšší
    pipeline = [
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m", "date": "$order_date"}},
                "total_sales": {"$sum": {"$multiply": ["$price", "$quantity"]}}
            }
        },
        { "$sort": { "total_sales": -1 } },
        { "$limit": 1 }
    ]

    print("Nejvyšší prodeje během roku:")
    for result in collection.aggregate(pipeline):
        print(result)

def total_sales_by_category_region(collection):
    # Seskupení dat podle kategorie a regionu zákazníka a vypočet celkového příjemu
    pipeline = [
        {"$group": {"_id": {"category": "$category", "region": "$customer_region"}, 
        "total_sales": {"$sum": {"$multiply": ["$price", "$quantity"]}}}}
    ]

    print("Celkový příjem za kategorii a region:")
    for result in collection.aggregate(pipeline):
        print(result)

def total_orders_by_customer(collection):
    # Spočítání, kolik objednávek vytvořil každý zákazník, a určení, kolik zákazníků vytvořilo více než 5 objednávek
    pipeline = [
        {"$group": {"_id": "$customer_id", "total_orders": {"$sum": 1}}},
        {"$match": {"total_orders": {"$gt": 5}}},
        {"$count": "customers_with_more_than_5_orders"}
    ]

    print("Počet zákazníků s více než 5 objednávkami:")
    for result in collection.aggregate(pipeline):
        print(result)

def return_analysis(collection):
    # Spojení s další kolekcí ($lookup): Analýza vratek
    # Propojení kolekcí orders s kolekcí returns pomocí $lookup, 
    # pro zjištění kolik procent objednávek bylo vráceno v jednotlivých kategoriích produktů
    pipeline = [
        {
            "$lookup": {
                "from": "returns",
                "localField": "order_id",
                "foreignField": "order_id",
                "as": "return_data"
            }
        },
        {
            "$group": {
                "_id": "$category",
                "total_orders": {"$sum": 1},
                "total_returns": {"$sum": {"$cond": [{"$gt": [{"$size": "$return_data"}, 0]}, 1, 0]}}
            }
        }, 
        {
            "$project": {
                "total_orders": 1,
                "total_returns": 1,
                "return_rate": {"$divide": ["$total_returns", "$total_orders"]}
            }
        }
    ]

    print("Analýza vratek:")
    for result in collection.aggregate(pipeline):
        print(result)

def  unwind(collection):
    # Rozbalení polí ($unwind): Práce s více položkami na objednávku
    # Použití $unwind k „rozbalení“ položek objednávky na jednotlivé dokumenty, a pak:
    # Seskupení podle product_name a spočítáí celkového početu prodaných kusů každého produktu
    # Identifikace produktů, které jsou nejčastěji součástí větších objednávek (například těch, které obsahují 3 a více položek)
    pipeline = [
        {"$unwind": "$items"},
        {"$group": {"_id": "$items.product_name", "total_quantity": {"$sum": "$items.quantity"}}}
    ]

    print("Celkový počet prodaných kusů produktů:")
    for result in collection.aggregate(pipeline):
        print(result)

    pipeline = [
        {
            "$match": {
                "$expr": {"$gte": [{"$size": "$items"}, 3]}
            }
        },
        {
            "$unwind": "$items"
        },
        {
            "$group": {
                "_id": "$items.product_name", 
                "total_quantity": {"$sum": "$items.quantity"}
            }
        },
        {
            "$sort": {"total_quantity": -1}
        },
        {
            "$limit": 3
        }
    ]

    print("Nejčastější položky ve velkých objednávkách:")
    for result in collection.aggregate(pipeline):
        print(result)

def bucketing(collection):
    # Hierarchické seskupování ($bucket nebo $bucketAuto): Cenové segmenty produktů
    # Vytvoření cenových segmentů pro produkty pomocí $bucket nebo $bucketAuto. Například:
    # Segment „Nízká cena“ pro produkty do 500 Kč
    # Segment „Střední cena“ pro produkty mezi 500 a 10000 Kč
    # Segment „Vysoká cena“ pro produkty nad 1000 Kč
    # Určení početu produktů v každém segmentu a zjistění, která cenová skupina se prodává nejvíce v jednotlivých regionech

    # bucket si vytvoří bucket 0-500, 500-1000, 1000-inf a do každého bucketu přiřadí počet produktů a všechny regiony, jejich cena spadá do kategorie
    pipeline = [
        {
            "$bucket": {
                "groupBy": "$price",  # Hlavní seskupení podle ceny
                "boundaries": [0, 500, 1000, float('inf')],
                "default": "Unknown",
                "output": {
                    "count": { "$sum": 1 },
                    "regions": {
                        "$push": {
                            "region": "$customer_region"
                        }
                    }
                }
            }
        },
        {
            "$unwind": "$regions"
        },
        {
            "$group": {
                "_id": {
                    "region": "$regions.region",
                    "price_bucket": "$_id"
                },
                "count": { "$sum": 1 }
            }
        },
        {
            "$sort": {
                "_id.region": 1,
                "_id.price_bucket": 1,
            }
        },
        # {
        #     "$project": {
        #         "_id": 0,
        #         "region": "$_id.region",
        #         "price_bucket": "$_id.price_bucket",
        #         "count": 1
        #     }
        # }
    ]

    print("Cenové segmenty produktů:")
    for result in collection.aggregate(pipeline):
        print(result)

def return_reason_analysis(collection):
    # Analýza důvodů vratek
    # Vytvoření textového indexu na pole reason v kolekci returns pro textové vyhledávání -> provedeno v generate_data.py
    # Vyhledejte všechny záznamy, kde důvod vrácení obsahuje klíčové slovo „poškozené“ nebo „neodpovídá“
    # Spočítání, jak často se tyto důvody vracení objevují a identifikace regionu s nejvyšším počtem takto označených vratek
    pipeline = [
        # Můžu použít toto, nebo je to neefektivní?
        # { 
        #     "$match": {
        #         "reason": {"$in": ["Defective", "Not as described"]}
        #     }
        # },
        {
            "$match": {
                "$text": { "$search": "defective described" }
            }
        },
        {
            "$lookup": {
                "from": "orders",
                "localField": "order_id",
                "foreignField": "order_id",
                "as": "order_data"
            }
        },
        {
            "$group": { 
                "_id": {
                    "reason": "$reason",
                    "region": "$order_data.customer_region"
                },
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {
                "_id.reason": -1,
                "count": -1
            }
        },
        {
            "$group": {
                "_id": "$_id.reason",
                "region_with_max_returns": { "$first": "$_id.region" },
                "max_count": { "$first": "$count" }
            }
        }
    ]

    print("Důvody vratek:")
    for result in collection.aggregate(pipeline):
        print(result)

def season_sales(collection):
    # Prodeje v sezónních obdobích
    # Vytvoření agregace, která sleduje počet prodejů pro každé roční období (jaro, léto, podzim, zima) na základě data objednávky
    # Extrakce měsíce pomocí $dateToString z order_date a přiřazení k příslušnému období
    # Vyhodnocení, které produkty nebo kategorie mají sezónní výkyvy a v kterém období se prodávají nejvíce
    pipeline = [
        {
            "$addFields": {
                "season": {
                    "$switch": {
                        "branches": [
                            {"case": {"$in": [{"$month": "$order_date"}, [3, 4, 5]]}, "then": "Spring"},
                            {"case": {"$in": [{"$month": "$order_date"}, [6, 7, 8]]}, "then": "Summer"},
                            {"case": {"$in": [{"$month": "$order_date"}, [9, 10, 11]]}, "then": "Autumn"},
                            {"case": {"$in": [{"$month": "$order_date"}, [12, 1, 2]]}, "then": "Winter"}
                        ],
                        "default": "Unknown"
                    }
                }
            }
        },
        {
            "$addFields": {
                "season_order": {
                    "$switch": {
                        "branches": [
                            {"case": {"$eq": ["$season", "Spring"]}, "then": 1},
                            {"case": {"$eq": ["$season", "Summer"]}, "then": 2},
                            {"case": {"$eq": ["$season", "Autumn"]}, "then": 3},
                            {"case": {"$eq": ["$season", "Winter"]}, "then": 4}
                        ],
                        "default": 0
                    }
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "season": "$season",
                    "category": "$category",
                    "season_order": "$season_order"
                },
                "sales_count": {
                    "$sum": 1
                }
            }
        },

        # Nejvíc prodávané produkty v jednotlivých obdobích
        # {
        #     "$sort": {
        #         "_id.category": 1,
        #         "sales_count": -1
        #     }
        # },
        # {
        #     "$group": {
        #         "_id": "$_id.category",
        #         "max_sales": {
        #             "$first": "$sales_count"
        #         },
        #         "season": {
        #             "$first": "$_id.season"
        #         }
        #     }
        # }

        # Výkyvy v prodejích
        {
            "$setWindowFields": {
                "partitionBy": "$_id.category",  # Rozdělení podle kategorie
                "sortBy": { "_id.season_order": 1 },
                "output": {
                    "prev_sales_count": { "$shift": { "output": "$sales_count", "by": -1 } }  # Posun o -1 pro předchozí sezónu
                }
            }
        },   
        {
            "$set": {
                "sales_diff": { "$subtract": ["$sales_count", "$prev_sales_count"] }  # Výpočet rozdílu
            }
        },   
        {
            "$match": {
                "$expr": {"$gt": [{"$abs": "$sales_diff"}, 40]} # Rozdíl v prodejích o více než 40
            }
        },
        {
            "$group": {
                "_id": "$_id.category"
            }
        }     
    ]

    print("Nejvíc prodávané kategorie produktů v obdobích/kategorie produktů se sezoním výkyvem:")
    for result in collection.aggregate(pipeline):
        print(result)

def price_margin(collection):
    # Výpočet marže
    # Výpočet marže pomocí $addFields jako price - cost_price a označrní produktů, které mají marži nižší než průměrná marže pro danou kategorii
    # Filtrace produktů pomocí $expr s nízkou marží a určení, které kategorie obsahují nejvíce těchto produktů
    
    # tady počítám jednu společnou průměrnou marži a ne pro každou kategorii zvlášť
    pipeline = [
        {
            "$addFields": {
                "margin": {"$subtract": ["$price", "$cost_price"]}
            }
        },
        {
            "$lookup": {
                "from": "orders",
                "pipeline": [
                    {
                        "$addFields": {
                            "margin": { "$subtract": ["$price", "$cost_price"] }
                        }
                    },
                    {
                        "$group": {
                            "_id": None,
                            "avg_margin": {"$avg": "$margin"}
                        }
                    }
                ],
                "as": "avg_margin"
            }
        },
        {
            "$unwind": "$avg_margin"
        },
        # {
        #     "$group": {
        #         "_id": None,
        #         "avg_margin": {"$avg": "$margin"}
        #     }
        # },
        {
            "$match": {
                "$expr": {"$lt": ["$margin", "$avg_margin.avg_margin"]}
            }
        },
        {
            "$group": {
                "_id": "$category",
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"count": -1}
        },
        {
            "$limit": 1
        }
    ]

    # tady už počítám průměrnou marži pro každou kategorii zvlášť
    pipeline = [
        {
            "$addFields": {
                "margin": {"$subtract": ["$price", "$cost_price"]}
            }
        },
        {
            "$lookup": {
                "from": "orders",
                "let": {"category": "$category"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {"$eq": ["$category", "$$category"]}
                        }
                    },
                    {
                        "$group": {
                            "_id": "$category",
                            "avg_margin": {"$avg": { "$subtract": ["$price", "$cost_price"] }}
                        }
                    }
                ],
                "as": "avg_margin"
            }
        },
        {
            "$unwind": "$avg_margin"
        },
        {
            "$match": {
                "$expr": {"$lt": ["$margin", "$avg_margin.avg_margin"]}
            }
        },
        {
            "$group": {
                "_id": "$category",
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"count": -1}
        }
    ]

    print("Kategorie s nejnižší marží:")
    for result in collection.aggregate(pipeline):
        print(result)

def price_margin_with_second_collection(collection):
    # Výpočet marže
    # Výpočet marže pomocí $addFields jako price - cost_price a označrní produktů, které mají marži nižší než průměrná marže pro danou kategorii
    # Filtrace produktů pomocí $expr s nízkou marží a určení, které kategorie obsahují nejvíce těchto produktů
    # Pipeline pro výpočet průměrné marže podle kategorie

    # Vytvoření pomocné kolekce s průměrnými maržemi pro každou kategorii
    pipeline = [
        {
            "$group": {
                "_id": "$category",
                "avg_margin": {"$avg": {"$subtract": ["$price", "$cost_price"]}}
            }
        },
        {
            "$out": "avg_margins"  # Název nové kolekce
        }
    ]

    # Spuštění pipeline a vytvoření nové kolekce
    collection.aggregate(pipeline)
    
    pipeline = [
        {
            "$addFields": {
                "margin": {"$subtract": ["$price", "$cost_price"]}
            }
        },
        {
            "$lookup": {
                "from": "avg_margins",  # pomocná kolekce s předpočítanými průměrnými maržemi
                "localField": "category",
                "foreignField": "_id",
                "as": "avg_margin"
            }
        },
        {
            "$unwind": "$avg_margin"
        },
        {
            "$match": {
                "$expr": {"$lt": ["$margin", "$avg_margin.avg_margin"]}
            }
        },
        {
            "$group": {
                "_id": "$category",
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"count": -1}
        }
    ]

    print("Kategorie s nejnižší marží:")
    for result in collection.aggregate(pipeline):
        print(result)

    # Smazání pomocné kolekce
    db["avg_margins"].drop()


if __name__ == "__main__":
    # Připojení k MongoDB
    # client = pymongo.MongoClient("mongodb://localhost:27017/")
    client = pymongo.MongoClient("mongodb://mongodb:27017/")
    db = client["ecommerce"]
    orders_collection = db["orders"]
    returns_collection = db["returns"]

    # Spuštění jednotlivých analýz
    top_5(orders_collection)
    avg_price(orders_collection)
    total_sales_in_time(orders_collection)
    highest_sales_in_month(orders_collection)
    total_sales_by_category_region(orders_collection)
    total_orders_by_customer(orders_collection)
    return_analysis(orders_collection)
    unwind(orders_collection)
    bucketing(orders_collection)
    return_reason_analysis(returns_collection) 
    season_sales(orders_collection) 
    # price_margin(orders_collection)  # Pozor trvá dlouho
    price_margin_with_second_collection(orders_collection)

    # Uzavření připojení
    client.close()
