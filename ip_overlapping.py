from dataclasses import dataclass
from typing import List, Tuple, Optional
from rich.console import Console
from rich.table import Table
import pandas as pd

console = Console()


@dataclass
class CidrRange:
    cidr: str
    start: int
    end: int


class CIDRUtils:
    """
    CIDR/IP utilities supporting:
    - requested_cidr vs available_cidr
    - requested_cidr vs list of available_cidrs
    - overlap check inside available list (two-pointer)
    """

    # -------------------------------
    # IP <-> INT conversions
    # -------------------------------
    @staticmethod
    def ip_to_int(ip: str) -> int:
        parts = list(map(int, ip.split(".")))
        return (parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]

    @staticmethod
    def int_to_ip(value: int) -> str:
        return f"{(value >> 24) & 0xFF}.{(value >> 16) & 0xFF}.{(value >> 8) & 0xFF}.{value & 0xFF}"

    # -------------------------------
    # CIDR → numeric range
    # -------------------------------
    @staticmethod
    def cidr_to_range(cidr: str) -> CidrRange:
        ip_str, prefix = cidr.split("/")
        prefix = int(prefix)

        ip_int = CIDRUtils.ip_to_int(ip_str)
        mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF

        start = ip_int & mask
        end = start | (~mask & 0xFFFFFFFF)

        return CidrRange(cidr=cidr, start=start, end=end)

    # -------------------------------
    # Range overlap logic
    # -------------------------------
    @staticmethod
    def ranges_overlap(r1: CidrRange, r2: CidrRange) -> bool:
        return r1.start <= r2.end and r2.start <= r1.end

    @staticmethod
    def get_overlap_range(r1: CidrRange, r2: CidrRange) -> Optional[Tuple[int, int]]:
        start = max(r1.start, r2.start)
        end = min(r1.end, r2.end)
        return (start, end) if start <= end else None

    # ====================================================================
    # 1) requested_cidr vs available_cidr
    # ====================================================================
    def requested_cidr_vs_available_cidr(self, requested_cidr: str, available_cidr: str):
        req = self.cidr_to_range(requested_cidr)
        avail = self.cidr_to_range(available_cidr)

        if not self.ranges_overlap(req, avail):
            return None

        overlap = self.get_overlap_range(req, avail)
        return {
            "requested_cidr": requested_cidr,
            "available_cidr": available_cidr,
            "start": self.int_to_ip(overlap[0]),
            "end": self.int_to_ip(overlap[1]),
        }

    def print_requested_cidr_vs_available_cidr(self, requested_cidr: str, available_cidr: str):
        result = self.requested_cidr_vs_available_cidr(requested_cidr, available_cidr)

        table = Table(title="Requested CIDR vs Available CIDR Overlap")
        table.add_column("Requested CIDR", justify="center", style="cyan")
        table.add_column("Available CIDR", justify="center", style="magenta")
        table.add_column("Overlap Range", justify="center", style="green")

        if result:
            table.add_row(
                result["requested_cidr"],
                result["available_cidr"],
                f"{result['start']} → {result['end']}"
            )
        else:
            table.add_row(requested_cidr, available_cidr, "[red]No Overlap[/red]")

        console.print(table)

    # ====================================================================
    # 2) requested_cidr vs list of available_cidrs
    # ====================================================================
    def requested_cidr_vs_available_list(self, requested_cidr: str, available_cidrs: List[str]):
        req = self.cidr_to_range(requested_cidr)
        results = []

        for av in available_cidrs:
            avail = self.cidr_to_range(av)

            if self.ranges_overlap(req, avail):
                o = self.get_overlap_range(req, avail)
                results.append({
                    "requested_cidr": requested_cidr,
                    "available_cidr": av,
                    "start": self.int_to_ip(o[0]),
                    "end": self.int_to_ip(o[1]),
                })

        return results

    def print_requested_cidr_vs_available_list(self, requested_cidr: str, available_cidrs: List[str]):
        results = self.requested_cidr_vs_available_list(requested_cidr, available_cidrs)

        table = Table(title=f"Requested CIDR vs Available List: {requested_cidr}", show_lines=True)
        table.add_column("Requested CIDR", style="cyan", justify="center")
        table.add_column("Available CIDR", style="magenta", justify="center")
        table.add_column("Overlap Range", style="green", justify="center")

        if results:
            for r in results:
                table.add_row(
                    r["requested_cidr"],
                    r["available_cidr"],
                    f"{r['start']} → {r['end']}"
                )
        else:
            table.add_row(requested_cidr, "[green]No Overlap Found[/green]", "-")

        console.print(table)

    # ====================================================================
    # 3) Internal overlap inside available list (Two-pointer)
    # ====================================================================
    def available_list_internal_overlap(self, available_cidrs: List[str]):
        ranges = [self.cidr_to_range(c) for c in available_cidrs]
        ranges.sort(key=lambda x: x.start)

        overlaps = []
        i, j = 0, 1

        while j < len(ranges):
            r1 = ranges[i]
            r2 = ranges[j]

            if self.ranges_overlap(r1, r2):
                o = self.get_overlap_range(r1, r2)
                overlaps.append({
                    "available_cidr_1": r1.cidr,
                    "available_cidr_2": r2.cidr,
                    "start": self.int_to_ip(o[0]),
                    "end": self.int_to_ip(o[1]),
                })
                j += 1
            else:
                i = j
                j += 1

        return overlaps

    def print_available_list_internal_overlap(self, available_cidrs: List[str]):
        results = self.available_list_internal_overlap(available_cidrs)

        table = Table(title="Overlap Within Available CIDR List", show_lines=True)
        table.add_column("Available CIDR 1", style="cyan", justify="center")
        table.add_column("Available CIDR 2", style="magenta", justify="center")
        table.add_column("Overlap Range", style="green", justify="center")

        if results:
            for r in results:
                table.add_row(
                    r["available_cidr_1"],
                    r["available_cidr_2"],
                    f"{r['start']} → {r['end']}"
                )
        else:
            table.add_row("-", "-", "[green]No Internal Overlaps[/green]")

        console.print(table)

    # ====================================================================
    # 4) Load available_cidrs from CSV/Excel
    # ====================================================================
    def load_available_from_excel(self, path: str, column: str) -> List[str]:
        df = pd.read_excel(path)
        return df[column].dropna().tolist()

    def load_available_from_csv(self, path: str, column: str) -> List[str]:
        df = pd.read_csv(path)
        return df[column].dropna().tolist()


if __name__ == "__main__":
    cidr_utils = CIDRUtils()
    
    # -----------------------------
    # 1) requested_cidr vs available_cidr
    # -----------------------------
    requested_cidr = "10.0.4.0/23"
    available_cidr = "10.0.0.0/16"
    # cidr_utils.print_requested_cidr_vs_available_cidr(requested_cidr, available_cidr)
    
    # -----------------------------
    # 2) requested_cidr vs available list
    # -----------------------------
    requested_cidr = "10.0.4.0/23"
    available_cidrs = [
        "10.0.0.0/16",
        "10.0.5.0/24",
        "192.168.1.0/24",
        "172.16.0.0/12"
    ]
    # cidr_utils.print_requested_cidr_vs_available_list(requested_cidr, available_cidrs)
    
    # -----------------------------
    # 3) Internal overlap inside available list (two-pointer)
    # -----------------------------
    available_cidrs_list = [
        "10.0.0.0/16",
        "10.0.5.0/24",
        "10.0.4.0/23",
        "192.168.1.0/24",
        "172.16.0.0/12"
    ]
    # cidr_utils.print_available_list_internal_overlap(available_cidrs_list)
    
    # -----------------------------
    # 4) Load available_cidrs from CSV/Excel
    # -----------------------------
    # Example usage (uncomment and provide valid paths to use):
    available_from_excel = cidr_utils.load_available_from_excel("IPAM-Updated-CIDR.xlsx", "cidr")
    # available_from_csv = cidr_utils.load_available_from_csv("available_cidrs.csv ", "CIDR")
    
    # print("CIDR Ranges loaded from Excel:", available_from_excel)
    
    cidr_utils.print_available_list_internal_overlap(available_from_excel)

