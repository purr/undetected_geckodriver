import os
import unittest
import undetected_geckodriver

class TestPatch(unittest.TestCase):
    def test_patch(self):
        driver = undetected_geckodriver.Firefox()
        dir = driver._get_undetected_firefox_path()
        patched_file = os.path.join(
            dir,
            driver._platform_dependent_params["xul"]
        )

        with open(patched_file, "rb") as file:
            libxul_data = file.read()

        self.assertFalse(
            b"webdriver" in libxul_data
        )

        driver.close()

if __name__ == '__main__':
    unittest.main()
