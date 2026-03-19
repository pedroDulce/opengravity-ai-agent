# screenshot_dashboard.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
import time

def tomar_screenshot_dashboard(url="http://localhost:8501", output="dashboard.png"):
    """Toma una captura del dashboard"""
    
    # Configurar Chrome en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get(url)
        time.sleep(5)  # Esperar a que cargue
        
        # Tomar screenshot
        driver.save_screenshot(output)
        
        # Recortar para mostrar solo la parte importante
        img = Image.open(output)
        width, height = img.size
        img_cropped = img.crop((0, 0, width, 800))  # Ajustar según necesites
        img_cropped.save(output)
        
        print(f"✅ Screenshot guardado: {output}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    tomar_screenshot_dashboard()