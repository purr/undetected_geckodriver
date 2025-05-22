import os
import unittest
import undetected_geckodriver


class TestPatch(unittest.TestCase):

    def setUp(self):
        overridden_path = os.environ.get("ACTIONS_FF_OVERRIDE")
        if (overridden_path is not None):
            overridden_path = os.path.abspath(overridden_path)

        self.driver = undetected_geckodriver.Firefox(
            lookup_path=overridden_path
        )
    def tearDown(self):
        self.driver.quit()

    def test_patch(self):
        """
        Tests whether or not the patch took hold at the expected location.
        This will fail on unsupported operating systems, or operating systems
        where the patch just generally fails for whatever reason.
        """
        dir = self.driver._get_undetected_firefox_path()
        patched_file = os.path.join(
            dir,
            self.driver._platform_dependent_params["xul"]
        )

        with open(patched_file, "rb") as file:
            libxul_data = file.read()

        self.assertTrue(len(libxul_data) > 0)
        self.assertFalse(
            b"webdriver" in libxul_data
        )

    def test_webdriver_gone(self):
        self.assertTrue(
            self.driver.execute_script("return navigator !== null")
        )
        self.assertIsNone(
            self.driver.execute_script("return navigator.webdriver")
        )

if __name__ == '__main__':
    unittest.main()
