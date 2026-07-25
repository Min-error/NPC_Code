from __future__ import annotations

import csv
from pathlib import Path


ERROR_PAIRS = {
    "R0": ("L0->L1", "L1->L0"),
    "R1": ("L1->L2", "L2->L1"),
    "R2": ("L2->L3", "L3->L2"),
    "R3": ("L3->L4", "L4->L3"),
    "R4": ("L4->L5", "L5->L4"),
    "R5": ("L5->L6", "L6->L5"),
    "R6": ("L6->L7", "L7->L6"),
}
PAGE_SIZES = {"3DV7": 18432, "X3_9070": 18368}


def main() -> None:
    input_path = Path(__file__).with_name("sample_wl_errors.csv")
    with input_path.open(newline="", encoding="utf-8") as source:
        row = next(csv.DictReader(source))

    boundary_errors = {
        boundary: int(row[left]) + int(row[right])
        for boundary, (left, right) in ERROR_PAIRS.items()
    }
    page_errors = {
        "LSB": boundary_errors["R0"] + boundary_errors["R4"],
        "CSB": (
            boundary_errors["R1"]
            + boundary_errors["R3"]
            + boundary_errors["R5"]
        ),
        "MSB": boundary_errors["R2"] + boundary_errors["R6"],
    }
    total_error = sum(boundary_errors.values())

    print("Boundary errors:", boundary_errors)
    print("Page errors:", page_errors)
    print("WL total error:", total_error)
    for chip, page_size in PAGE_SIZES.items():
        print(f"{chip} WL RBER: {total_error / (page_size * 8):.12f}")


if __name__ == "__main__":
    main()
