"""Aleksandr Polskiy this script takes a list of experimental_tests result tuples, parses it
and determines if experimental_tests are flaky depending on whether the following
combinations of experimental_tests results are present PASS and FAIL, PASS and SKIP,
FAIL and SKIP, if they are tests need to be fixed in order to run. SKIPs in themselves
are treated same as FAIL, as experimental_tests FAILS to setup and execute.
List of flaky tests is printed in the end"""
import unittest

def print_flaky_tests(input:list[tuple]):
    """Function extracts experimental_tests results form a list of tuples
    and appends them to dictionary, while evaluating if tests are flaky"""
    testresults={}
    flaky_tests=set()
    for result in input:
        if not testresults[result[0]]["FLAKY"]==True:
            testresults[result[0]] = testresults.get(result[0],{})
            testresults[result[0]]["PASS"] = testresults.get(result[0]).get("PASS", 0)
            testresults[result[0]]["FAIL"] = testresults.get(result[0]).get("FAIL",0)
            testresults[result[0]]["SKIP"] = testresults.get(result[0]).get("SKIP", 0)
            testresults[result[0]]["FLAKY"] = testresults.get(result[0]).get("FLAKY", False)

        testresults[result[0]][result[1]]+=1

        if testresults[result[0]]["FLAKY"] == False:
            flaky = (testresults[result[0]]["FAIL"] > 0)+(testresults[result[0]]["PASS"] > 0)+(testresults[result[0]]["SKIP"] > 0)
            if flaky >=2:
                print(f"{result[0]} \n")
                flaky_tests.add(result[0])
                testresults[result[0]]["FLAKY"] = True

    return flaky_tests, testresults

class TestFlaky(unittest.TestCase):
    test_results = [
    ("test_login_page", "PASS"),
    ("test_page_loaded", "PASS"),
    ("test_links_work","FAIL"),
    ("test_visit_about_page","SKIP"),
    ("test_api_v1_auth", "FAIL"),
    ("test_login_page", "SKIP"),
    ("test_db_connection", "PASS"),
    ("test_api_v1_auth", "PASS"),
    ("test_ui_header", "FAIL"),
    ("test_visit_about_page", "SKIP"),
    ("test_login_page", "PASS"),
    ("test_api_v1_auth", "FAIL"),
    ("test_links_work", "FAIL"),
    ("test_page_loaded", "PASS"),
    ("test_skip_fail_added", "SKIP"),
    ("test_skip_fail_added", "FAIL"),
    ("test_pass_skip_added", "PASS"),
    ("test_pass_skip_added", "SKIP"),
    ]
    #flaky_list = print_flaky_tests(test_results)
    flaky_list, test_statistics = print_flaky_tests(test_results)

    print(f"Following tests are flaky: {flaky_list}")
    assert len(flaky_list) > 0, "No flaky tests found"

if __name__=="__main__":
    test_results = [
    ("test_login_page", "PASS"),
    ("test_page_loaded", "PASS"),
    ("test_links_work","FAIL"),
    ("test_visit_about_page","SKIP"),
    ("test_api_v1_auth", "FAIL"),
    ("test_login_page", "SKIP"),
    ("test_db_connection", "PASS"),
    ("test_api_v1_auth", "PASS"),
    ("test_ui_header", "FAIL"),
    ("test_visit_about_page", "SKIP"),
    ("test_login_page", "PASS"),
    ("test_api_v1_auth", "FAIL"),
    ("test_links_work", "FAIL"),
    ("test_page_loaded", "PASS"),
    ("test_skip_fail_added", "SKIP"),
    ("test_skip_fail_added", "FAIL"),
    ("test_pass_skip_added", "PASS"),
    ("test_pass_skip_added", "SKIP"),
    ]
    #flaky_list = print_flaky_tests(test_results)
    print(f"Following tests are flaky: {print_flaky_tests(test_results)}")



