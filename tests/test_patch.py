import os
import unittest
import undetected_geckodriver

class TestPatch(unittest.TestCase):
    def test_patch(self):
        """
        Tests whether or not the patch took hold at the expected location.
        This will fail on unsupported operating systems, or operating systems
        where the patch just generally fails for whatever reason.
        """
        overridden_path = os.environ.get("ACTIONS_FF_OVERRIDE")
        driver = undetected_geckodriver.Firefox(
            lookup_path=overridden_path
        )
        dir = driver._get_undetected_firefox_path()
        patched_file = os.path.join(
            dir,
            driver._platform_dependent_params["xul"]
        )

        with open(patched_file, "rb") as file:
            libxul_data = file.read()

        self.assertTrue(len(libxul_data) > 0)
        self.assertFalse(
            b"webdriver" in libxul_data
        )

        driver.close()

if __name__ == '__main__':
    unittest.main()
