import os
import pandas as pd
from collections import defaultdict
from openpyxl import load_workbook

def mapper(orders, mapping):
    """
    orders  – list of dicts
    mapping – list of tuples (name, ids)

    works with:
      source_mapping:
        [('Allegro', ('allegro', 0)), ('Woocommerce', ('shop', 0)),
         ('Zamówienie promocyjne', ('personal', 61095)),
         ('Zamówienie B2B', ('personal', 61096))]

      id_mapping (statusy):
        [('Dostarczone', 221934), ('Wysłane', 221932), ('Do wysłania', 221931)]

      name_mapping (produkty):
        [('F_maly_pies', ('330762872', 79)), ('F_duzy_pies', ('330762892', 77)), ...]
    """

    if not mapping:
        return orders

    # check if all ids in mapping are tuples
    all_tuples = all(isinstance(ids, tuple) for _, ids in mapping)

    # STATUSES – mapping type: ('Dostarczone', 221934)
    if not all_tuples:
        status_dict = {status_id: name for name, status_id in mapping}
        for order in orders:
            status_id = order.get("order_status")
            order["order_status_name"] = status_dict.get(status_id, "ID not found")
        return orders

    #  mapping with tuples → can be source or products
    ids_flat = set()
    for _, ids in mapping:
        for v in ids:
            ids_flat.add(str(v))

    # check where these IDs appear in orders
    has_source_match = any(
        str(o.get("order_source")) in ids_flat or str(o.get("order_source_id")) in ids_flat
        for o in orders
    )

    has_product_match = any(
        ("products" in o and any(str(p.get("product_id")) in ids_flat for p in o["products"]))
        or ("product_id" in o and str(o.get("product_id")) in ids_flat)
        for o in orders
    )

    # SOURCES
    if has_source_match and not has_product_match:
        for order in orders:
            src = str(order.get("order_source"))
            src_id = order.get("order_source_id")

            label = "ID not found"

            for name, ids in mapping:
                id_src, id_num = ids  # can be ('allegro', 0) or ('personal', 61095)

                # if ID found, match it
                if id_num != 0:
                    if src_id == id_num:
                        label = name
                        break
                else:
                    # no ID -> match by source string
                    if src == str(id_src):
                        label = name
                        break

            order["order_source_name"] = label

        return orders

    # PRODUCTS
    if has_product_match:
        for order in orders:

            if "products" in order and isinstance(order["products"], list):
                for prod in order["products"]:
                    prod_id = str(prod.get("product_id"))
                    label = "ID not found"

                    for name, ids in mapping:
                        bl_id, woo_id = ids   # e.g. ('330762872', 79)
                        if prod_id == str(bl_id) or prod_id == str(woo_id):
                            label = name
                            break

                    prod["product_name"] = label

            # fallback: old model with a single product_id per order
            elif "product_id" in order:
                prod_id = str(order.get("product_id"))
                label = "ID not found"

                for name, ids in mapping:
                    bl_id, woo_id = ids
                    if prod_id == str(bl_id) or prod_id == str(woo_id):
                        label = name
                        break

                order["product_name"] = label

        return orders

    # if nothing recognized, do not change anything
    return orders

def aggregate_products(orders):
    """
    returns a nested dictionary:
    {
        order_source_name: {
            product_name: total_quantity
        }
    }
    """
    agg = defaultdict(lambda: defaultdict(int))

    for order in orders:
        source = order.get("order_source_name")

        for product in order.get("products"):
            name = product.get("product_name")
            qty = product.get("quantity", 1)

            agg[source][name] += qty

    return {src: dict(products) for src, products in agg.items()}



