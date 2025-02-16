from selenium import webdriver
from webdriver_manager.opera import OperaDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

def setup_driver():
    options = webdriver.ChromeOptions()  # Opera uses ChromeOptions since it's Chromium-based
    options.binary_location = "C:/Users/YourUsername/AppData/Local/Programs/Opera GX/launcher.exe"  # Path to Opera GX
    driver = webdriver.Chrome(OperaDriverManager().install(), options=options)
    driver.get("http://localhost:5000")
    return driver

def test_registration(driver):
    driver.get("http://localhost:5000/")
    driver.find_element(By.LINK_TEXT, "Register").click()
    
    username = driver.find_element(By.NAME, "username")
    password = driver.find_element(By.NAME, "password")
    confirm_password = driver.find_element(By.NAME, "confirm_password")
    submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    
    username.send_keys("selenium_user")
    password.send_keys("ValidPass123")
    confirm_password.send_keys("ValidPass123")
    submit.click()
    
    time.sleep(2)
    assert "Registration successful!" in driver.page_source

def test_login(driver):
    driver.get("http://localhost:5000/login")
    
    username = driver.find_element(By.NAME, "username")
    password = driver.find_element(By.NAME, "password")
    submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    
    username.send_keys("selenium_user")
    password.send_keys("ValidPass123")
    submit.click()
    
    time.sleep(2)
    assert "Login successful!" in driver.page_source

def test_generate_letter(driver):
    driver.get("http://localhost:5000/generate_letter")
    letter_input = driver.find_element(By.NAME, "letter")
    submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    
    letter_input.send_keys("A")
    submit.click()
    
    time.sleep(2)
    assert "Generating content for letter" in driver.page_source

def test_generate_sentence(driver):
    driver.get("http://localhost:5000/generate_sentence")
    text_input = driver.find_element(By.NAME, "text")
    submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    
    text_input.send_keys("HELLO WORLD")
    submit.click()
    
    time.sleep(2)
    assert "Sentence image saved to Supabase successfully" in driver.page_source

def test_invalid_registration(driver):
    driver.get("http://localhost:5000/")
    driver.find_element(By.LINK_TEXT, "Register").click()
    
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
        test_generate_letter(driver)
        test_generate_sentence(driver)
        test_invalid_registration(driver)
        print("All Selenium tests passed successfully!")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_tests()
