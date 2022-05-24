# import json
#
# import requests
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# import time
# import json
# from bs4 import BeautifulSoup


def get_index(url="https://vk.com/decanat_rk"):
    s = Service('C:\\Users\\bushu\\PycharmProjects\\Project\\chromedriver\\chromedriver.exe')
    driver = webdriver.Chrome(service=s)

    try:
        driver.get(url=url)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        button_not_now = driver.find_element(by=By.CLASS_NAME, value="JoinForm__notNowLink")
        button_not_now.click()

        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        data = driver.page_source
        with open("data/index.html", "w", encoding="utf-8") as file:
            file.write(data)
        time.sleep(2)

    except Exception as ex:
        print(ex)
    finally:
        driver.close()
        driver.quit()


def get_message():
    with open("data/index.html", encoding="utf-8") as f:
        src = f.read()

    with open("data/all_posts.json", "r") as f:
        all_posts = json.load(f)

    soup = BeautifulSoup(src, "html.parser")
    page_wall_posts = soup.find_all("div", class_="post")

    new_posts = {}
    last_posts = []

    # Проверка первого на закрепление
    wall_post = page_wall_posts[0]
    fixed = False
    if 'post_fixed' in wall_post.attrs['class']:
        fixed = True

    for wall_post in page_wall_posts:
        post_id = wall_post["id"].split('_')[1]
        last_posts.append(post_id)

        if post_id not in all_posts.keys():
            wall_text = wall_post.find("div", class_="wall_text")

            if wall_text is not None:
                wall_post_cont = wall_text.find("div", class_="wall_post_cont")

                if len(wall_post_cont.contents) != 0:
                    new_posts[post_id] = {}
                    new_posts[post_id]["Fixed"] = fixed

                    copy_quote_url = ''

                    copy_quote = wall_text.find("div", class_="copy_quote")

                    page_post_sized_thumbs = wall_post_cont.find("div", class_="page_post_sized_thumbs")
                    page_doc_row = wall_post_cont.find("div", class_="page_doc_row")
                    wall_post_text = wall_post_cont.find("div", class_="wall_post_text")
                    wall_post_more = wall_post_cont.find("a", class_="wall_post_more")
                    wall_post_text.name = "a"

                    for img in wall_post_text.find_all("img"):
                        alt = img.attrs["alt"]
                        img.replace_with(alt)

                    if wall_post_more is not None:
                        wall_post_more.find_previous().decompose()
                        wall_post_more.decompose()
                        wall_post_text.span.unwrap()

                    for br in wall_post_text.find_all("br"):
                        br.replace_with('\n')

                    if page_post_sized_thumbs is not None:
                        photo = page_post_sized_thumbs.a["style"]
                        photo = photo.split('(')[1]
                        new_posts[post_id]["wall_post_photo"] = photo[0:-2]
                    else:
                        new_posts[post_id]["wall_post_photo"] = None

                    if page_doc_row is not None:
                        doc = page_doc_row.a.get("href")
                        new_posts[post_id]["page_doc_row"] = "https://vk.com" + doc
                    else:
                        new_posts[post_id]["page_doc_row"] = None

                    if copy_quote is not None:
                        copy_post_header = copy_quote.find("a", class_="copy_author")
                        copy_quote_url = f"\n\n<a href='https://vk.com{copy_post_header.get('href')}?w=wall" \
                                         f"{copy_post_header['data-post-id']}'>{copy_post_header.get_text()}</a>"

                    new_posts[post_id]["wall_post_text"] = str(wall_post_text) + copy_quote_url

    with open("data/new_posts.json", 'w', encoding="utf-8") as f:
        json.dump(dict(sorted(new_posts.items(), key=lambda x: x[0])), f, indent=4, ensure_ascii=False)
    with open("data/last_posts.json", 'w') as f:
        json.dump(last_posts, f)

    return fixed


def get_page_avatar_img():
    with open("data/index.html", encoding="utf-8") as file:
        src = file.read()

    soup = BeautifulSoup(src, "lxml")
    page_avatar_img = soup.find("img", class_="page_avatar_img")["src"]
    photo = requests.get(page_avatar_img)
    photo_path = "data/page_avatar.png"

    with open(photo_path, 'rb') as f:
        last_photo = f.read()

    if last_photo != photo.content:
        with open(photo_path, "wb") as f:
            f.write(photo.content)
        return True
    return False


def get_page_doc(wall_text):
    doc_title = wall_text.find('a', class_="page_doc_title").get_text()
    doc_href = wall_text.find('a', class_="page_doc_title").get("href")

    doc = requests.get(doc_href)
    doc_path = "data/" + doc_title
    with open(doc_path, "wb") as f:
        f.write(doc.content)

    return doc_path


if __name__ == '__main__':
    # get_index()
    get_message()
    # get_page_avatar_img()
