from collections import defaultdict
import json
from fetch_orders import fetch_orders,  save_orders_to_file
from utils import mapper, aggregate_products
import datetime
import os
from dotenv import load_dotenv


if __name__ == "__main__":
    load_dotenv()
    token = os.environ["BASELINKER_TOKEN"]
    date_input = input("Enter date (YYYY-MM-DD): ").strip()
    orders_response = fetch_orders(date_str=date_input, token=token)

    # save raw data to file
    date_str = datetime.datetime.now().strftime("%Y_%m_%d__%H-%M-%S")
    filename = f"{date_str}_orders.json"
    response_dir = "responses"
    response_raw_dir = f"{response_dir}/raw"
    response_clean_dir = f"{response_dir}/clean"
    os.makedirs(response_raw_dir, exist_ok=True)
    os.makedirs(response_clean_dir, exist_ok=True)

    path = os.path.join(response_raw_dir, filename)
    save_orders_to_file(orders_response, path)

    clean = []
    # traverse JSON and save needed data from response
    # products need to be saved as whole list, becuase each individual is needed later
    for item in orders_response["orders"]:
        products = []

        for p in item["products"]:
            products.append({
                "product_id": str(p["product_id"]),
                "name": p.get("name"),
                "quantity": p.get("quantity"),
            })

        clean.append({
            "order_id": item["order_id"],
            "order_source": item["order_source"],
            "order_source_id": item["order_source_id"],
            "order_status": item["order_status_id"],
            "products": products
        })


    print(json.dumps(clean, indent=4, ensure_ascii=False))

    # mapping correct values
    # there are different names for the same product in Base, so we eed to map them crrectly
    # same goes for statuses and sources
    source_names = ['Allegro', 'Woocommerce', 'Zamówienie promocyjne', 'Zamówienie B2B']
    source_ids = ['allegro', 'shop', 'personal', 'personal']
    source_numeric = [0, 0, 61095, 61096]
    source_mapping = list(zip(source_names, zip(source_ids, source_numeric)))

    product_names = ['F_maly_pies', 'F_duzy_pies', 'F_kot', 'maly_pies', 'kot', 'duzy_pies']
    baselinker_ids = ['330762872', '330762892', '330762910', '330762926', '330762937', '330762947']
    woo_ids = [79, 77, 78, 82, 81, 80]
    name_mapping = list(zip(product_names, zip(baselinker_ids, woo_ids)))

    status_names = ['Dostarczone', 'Wysłane', 'Do wysłania']
    status_ids = [221934, 221932, 221931]
    id_mapping = list(zip(status_names, status_ids))

    # add to clean
    clean = mapper(clean, source_mapping)
    clean = mapper(clean, id_mapping)
    clean = mapper(clean, name_mapping)

    save_orders_to_file(clean, os.path.join(response_clean_dir, f"clean_{filename}"))

    # aggregate products to their respective source category and print results
    aggregated = aggregate_products(clean)
    promo_counts, other_counts = defaultdict(int), defaultdict(int)
    promo_source = "Zamówienie promocyjne"

    for source, products in aggregated.items():
        for product_name, qty in products.items():
            if source == promo_source:
                promo_counts[product_name] += qty
            else:
                other_counts[product_name] += qty

    print("Promotional orders product counts:")
    print(dict(promo_counts))
    print("Other orders product counts:")
    print(dict(other_counts))


