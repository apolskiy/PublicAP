"""Shared pytest configuration for both emulator test directories.

Sits one level above ``tests/`` and ``image_tests/`` so the assigned-test-ID
mechanism is defined exactly once. Putting it in each of the two sibling
conftests instead would be two copies of the same rule, and the copy that stops
matching is the one nobody notices.
"""

from __future__ import annotations

import pytest


def _publish_test_ids(items: list[pytest.Item]) -> None:
    """Republish each test's assigned ID as a JUnit ``<property>``.

    The ID is authored once as ``@pytest.mark.test_id("PAP_10001")``. This suite
    reports through JUnit XML only - it uses no Allure - so ``user_properties``
    is the whole of the delivery mechanism here, and it is what pytest serializes
    into ``<property name="test_id" value="..."/>`` inside each ``<testcase>``.

    The ID exists because a test's name is not a stable identity. Renaming a test
    forks its history in any store keyed on the name, silently turning one test
    with a long record into two with short ones. See
    PortfolioTestInsights/DESIGN.md section 7.

    Args:
        items: Every collected item, annotated in place. Items carrying no
            marker are left untouched.
    """
    for item in items:
        marker = item.get_closest_marker("test_id")
        if marker is None or not marker.args:
            continue
        item.user_properties.append(("test_id", str(marker.args[0])))


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Attach assigned test IDs to every collected item.

    Args:
        items: Every collected item, annotated in place.
    """
    _publish_test_ids(items)
