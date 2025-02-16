from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def setup_driver():
    options = webdriver.ChromeOptions()  
    service = Service(ChromeDriverManager().install())  
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("http://localhost:5000")  # Navigate directly to landing page
    return driver

def test_registration(driver):
    driver.get("http://localhost:5000/")  # Ensure we're on the landing page

    # Wait for the username field to appear
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))

    # Fill in the form
    username = driver.find_element(By.NAME, "username")
    password = driver.find_element(By.NAME, "password")
    confirm_password = driver.find_element(By.NAME, "confirm_password")
    submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

    username.send_keys("selenium_user")
    password.send_keys("ValidPass123")
    confirm_password.send_keys("ValidPass123")
    submit.click()

    # Wait for flash message to appear
    time.sleep(2)  # Allow form submission to process
    assert "Registration successful!" in driver.page_source  # Adjust message as needed

def test_login(driver):
    driver.get("http://localhost:5000/login")  # Login page exists in your HTML

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))

    username = driver.find_element(By.NAME, "username")
    password = driver.find_element(By.NAME, "password")
    submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

    username.send_keys("selenium_user")
    password.send_keys("ValidPass123")
    submit.click()

    gen_letter_btn = driver.find_element(By.XPATH, "//a[@href='/generate_letter' and contains(@class, 'btn-option')]")


    gen_letter_btn.click()

    time.sleep(2)
    assert "Login successful!" in driver.page_source  # Adjust message if needed

def test_invalid_registration(driver):
    driver.get("http://localhost:5000/")  # Landing page is also registration

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))

    username = driver.find_element(By.NAME, "username")
    password = driver.find_element(By.NAME, "password")
    confirm_password = driver.find_element(By.NAME, "confirm_password")
    submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

    username.send_keys("a")  # Invalid username length
    password.send_keys("ValidPass123")
    confirm_password.send_keys("ValidPass123")
    submit.click()

    time.sleep(2)
    assert "Username must be at least 3 characters long." in driver.page_source

def run_tests():
    driver = setup_driver()
    try:
        test_registration(driver)
        test_login(driver)
        test_invalid_registration(driver)
        print("All Selenium tests passed successfully!")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_tests()
