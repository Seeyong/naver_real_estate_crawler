'''
실거래가
multiprocessing
엑셀파일 추출 완료 후 텔레그램 메시징
시 vs 도 unmatched resolvingv ex) 성남시 분당구 분당

2018. 10. 23 Developed by Seeyong
Naver Officetel Crawler
V 1.1.5
'''
'''
오피스텔 : rletTypeCd=A02
매매 : tradeTypeCd=A1
Highest Year of School Completed : hscpTypeCd=A02
법정동 코드 API http://juso.seoul.go.kr/openapi/helps/SearchApi_jibun.aspx
http://www.code.go.kr/
'''

# Import Libraries
import sys
from urllib import request as rq
from bs4 import BeautifulSoup as bs
from datetime import datetime
import pandas as pd
from tqdm import tqdm
from time import sleep
import random
from lxml.html import fromstring
import requests
from itertools import cycle
import socket

# Get city/district/village list
def getRegionList(df_village_code):
    # get 동 list
    village_lists = list(df_village_code['법정동명'].str.split(' '))
    village_list = [x[-1] for x in village_lists]

    # get 도시 list
    city_list = [x[0] for x in village_lists]

    # get 구 list : 제주특별자치도의 경우 제주시&서귀포시
    district_list = []
    for village in village_lists:
        if len(village) > 1:
            district_list.append(village[1])
        else:
            district_list.append(village[0])

    return city_list, district_list, village_list

# Get province from user
def getProvince(df_village_code):

    def getCityNumber(df_village_code):
        # city selection process
        city_number = "0.EXIT |\n"
        city_dict = {0: 0}
        city_list = list(df_village_code["도시"].unique())

        for number, city in enumerate(city_list):
            if (number + 1) % 3 == 0:
                city_number += str(number + 1) + '.' + city + ' | \n'
            else:
                city_number += str(number + 1) + '.' + city + ' | '

            city_dict[number + 1] = city

        while True:
            try:
                province_num = int(input("원하는 도시의 번호를 선택해주세요\n" + city_number))

                if province_num == 0:
                    print("프로그램이 종료되었습니다.")
                    sys.exit()
                else:
                    province = city_dict[province_num]
                    return province

            except ValueError as e:
                print("숫자로 입력해주세요.")
                continue
            except KeyError as k:
                print("0 ~ %d 사이의 숫자로 입력해주세요."%(len(city_dict)-1))
                continue
            break

        return province

    def getDistNumber(df_village_code, province):
        # district selection process
        district_number = "0.도시 다시 선택하기 |\n"
        district_dict = {}
        district_list = list(df_village_code[df_village_code['도시'] == province]["구/군"].unique())
        district_list

        for number, district in enumerate(district_list):
            if (number + 1) % 3 == 0:
                district_number += str(number + 1) + '.' + district + ' | \n'
            else:
                district_number += str(number + 1) + '.' + district + ' | '

            district_dict[number + 1] = district

        while True:
            try:
                district_num = int(input("원하는 군/구의 번호를 선택해주세요\n" + district_number))

                if district_num == 0:
                    province = getCityNumber(df_village_code)
                    district = getDistNumber(province)
                    return district, province
                else:
                    district = district_dict[district_num]
            except ValueError as e:
                print("숫자로 입력해주세요.")
                continue
            except KeyError as k:
                print("0 ~ %d 사이의 숫자로 입력해주세요." % (len(district_dict) - 1))
                continue
            break

        return district, province

    def getVillageNumber(df_village_code, district, province):
        # village selection process
        village_number = "0.구/군 다시 선택하기 |\n"
        village_dict = {}
        village_list = list(df_village_code[df_village_code['구/군'] == district]["동"].unique())
        village_list

        for number, village in enumerate(village_list):
            if (number + 1) % 3 == 0:
                village_number += str(number + 1) + '.' + village + ' | \n'
            else:
                village_number += str(number + 1) + '.' + village + ' | '

            village_dict[number + 1] = village

        while True:
            try:
                village_num = int(input("원하는 동의 번호를 선택해주세요\n" + village_number))
                if village_num == 0:
                    district, province = getDistNumber(df_village_code, province)
                    village = getVillageNumber(df_village_code, district, province)
                    return village
                else:
                    village = village_dict[village_num]
            except ValueError as e:
                print("숫자로 입력해주세요.")
                continue
            except KeyError as k:
                print("1 ~ %d 사이의 숫자로 입력해주세요." % (len(village_dict) - 1))
                continue
            break

        return village

    province = getCityNumber(df_village_code)
    district, province = getDistNumber(df_village_code, province)
    village = getVillageNumber(df_village_code, district, province)

    return village

# get free proxies(IP address:PORT)
def getProxies():
    # set url elem&soup
    url = 'https://www.proxynova.com/proxy-server-list/country-kr/'
    url_elem = rq.urlopen(url).read()
    url_soup = bs(url_elem, 'html.parser')
    ips = url_soup.find('div', {'id': 'bla'}).find_all('abbr')
    ports = url_soup.find_all('td')
    proxy_speeds = url_soup.find_all('small')

    result = []
    for i in range(len(ips)):
        if i < 12:
            # ip title
            title = ips[i]['title'] + ':'

            # port number
            port = ports[1 + (i * 8)].text.replace('\n', '')

            # proxy speed
            speed = int(proxy_speeds[i].text.split(' ')[0])

            result.append([title, port, speed])
        else:
            # ip title
            title = ips[i]['title'] + ':'

            # port number
            port = ports[2 + (i * 8)].text.replace('\n', '')

            # proxy speed
            speed = int(proxy_speeds[i].text.split(' ')[0])

            result.append([title, port, speed])

    # create to DataFrame
    result = pd.DataFrame(result)
    column_list = ['IP', 'PORT', 'SPEED']
    result
    result.columns = column_list
    result = result[~result['IP'].str.contains('amazon')]
    result['IP:PORT'] = result['IP'] + result['PORT']

    # filter IP's speed exceed 1500
    result = result[result['SPEED'] > 1500]

    # get another ip:port every cycle
    ip_ports = cycle(set(result['IP:PORT']))
    ip_ports

    return ip_ports

# Get contents_urls
def getContentsUrls(village, df_village_code):
    root_url = "https://land.naver.com/"
    searching_url_dict = {}
    max_page = 20

    city = df_village_code[df_village_code["동"] == village]['도시'].values[0]
    district = df_village_code[df_village_code["동"] == village]['구/군'].values[0]
    code = df_village_code[df_village_code["동"] == village]['법정동코드'].values[0]
    for page_number in range(1, max_page + 1):

            # tradeType = {'rent' : 'B2', 'purchase' : 'A1'}
            # propertyType = {'officetel' : 'A02', 'store' : 'D02', 'office' : 'D01', 'factory' : 'E02'}

            # url for factory
            # basic_url = 'https://land.naver.com/article/articleList.nhn?rletTypeCd=E02&tradeTypeCd=B2&rletNo=&cortarNo={code}&hscpTypeCd=E02%3AE04&mapX=&mapY=&mapLevel=&page={page_number}&articlePage=&ptpNo=&rltrId=&mnex=&bildNo=&articleOrderCode=&cpId=&period=&prodTab=&atclNo=&atclRletTypeCd=&location=2089&bbs_tp_cd=&sort=&siteOrderCode=&schlCd=&tradYy=&exclsSpc=&splySpcR=&cmplYn=#_content_list_target'.format(
            #     code=code, page_number=page_number)

            # url for office
            basic_url = 'https://land.naver.com/article/articleList.nhn?rletTypeCd=D01&tradeTypeCd=B2&rletNo=&cortarNo={code}&hscpTypeCd=D01&mapX=&mapY=&mapLevel=&page={page_number}&articlePage=&ptpNo=&rltrId=&mnex=&bildNo=&articleOrderCode=&cpId=&period=&prodTab=&atclNo=&atclRletTypeCd=&location=3409&bbs_tp_cd=&sort=&siteOrderCode=&schlCd=&tradYy=&exclsSpc=&splySpcR=&cmplYn=#_content_list_target'.format(
                code=code, page_number=page_number)

            # url for store
            # basic_url = 'https://land.naver.com/article/articleList.nhn?rletTypeCd=D02&tradeTypeCd=B2&rletNo=&cortarNo={code}&hscpTypeCd=D02&mapX=&mapY=&mapLevel=&page={page_number}&articlePage=&ptpNo=&rltrId=&mnex=&bildNo=&articleOrderCode=&cpId=&period=&prodTab=&atclNo=&atclRletTypeCd=&location=2089&bbs_tp_cd=&sort=&siteOrderCode=&schlCd=&tradYy=&exclsSpc=&splySpcR=&cmplYn=#_content_list_target'.format(
            #     code=code, page_number=page_number)

            # url for Officetel
            # basic_url = 'https://land.naver.com/article/articleList.nhn?rletTypeCd=A02&tradeTypeCd=A1&hscpTypeCd=A02&cortarNo={code}&articleOrderCode=&siteOrderCode=&cpId=&mapX=&mapY=&mapLevel=&minPrc=&maxPrc=&minWrrnt=&maxWrrnt=&minLease=&maxLease=&minSpc=&maxSpc=&subDist=&mviDate=&hsehCnt=&rltrId=&mnex=&mHscpNo=&mPtpRange=&mnexOrder=&location=1924&ptpNo=&bssYm=&schlCd=&cmplYn=&page={page_number}#_content_list_target'.format(
            #     code=code, page_number=page_number)
            basic_url = rq.Request(basic_url,
                                   headers={
                                       'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'
                                   })
            basic_html = rq.urlopen(basic_url).read()
            basic_soup = bs(basic_html, "html.parser")
            basic_elems = basic_soup.find_all("span", {"class": "btn_naverlink"})

            # ban 방지용 : 페이지가 3의 배수일 때 쉼
            if page_number % 3 == 0:
                # sleeptime = random.randint(5, 10)
                sleep(25)

            # 마지막 페이징에서 break
            if basic_elems == []:
                break

            else:
                for i in range(len(basic_elems)):
                    estate_url = root_url + basic_elems[i].find("a").attrs["href"]
                    searching_url_dict[estate_url] = [city, district, village]

    return searching_url_dict

# Get contents
def getContentsTitle(searching_soup):
    # title
    try:
        title_elem = searching_soup.find("h2", {"class":"t_adr"})
        title = title_elem.text
    except (ValueError, AttributeError, IndexError) as e:
        title = "-"
    return title

def getContentsPrice(searching_soup):
    # get price
    try:
        rate_basic = searching_soup.find_all("p", {"class":"rate_info"})
        price = rate_basic[1].find_all("span")[0].text
        price = int(price.split("만")[0].replace(",",""))
    except (ValueError, AttributeError, IndexError) as e:
        price = 0
    return price

def getContractArea(searching_soup):
    # get contract area
    try:
        rate_basic = searching_soup.find_all("p", {"class":"rate_info"})
        areas = ""
        area = rate_basic[0].find_all("span")
        for i in range(len(area)):
            areas += area[i].text

        areas_list = areas.split('/')
        contract_area = float(areas_list[0])
    except (ValueError, AttributeError, IndexError) as e:
            contract_area = 0
    return contract_area

def getExclusiveArea(searching_soup):
    # get exclusive area
    try:
        rate_basic = searching_soup.find_all("p", {"class":"rate_info"})
        areas = ""
        area = rate_basic[0].find_all("span")
        for i in range(len(area)):
            areas += area[i].text

        areas_list = areas.split('/')
        exclusive_area = float(areas_list[1].split('㎡')[0])
    except (ValueError, AttributeError, IndexError) as e:
            exclusive_area = 0
    return exclusive_area

def getSpecificFloor(searching_soup):
    # specific floor
    try:
        summary_basic = searching_soup.find("div", {"class":"view_info"}).find_all("div", {"class":"inner"})
        floors = summary_basic[1].text.split("/")
        specific_floor = int(floors[0])
    except (ValueError, AttributeError, IndexError) as e:
        specific_floor = 0
    return specific_floor

def getTotalFloor(searching_soup):
    # total floor
    try:
        summary_basic = searching_soup.find("div", {"class":"view_info"}).find_all("div", {"class":"inner"})
        floors = summary_basic[1].text.split("/")
        total_floor = int(floors[1].split("층")[0])
    except (ValueError, AttributeError, IndexError) as e:
        total_floor = 0
    return total_floor

def getRooms(searching_soup):
    # rooms
    try:
        summary_basic = searching_soup.find("div", {"class":"view_info"}).find_all("div", {"class":"inner"})
        room_and_bath = summary_basic[3].text.split("/")
        rooms = int(room_and_bath[0])
    except (ValueError, AttributeError, IndexError) as e:
        rooms = 0
    return rooms

def getBaths(searching_soup):
    # baths
    try:
        summary_basic = searching_soup.find("div", {"class":"view_info"}).find_all("div", {"class":"inner"})
        room_and_bath = summary_basic[3].text.split("/")
        baths = int(room_and_bath[1].split('개')[0])
    except (ValueError, AttributeError, IndexError) as e:
        baths = 0
    return baths

def getLoanAmount(searching_soup):
    # loan amount
    try:
        summary_basic = searching_soup.find("div", {"class":"view_info"}).find_all("div", {"class":"inner"})
        loan_amount = int(summary_basic[5].text.split("만")[0].replace(',',''))
    except (ValueError, AttributeError, IndexError) as e:
        loan_amount = 0
    return loan_amount

def getMoveable(searching_soup):
    # moveable
    try:
        summary_basic = searching_soup.find("div", {"class":"view_info"}).find_all("div", {"class":"inner"})
        moveable = summary_basic[7].text
    except (ValueError, AttributeError, IndexError) as e:
        moveable = "-"
    return moveable

def getAdminCost(searching_soup):
    # administration cost
    try:
        summary_basic = searching_soup.find("div", {"class":"view_info"}).find_all("div", {"class":"inner"})
        administration_cost = int(summary_basic[9].text.split("원")[0].strip().replace(",",""))
    except (ValueError, AttributeError, IndexError) as e:
        administration_cost = 0
    return administration_cost

def getDepositAmount(searching_soup):
    # deposit amount
    try:
        # for purchasing
        # summary_basic = searching_soup.find("div", {"class":"view_info"}).find_all("div", {"class":"inner"})
        # deposit_and_rentfee = summary_basic[11].text.split("/")
        # deposit = int(deposit_and_rentfee[0].replace(',','').strip())

        # for rent
        rate_basic = searching_soup.find_all("p", {"class": "rate_info"})
        deposit_and_rentfee = rate_basic[1].text.replace('\n', '').replace('만원', '').split('/')
        deposit = int(deposit_and_rentfee[0].replace(',', ''))
    except (ValueError, AttributeError, IndexError) as e:
        deposit = 0
    return deposit

def getRentFee(searching_soup):
    # rent fee
    try:
        # for purchasing
        # summary_basic = searching_soup.find("div", {"class":"view_info"}).find_all("div", {"class":"inner"})
        # deposit_and_rentfee = summary_basic[11].text.split("/")
        # rent_fee = int(deposit_and_rentfee[1].split("만")[0].strip().replace(',',''))

        # for rent
        rate_basic = searching_soup.find_all("p", {"class": "rate_info"})
        deposit_and_rentfee = rate_basic[1].text.replace('\n', '').replace('만원', '').split('/')
        rent_fee = int(deposit_and_rentfee[1].replace(',', ''))
    except (ValueError, AttributeError, IndexError) as e:
        rent_fee = 0
    return rent_fee

def getChar(searching_soup):
    # characteristics
    try:
        summary_basic = searching_soup.find("div", {"class":"view_info"}).find_all("div", {"class":"inner"})
        characteristics = summary_basic[13].text
    except (ValueError, AttributeError, IndexError) as e:
        characteristics = "-"
    return characteristics

def getInterm(searching_soup):
    # intermediary
    try:
        summary_basic = searching_soup.find("div", {"class":"view_info"}).find_all("div", {"class":"inner"})
        intermediary = summary_basic[15].text
    except (ValueError, AttributeError, IndexError) as e:
        intermediary = "-"
    return intermediary

def getUtilityBills(searching_soup):
    # utility bills
    try:
        tax_soup = searching_soup.find_all('ul', {"class": "lst_tax"})[1]
        replaceable_chr_list = ['\\', 'n', 't', ',', ' ', '약', '원']
        utility_bills = tax_soup.find("strong", {"class": "highlight"}).text

        for i in replaceable_chr_list:
            utility_bills = utility_bills.replace(i, '').strip()

        utility_bills = int(utility_bills)

    except (ValueError, AttributeError, IndexError) as e:
        utility_bills = 0

    return utility_bills

def getIntermPay(searching_soup):
    # intermediate pay
    try:
        intermediate_soup = searching_soup.find_all('ul', {"class":"lst_tax"})[0]
        intermediate_pay = int(intermediate_soup.find("strong").text)
    except (ValueError, AttributeError, IndexError) as e:
        intermediate_pay = 0
    return intermediate_pay

def getCompletionDate(searching_soup):
    # completion date
    try:
        completion_elem = searching_soup.find("div", {"class":"div_detail"}).find_all("div", {"class":"inner"})
        completion_date = datetime.strptime(completion_elem[-1].text, '%Y.%m.')
    except (ValueError, AttributeError, IndexError) as e:
        completion_date = datetime(1900, 1, 1)
    return completion_date

def getHouseholds(searching_soup):
    # all households
    try:
        detail_soup = searching_soup.find('div', {'class','div_detail'}).find_all('div', {'class', 'inner'})
        households = int(detail_soup[3].text.split(' ')[0])
    except (ValueError, AttributeError, IndexError) as e:
        households = 0
    return households

def getParkingNumber(searching_soup):
    # parking number
    try:
        detail_soup = searching_soup.find('div', {'class','div_detail'}).find_all('div', {'class', 'inner'})
        parkingnumber = int(detail_soup[5].text.split(' ')[0])
    except (ValueError, AttributeError, IndexError) as e:
        parkingnumber = 0
    return parkingnumber

# Create an Excel file
def createExcelFile(df, province):
    today = datetime.today()
    str_today = str(today.year) + str(today.month) + str(today.day)
    # change file name along with PropertyType
    file_name = province + '_' + "Office_" + str_today + ".xlsx"
    sheet_name = province + "_" + str_today
    writer = pd.ExcelWriter(file_name)
    df.to_excel(writer, sheet_name)
    writer.save()

# get info list
def getInfoList(url, searching_url_dict):
    try:
        url_user = rq.Request(url,
                              headers={
                                  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'
                              })
        searching_html = rq.urlopen(url_user).read()
        searching_soup = bs(searching_html, "html.parser")

        # get region info
        city = searching_url_dict[url][0]
        district = searching_url_dict[url][1]
        village = searching_url_dict[url][2]

        # get contents
        title = getContentsTitle(searching_soup)
        price = getContentsPrice(searching_soup)
        contract_area = getContractArea(searching_soup)
        exclusive_area = getExclusiveArea(searching_soup)
        specific_floor = getSpecificFloor(searching_soup)
        total_floor = getTotalFloor(searching_soup)
        rooms = getRooms(searching_soup)
        baths = getBaths(searching_soup)
        loan_amount = getLoanAmount(searching_soup)
        moveable = getMoveable(searching_soup)
        administration_cost = getAdminCost(searching_soup)
        deposit = getDepositAmount(searching_soup)
        rent_fee = getRentFee(searching_soup)
        characteristics = getChar(searching_soup)
        intermediary = getInterm(searching_soup)
        utility_bills = getUtilityBills(searching_soup)
        intermediate_pay = getIntermPay(searching_soup)
        completion_date = getCompletionDate(searching_soup)
        households = getHouseholds(searching_soup)
        parkingnumber = getParkingNumber(searching_soup)

        info_list = [city, district, village, title, price, contract_area, exclusive_area, specific_floor, total_floor,
                     rooms, baths, loan_amount, moveable,
                     administration_cost, deposit, rent_fee, characteristics, intermediary, utility_bills, intermediate_pay,
                     completion_date, households, parkingnumber, url]
        return info_list

    except:
        pass

# Create a DataFrame
def getResult(searching_url_dict, proxy_pool):
    # create null list for DataFrame
    result = []

    for url in tqdm(searching_url_dict):
        # under 30 urls -> use own IP address
        if len(searching_url_dict) <= 30:
            info_list = getInfoList(url, searching_url_dict)
            result.append(info_list)

        else:
            while True:
                try:
                    # get a Free proxy from the pool
                    proxy = next(proxy_pool)
                    handler = rq.ProxyHandler({'http': proxy, "https": proxy})
                    opener = rq.build_opener(handler)
                    rq.install_opener(opener)
                    print(proxy)

                    info_list = getInfoList(url, searching_url_dict)
                    result.append(info_list)
                except:
                    # use my own proxy
                    handler = rq.ProxyHandler()
                    opener = rq.build_opener(handler)
                    rq.install_opener(opener)
                    print(socket.gethostbyname(socket.gethostname()))

                    info_list = getInfoList(url, searching_url_dict)
                    result.append(info_list)
                break

    result = [x for x in result if x is not None]

    # Create result DataFrame
    result = pd.DataFrame(result)

    return result

# Adjust the DataFrame
def addCalcColumns(df):
    interest_rate = 0.038
    loanable_rate = 0.68
    a_area = 3.305785 # 1평

    try:
        df['매매가'] = df['매매가'] * 10000
        df['융자금'] = df['융자금'] * 10000
        df['전용률'] = df['전용면적'] / df['계약면적']
        df['전용률'] = df['전용률'].round(2)
        df['계약평단가'] = df['매매가'] / df['계약면적'] * a_area
        df['전용평단가'] = df['매매가'] / df['전용면적'] * a_area
        df['월세'] = df['월세'] * 10000
        df['보증금'] = df['보증금'] * 10000
        df['연세'] = df['월세'] * 12
        df['대출금'] = df['매매가'] * loanable_rate
        df['중개보수'] = df['중개보수'] * 10000
        df['실질매입비용'] = df['매매가'] - df['보증금'] + df['공과금'] + (df['중개보수'])
        df['자기자금'] = df['실질매입비용'] - df['대출금']
        df['자기자금이자'] = df['자기자금'] * interest_rate
        df['연이자'] = df['대출금'] * interest_rate
        df['연수익금'] = df['연세'] - df['연이자']
        df['자기자금수익률'] = (df['연수익금'] / df['자기자금']) * 100
        df['현재일자'] = datetime.today()
        df['연기간차이'] = df['현재일자'] - df['신축일자']
        df['연기간차이'] = df['연기간차이'].dt.days / 365
        df['연기간차이'] = df['연기간차이'].round(2)
        df['적정매입가'] = (df['월세'] * 250) + df['보증금'] - (df['연기간차이'] * 2000000)
        df['공짜수익'] = df['연수익금'] - df['자기자금이자']
        df['매입여부'] = df['매매가'] < df['적정매입가']
        df['대출없는수익률'] = df['연세'] / (df['매매가'] - df['보증금'])
        df['대출없는수익률'] = df['대출없는수익률'].round(2)
        df['세대당주차대수'] = df['총주차대수'] / df['총세대수']
        df['세대당주차대수'] = df['세대당주차대수'].round(2)
    except (ValueError, AttributeError, IndexError, ZeroDivisionError) as e:
        pass

    return df

# Main function
def main():
    # public village infos
    df_village_code = pd.read_csv('koreaRegionCode.txt', sep='\t',
                                  dtype={'법정동코드': str})  # 'http://bit.ly/2PeVzTS' : crawling from the web with this url
    df_village_code = df_village_code[df_village_code["폐지여부"] == "존재"]

    # get Region list
    city_list, district_list, village_list = getRegionList(df_village_code)

    # create village_DataFrame
    df_village_code["도시"] = city_list
    df_village_code["구/군"] = district_list
    df_village_code["동"] = village_list
    df_village_code = df_village_code[df_village_code['동'] != df_village_code['도시']]
    df_village_code = df_village_code[~df_village_code['동'].str.endswith('구')]

    # get province from user
    village = getProvince(df_village_code)

    # rotate proxies
    proxy_pool = getProxies()

    # get contents urls
    searching_url_dict = getContentsUrls(village, df_village_code)

    # get informations
    result = getResult(searching_url_dict, proxy_pool)

    # set column name
    column_list = ['도시', '구/군', '동', '물건명', '매매가', '계약면적', '전용면적', '해당층', '총층', '방개수', '욕실수', '융자금', '입주가능일',
                   '월관리비', '보증금', '월세', '특징', '중개업소', '공과금', '중개보수', '신축일자', '총세대수', '총주차대수', '물건url']
    result.columns = column_list

    # add other columns
    result = addCalcColumns(result)

    # rearrange column of DataFrame
    rearranged_column = ['도시', '구/군', '동', '물건명', '매매가', '융자금', '계약면적', '전용면적', '전용률', '계약평단가', '전용평단가',
                         '보증금', '월세', '연세', '월관리비', '공과금', '중개보수', '입주가능일', '특징', '해당층', '총층', '방개수',
                         '욕실수', '총세대수', '총주차대수', '세대당주차대수', '신축일자', '연기간차이', '대출금', '연이자', '자기자금',
                         '자기자금이자', '연수익금', '자기자금수익률', '실질매입비용', '적정매입가', '매입여부', '공짜수익', '대출없는수익률',
                         '중개업소', '물건url']
    result = result[rearranged_column]  # 현재일자 column 제외

    # Create into an Excel file
    createExcelFile(result, village)

if __name__ == "__main__":
    while True:
        try:
            main()
        except ValueError as e:
            print("등록된 물건이 없습니다.")
            continue
        break