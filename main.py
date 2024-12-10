import threading
import time
import logging
from typing import Dict

# Ensure these are imported correctly
from core.router import Router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RIPSimulation:
    def __init__(self):
        self.routers: Dict[str, Router] = {}
        self.network_topology: Dict[str, Dict[str, int]] = {}

    def add_router(self, router: Router):
        """
        Add a router to the simulation

        Args:
            router (Router): Router object to add
        """
        try:
            if router.id in self.routers:
                logger.warning(f"Router {router.id} already exists. Skipping.")
                return

            self.routers[router.id] = router
            logger.info(f"Router {router.id} added successfully.")
        except Exception as e:
            logger.error(f"Error adding router: {e}")

    def connect_routers(self, router1_id: str, router2_id: str, cost: int):
        """
        Connect two routers with a specific link cost

        Args:
            router1_id (str): ID of first router
            router2_id (str): ID of second router
            cost (int): Link cost between routers
        """
        try:
            # Validate routers exist
            if router1_id not in self.routers or router2_id not in self.routers:
                raise ValueError("Both routers must exist before connecting")

            # Bidirectional connection
            self.network_topology.setdefault(router1_id, {})[router2_id] = cost
            self.network_topology.setdefault(router2_id, {})[router1_id] = cost

            logger.info(f"Connected {router1_id} and {router2_id} with cost {cost}")
        except Exception as e:
            logger.error(f"Error connecting routers: {e}")

    def simulate_rip(self):
        """
        Simulate RIP routing updates
        """

        def update_routing_tables():
            """
            Periodic routing table update thread
            """
            try:
                while True:
                    for router_id, router in list(self.routers.items()):
                        # Create a copy of neighbors to avoid runtime modification issues
                        neighbors = list(self.network_topology.get(router_id, {}).items())

                        for neighbor, link_cost in neighbors:
                            try:
                                neighbor_router = self.routers[neighbor]
                                updated = router.update_routing_table(
                                    neighbor_router.routing_table,
                                    neighbor,
                                    link_cost
                                )

                                if updated:
                                    logger.info(f"Routing table updated for router {router_id}")
                            except Exception as neighbor_error:
                                logger.error(f"Error updating route from {router_id} to {neighbor}: {neighbor_error}")

                    # Wait before next update
                    time.sleep(5)

            except Exception as e:
                logger.critical(f"Routing simulation failed: {e}")

        # Start as a daemon thread
        thread = threading.Thread(target=update_routing_tables, daemon=True)
        thread.start()
        logger.info("RIP Routing simulation started")

    def print_routing_tables(self):
        """
        Print routing tables for all routers
        """
        for router_id, router in self.routers.items():
            print(f"\nRouting Table for Router {router_id}:")
            for dest, route_info in router.routing_table.items():
                print(f"  Destination: {dest}")
                print(f"    Cost: {route_info['cost']}")
                print(f"    Next Hop: {route_info['next_hop']}")
                print(f"    Timestamp: {route_info['timestamp']}")


def main():
    try:
        # Create simulation
        simulation = RIPSimulation()

        # Create routers
        router1 = Router("R1")
        router2 = Router("R2")
        router3 = Router("R3")

        # Add routers to simulation
        simulation.add_router(router1)
        simulation.add_router(router2)
        simulation.add_router(router3)

        # Connect routers
        simulation.connect_routers(router1.id, router2.id, 1)
        simulation.connect_routers(router2.id, router3.id, 2)

        # Start RIP simulation
        simulation.simulate_rip()

        # Run for a while to see routing updates
        try:
            while True:
                time.sleep(20)  # Keep main thread alive
                simulation.print_routing_tables()
        except KeyboardInterrupt:
            logger.info("Simulation stopped by user")

    except Exception as e:
        logger.critical(f"Simulation initialization failed: {e}")


if __name__ == "__main__":
    main()