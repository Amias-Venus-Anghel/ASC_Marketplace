"""
This module represents the Marketplace.

Computer Systems Architecture Course
Assignment 1
March 2021
"""

from threading import Lock
import time
import logging
from logging.handlers import RotatingFileHandler
import unittest


class TCoffee:
    """
    Test class Coffee
    """
    def __init__(self, name, price):
        self.name = name
        self.price = price


class TestMarketplace(unittest.TestCase):
    """
    Testing class for marketplace
    """

    def test_register_producer(self):
        """ test function register_producer of marketplace """
        # initializations
        marketplace = Marketplace(15)
        producer_id0 = marketplace.register_producer()
        producer_id1 = marketplace.register_producer()
        producer_id2 = marketplace.register_producer()
        producer_id3 = marketplace.register_producer()
        # check correct id assignation
        self.assertEqual(producer_id0, 0)
        self.assertEqual(producer_id1, 1)
        self.assertEqual(producer_id2, 2)
        self.assertEqual(producer_id3, 3)

    def test_publish(self):
        """ test function publish of marketplace """
        # initializations
        marketplace = Marketplace(2)
        producer_id = marketplace.register_producer()
        product = TCoffee("TestCoffee", 10)
        # check marketplace limit for producer
        self.assertTrue(marketplace.publish(producer_id, product))
        self.assertTrue(marketplace.publish(producer_id, product))
        self.assertFalse(marketplace.publish(producer_id, product))

    def test_new_cart(self):
        """ test function new_cart of marketplace """
        # initializations
        marketplace = Marketplace(15)
        cart0 = marketplace.new_cart()
        cart1 = marketplace.new_cart()
        # check correct cart id assignation
        self.assertEqual(cart0, 0)
        self.assertEqual(cart1, 1)
        # check existence of carts
        self.assertTrue(len(marketplace.carts) == 2)

    def test_register_consumer(self):
        """ test function register_consumer of marketplace """
        # initializations
        marketplace = Marketplace(15)
        cart_id = marketplace.new_cart()
        name = "Consumer"
        marketplace.register_consumer(name, cart_id)
        # check existence of mapping
        self.assertIn(cart_id, marketplace.consumers)
        # check correct mapping
        self.assertEqual(marketplace.consumers[cart_id], name)

    def test_add_to_cart(self):
        """ test function add_to_cart of marketplace """
        # initializations
        marketplace = Marketplace(15)
        cart_id = marketplace.new_cart()
        name = "Consumer"
        marketplace.register_consumer(name, cart_id)
        producer_id = marketplace.register_producer()
        product = TCoffee("TestCoffee", 10)
        # check: no product on the market
        self.assertFalse(marketplace.add_to_cart(cart_id, product))
        # check: product was added
        marketplace.publish(producer_id, product)
        self.assertTrue(marketplace.add_to_cart(cart_id, product))
        # check: product is in a cart, can't be added again
        self.assertFalse(marketplace.add_to_cart(cart_id, product))

    def test_remove_from_cart(self):
        """ test function remove_from_cart of marketplace """
        # initializations
        marketplace = Marketplace(15)
        cart_id = marketplace.new_cart()
        name = "Consumer"
        marketplace.register_consumer(name, cart_id)
        producer_id = marketplace.register_producer()
        product = TCoffee("TestCoffee", 10)
        # check product in cart
        marketplace.publish(producer_id, product)
        marketplace.add_to_cart(cart_id, product)
        self.assertEqual(len(marketplace.carts[cart_id][product.name]), 1)
        self.assertEqual(len(marketplace.products_dictionary[product.name]), 0)
        # check product not in cart anymore
        marketplace.remove_from_cart(cart_id, product)
        self.assertEqual(len(marketplace.carts[cart_id][product.name]), 0)
        self.assertEqual(len(marketplace.products_dictionary[product.name]), 1)

    def test_place_order(self):
        """ test function place_order of marketplace """
        # initializations
        marketplace = Marketplace(15)
        cart_id = marketplace.new_cart()
        name = "Consumer"
        marketplace.register_consumer(name, cart_id)
        producer_id = marketplace.register_producer()
        product0 = TCoffee("TestCoffee", 10)
        product1 = TCoffee("TestCoffee2", 13)
        # check one item order
        marketplace.publish(producer_id, product0)
        marketplace.add_to_cart(cart_id, product0)
        products = marketplace.place_order(cart_id)
        self.assertIn(product0, products)
        # check multiple items order
        marketplace.publish(producer_id, product0)
        marketplace.publish(producer_id, product1)
        marketplace.add_to_cart(cart_id, product0)
        marketplace.add_to_cart(cart_id, product1)
        products = marketplace.place_order(cart_id)
        self.assertIn(product0, products)
        self.assertIn(product1, products)


class Marketplace:
    """
    Class that represents the Marketplace. It's the central part of the implementation.
    The producers and consumers use its methods concurrently.
    """
    def __init__(self, queue_size_per_producer):
        """
        Constructor

        :type queue_size_per_producer: Int
        :param queue_size_per_producer: the maximum size of a queue associated with each producer
        """
        # lock for managing access to marketplace
        self.lock = Lock()
        self.queue_size = queue_size_per_producer
        # producer id counter
        self.producers = 0
        # mapping of products in the marketplace
        self.products_dictionary = {}
        # list of carts
        self.carts = []
        # mapping of cart_ids to consumer names
        self.consumers = {}
        # mapping of producers ids to their number of products
        self.producers_count = []

        # logger formating
        self.logger = logging.getLogger('Marcketplace')
        self.logger.setLevel(logging.INFO)
        log_handler = RotatingFileHandler('marketplace.log', maxBytes=35000, backupCount=4)
        formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%H:%M:%S')
        formatter.converter = time.gmtime
        log_handler.setFormatter(formatter)
        self.logger.addHandler(log_handler)

    def register_producer(self):
        """
        Returns an id for the producer that calls this.
        """
        self.logger.info("<register_producer> Register producer")
        with self.lock:
            # get next available producer id
            producer_id = self.producers
            self.producers_count.append(0)
            # increment counter of producers
            self.producers = self.producers + 1

        self.logger.info("<register_producer> Producer was registered")
        return producer_id

    def publish(self, producer_id, product):
        """
        Adds the product provided by the producer to the marketplace

        :type producer_id: String
        :param producer_id: producer id

        :type product: Product
        :param product: the Product that will be published in the Marketplace

        :returns True or False. If the caller receives False, it should wait and then try again.
        """
        self.logger.info("<publish> Producer %s wants to publish %s", producer_id, product)
        # check if producer has reached the limit of products in the marketplace
        if self.producers_count[producer_id] == self.queue_size:
            self.logger.info("<publish> Product was not published")
            return False

        with self.lock:
            # check if product has a list associated to it
            if product.name not in self.products_dictionary:
                self.products_dictionary[product.name] = []
            # add the tuple of product and producer_id to the list
            self.products_dictionary[product.name].append((product, producer_id))
            # increment the number of products the producer has on the marketplace
            self.producers_count[producer_id] += 1

        self.logger.info("<publish> Product was published successfully")
        return True

    def new_cart(self):
        """
        Creates a new cart for the consumer

        :returns an int representing the cart_id
        """
        self.logger.info("<new_cart> A new cart is being created")
        with self.lock:
            # new cart dictionary
            cart = {}
            # add cart to the list of carts
            self.carts.append(cart)

            self.logger.info("<new_cart> A new cart was created")
            return len(self.carts) - 1

    def register_consumer(self, name, cart_id):
        """
        Maps a cart to a consumer name

        :type name: String
        :param name: name of consumer

        :type cart_id: int
        :param cart_id: consumers's cart id
        """
        self.logger.info("<register_consumer> Consumer %s registers with cart %s", name, cart_id)
        with self.lock:
            self.consumers[cart_id] = name
        self.logger.info("<register_consumer> Consumer %s was registered with their cart", name)

    def add_to_cart(self, cart_id, product):
        """
        Adds a product to the given cart. The method returns

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to add to cart

        :returns True or False. If the caller receives False, it should wait and then try again
        """
        self.logger.info("<add_to_cart> Consumer wished to add %s to cart %s", product, cart_id)
        with self.lock:
            # check if product is available in marketplace
            if product.name not in self.products_dictionary:
                self.logger.info("<add_to_cart> Product is not available")
                return False
            if len(self.products_dictionary[product.name]) < 1:
                self.logger.info("<add_to_cart> Product is not available")
                return False
            # extract product from marketplace
            product_to_add = self.products_dictionary[product.name].pop(0)
            # add product to cart
            if product.name not in self.carts[cart_id]:
                self.carts[cart_id][product.name] = []
            self.carts[cart_id][product.name].append(product_to_add)

        self.logger.info("<add_to_cart> Product added successfully to cart")
        return True

    def remove_from_cart(self, cart_id, product):
        """
        Removes a product from cart.

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to remove from cart
        """
        self.logger.info("<remove_from_cart> Consumer removes %s from cart %s", product, cart_id)
        with self.lock:
            # extract product from cart
            product_removed = self.carts[cart_id][product.name].pop(0)
            self.products_dictionary[product.name].append(product_removed)
        self.logger.info("<remove_from_cart> Product removed from cart successfully")

    def place_order(self, cart_id):
        """
        Return a list with all the products in the cart.

        :type cart_id: Int
        :param cart_id: id cart
        """
        self.logger.info("<place_order> Products in cart %s are being bought", cart_id)

        bought_products = []

        for key in self.carts[cart_id]:
            for prod in self.carts[cart_id][key]:
                product = prod[0]
                bought_products.append(product)
                with self.lock:
                    # modify producer count of products on the marketplace
                    self.producers_count[prod[1]] -= 1
                print(f"{self.consumers[cart_id]} bought {product}")
        # empty consumer's cart to be used again
        self.carts[cart_id].clear()
        self.logger.info("<place_order> Order placed successfully")
        return bought_products
