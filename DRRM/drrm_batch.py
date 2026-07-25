from __future__ import annotations

import argparse
import csv
import math
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from statistics import mean


SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = SCRIPT_DIR.parent
OUT_ROOT = SCRIPT_DIR / "results"

VOLTAGE_COLS = [f"R{i}" for i in range(7)]
RETENTION_SUFFIX = {1: "1m", 3: "3m", 6: "6m", 12: "12m"}
RETENTION_HOURS = {
    1: 30 * 24,
    3: 3 * 30 * 24,
    6: 6 * 30 * 24,
    12: 12 * 30 * 24,
}
OVD_RETENTION_MONTHS = 1

ERROR_PAIRS = {
    "R0": ("L0->L1", "L1->L0"),
    "R1": ("L1->L2", "L2->L1"),
    "R2": ("L2->L3", "L3->L2"),
    "R3": ("L3->L4", "L4->L3"),
    "R4": ("L4->L5", "L5->L4"),
    "R5": ("L5->L6", "L6->L5"),
    "R6": ("L6->L7", "L7->L6"),
}

AVERAGED_FIELDS = (
    ["wl", "block_count"]
    + [f"{col}_pred" for col in VOLTAGE_COLS]
    + [f"{col}_int" for col in VOLTAGE_COLS]
    + [f"avg_{col}_error" for col in VOLTAGE_COLS]
    + [
        "avg_LSB_error",
        "avg_CSB_error",
        "avg_MSB_error",
        "avg_WL_total_error",
        "avg_WL_RBER",
    ]
)


@dataclass(frozen=True)
class DatasetConfig:
    name: str
    best_offset_root: Path
    wl_error_root: Path
    pe_blocks: dict[int, tuple[int, int]]
    page_size: int
    expected_wl_count: int
    bits_per_cell: int = 8

    @property
    def rber_denominator(self) -> int:
        return self.page_size * self.bits_per_cell


@dataclass(frozen=True)
class Job:
    sweep: str
    dataset: DatasetConfig
    pe: int
    target_retention_months: int
    source_retention_months: int

    @property
    def condition_label(self) -> str:
        return f"PE{self.pe}_{RETENTION_SUFFIX[self.target_retention_months]}"

    @property
    def compute_key(self) -> tuple[str, int, int, int]:
        return (
            self.dataset.name,
            self.pe,
            self.target_retention_months,
            self.source_retention_months,
        )

    @property
    def output_path(self) -> Path:
        return (
            OUT_ROOT
            / self.sweep
            / self.dataset.name
            / self.condition_label
            / f"{self.dataset.name}_{self.condition_label}_block_average_by_wl.csv"
        )


DATASETS = (
    DatasetConfig(
        name="3DV7",
        best_offset_root=WORKSPACE / "3DV7_best_vth_offset_and_error",
        wl_error_root=WORKSPACE / "3DV7",
        pe_blocks={
            3000: (75, 76),
            4000: (78, 82),
            5000: (77, 79),
            6000: (86, 87),
        },
        page_size=18432,
        expected_wl_count=1408,
    ),
    DatasetConfig(
        name="X3_9070",
        best_offset_root=WORKSPACE / "X3_9070_best_vth_offset_and_error",
        wl_error_root=WORKSPACE / "X3_9070",
        pe_blocks={
            3000: (725, 729),
            4000: (732, 733),
            5000: (741, 745),
            6000: (748, 749),
        },
        page_size=18368,
        expected_wl_count=1392,
    ),
)


_BEST_OFFSET_CACHE: dict[tuple[str, int, int], list[dict[str, int | float]]] = {}
_CONDITION_MEAN_CACHE: dict[tuple[str, int, int], dict[str, float]] = {}
_OVD_CACHE: dict[tuple[str, int], dict[int, dict[str, float]]] = {}


def round_half_away_from_zero(value: float) -> int:
    sign = 1 if value >= 0 else -1
    return sign * int(math.floor(abs(value) + 0.5))


def read_best_offset_rows(
    dataset: DatasetConfig, block: int, retention_months: int
) -> list[dict[str, int | float]]:
    cache_key = (dataset.name, block, retention_months)
    cached = _BEST_OFFSET_CACHE.get(cache_key)
    if cached is not None:
        return cached

    path = (
        dataset.best_offset_root
        / f"{block}_{RETENTION_SUFFIX[retention_months]}"
        / "best_vth_offset.csv"
    )
    if not path.is_file():
        raise FileNotFoundError(path)

    rows: list[dict[str, int | float]] = []
    with path.open(newline="") as source:
        reader = csv.DictReader(source)
        for source_row in reader:
            row: dict[str, int | float] = {"wl": int(source_row[""])}
            for col in VOLTAGE_COLS:
                row[col] = float(source_row[col])
            rows.append(row)

    if len(rows) != dataset.expected_wl_count:
        raise ValueError(
            f"{path} has {len(rows)} WL rows; expected {dataset.expected_wl_count}"
        )

    _BEST_OFFSET_CACHE[cache_key] = rows
    return rows


def condition_mean(
    dataset: DatasetConfig, pe: int, retention_months: int
) -> dict[str, float]:
    cache_key = (dataset.name, pe, retention_months)
    cached = _CONDITION_MEAN_CACHE.get(cache_key)
    if cached is not None:
        return cached

    values = {col: [] for col in VOLTAGE_COLS}
    for block in dataset.pe_blocks[pe]:
        for row in read_best_offset_rows(dataset, block, retention_months):
            for col in VOLTAGE_COLS:
                values[col].append(float(row[col]))

    result = {col: mean(values[col]) for col in VOLTAGE_COLS}
    _CONDITION_MEAN_CACHE[cache_key] = result
    return result


def compute_base_voltage(
    dataset: DatasetConfig,
    pe: int,
    source_retention_months: int,
    target_retention_months: int,
) -> dict[str, float]:
    source_mean = condition_mean(dataset, pe, source_retention_months)
    log_source = math.log10(RETENTION_HOURS[source_retention_months])
    log_target = math.log10(RETENTION_HOURS[target_retention_months])
    base: dict[str, float] = {}
    for col in VOLTAGE_COLS:
        slope = source_mean[col] / log_source
        base[col] = slope * log_target
    return base


def compute_ovd(dataset: DatasetConfig, pe: int) -> dict[int, dict[str, float]]:
    cache_key = (dataset.name, pe)
    cached = _OVD_CACHE.get(cache_key)
    if cached is not None:
        return cached

    global_mean = condition_mean(dataset, pe, OVD_RETENTION_MONTHS)
    by_wl: dict[int, dict[str, list[float]]] = {}
    for block in dataset.pe_blocks[pe]:
        for row in read_best_offset_rows(dataset, block, OVD_RETENTION_MONTHS):
            wl = int(row["wl"])
            wl_values = by_wl.setdefault(wl, {col: [] for col in VOLTAGE_COLS})
            for col in VOLTAGE_COLS:
                wl_values[col].append(float(row[col]) - global_mean[col])

    if len(by_wl) != dataset.expected_wl_count:
        raise ValueError(
            f"{dataset.name} PE{pe} OVD has {len(by_wl)} WLs; "
            f"expected {dataset.expected_wl_count}"
        )

    result = {
        wl: {col: mean(values[col]) for col in VOLTAGE_COLS}
        for wl, values in sorted(by_wl.items())
    }
    _OVD_CACHE[cache_key] = result
    return result


def build_voltage_rows(
    dataset: DatasetConfig,
    pe: int,
    source_retention_months: int,
    target_retention_months: int,
) -> list[dict[str, int | float]]:
    base = compute_base_voltage(
        dataset,
        pe,
        source_retention_months,
        target_retention_months,
    )
    ovd_by_wl = compute_ovd(dataset, pe)

    rows: list[dict[str, int | float]] = []
    for wl, ovd in sorted(ovd_by_wl.items()):
        row: dict[str, int | float] = {"wl": wl}
        for col in VOLTAGE_COLS:
            value = base[col] + ovd[col]
            row[f"{col}_pred"] = value
            row[f"{col}_int"] = round_half_away_from_zero(value)
        rows.append(row)
    return rows


def read_errors_at_selected_voltages(
    dataset: DatasetConfig,
    block: int,
    retention_months: int,
    voltage_row: dict[str, int | float],
) -> dict[str, int]:
    wl = int(voltage_row["wl"])
    path = (
        dataset.wl_error_root
        / f"{block}_{RETENTION_SUFFIX[retention_months]}"
        / f"WL{wl}.csv"
    )
    if not path.is_file():
        raise FileNotFoundError(path)

    voltage_to_cols: dict[int, list[str]] = {}
    for col in VOLTAGE_COLS:
        voltage = int(voltage_row[f"{col}_int"])
        voltage_to_cols.setdefault(voltage, []).append(col)

    found: dict[str, int] = {}
    with path.open(newline="") as source:
        reader = csv.reader(source)
        header = next(reader)
        indexes = {name: index for index, name in enumerate(header)}
        for required_col in {name for pair in ERROR_PAIRS.values() for name in pair}:
            if required_col not in indexes:
                raise ValueError(f"{path} is missing column {required_col}")

        for source_row in reader:
            voltage = int(source_row[0])
            cols = voltage_to_cols.get(voltage)
            if cols is None:
                continue
            for col in cols:
                left_col, right_col = ERROR_PAIRS[col]
                found[col] = (
                    int(source_row[indexes[left_col]])
                    + int(source_row[indexes[right_col]])
                )
            if len(found) == len(VOLTAGE_COLS):
                break

    missing = [col for col in VOLTAGE_COLS if col not in found]
    if missing:
        requested = ", ".join(
            f"{col}={int(voltage_row[f'{col}_int'])}" for col in missing
        )
        raise ValueError(f"{path} lacks requested voltage rows: {requested}")
    return found


def compute_block_row(
    dataset: DatasetConfig,
    block: int,
    retention_months: int,
    voltage_row: dict[str, int | float],
) -> dict[str, int | float]:
    errors = read_errors_at_selected_voltages(
        dataset,
        block,
        retention_months,
        voltage_row,
    )
    total_error = sum(errors.values())
    return {
        "wl": int(voltage_row["wl"]),
        **{f"{col}_error": errors[col] for col in VOLTAGE_COLS},
        "LSB_error": errors["R0"] + errors["R4"],
        "CSB_error": errors["R1"] + errors["R3"] + errors["R5"],
        "MSB_error": errors["R2"] + errors["R6"],
        "WL_total_error": total_error,
        "WL_RBER": total_error / dataset.rber_denominator,
    }


def compute_averaged_rows(job: Job, workers: int) -> list[dict[str, int | float]]:
    voltage_rows = build_voltage_rows(
        job.dataset,
        job.pe,
        job.source_retention_months,
        job.target_retention_months,
    )
    sums_by_wl = {
        int(row["wl"]): {
            **{f"{col}_error": 0.0 for col in VOLTAGE_COLS},
            "LSB_error": 0.0,
            "CSB_error": 0.0,
            "MSB_error": 0.0,
            "WL_total_error": 0.0,
            "WL_RBER": 0.0,
        }
        for row in voltage_rows
    }

    with ThreadPoolExecutor(max_workers=workers) as executor:
        for block in job.dataset.pe_blocks[job.pe]:
            rows = executor.map(
                lambda voltage_row: compute_block_row(
                    job.dataset,
                    block,
                    job.target_retention_months,
                    voltage_row,
                ),
                voltage_rows,
            )
            for row in rows:
                wl = int(row["wl"])
                for field in sums_by_wl[wl]:
                    sums_by_wl[wl][field] += float(row[field])

    block_count = len(job.dataset.pe_blocks[job.pe])
    averaged_rows: list[dict[str, int | float]] = []
    for voltage_row in voltage_rows:
        wl = int(voltage_row["wl"])
        sums = sums_by_wl[wl]
        out: dict[str, int | float] = {"wl": wl, "block_count": block_count}
        for col in VOLTAGE_COLS:
            out[f"{col}_pred"] = float(voltage_row[f"{col}_pred"])
            out[f"{col}_int"] = int(voltage_row[f"{col}_int"])
            out[f"avg_{col}_error"] = sums[f"{col}_error"] / block_count
        out["avg_LSB_error"] = sums["LSB_error"] / block_count
        out["avg_CSB_error"] = sums["CSB_error"] / block_count
        out["avg_MSB_error"] = sums["MSB_error"] / block_count
        out["avg_WL_total_error"] = sums["WL_total_error"] / block_count
        out["avg_WL_RBER"] = sums["WL_RBER"] / block_count
        averaged_rows.append(out)
    return averaged_rows


def write_result(path: Path, rows: list[dict[str, int | float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=AVERAGED_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def build_jobs() -> list[Job]:
    jobs: list[Job] = []
    for dataset in DATASETS:
        for target_retention in (1, 3, 6, 12):
            source_retention = 6 if target_retention == 12 else 12
            jobs.append(
                Job(
                    sweep="retention_sweep_pe3000",
                    dataset=dataset,
                    pe=3000,
                    target_retention_months=target_retention,
                    source_retention_months=source_retention,
                )
            )
        for pe in (3000, 4000, 5000, 6000):
            jobs.append(
                Job(
                    sweep="pe_sweep_3month",
                    dataset=dataset,
                    pe=pe,
                    target_retention_months=3,
                    source_retention_months=12,
                )
            )
    return jobs


def parse_args() -> argparse.Namespace:
    default_workers = min(8, max(1, os.cpu_count() or 1))
    parser = argparse.ArgumentParser(
        description=(
            "Generate only block-average-by-WL DRRM result CSVs for the "
            "PE3000 retention sweep and the 3-month P/E sweep."
        )
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=default_workers,
        help=f"parallel WL readers (default: {default_workers})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.workers < 1:
        raise ValueError("--workers must be at least 1")

    jobs = build_jobs()
    result_cache: dict[
        tuple[str, int, int, int], list[dict[str, int | float]]
    ] = {}

    print(f"Output root: {OUT_ROOT}")
    print(f"Workers: {args.workers}")
    for index, job in enumerate(jobs, start=1):
        rows = result_cache.get(job.compute_key)
        cache_note = "reused" if rows is not None else "computed"
        if rows is None:
            print(
                f"[{index:02d}/{len(jobs)}] Computing {job.dataset.name} "
                f"{job.condition_label} from "
                f"{RETENTION_SUFFIX[job.source_retention_months]}..."
            )
            rows = compute_averaged_rows(job, args.workers)
            result_cache[job.compute_key] = rows
        write_result(job.output_path, rows)
        print(
            f"[{index:02d}/{len(jobs)}] Wrote {job.output_path} "
            f"({len(rows)} WLs, {cache_note})"
        )

    print(
        f"Done: {len(jobs)} CSV files, "
        f"{len(result_cache)} unique conditions computed."
    )


if __name__ == "__main__":
    main()
