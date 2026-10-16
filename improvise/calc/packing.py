"""Packing line sizing for snacks and other loose products (multihead weigher + VFFS)."""

from __future__ import annotations

import math

from ..tools import tool


@tool
def snack_packing_capacity(product_kg_per_h: float, bag_weight_g: float, bulk_density_g_per_L: float = 0,
                           weigher_max_wpm: float = 0, vffs_max_bpm: float = 0, packing_efficiency: float = 0.85,
                           fill_ratio: float = 0.6) -> dict:
    """Bags per minute, number of weighers / VFFS baggers and bag volume for a snack packing line.

    Args:
        product_kg_per_h: product reaching packing in kg/h (after seasoning/cooling)
        bag_weight_g: net weight per bag in g
        bulk_density_g_per_L: product bulk density (e.g. extruded corn snack ~70 g/L); 0 = skip bag volume
        weigher_max_wpm: rated weighings per minute of one multihead weigher for THIS product (supplier); 0 = skip
        vffs_max_bpm: rated bags per minute of one VFFS for this bag size and film (supplier); 0 = skip
        packing_efficiency: share of time the packing line really runs (stops, film changes), default 0.85
        fill_ratio: product volume / inner bag volume for snacks (headspace for N2 and cushioning), default 0.6
    """
    if product_kg_per_h <= 0 or bag_weight_g <= 0:
        raise ValueError("product_kg_per_h and bag_weight_g must be > 0")
    bpm = product_kg_per_h * 1000 / bag_weight_g / 60
    design_bpm = bpm / packing_efficiency
    res = {"bags_per_min": round(bpm, 1), "bags_per_hour": round(bpm * 60), "design_bags_per_min": round(design_bpm, 1)}
    if weigher_max_wpm:
        res["multihead_weighers"] = math.ceil(design_bpm / weigher_max_wpm)
    if vffs_max_bpm:
        n = math.ceil(design_bpm / vffs_max_bpm)
        res["vffs_baggers"] = n
        res["vffs_speed_each_bpm"] = round(design_bpm / n, 1)
        res["vffs_utilisation"] = round(design_bpm / (n * vffs_max_bpm), 2)
    if bulk_density_g_per_L:
        prod_L = bag_weight_g / bulk_density_g_per_L
        res["product_volume_per_bag_L"] = round(prod_L, 2)
        res["inner_bag_volume_L"] = round(prod_L / fill_ratio, 2)
        res["surge_bin_L_per_minute_of_buffer"] = round(product_kg_per_h * 1000 / 60 / bulk_density_g_per_L, 1)
    res["next_step"] = ("Ask the weigher/VFFS supplier for rated speeds for this product, bag size and film if not "
                        "given; bag width/length from inner_bag_volume_L with the supplier's bag-size chart.")
    return res
