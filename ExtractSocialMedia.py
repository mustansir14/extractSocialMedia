import requests
from html_to_etree import parse_html_bytes
from extract_social_media import find_links_tree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from selenium.webdriver.chrome.options import Options


headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}

input_file = "Sample.csv"
website_column = "Company website"

debug_mode = False

df = pd.read_csv(input_file)

def login_linkedin(email, password):
	chrome_options = Options()
	#chrome_options.add_argument("--headless")
	#chrome_options.add_argument("--log-level=3")
	driver = webdriver.Chrome(options=chrome_options)
	driver.get("https://linkedin.com")
	driver.find_element_by_xpath('//*[@id="session_key"]').send_keys(email)
	driver.find_element_by_xpath('//*[@id="session_password"]').send_keys(password)
	driver.find_element_by_xpath("/html/body/main/section[1]/div[2]/form/button").click()
	return driver

def get_post_linkedin(url, driver):
	try:
		post = driver.find_element_by_class_name('feed-shared-update-v2')
		time = post.find_elements_by_class_name("visually-hidden")[1].text
		text = post.find_element_by_class_name("break-words").text
		#print(url, time, text)
		return text, time
	except Exception as e:
		if debug_mode:
			print(url, str(e))
		return "", ""

def get_post_facebook(url, driver):
	try:
		driver.get(url)
		try:
			WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "_1dwg._1w_m._q7o")))
		except:
			driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
			close = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "expanding_cta_close_button")))
			time.sleep(1)
			close.click()
			WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "_1dwg._1w_m._q7o")))
		posts = driver.find_elements_by_class_name("_1dwg._1w_m._q7o")
		for post in posts:
			try:
				text = post.find_element_by_tag_name("p").text
				date = post.find_element_by_class_name("timestampContent").text
				break
			except Exception as e:
				if debug_mode:
					print(url, str(e))
				continue
		#print(url, text, date)
		return text, date
	except Exception as e:
		if debug_mode:
			print(url, str(e))
		return "", ""

def get_post_twitter(url, driver):
	try:
		driver.get(url)
		WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "css-1dbjc4n.r-16y2uox.r-1wbh5a2.r-1ny4l3l.r-1udh08x.r-1yt7n81.r-ry3cjt")))
		tweets = driver.find_elements_by_class_name("css-1dbjc4n.r-16y2uox.r-1wbh5a2.r-1ny4l3l.r-1udh08x.r-1yt7n81.r-ry3cjt")
		for tweet in tweets:
			if "Pinned Tweet" not in tweet.text:
				text = tweet.find_element_by_class_name("css-901oao.r-hkyrab.r-1qd0xha.r-a023e6.r-16dba41.r-ad9z0x.r-bcqeeo.r-bnwqim.r-qvutc0").text
				time = tweet.find_element_by_tag_name("time").text
				break
		#print(url, text, time)
		return text, time
	except Exception as e:
		if debug_mode:
			print(url, str(e))
		return "", ""

driver = login_linkedin("satellitepython123@gmail.com", "passforlinkedin")
#driver = webdriver.Chrome()

for index, row in df.iterrows():
	try:
		website = df.loc[index,website_column]
		if "https://" in website:
			res = requests.get(website, headers=headers)
		else:
			res = requests.get('https://' + website, headers=headers)
	except Exception as e:
		if debug_mode:
			print(website, str(e))
		continue
	tree = parse_html_bytes(res.content, res.headers.get('content-type'))
	links = set(find_links_tree(tree))
	#print(website, links)
	for link in links:
		if "twitter" in link:
			df.loc[index, "Twitter Link"] = link
			df.loc[index, "Latest Twitter Post"], df.loc[index, "Latest Twitter Post Date/Time"] = get_post_twitter(link, driver)
		elif "linkedin" in link:
			df.loc[index, "Linkedin Link"] = link
			df.loc[index, "Latest Linkedin Post"], df.loc[index, "Latest Linkedin Post Date/Time"] = get_post_linkedin(link, driver)
		elif "facebook" in link and "share" not in link:
			df.loc[index, "Facebook Link"] = link
			df.loc[index, "Latest Facebook Post"], df.loc[index, "Latest Facebook Post Date/Time"] = get_post_facebook(link, driver)
	print(str(index+1) + " websites done.")
	if index % 10 == 0:
		df.to_csv(input_file.replace(".csv", "_results.csv"), index=False)

df.to_csv(input_file.replace(".csv", "_results.csv"), index=False)

