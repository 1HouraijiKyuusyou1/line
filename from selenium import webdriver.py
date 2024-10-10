from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time  # 確保導入time模組
from itertools import product  # 使用 product 函數來產生多重組合

def initialize_driver():
    driver = webdriver.Chrome()
    driver.get("https://sss.must.edu.tw/RWD_CosInfo/")
    return driver

def search_course(driver, course_name):
    try:
        search = driver.find_element(By.NAME, "cosn")
        search.send_keys(course_name)
        search.send_keys(Keys.RETURN)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "dynamic-table"))
        )
    except Exception as e:
        print(f"搜索課程時發生錯誤: {e}")

def scrape_courses(driver):
    courses = []
    page_count = 0  # 初始化頁面計數器

    while page_count < 1:  # 限制最多翻頁兩次
        try:
            table = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "dynamic-table"))
            )
            rows = table.find_elements(By.TAG_NAME, "tr")

            for row in rows[1:]:  # 跳過標題行
                cols = row.find_elements(By.TAG_NAME, "td")
                course_info = {
                    "課名": cols[2].text,
                    "開課班級": cols[4].text,
                    "授課教師": cols[10].text,
                    "上課時間": cols[12].text,
                }
                # 檢查上課時間是否為 ---
                if course_info["上課時間"] == "---":
                    print(f"跳過課程: {course_info['課名']}，因為上課時間為 ---")
                    continue  # 跳過此課程
                
                courses.append(course_info)

            try:
                next_button = driver.find_element(By.LINK_TEXT, "下一頁")
                if "disabled" in next_button.get_attribute("class"):
                    print("已經到達最後一頁，無法翻頁")
                    break
                next_button.click()
                time.sleep(4)  # 等待新頁面加載
                page_count += 1  # 增加頁面計數器
            except Exception as e:
                print(f"翻頁時發生錯誤: {e}")
                break

        except Exception as e:
            print(f"擷取課程時發生錯誤: {e}")
            break
    
    return courses

def print_course(course):
    print("課名: {}\n開課班級: {}\n授課教師: {}\n上課時間: {}\n".format(
        course["課名"],
        course["開課班級"],
        course["授課教師"],
        course["上課時間"]
    ))
    print("-" * 20)

def parse_class_times(class_times):
    parsed_times = []
    for time_slot in class_times.split(", "):
        if time_slot.strip() == "---":
            continue

        try:
            day, period = time_slot.split("-")
            parsed_times.append((int(day), int(period)))
        except ValueError:
            print(f"時間格式錯誤: {time_slot}")

    return parsed_times 

def check_time_conflict(course1, course2):
    times1 = parse_class_times(course1["上課時間"])
    times2 = parse_class_times(course2["上課時間"])

    for day1, period1 in times1:
        for day2, period2 in times2:
            if day1 == day2 and period1 == period2:
                return True
    return False

def find_matching_courses(categories):
    matched_courses = []
    
    # 利用 product 函數生成每個類別中的所有組合
    for course_combo in product(*categories):
        day_sets = [set(day for day, _ in parse_class_times(course["上課時間"])) for course in course_combo]

        # 確保每門課至少有一天是重疊的
        if all(day_sets[0].intersection(day_set) for day_set in day_sets[1:]):
            # 確保課程之間無時間衝突
            if all(not check_time_conflict(course1, course2) for i, course1 in enumerate(course_combo) for course2 in course_combo[i+1:]):
                matched_courses.append(course_combo)

    return matched_courses

# 主程式碼
n = int(input("請輸入想要查找的課程類別數量："))
categories = [[] for _ in range(n)]  # N 類課程的列表

# 輸入 N 類課程
for i in range(n):
    driver = initialize_driver()
    course_name = input(f"請輸入第 {i + 1} 類課程名稱：")
    search_course(driver, course_name)
    categories[i] = scrape_courses(driver)
    driver.close()

# 尋找符合條件的課程
matched_course_combinations = find_matching_courses(categories)

print("\n推薦的課程組合（每一門課程來自不同類別且無時間衝突）：")
for idx, course_combo in enumerate(matched_course_combinations, start=1):
    print(f"推薦的課程組合 {idx}:")
    for course in course_combo:
        print_course(course)