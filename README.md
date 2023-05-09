# WebSDRcat

Minimal python code, demonstrating bidirectional synchronization of a radio with a WebSDR in a browser.

This requires to install

- hamlib (https://hamlib.github.io/hamlib/), which is used to control the radio with CAT commands, by
      . rigctld (https://hamlib.github.io/hamlib/rigctld.1.html)
      . rigctl (https://hamlib.github.io/hamlib/rigctl.1.html)

- Python (https://www.python.org/), which is used to run this script, and the following Python packages
- Selenium (https://www.selenium.dev/), which is used to control the browser
- the Chrome driver (https://chromedriver.chromium.org/downloads), which is used to control the Chrome browser
- the Chrome browser (https://www.google.com/chrome/)
- a known WebSDR (tested so far only with http://websdr.ewi.utwente.nl:8901/)


9 May 2023 - Michele Giugliano, PhD (iv3ifz)
