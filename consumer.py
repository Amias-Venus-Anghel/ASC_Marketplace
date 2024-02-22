"""
This module represents the Consumer.

Computer Systems Architecture Course
Assignment 1
March 2021
"""

from threading import Thread
import time

class Consumer(Thread):
    """
    Class that represents a consumer.
    """

    def __init__(self, carts, marketplace, retry_wait_time, **kwargs):
        """
        Constructor.

        :type carts: List
        :param carts: a list of add and remove operations

        :type marketplace: Marketplace
        :param marketplace: a reference to the marketplace

        :type retry_wait_time: Time
        :param retry_wait_time: the number of seconds that a producer must wait
        until the Marketplace becomes available

        :type kwargs:
        :param kwargs: other arguments that are passed to the Thread's __init__()
        """
        Thread.__init__(self, **kwargs)
        self.carts = carts
        self.marketplace = marketplace
        self.wait_time = retry_wait_time
        self.name = kwargs["name"]

    def run(self):
        card_id = self.marketplace.new_cart()
        self.marketplace.register_consumer(self.name, card_id)
        for cart in self.carts:
            for operation in cart:
                i = 0
                while i < int(operation["quantity"]):
                    if operation["type"] == "add":
                        if not self.marketplace.add_to_cart(card_id, operation["product"]):
                            # wait to retry adding the product to cart
                            time.sleep(self.wait_time)
                            continue
                        time.sleep(self.wait_time)
                        # add next product
                        i += 1
                    elif operation["type"] == "remove":
                        self.marketplace.remove_from_cart(card_id, operation["product"])
                        i += 1
            self.marketplace.place_order(card_id)
