from datetime import datetime
from typing import Dict, List, Tuple
from unittest import TestCase, mock
import csv
import io

import src.cohort_customer_segment_tree as cohort_customer_segment_tree
from src import customers
from src import utils

import tests.fixtures.customers as fixtures_customers
import tests.utils


class TestCohortCustomerIndexBuilder(TestCase):

    def setUp(self):
        self.cohort_date = datetime.strptime("2019-12-21", "%Y-%m-%d")
        self.cohort_id = utils.calculate_week_id(self.cohort_date.date())

    def test_constructor(self) -> None:
        csv_file = io.StringIO(fixtures_customers.ONE_ROW)
        customers_csv_reader = csv.reader(csv_file)
        tree_builder = cohort_customer_segment_tree.CohortCustomerSegmentsTreeBuilder(
            customers.CustomersReader(customers_csv_reader, "-0500"))
        self.assertIsInstance(tree_builder.customers_reader, customers.CustomersReader)
        self.assertEqual(tree_builder.cohorts, {})

    def test_build_cohort_index_the_first_row(self) -> None:
        with mock.patch.object(
                cohort_customer_segment_tree.CohortCustomerSegmentsTreeBuilder,
                "add_customer",
                mock.MagicMock(
                    return_value=None)
        ) as add_customer_mock:
            tree_builder = tests.utils.cohort_index_builder(fixtures_customers.ONE_ROW)
            tree_builder.build()

        add_customer_mock.assert_called_once()
        self.assertEqual(35410, add_customer_mock.call_args[0][0].customer_id)
        self.assertEqual(datetime.strptime("2015-07-03 17:01:11-0500", "%Y-%m-%d %H:%M:%S%z"),
                         add_customer_mock.call_args[0][0].created)

    def test_build_cohort_index_five_rows(self) -> None:
        with mock.patch.object(
                cohort_customer_segment_tree.CohortCustomerSegmentsTreeBuilder,
                "add_customer",
                mock.MagicMock(
                    return_value=None)
        ) as add_customer_mock:
            tree_builder = tests.utils.cohort_index_builder(fixtures_customers.FIVE_ROWS)
            tree_builder.build()

        self.assertEqual(5, add_customer_mock.call_count)
        self.assertEqual(35414, add_customer_mock.call_args[0][0].customer_id)
        self.assertEqual(datetime.strptime("2015-07-03 17:21:55-0500", "%Y-%m-%d %H:%M:%S%z"),
                         add_customer_mock.call_args[0][0].created)

    def test_add_customer(self):
        tree_builder = cohort_customer_segment_tree.CohortCustomerSegmentsTreeBuilder(
            customers.CustomersReader(io.StringIO("x"), "-0500"))

        tree_builder.add_customer(customers.Customer(10, self.cohort_date))
        self.assertIn(self.cohort_id, tree_builder.cohorts)
        self.assertEqual(cohort_customer_segment_tree.CohortCustomerSegmentsTreeBuilderNode(10),
                         tree_builder.cohorts[self.cohort_id].root_node)

        tree_builder.add_customer(customers.Customer(11, self.cohort_date))
        self.assertIn(self.cohort_id, tree_builder.cohorts)
        self.assertEqual((10, 11),
                         tree_builder.cohorts[
                             self.cohort_id].root_node.subtree_range)

        tree_builder.add_customer(customers.Customer(9, self.cohort_date))
        self.assertIn(self.cohort_id, tree_builder.cohorts)
        self.assertEqual((9, 11),
                         tree_builder.cohorts[
                             self.cohort_id].root_node.subtree_range)

        tree_builder.add_customer(customers.Customer(13, self.cohort_date))
        self.assertIn(self.cohort_id, tree_builder.cohorts)
        self.assertEqual((9, 13),
                         tree_builder.cohorts[
                             self.cohort_id].root_node.subtree_range)
        self.assertEqual(1,
                         len(tree_builder.cohorts[self.cohort_id].root_node.subtree))

        tree_builder.add_customer(customers.Customer(7, self.cohort_date))
        self.assertIn(self.cohort_id, tree_builder.cohorts)
        self.assertEqual(cohort_customer_segment_tree.CohortCustomerSegmentsTreeBuilderNode(7),
                         tree_builder.cohorts[self.cohort_id].root_node)
        self.assertEqual(2, len(tree_builder.cohorts[self.cohort_id].root_node.subtree))

    def test_build_cohort_index_five_rows_one_cohort(self) -> None:
        tree_builder = tests.utils.cohort_index_builder(fixtures_customers.FIVE_ROWS_ONE_COHORT)
        tree_builder.build()

        self.assertEqual(1, len(tree_builder.cohorts))
        customer_id_range_nodes = list(tree_builder.cohorts.values())[0]
        self.assertEqual((35410, 35414), customer_id_range_nodes.root_node.subtree_range)

    def test_build_cohort_index_five_rows_two_cohorts(self):
        tree_builder = tests.utils.cohort_index_builder(fixtures_customers.FIVE_ROWS_TWO_COHORTS)
        tree_builder.build()

        self.assertEqual(2, len(tree_builder.cohorts))
        self.assertTupleEqual((35410, 35411),
                              tree_builder.cohorts[
                                  2321].root_node.subtree_range)
        self.assertTupleEqual((35412, 35414),
                              tree_builder.cohorts[
                                  2326].root_node.subtree_range)

    def test_build_cohort_index_five_rows_two_timezone_cohorts(self):
        tree_builder = tests.utils.cohort_index_builder(fixtures_customers.FIVE_ROWS_TWO_TIMEZONE_COHORTS)
        tree_builder.build()

        self.assertEqual(2, len(tree_builder.cohorts))
        self.assertTupleEqual((35410, 35411), tree_builder.cohorts[2321].root_node.subtree_range)
        self.assertTupleEqual((35412, 35414), tree_builder.cohorts[2322].root_node.subtree_range)

    def test_build_cohort_index_five_rows_two_overlapping_cohorts(self):
        tree_builder = tests.utils.cohort_index_builder(fixtures_customers.FIVE_ROWS_TWO_OVERLAPPING_COHORTS)
        tree_builder.build()

        self.assertEqual(2, len(tree_builder.cohorts))
        self.assertTupleEqual((35410, 35413), tree_builder.cohorts[2321].root_node.subtree_range)
        self.assertEqual(1, len(tree_builder.cohorts[2321].root_node.subtree))
        self.assertTupleEqual((35413, 35413), tree_builder.cohorts[2321].root_node.subtree[0].subtree_range)
        self.assertTupleEqual((35411, 35414), tree_builder.cohorts[2327].root_node.subtree_range)
        self.assertEqual(1, len(tree_builder.cohorts[2327].root_node.subtree))
        self.assertTupleEqual((35414, 35414), tree_builder.cohorts[2327].root_node.subtree[0].subtree_range)

    def test_build_cohort_index_five_rows_one_merged_cohort(self):
        tree_builder = tests.utils.cohort_index_builder(fixtures_customers.FIVE_ROWS_ONE_COHORT_MULTI_SEGMENTS)
        tree_builder.build()

        self.assertEqual(1, len(tree_builder.cohorts))
        self.assertTupleEqual((35410, 35414), tree_builder.cohorts[2321].root_node.subtree_range)
        self.assertTupleEqual((35410, 35414), tree_builder.cohorts[2321].root_node.subtree_range)
        self.assertEqual(0, len(tree_builder.cohorts[2321].root_node.subtree))

    def test_building_full_tree_no_flatten(self):
        customers_file_path = tests.utils.top_module_path() + "/e2e/fixtures/customers.csv"
        timezone = utils.parse_timezone("-0500")
        with open(customers_file_path) as customers_csv_file, mock.patch.object(
                cohort_customer_segment_tree.CohortCustomerSegmentsTreeBuilder, "flatten",
                mock.MagicMock(return_value=None)) as flatten_mock:
            tree_builder = cohort_customer_segment_tree.CohortCustomerSegmentsTreeBuilder(
                customers.CustomersReader(csv.reader(customers_csv_file), timezone))
            tree_builder.build()

        flatten_mock.assert_called_once()

        self.validate_cohort_customer_tree(tree_builder.cohorts)

    def validate_cohort_customer_tree_node(self,
                                           node: cohort_customer_segment_tree.CohortCustomerSegmentsTreeBuilderNode):
        self.assertLessEqual(node.segment[0], node.segment[1])
        self.assertLessEqual(node.subtree_range[0], node.subtree_range[1])
        self.assertEqual(node.subtree_range[0], node.segment[0])
        self.assertEqual(node.subtree_range[1], node.segment[1] if len(node.subtree) == 0 else
                         node.subtree[-1].subtree_range[1])

        try:
            if len(node.subtree) > 0:
                self.assertLess(node.segment[1] + 1, node.subtree[0].segment[0])
                self.assertEqual(0, len(node.subtree[-1].subtree))
        except AssertionError as err:
            raise err

        try:
            for i in range(len(node.subtree) - 1):
                self.assertLess(node.subtree[i].subtree_range[1] + 1, node.subtree[i + 1].subtree_range[0])
        except AssertionError as err:
            raise err

        for node in node.subtree:
            self.validate_cohort_customer_tree_node(node)

    def validate_cohort_customer_tree(self,
                                      cohort_customer_tree:
                                      Dict[int,
                                           cohort_customer_segment_tree.CohortCustomerSegmentsTreeBuilderRootNode]
                                      ) -> None:
        for root_node in cohort_customer_tree.values():
            self.validate_cohort_customer_tree_node(root_node.root_node)

    def test_building_full_tree_with_flatten(self):
        customers_file_path = tests.utils.top_module_path() + "/e2e/fixtures/customers.csv"
        timezone = utils.parse_timezone("-0500")
        with open(customers_file_path) as customers_csv_file:
            tree_builder = cohort_customer_segment_tree.CohortCustomerSegmentsTreeBuilder(
                customers.CustomersReader(csv.reader(customers_csv_file), timezone))
            tree_builder.build()

        self.validate_flatten_tree(tree_builder.cohorts)

    def validate_flatten_tree(self,
                              cohort_customer_tree:
                              Dict[int,
                                   cohort_customer_segment_tree.CohortCustomerSegmentsTreeBuilderRootNode]
                              ) -> None:

        for root_node in cohort_customer_tree.values():
            self.validate_flatten_tree_node(root_node.segments, root_node.root_node.subtree_range)

    def validate_flatten_tree_node(self, segments: List[Tuple[int, int]], cohort_range: Tuple[int, int]):

        try:
            self.assertEqual(cohort_range, (segments[0][0], segments[-1][1]))
            for i in range(len(segments) - 1):
                self.assertLess(segments[i][1] + 1,
                                segments[i + 1][0])
        except AssertionError as err:
            raise err
