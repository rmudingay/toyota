#!/usr/bin/env python3

import os
import sys
import json
import logging
import pathlib
import argparse
from datetime import datetime
from requests import Session
from typing import Optional, List, Dict, Callable


logging.basicConfig(stream=sys.stderr, level=logging.WARN)


DATE_STRUCT: dict[str, dict] = {"steps": {}, "deliveries": {}}


class ToyotaSession:
    """handle session with toyota APIs, including authentication"""

    BASE_HEADERS = {
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
        "Sec-Fetch-Dest": "empty",
        "X-TME-BRAND": "TOYOTA",
        "X-TME-LC": "en-gb",
    }
    AUTH_URL = "https://ssoms.toyota-europe.com/authenticate"
    ORDERS_URL = "https://weblos.toyota-europe.com/leads/ordered"
    ORDER_DETAILS_URL_TEMPLATE = (
        "https://cpb2cs.toyota-europe.com/api/orderTracker/user/{}/orderStatus/{}"
    )

    def __init__(self, username: str, password: str):
        self.session = Session()
        self.session.headers.update(self.BASE_HEADERS)
        self.username = username
        self.password = password
        self.token = ""
        self.uuid = ""
        self._authenticate()

    def _authenticate(self):
        """auth user and sets token and uuid for the session"""
        response = self.session.post(
            self.AUTH_URL,
            json={"username": self.username, "password": self.password},
            timeout=10,
        )
        if not response.ok:
            raise ValueError(f"auth failed ({response.status_code}): {response.text}")

        data = response.json()
        self.token = data["token"]
        self.uuid = data["customerProfile"]["uuid"]
        self.session.headers.update({"x-tme-token": self.token})

    def fetch_orders(self) -> List[str]:
        """get list of orders for the authenticated user"""
        response = self.session.get(
            self.ORDERS_URL,
            params={"displayPreApprovedCars": "true", "displayVOTCars": "true"},
            timeout=10,
        )
        if not response.ok:
            raise ValueError(
                f"failed to fetch orders ({response.status_code}): {response.text}"
            )

        orders = response.json()
        return [order["id"] for order in orders]

    def fetch_order_details(self, order_id: str) -> Dict:
        """get details for a specific order"""
        response = self.session.get(
            self.ORDER_DETAILS_URL_TEMPLATE.format(self.uuid, order_id),
            timeout=10,
        )
        if not response.ok:
            raise ValueError(
                f"failed to fetch order details ({response.status_code}): {response.text}"
            )

        return response.json()


class Reporter:
    """order details"""

    # Class attributes for terminal color codes and other constants
    RESET = "\033[0m"
    BOLD = "\033[1m"
    INVERT = "\033[7m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    SP = "  "

    @classmethod
    def print_order(cls, status: str, length: int) -> str:
        """prints detailed information about a given order"""
        color_code = cls.RED if status == "pending" else cls.GREEN  # Simplified example
        return f"{cls.BOLD}{color_code}{status}{cls.RESET}{' '*(length - len(status))}"

    @classmethod
    def _print_table(cls, table: list, fmt_data: Callable[[list, list[int]], list]):
        # get max column length
        lengths = [0] * len(table[0])
        for data in table:
            for idx, val in enumerate(data):
                lengths[idx] = max(lengths[idx], len(val))

        # generate format string
        fmt = f"{cls.SP}│"
        for length in lengths:
            fmt += f" {{:<{length}}} │"

        # print headers and separator
        print(fmt.format(*table[0]))
        print(f"{cls.SP}├" + "┼".join("─" * (ln + 2) for ln in lengths) + "┤")

        # print steps
        for data in table[1:]:
            print(fmt.format(*fmt_data(data, lengths)))

    @classmethod
    def _load_dates(cls, filename: str) -> tuple[pathlib.Path, dict]:
        dates_file = pathlib.Path(filename)

        dates = DATE_STRUCT

        if dates_file.exists():
            with dates_file.open("r") as fp:
                dates = json.load(fp)

        return dates_file, dates

    @classmethod
    def _save_dates(cls, dates_file: pathlib.Path, dates: dict):
        with dates_file.open("w") as fp:
            json.dump(dates, fp)

    @classmethod
    def print_order(cls, order: dict, store_dates: Optional[bool] = False):
        # print(order)
        if store_dates:
            dates_file, dates = cls._load_dates(
                f"{order['orderDetails']['orderId']}.json"
            )

        details = order["orderDetails"]
        status = order["currentStatus"]

        print()
        print(f"{cls.SP}{cls.INVERT}{cls.BOLD} Order {details['orderId']} {cls.RESET}")
        print()
        print(f"{cls.SP}{cls.BOLD}Status{cls.RESET}: {status['currentStatus']}")
        print(
            f"{cls.SP}{cls.BOLD}Estimated Delivery?{cls.RESET}: {order.get('etaToFinalDestination', 'N/A')} / {status.get('estimatedDeliveryToFinalDestination', 'N/A')}"
        )
        print()
        print(f"{cls.SP}{cls.BOLD}Call Off?{cls.RESET}: {status['callOffStatus']}")
        print(
            f"{cls.SP}{cls.BOLD}Delayed?{cls.RESET}: {status['isDelayed'] if status.get('isDelayed') else False}"
        )
        print(
            f"{cls.SP}{cls.BOLD}Damage?{cls.RESET}: {status['damageCode'] if status.get('damageCode') else None}"
        )
        print()
        print(f"{cls.SP}{cls.BOLD}Vehicle{cls.RESET}: {details.get('vehicleModel')}")
        print(f"{cls.SP}{cls.BOLD}Engine{cls.RESET}: {details.get('engine')}")
        print(
            f"{cls.SP}{cls.BOLD}Transmission{cls.RESET}: {details.get('transmission')}"
        )
        print(
            f"{cls.SP}{cls.BOLD}Color Code{cls.RESET}: {details.get('vehicleExternalColor')}"
        )
        print()
        print(f"{cls.SP}{cls.BOLD}VIN{cls.RESET}: {details.get('vin')}")

        steps = order.get("preprocessed", {}).get("steps")

        if steps:
            print()

            table = [["Step", "Location", "Status"]]

            if store_dates:
                table[0].append("Dates")

            for k, v in steps.items():
                table.append([k, v.get("location", ""), v["status"]])

                if store_dates:
                    if k not in dates["steps"]:
                        dates["steps"][k] = {}

                    if (
                        v["status"] not in dates["steps"][k]
                        and v["status"] != "pending"
                    ):
                        dates["steps"][k][v["status"]] = datetime.today().strftime(
                            "%Y-%m-%d"
                        )

                    table[-1].append(
                        " | ".join(
                            f"{kd}: {vd}" for kd, vd in dates["steps"][k].items()
                        )
                    )

            if store_dates:
                fmt_fn = lambda data, lengths: [
                    *data[:-2],
                    data[-2],
                    data[-1],
                ]
            else:
                fmt_fn = lambda data, lengths: [
                    *data[:-1],
                    data[-1],
                ]

            cls._print_table(table, fmt_fn)

        else:
            print(f"\n{cls.SP}order has no steps.")

        deliveries = order.get("intermediateDeliveries")

        if deliveries:
            print()
            table = [["Loc. Code", "Location", "Loc. Type", "Transport", "Visited"]]

            if store_dates:
                table[0].append("Dates")

            for d in deliveries:
                table.append(
                    [
                        f"{d['locationCode']}, {d['countryCode']}",
                        f"{d['locationName']}, {d['countryName']}",
                        d["destinationType"],
                        d["transportMethod"],
                        d["isVisited"],
                    ]
                )

                if store_dates:
                    if d["locationCode"] not in dates["deliveries"]:
                        dates["deliveries"][d["locationCode"]] = {}

                    if (
                        d["isVisited"] not in dates["deliveries"][d["locationCode"]]
                        and d["isVisited"] != "notVisited"
                    ):
                        dates["deliveries"][d["locationCode"]][
                            d["isVisited"]
                        ] = datetime.today().strftime("%Y-%m-%d")

                    table[-1].append(
                        " | ".join(
                            f"{kd}: {vd}"
                            for kd, vd in dates["deliveries"][d["locationCode"]].items()
                        )
                    )

            if store_dates:
                fmt_fn = lambda data, lengths: [
                    *data[:-2],
                    data[-2],
                    data[-1],
                ]
            else:
                fmt_fn = lambda data, lengths: [
                    *data[:-1],
                    data[-1],
                ]

            cls._print_table(table, fmt_fn)

        else:
            print(f"\n{cls.SP}order has no deliveries.")

        print()

        if store_dates:
            cls._save_dates(dates_file, dates)


def main(username: str, password: str, store_dates: Optional[bool] = False):
    toyota_session = ToyotaSession(username, password)
    orders = toyota_session.fetch_orders()

    for order_id in orders:
        order_details = toyota_session.fetch_order_details(order_id)
        Reporter.print_order(order_details, store_dates)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="track order details from toyota.")

    parser.add_argument("--username", required=True, help="toyota account username.")
    parser.add_argument("--password", required=True, help="toyota account password.")
    parser.add_argument(
        "--store-dates", action="store_true", help="Store state changes dates."
    )

    args = parser.parse_args()

    main(args.username, args.password, args.store_dates)
