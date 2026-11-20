#!/usr/bin/env python3
"""Material-only costing with dated supplier evidence and explicit missing items."""

from collections import Counter
from datetime import date
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
import csv
import json
from pathlib import Path

D = lambda n: Decimal(str(n))
MONEY = Decimal(".01")


def amount(n):
    return float(D(n).quantize(MONEY, rounding=ROUND_HALF_UP))


def purchase_quantity(quantity, step):
    if D(step) <= 0:
        raise ValueError("Purchase increment must be positive")
    return (D(quantity) / D(step)).to_integral_value(rounding=ROUND_CEILING) * D(step)


def estimate(project, boards, catalog):
    config = project.get("pricing") or {}
    asof = date.fromisoformat(config.get("as_of_date", catalog["checked_on"]))
    counts = Counter(b["material"] for b in boards)
    rows = []
    issues = []
    products = catalog["products"]

    def add(label, qty, unit, pid=None, provisional=False, note=""):
        item = products.get(pid) if pid else None
        row = dict(
            label=label,
            quantity=qty,
            unit=unit,
            product_id=pid,
            provisional=provisional,
            note=note,
            total_eur=None,
            unit_price_eur=None,
        )
        if qty is None:
            row["note"] = (note + " Не е потвърдено количество.").strip()
        if not item:
            row["note"] = (row["note"] + " Няма избран проверен артикул.").strip()
        else:
            row.update(
                sku=item["sku"],
                source=item["url"],
                checked_on=item["checked_on"],
                supplier=item["supplier"],
            )
            age = (asof - date.fromisoformat(item["checked_on"])).days
            if age < 0 or age > config.get("max_price_age_days", 7):
                row["note"] += " Цената трябва да се обнови."
                row["stale"] = True
            if item.get("currency") != "EUR" or item.get("vat_included") is not True:
                row["note"] += " Непотвърдена валута или ДДС."
            else:
                row["unit_price_eur"] = item["price_eur"]
            if (
                item.get("currency") == "EUR"
                and item.get("vat_included") is True
                and qty is not None
            ):
                if qty < 0:
                    raise ValueError("Negative purchase quantity")
                q = D(qty)
                expected = item["unit"]
                if unit != expected:
                    raise ValueError(f"Unit mismatch for {pid}: {unit}/{expected}")
                buy = purchase_quantity(
                    q,
                    item.get(
                        "purchase_increment",
                        1 if unit in ("board", "piece", "pair", "pack") else 0.01,
                    ),
                )
                row["purchase_quantity"] = float(buy)
                row["unit_price_eur"] = item["price_eur"]
                row["total_eur"] = amount(buy * D(item["price_eur"]))
                if item.get("regular_price_eur") is not None:
                    row["regular_total_eur"] = amount(
                        buy * D(item["regular_price_eur"])
                    )
                    row["note"] += " Промоция; срокът не е потвърден."
        if provisional:
            row["note"] += " Примерен избор, не е потвърден от Стоян."
        if row["total_eur"] is None or row.get("stale") or provisional:
            issues.append(label)
        rows.append(row)

    for mid, m in project["materials"].items():
        selection = config.get("materials", {}).get(mid, {})
        if not m.get("stock"):
            area = (
                sum(
                    p["size_mm"][p["panel_axes"][0]] * p["size_mm"][p["panel_axes"][1]]
                    for p in project["parts"]
                    if p["material"] == mid
                )
                / 1e6
            )
            add(
                m["name"],
                None,
                "board",
                selection.get("product_id"),
                note=f"Нетна площ на детайлите {area:.3f} m²; липсва складов формат/разкрой.",
            )
            continue
        pid = selection.get("product_id")
        item = products.get(pid)
        if item and sorted(item.get("sheet_mm", [])) != sorted(
            [m["stock"]["x_mm"], m["stock"]["y_mm"]]
        ):
            raise ValueError(f"Price sheet format differs from nesting: {mid}")
        if item and item.get("thickness_mm") != m["thickness_mm"]:
            raise ValueError(f"Price thickness mismatch: {mid}")
        add(
            m["name"],
            counts[mid],
            "board",
            pid,
            not selection.get("confirmed", False),
            note="Покупка на цели плочи по разкроя; отпадъкът не се начислява втори път.",
        )
    edge_lengths = {}
    for p in project["parts"]:
        u, v = [p["size_mm"][i] for i in p["panel_axes"]]
        for edge, thickness in p["bands_mm"].items():
            if thickness:
                key = f'{p["material"]}:{thickness:g}'
                edge_lengths[key] = (
                    edge_lengths.get(key, D(0)) + D(v if edge[0] == "u" else u) / 1000
                )
    for key, length in edge_lengths.items():
        choice = config.get("edges", {}).get(key, {})
        extra = D(choice.get("waste_fraction", 0))
        if extra < 0 or extra > 1:
            raise ValueError("Edge waste_fraction must be between 0 and 1")
        material_id, thickness = key.split(":")
        add(
            "Кант "
            + project["materials"][material_id]["name"]
            + " "
            + thickness
            + " mm",
            float(length * (1 + extra)),
            "m",
            choice.get("product_id"),
            not choice.get("confirmed", False),
            note=f"Номинално {length} m; резерв {extra*100}%. Кантиране като услуга не е включено.",
        )
    for extra in config.get("hardware", []):
        add(
            extra["label"],
            extra.get("quantity"),
            extra.get("unit", "piece"),
            extra.get("product_id"),
            not extra.get("confirmed", False),
            extra.get("note", ""),
        )
    # Explicit scope completeness prevents a partial subtotal being presented as a final quote.
    if config.get("material_scope_complete") is not True:
        issues.append("Пълнотата на материалите и обкова не е потвърдена")
    total = sum(
        (D(row["total_eur"]) for row in rows if row["total_eur"] is not None), D(0)
    )
    regular = sum(
        (
            D(row.get("regular_total_eur", row["total_eur"]))
            for row in rows
            if row["total_eur"] is not None
        ),
        D(0),
    )
    return dict(
        scope="materials_only",
        currency="EUR",
        vat_basis="supplier_prices_including_vat",
        as_of_date=asof.isoformat(),
        status="incomplete" if issues else "estimated_materials",
        estimated_priced_subtotal_eur=amount(total),
        same_items_regular_price_subtotal_eur=amount(regular),
        materials_total_eur=None if issues else amount(total),
        labor_eur=None,
        profit_eur=None,
        client_total_eur=None,
        rows=rows,
        unresolved=issues,
        exclusions=[
            "Труд",
            "Проектиране",
            "Разкрой/кантиране като услуги",
            "Транспорт и доставка",
            "Монтаж",
            "Печалба и продажна цена",
        ],
        note="Това е оценка на остойностената част от материалите, не крайна цена на мебелта. Непопълнените позиции не са нула.",
    )


def write_estimate(project, boards, catalog, out):
    result = estimate(project, boards, catalog)
    (out / "materials-cost.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2)
    )
    columns = [
        "label",
        "quantity",
        "unit",
        "purchase_quantity",
        "unit_price_eur",
        "total_eur",
        "provisional",
        "sku",
        "supplier",
        "source",
        "checked_on",
        "note",
    ]
    with (out / "materials-cost.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(result["rows"])
    return result
