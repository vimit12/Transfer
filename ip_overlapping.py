from ipaddress import ip_network
from rich.console import Console
from rich.table import Table

console = Console()


def get_overlap_ips(net1, net2):
    """
    Returns a tuple (start_ip, end_ip) of overlapping range,
    or None if no overlap exists.
    """
    start = max(net1.network_address, net2.network_address)
    end = min(net1.broadcast_address, net2.broadcast_address)

    if start <= end:
        return start, end
    return None


def check_cidr_overlap_with_ips(given_cidr, cidr_list):
    given_net = ip_network(given_cidr)
    results = []

    for cidr in cidr_list:
        net = ip_network(cidr)

        if given_net.overlaps(net):
            overlap_range = get_overlap_ips(given_net, net)
            results.append((net, overlap_range))

    return results


if __name__ == "__main__":
    # Example CIDR list
    cidr_ranges = [
        "10.0.0.0/16",
        "10.0.5.0/24",
        "192.168.1.0/24",
        "172.16.0.0/12"
    ]

    cidr_to_check = "10.0.4.0/23"

    overlaps = check_cidr_overlap_with_ips(cidr_to_check, cidr_ranges)

    # Build Rich Output Table
    table = Table(title="CIDR Overlap Report", show_lines=True)
    table.add_column("Given CIDR", style="cyan", justify="center")
    table.add_column("Overlapping CIDR", style="magenta", justify="center")
    table.add_column("Overlapping IP Range", style="green", justify="center")

    if overlaps:
        for net, overlap_range in overlaps:
            if overlap_range:
                start_ip, end_ip = overlap_range
                ip_range_str = f"{start_ip} → {end_ip}"
            else:
                ip_range_str = "[red]No Overlap[/red]"

            table.add_row(cidr_to_check, str(net), ip_range_str)

    else:
        table.add_row(cidr_to_check, "[green]No Overlap[/green]", "-")

    console.print(table)
