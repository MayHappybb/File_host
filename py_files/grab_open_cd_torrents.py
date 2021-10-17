# 暂时只能查询MB大小的种子
# “50%”图像xpath: /html/body/center/div/table/tbody/tr/td/table[2]/tbody/tr/td/form[2]/table/tbody/tr[46]/td[3]/table/tbody/tr/td[2]/div/img
# 种子链接xpath:   /html/body/center/div/table/tbody/tr/td/table[2]/tbody/tr/td/form[2]/table/tbody/tr[46]/td[3]/table/tbody/tr/td[1]/a
# 种子大小xpath:   /html/body/center/div/table/tbody/tr/td/table[2]/tbody/tr/td/form[2]/table/tbody/tr[46]/td[7]

import re
import time
import requests
from bs4 import BeautifulSoup

time_begin = time.time()    #计时开始，计算程序运行时间

torrent_num = 2            #爬取种子数量
torrent_type = '50%'       #优惠类型:'Free'、'30%'、'50%'、'2X 50%'、'2X'
torrent_min_size = 10 #MB      #只爬取比此数值大的种子，单位MB
begin_page = 1             #从第几页开始查寻，设置为0以禁用 

print("grab number:  " + str(torrent_num))
print("torrent type: " + torrent_type)
print("minimum size: " + str(torrent_min_size) + " MB")
print("begin page: ", begin_page)

#cookies
cookies = {"_ga": "", 
    "_gid": "",
    "c_lang_folder": "",
    "c_secure_login": "",
    "c_secure_pass": "",
    "c_secure_ssl": "",
    "c_secure_tracker_ssl": "",
    "c_secure_uid": ""}

url = "https://open.cd/torrents.php"
payload = {"inclbookmarked": "0", "incldead": "1", "spstate": "0", "option-torrents": "0", "sort": "5", "type": "asc", "page": "0"}
torrent_id = []

if begin_page == 0:     #若未设置此量，则从第0页开始查询
    page = 0    #当前页码
elif begin_page > 0:            #若设置了开始查询的初始页面（则begin_page最小为1），则
    # torrent_min_size = 1        #禁用要求种子最小尺寸，将torrent_min_size设置为1，即大于1MB的种子都爬取，相当于禁用torrent_min_size
    page = begin_page

#查找满足种子大小的页码
while 1:#size < torrent_min_size:
    payload["page"] = str(page)
    r = requests.get(url=url, params=payload, cookies=cookies)
    soup = BeautifulSoup(r.content, 'html.parser')
    size_char = soup.find('td', class_ = "rowfollow", string = re.compile("(M|G)B$")).string        #利用正则表达式查询最后两个字符为"MB"的字符串以获取此页面第一个种子的大小，字符串格式"xxx MB"或"xxx GB"
    if size_char[-2:] == "GB":                  #单位为GB
        size = float(size_char[:-3]) * 1024     #转化为float
    elif size_char[-2:] == "MB":                #单位为MB
        size = float(size_char[:-3])            #转化为float
    print("the minimum torrent of page "+str(page)+" is "+size_char)
    if size >= torrent_min_size:    #若该页最小的种子比所要求的最小值大
        if begin_page != 0 and page == begin_page:         #若设置了开始页码，且此时该页的最小种子大小满足要求，则从此页开始查询种子，无需page-1
            break
        page = page - 1             #则页码回退到上一页
        if page < 0:                #页码不能小于0
            page = 0
        break
    page = page + 1

print("From page " + str(page) + " begin to query")

record_begin_page = page    #记录开始查询的页码，用于写入生成的文档

#此页面部分种子大于torrent_min_size
payload["page"] = str(page)
print("Start querying page ", page)
r = requests.get(url=url, params=payload, cookies=cookies)
soup = BeautifulSoup(r.content, 'html.parser')
for link in soup.find_all("img"):
    if link.get("alt") == torrent_type:     #查找torrent_type标签(Free、30%、...)
        this_str_size = link.parent.parent.parent.parent.parent.next_sibling.next_sibling.next_sibling.next_sibling.string
        this_size = float(this_str_size[:-3])
        if this_size > torrent_min_size:    #如果此种子大小满足要求
            torrent_id.append(link.parent.parent.previous_sibling.find("a").get("href")[-11:-6])     #就添加此种子的id
            print("torrent ", torrent_id[-1], " fulfil requirements! " + "Found ", len(torrent_id), "/" + str(torrent_num))
            if len(torrent_id) == torrent_num:
                break

#查找符合要求的种子
while len(torrent_id) < torrent_num:
    page = page + 1
    payload["page"] = str(page)
    print("Start querying page ", page)
    r = requests.get(url=url, params=payload, cookies=cookies)
    soup = BeautifulSoup(r.content, 'html.parser')
    for link in soup.find_all("img"):
        if link.get("alt") == torrent_type:
            # print(link.parent.parent.previous_sibling.find("a").get("href")[22:27])       #提取torrent的id
            torrent_id.append(link.parent.parent.previous_sibling.find("a").get("href")[-11:-6])
            print("torrent ", torrent_id[-1], " fulfil requirements! " + "Found ", len(torrent_id), "/" + str(torrent_num))
            if len(torrent_id) == torrent_num:
                break
print("Grab all done!")

record_end_page = page    #记录查询完毕的页码，用于写入生成的文档

#查询密匙
control_web = requests.get(url="https://open.cd/usercp.php", cookies=cookies)
control_web_soup = BeautifulSoup(control_web.content, 'html.parser')
web_key = control_web_soup.find('td', string="密匙").next_sibling.string

#构建输出文件名
now_time = time.asctime(time.localtime(time.time()))        #写代码时输出为'Thu Oct 14 20:33:20 2021'
file_name = now_time[-4:] + '-' + str(time.localtime().tm_mon) + '-' + now_time[-16:-14] + '-' + now_time[-13:-11] + '-' + now_time[-10:-8] + '-' + now_time[-7:-5]
file_name = "./" + file_name + ".txt"
save_file = open(file_name, 'w')        #新建文件存放种子链接

save_file.write("日期：" + time.asctime(time.localtime(time.time())) + '\n')
save_file.write("爬取种子数量：" + str(torrent_num) + '\n')
save_file.write("优惠类型：" + torrent_type + '\n')
save_file.write("最小种子大小：" + str(torrent_min_size) + " MB" + '\n')
save_file.write("查询页码范围：" + str(record_begin_page) + " ～ " + str(record_end_page) + '\n')
save_file.write("------------------------------------------------------------------------------\n")

for i in range(len(torrent_id)):
    save_file.write("https://open.cd/download.php?id=" + torrent_id[i] + "&passkey=" + web_key + '\n')

save_file.close()

time_end = time.time()    #计时结束，计算程序运行时间
time_using = time_end - time_begin
if time_using >= 60:    #时间大于60s，单位换算
    time_using_str = str(int(time_using/60)) + "min" + str(round(time_using - int(time_using/60)*60)) + 's'
else:
    time_using_str = str(round(time_using)) + 's'
print("Runtime: ", time_using_str)
