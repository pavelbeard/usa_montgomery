import json

import seleniumbase
import tqdm
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By


def get_pages(url: str, driver: seleniumbase.Driver) -> seleniumbase.Driver:
    driver.get(url=url)
    # switch to frame
    frame1 = driver.find_element(By.TAG_NAME, "iframe")

    driver.switch_to_frame(frame1)
    # find
    checkbox = driver.find_element(By.XPATH, '//label[contains(@class, "ctp-checkbox-label")]//input')

    # bypass captcha
    checkbox.click()

    # switch to default
    driver.switch_to.default_content()
    driver.wait_for_element(selector='//h1[contains(@class, "header page-header twocolumn-layout__title")]',
                            by="xpath", timeout=10)

    return driver

def extract_more_data():
    pass

def get_data():
    url = "https://mdmontgomeryctyweb.myvscloud.com/webtrac/web/search.html?Action=Start&SubAction=&_csrf_token=cl6M1C6T731G2O2B383B2N405W415E6H1F5G4O6T4N1L4N5B5A4V0A6N4L4N6G095O5T5G6M6U5X3J4O4V015R5L6Q4H045N4M6F6H0F6J635L5R055N4R64520Q5Q4R5A&module=AR&keyword=&keywordoption=Match+One&type=Camps&primarycode=&season=&beginmonth=6&beginmonth=7&beginmonth=8&dayoption=All&showwithavailable=No&grade=&timeblock=&gender=&spotsavailable=&bydayonly=No&beginyear=&category=REC&display=Detail&search=yes&page=1&multiselectlist_value="
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36˘",
        "Accept-Encoding": "gzip,deflate,br",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # test
    driver = seleniumbase.Driver(uc=True, headless=True)

    nodes = []
    try:

        # parse
        soup = BeautifulSoup(get_pages(url=url, driver=driver).get_page_source(), "lxml")

        pages = int(soup.find("ul", class_="paging").find_all(
            class_="paging__listitem")[-1].find("button").get("data-click-set-value"))

        for page in tqdm.trange(1, pages + 1):
            # for page in tqdm.trange(1, 2):
            if page > 1:
                new_url = url.replace("&page=1", f"&page={page}")
                driver.get(url=new_url)

                driver.wait_for_element(selector='//h1[contains(@class, "header page-header twocolumn-layout__title")]',
                                        by="xpath", timeout=10)
                soup = BeautifulSoup(driver.get_page_source(), "lxml")

            # find all nodes
            content = soup.find_all("div", class_="result-content tablecollapsecontainer")

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
                        data_title = row.attrs['data-title']
                        data[data_title] = row.text

                    if (i + 1) % 10 == 0:
                        more = row.find("ul", class_="search-more__dropdown")

                        links = [link.find("a").get("href") for link in
                                 more.find_all(class_="search-more__item")[0:2]]

                        # scrap from fees
                        driver.get(url=links[0])

                        # attempt = 5
                        while True:
                            try:
                                driver.wait_for_element(by="xpath",
                                                        selector="//h1[contains(@class, 'header group__header')]",
                                                        timeout=10)
                                break
                            except Exception:
                                driver.get(url=links[0])
                                driver.wait_for_element(by="xpath",
                                                        selector="//h1[contains(@class, 'header group__header')]",
                                                        timeout=10)


                        fees = BeautifulSoup(driver.get_page_source(), "lxml")

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

                        # scrap from enrolls
                        driver.get(url=links[1])
                        while True:
                            try:
                                driver.wait_for_element(by="xpath",
                                                        selector="//h1[contains(@class, 'header group__header')]",
                                                        timeout=10)
                                break
                            except Exception:
                                driver.get(url=links[1])
                                driver.wait_for_element(by="xpath",
                                                        selector="//h1[contains(@class, 'header group__header')]",
                                                        timeout=10)

                        enrolls = BeautifulSoup(driver.get_page_source(), "lxml")

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

                        # concatenate
                        del data['']
                        data['more'] = {
                            "fees": fees_list,
                            "enrollment_counts": enroll_counts
                        }

                        data_list.append(data)
                        data = {}

                nodes.append({
                    "activity": node_name,
                    "description": node_description,
                    "data": data_list
                })

    except Exception as ex:
        print(ex, "ERROR")
    finally:
        with open("result.json", "w") as file:
            file.write(json.dumps(nodes, indent=4))

        driver.close()
        driver.quit()


def main():
    get_data()


if __name__ == "__main__":
    main()
