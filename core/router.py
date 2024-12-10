import time
import uuid
from typing import Dict, Any


class Router:
    def __init__(self, name: str = None):
        self.id = name if name else str(uuid.uuid4())
        self.routing_table: Dict[str, Dict[str, Any]] = {
            self.id: {
                "cost": 0,
                "next_hop": self.id,
                "timestamp": time.time()
            }
        }
        self.interfaces: Dict[str, Dict] = {}

    def update_routing_table(self, neighbor_table: Dict, neighbor_id: str, link_cost: int) -> bool:
        """
        Update routing table based on neighbor's routing information

        Args:
            neighbor_table (Dict): Routing table of neighboring router
            neighbor_id (str): ID of the neighboring router
            link_cost (int): Cost of link to the neighboring router

        Returns:
            bool: Whether routing table was updated
        """
        updated = False
        current_time = time.time()

        for dest, info in neighbor_table.items():
            # Implement split horizon and poison reverse
            new_cost = info["cost"] + link_cost

            # Update conditions
            if (dest not in self.routing_table or
                    new_cost < self.routing_table[dest]["cost"] or
                    self.routing_table[dest]["next_hop"] == neighbor_id):
                self.routing_table[dest] = {
                    "cost": new_cost,
                    "next_hop": neighbor_id,
                    "timestamp": current_time
                }
                updated = True

        return updated

    def add_interface(self, interface_id: str, ip: str, port: int):
        """
        Add network interface to router

        Args:
            interface_id (str): Unique identifier for interface
            ip (str): IP address
            port (int): Port number
        """
        self.interfaces[interface_id] = {
            "ip": ip,
            "port": port
        }