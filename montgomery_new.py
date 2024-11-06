import concurrent.futures
import json

import tqdm
from selenium.webdriver.common.by import By
from seleniumbase import Driver
from bs4 import BeautifulSoup

url = "https://mdmontgomeryctyweb.myvscloud.com/webtrac/web/search.html?Action=Start&SubAction=&_csrf_token" \
      "=cl6M1C6T731G2O2B383B2N405W415E6H1F5G4O6T4N1L4N5B5A4V0A6N4L4N6G095O5T5G6M6U5X3J4O4V015R5L6Q4H045N4M6F6H0F6J635L5R055N4R64520Q5Q4R5A&module=AR&keyword=&keywordoption=Match+One&type=Camps&primarycode=&season=&beginmonth=6&beginmonth=7&beginmonth=8&dayoption=All&showwithavailable=No&grade=&timeblock=&gender=&spotsavailable=&bydayonly=No&beginyear=&category=REC&display=Detail&search=yes&page=1&multiselectlist_value="


def bypass_captcha(driver: Driver,
                   selector='//h1[contains(@class, "header page-header twocolumn-layout__title")]') -> Driver:
    driver.switch_to_frame("iframe")
    driver.find_element(By.XPATH, '//label[contains(@class, "ctp-checkbox-label")]//input').click()
    driver.switch_to.default_content()
    driver.wait_for_element(selector=selector, by="xpath", timeout=30)

    return driver


def get_main_page() -> str:
    # open page
    driver = None
    try:
        driver = Driver(uc=True, headless=True)
        driver.get(url=url)
        # bypass captcha
        hacked_page = bypass_captcha(driver)
        hacked_page_source = hacked_page.get_page_source()

        # close browser
        hacked_page.quit()
        return hacked_page_source

    except Exception as ex:
        driver.quit()
        print(ex)
        return None


def get_more_page(link):
    driver = None
    attempts = 5
    while attempts != 0:
        try:
            driver = Driver(uc=True, headless=True)
            driver.get(url=link)
            driver = bypass_captcha(driver=driver, selector="//h1[contains(@class, 'header group__header')]")
            break
        except Exception:
            driver.quit()
            print(f"Attempts: {attempts}")
            attempts -= 1
            continue

    if driver is None:
        return []

    driver.wait_for_element(by="xpath",
                            selector="//h1[contains(@class, 'header group__header')]",
                            timeout=10)

    html_page = driver.get_page_source()
    # close browser
    driver.quit()
    return html_page


def scrap_fees(link):
    # caught fees
    fees = BeautifulSoup(get_more_page(link=link), "lxml")

    # doing fees
    fees_list = []
    for fee in fees.find("p").findChildren(
            "span", class_="info-block", recursive=False
    ):
        fee_data = {}
        # label
        label = fee.findNext("label")
        fee_data["residence"] = label.text.strip().replace("Resident", "Resident ")

        # lines
        lines = label.find_next_sibling("span")

        for line in lines.find_all(class_="info-block single-line"):
            fee_data[line.find(class_="info-block-label").text.strip()] = \
                line.find("span", class_="info-block-text").text.strip()

        fees_list.append(fee_data)

    return fees_list


def scrap_enrollments(link):
    # caught enrolls
    enrolls = BeautifulSoup(get_more_page(link=link), "lxml")
    enroll_counts = {}
    for enroll in enrolls.find("p").findChildren(
            "span", class_="info-block", recursive=False):

        for line in enroll.find_all(class_="info-block single-line"):
            try:
                label_inner = line.find("label", class_="info-block-label").text.strip()
            except Exception:
                label_inner = "N/A"
            try:
                text_inner = line.find("span", class_="info-block-text").text.strip()
            except Exception:
                text_inner = "N/A"

            enroll_counts[label_inner] = text_inner

    return enroll_counts


def find_nodes(html_page: BeautifulSoup):
    nodes = []
    content = html_page.find_all("div", class_="result-content tablecollapsecontainer")
    for content_item in content:
        print("Extracting content...")
        print("*" * 20)
        try:
            node_name = content_item.find("div", class_="result-header__info").find("h2").text
        except Exception:
            node_name = "N/A"

        try:
            node_description = content_item.find("div", class_="result-header__description").text
        except Exception:
            node_description = "N/A"

        node_data = content_item.find(attrs={"id": "arwebsearch_output_table"})

        # scrap rows
        rows = [d for d in node_data.find("tbody").find_all("td", class_="label-cell")]
        data_list = []
        data = {}
        for i, row in enumerate(rows):
            print(f"Extracting more data: {i}/{len(rows)} rows...")
            if row.attrs.get("data_title") != "":
                data_title = row.attrs['data-title'].replace(" ", "_").casefold()
                data[data_title] = row.text

            if (i + 1) % 10 == 0:
                more = row.find("ul", class_="search-more__dropdown")

                links = [link.find("a").get("href") for link in
                         more.find_all(class_="search-more__item")[0:2]]

                # concatenate
                del data['']
                data['more'] = {
                    # that is working bad
                    # "fees": scrap_fees(link=links[0]),
                    # "enrollment_counts": scrap_enrollments(link=links[1])
                    "links": links
                }

                data_list.append(data)
                data = {}

        nodes.append({
            "activity": node_name,
            "description": node_description,
            "data": data_list
        })

    return nodes


def parse_page(nwork, new_url):
    print(f"Executing... {nwork}")

    attempts = 5
    hacked_page = None
    driver = None
    while attempts != 0:
        try:
            driver = Driver(uc=True, headless=True)
            driver.get(new_url)
            hacked_page = bypass_captcha(driver)
            break
        except Exception:
            # if something went wrong...
            driver.quit()
            print(f"Attempts: {attempts}")
            attempts -= 1
            continue

    if hacked_page is None:
        return "something went wrong"

    hacked_page.wait_for_element(selector='//h1[contains(@class, "header page-header twocolumn-layout__title")]',
                                 by="xpath", timeout=10)
    source = hacked_page.get_page_source()

    # source = "success!"
    soup = BeautifulSoup(source, "lxml")

    # find nodes
    result = find_nodes(html_page=soup)

    # close page
    hacked_page.quit()
    return result


def parse(html):
    soup = BeautifulSoup(html, "lxml")
    pages = int(soup.find("ul", class_="paging").find_all(
        class_="paging__listitem")[-1].find("button").get("data-click-set-value"))

    urls = [url.replace("&page=1", f"&page={page}") for page in range(1, pages + 1)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(parse_page, nwork, new_url) for nwork, new_url in enumerate(urls)]

        concurrent.futures.wait(futures)
        futures_result = [future.result() for future in futures]
        result = json.dumps(futures_result, indent=4)

        with open("result1.json", "w") as file:
            file.write(result)
            print("File has written")


def parse_links():
    with open("result1.json", "r") as file:
        json_file = json.loads(file.read())

    for entry in tqdm.tqdm(json_file):
        for item in entry:
            for data_item in item.get("data"):
                links = data_item["more"]["links"]
                print("\n", "*" * 20, data_item["activity_#"])

                # functions = (
                #     scrap_fees,
                #     scrap_enrollments
                # )
                # args = (
                #     links[0],
                #     links[1]
                # )

                fees = scrap_fees(link=links[0])
                enrolls = scrap_enrollments(link=links[1])

                del data_item["more"]["links"]

                # with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                #     futures = [executor.submit(fn, arg) for fn, arg in zip(functions, args)]
                #     concurrent.futures.wait(futures)
                #     futures_result = [future.result() for future in futures]

                data_item["more"] = {
                    "fees": fees,
                    "enrolls": enrolls
                }

                print("\n", data_item["more"], "\n", "*" * 20)
                # if "more" in item and "links" in item["more"]:
                #     print(data_item)

    with open("result1.json", "w") as file:
        file.write(json.dumps(json_file, indent=4))



def main():
    # html = get_main_page()
    # if html is None:
    #     return
    #
    # parse(html=html)
    parse_links()


if __name__ == "__main__":
    main()
