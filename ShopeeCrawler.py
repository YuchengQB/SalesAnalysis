''' 擷取內容：1.品項名 2.售價 3.售出量 4.折扣 5.剩餘量 6.評價'''

from selenium import webdriver
from bs4 import BeautifulSoup as bs
import pandas as pd
import numpy as np
import time  #可以用time.localtime(time.time())擷取時間
import re
import datetime
import sqlite3

def picknum(x):
    pattern = re.compile(r'\d+')
    
    if x[0] == '還':
        result= pattern.findall(x)[0]
    elif "," in x:
        result= pattern.findall(x)[0]
        
    elif x[0]!="還" and len(x)<8:        #算每小時銷售量用，e.g.把2.7萬處理成27000
        result = int(float(x[:-1])*10000)

    else:               # XX件 X分鐘內售完 取件數
        result = pattern.findall(x)[0]

    return result

def picktime(x): #'5 件 1 小時內售完'、"10 件 32 分鐘內售完" 取時間
    pattern = re.compile(r'\d+')
    result= pattern.findall(x)[1]
    if x[-5]=="小": #照原本的數字
        result= int(result)
    else:
        result= round(int(result)/60,1)
    return result

print("開始時間：",time.ctime())
'''Driver 進網頁'''
driver = webdriver.Chrome("D:\chromedriver\chromedriver")
driver.implicitly_wait(8)
url = "https://shopee.tw/"
driver.get(url)


'''進網頁2'''
driver.find_element_by_xpath("/html/body/div[1]/div/div[3]/div/div/shopee-banner-popup-stateful//div/div/div/div/div/svg/path[2]").click()
time.sleep(3)
driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div[2]/div[4]/div[2]/div/div[1]/a/button").click()
#time.sleep(3)               #/html/body/div[1]/div/div[2]/div[2]/div[2]/div[3](這個index會變)     /div[2]/div/div[1]/a/button
print("及時熱賣title：",driver.title)

'''下拉到網頁底部以載入所有資料'''
for i in range(1,6):    
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(3)

#time.sleep(5)

'''網頁內容'''
soup = bs(driver.page_source,"lxml")
#

#
''' ****** P A R T 1 ****** '''
'''品項名稱、價錢'''
all_items=soup.find_all("div",{"class":"flash-sale-item-card__item-name-box"})
all_price=soup.find_all("span",{"class":'item-price-number'})
item_name=[]
item_price=[]
before_price=[]
for each_item,each_price,each_before in zip(all_items,all_price[1::2],all_price[0::2]):
    print(each_item.text)
    item_name.append(each_item.text)
    item_price.append(each_price.text.replace(',', ''))  #最後的replace是為了把原本有逗號的價錢改成純數字16,000->16000
    before_price.append(each_before.text.replace(',', ''))
    
print("總共",len(item_name),"項商品")
#改成int    
item_price = list(map(int, item_price))

print("預計",len(item_name) / 3.5 ,"分鐘完成")

'''建立最終輸出用dataframe'''
item_all={"item_name":item_name,"price":item_price}
item_df=pd.DataFrame(item_all)


'''分成尚有餘/已售完 (1.截取銷貨量 ; 2.折扣) *'''
sale_list=[]
discount_list=[]
for judgeidex in range(1,len(item_name)+1):
    #折扣的位置
    judgepath = "/html/body/div[1]/div/div[2]/div[2]/div/div[6]/div[2]/div["+ str(judgeidex) + "]/a/div[4]/div[3]/div/div"
    #xx分鐘內售完的位置
    judgepath_2 = "/html/body/div[1]/div/div[2]/div[2]/div/div[6]/div[2]/div["+ str(judgeidex)+ "]/a/div[4]/div[1]/div[2]"
    a=driver.find_element_by_xpath(judgepath)
    b=driver.find_element_by_xpath(judgepath_2)
    time.sleep(1)
    #還沒售完的
    if a.text != "售完" and b.text[-3:]!= "內售完":
        #熱賣中+即將售完
        #折扣
        discount_list.append( float(a.text.split('\n')[0]) )
        
        #銷貨量
        #print("以下即將售完")
        salepath = "/html/body/div[1]/div/div[2]/div[2]/div/div[6]/div[2]/div["+ str(judgeidex) + "]/a/div[4]/div[1]/div[2]/div/div[1]"
        sales= driver.find_element_by_xpath(salepath)
        time.sleep(1)
        
        if sales.text[3]==" ":   #熱賣中
            print(sales.text[4:])
            sale_list.append(sales.text[4:])
        else:
            print(sales.text)   #即將售完(沒有註明銷貨量 -> 進網頁截)
            driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[6]/div[2]/div["+ str(judgeidex) + "]/a").click()
            time.sleep(3)
            soup = bs(driver.page_source,"lxml")
            #soup.find("div",{"class":"aca9MM"}).text
            
            sale_list.append(soup.find("div",{"class":"aca9MM"}).text)
            
            driver.back()
            time.sleep(1)
    #售完的 折扣的位置會寫售完or下面會寫xx件xx分鐘內售完   
    else:
        #已售完
        #折扣(要另外算)
        discount=round((int(item_price[judgeidex-1])/int(before_price[judgeidex-1]))*10,1)
        discount_list.append(discount)
        
        #銷貨量
        #print("以下已售完")
        time.sleep(1)
        saleoutpath = "/html/body/div[1]/div/div[2]/div[2]/div/div[6]/div[2]/div["+ str(judgeidex) + "]/a//div[4]/div[1]/div[2]"
        saleout=driver.find_element_by_xpath(saleoutpath)
        print(saleout.text)
        #用RE抓出( XX件 X分鐘內售完 )中售出的數字
        saleout = picknum(saleout.text)
        sale_list.append(saleout)
    

    if judgeidex == round(((1+len(item_name)+1)/2 )):
        print("進度:完成 50%")


#將已銷售數量、折扣放進dataframe中
item_df.insert(1,column="sales_volume",value=sale_list)
item_df.insert(item_df.shape[1],column="discount",value=discount_list)

print("(colume2、4)完成時間：",time.ctime())

'''銷售量&時間correlation (每小時銷售量) 已售完的截時間 / 還沒賣完的截當前時間'''
""" ***要跑之前去蝦皮網站確認優惠時間間隔(有時候會變成10、12、14、18...這種區間)"""
hournow = time.localtime(time.time())[3]
minutenow = time.localtime(time.time())[4]
hournow_1=hournow
#現在是屬於哪個時段 timejudge
if minutenow >= 30:  #先處理四捨五入(13:45要算成從12點過了兩小時)
    hournow_1+=1
    

if 15 <= hournow < 20:
    hournow_1-=15
    
elif 20 <= hournow :
    hournow_1-=20
    
elif 0 <= hournow < 10:
    hournow_1=hournow
    
elif 10 <= hournow < 15:
    hournow_1-=10

if hournow==0 and minutenow<30:  #0:00~0:30這段時間hournow_1無法被進位到一小時(13:15的hournow_1是1，可以除)
    hournow_1=0.5

#現在有時間了 只要把售出量與時間相除就可以了
#每個品項要除的時間
saletime_list=[]
print("時間進度：",end="")
for judgeidex in range(1,len(item_name)+1):
    judgepath = "/html/body/div[1]/div/div[2]/div[2]/div/div[6]/div[2]/div["+ str(judgeidex) + "]/a/div[4]/div[3]/div/div"
    
    judgepath_2 = "/html/body/div[1]/div/div[2]/div[2]/div/div[6]/div[2]/div["+ str(judgeidex)+ "]/a/div[4]/div[1]/div[2]"
    
    a=driver.find_element_by_xpath(judgepath)
    b=driver.find_element_by_xpath(judgepath_2)

    time.sleep(1)
    
    if a.text!= "售完"and b.text[-3:]!= "內售完":
        saletime_list.append(hournow_1)
        print(judgeidex,end="、")
    else:#賣完的要抓時間
        print(judgeidex,"(售罄)",end="、")#前面加點東西不然只會一直跳售磬時間而已
        #time.sleep(1)
        saleoutpath = "/html/body/div[1]/div/div[2]/div[2]/div/div[6]/div[2]/div["+ str(judgeidex) + "]/a//div[4]/div[1]/div[2]"
        saleout=driver.find_element_by_xpath(saleoutpath)
        saleout_time= picktime(saleout.text)
        saletime_list.append(saleout_time)
print()
print("timedata完成時間：",time.ctime())

#相除
salerate=[]
for eachvolume,eachtime in zip(sale_list,saletime_list):
    if eachvolume[-1]=="萬":
        eachvolume = picknum(eachvolume)
    else:
        
        if "," in eachvolume:
            eachvolume = picknum(eachvolume)
        
        eachvolume = int(eachvolume)
    salerate.append(round((eachvolume/eachtime),1))
    print("每小時售出",round((eachvolume/eachtime),1),"個")

#將每小時銷售量匯入dataframe中
item_df.insert(item_df.shape[1],column="每小時銷售量",value=salerate)

print("(colume5)完成時間：",time.ctime())



''' ****** P A R T 2 ****** '''
'''剩餘數量、商品評價 (進網頁截取) 已售罄的不用進，給default值 / 還有剩餘的要進網頁截、總售出數'''
'''18禁商品處理'''
'''  跑這裡會很花時間，要處理超過時間的狀況 (跑到一半該區間結束) '''
rating_list=[]
remain_list=[]
total_sale_list=[]
for judgeidex in range(1,len(item_name)+1):
    judgepath = "/html/body/div[1]/div/div[2]/div[2]/div/div[6]/div[2]/div["+ str(judgeidex) + "]/a/div[4]/div[3]/div/div"
    
    judgepath_2 = "/html/body/div[1]/div/div[2]/div[2]/div/div[6]/div[2]/div["+ str(judgeidex)+ "]/a/div[4]/div[1]/div[2]"
    
    a=driver.find_element_by_xpath(judgepath)
    b=driver.find_element_by_xpath(judgepath_2)
    
    if a.text != "售完" and b.text[-3:]!= "內售完": #還沒售完，點進頁面找
        linkpath="/html/body/div[1]/div/div[2]/div[2]/div/div[6]/div[2]/div["+str(judgeidex)+ "]/a"
        
        #很容易跑error，有問題的話重新整理
        while True:
            try:
                driver.find_element_by_xpath(linkpath).click()
                break
            except:
                print("進入error:refresh")
                driver.refresh()
                time.sleep(3)
                driver.find_element_by_xpath(linkpath).click()
        
        #處理18+商品
        try: 
            driver.find_element_by_xpath("/html/body/div[10]/div/div[2]/div/div[2]/button[1]").click()
        except:
            pass

        soup = bs(driver.page_source,"lxml")
        time.sleep(2)
        
        ##評價(要分是否已經評價)
        #有評價的
        try:
            ratingpath = "/html/body/div[1]/div/div[2]/div[2]/div[2]/div[2]/div[3]/div/div[2]/div[1]/div[1]"
            rating = driver.find_element_by_xpath(ratingpath).text
            rating_list.append(float(rating))
        #尚未有評價
        except:
            rating_list.append(-99)
                     
        
        ##剩餘數量 
        '''每個商品的剩餘數量的XPATH index不同... '''
        '''class都一樣 -> 用div[@class=" "] 抓到正確路徑'''
        #前面都長這樣
        #/html/body/div[1]/div/div[2]/div[2]/div[2]/div[2]/div[3]/div/div[4]/div/
        #接下來有差，要根據class找路徑(有四層div要特別抓)
        #//div[@class='flex _3AHLrn _2XdAdB']/div[@class='flex flex-column']/div[@class='flex items-center _90fTvx']/div[@class='flex items-center']/div[2]
        
        remainpath =" /html/body/div[1]/div/div[2]/div[2]/div[2]/div[2]/div[3]/div/div[4]/div//div[@class='flex _3AHLrn _2XdAdB']/div[@class='flex flex-column']/div[@class='flex items-center _90fTvx']/div[@class='flex items-center']/div[2]"
        
        print("第",judgeidex,"樣商品：",end="")
        #中間加個東西，不然很容易跑error
        
        try:
            remain = driver.find_element_by_xpath(remainpath)
        except:
            print("取剩餘error:refresh")
            driver.refresh()
            
            time.sleep(3)
            remain = driver.find_element_by_xpath(remainpath)

              

        print(remain.text)
        
        remain=int(picknum(remain.text))
        remain_list.append(remain)
        
        #總銷售量
        '''最新增加的欄位'''
        totalpath="/html/body/div[1]/div/div[2]/div[2]/div[2]/div[2]/div[3]/div/div[2]//div[@class='flex _210dTF']/div[1]"
                   
        totalsale= driver.find_element_by_xpath(totalpath)
        
        #拆成1.2萬 / 441
            
        if "萬" in totalsale.text:
            totalsale=int(picknum(totalsale.text))
        
        elif "," in totalsale.text: #這裡的re是最後加的 if條件不好取所以直接寫rather than用picknum()
            pattern = re.compile(r'\d+')
            totalsale = int(pattern.findall(totalsale.text)[0]+pattern.findall(totalsale.text)[1])
            
        else:
            totalsale=int(totalsale.text)
            
        total_sale_list.append(totalsale)
        
        
        
        driver.back()
        time.sleep(1)
        
        
    else: #賣完的直接加
        rating_list.append(np.nan)
        remain_list.append(0)
        total_sale_list.append(np.nan)
        print("第",judgeidex,"樣商品：還剩0件")

#remain_list全部改成int    
remain_list = list(map(int, remain_list))

#將評價、剩餘量、總銷售量匯入dataframe中
item_df.insert(item_df.shape[1],column="剩餘量",value=remain_list)
item_df.insert(item_df.shape[1],column="總銷售量",value=total_sale_list)
item_df.insert(item_df.shape[1],column="商品評價",value=rating_list)

print("(colume6、7、8)完成時間：",time.ctime())        

driver.close()

''' ****** P A R T 3 ****** '''
'''寫檔''' 
#encoding="utf-8"會跑出亂碼
fname= time.strftime("%m%d_%H_%M", time.localtime())+ "_Shopee.csv"
item_df.to_csv(fname,index=False,encoding="utf_8_sig",sep=',')


''' ****** P A R T 4 ****** '''
'''存入資料庫'''
#建立database、連線
conn = sqlite3.connect("ShopeeDB.sqlite")

cursor = conn.cursor()

#建立資料表
#全體資料表
cursor.execute('CREATE TABLE IF NOT EXISTS Shopee_ALL(item_name , sales_volume, price, discount, 每小時銷售量, 剩餘量, 總銷售量, 商品評價)')
#本次新增的資料
cursor.execute('CREATE TABLE IF NOT EXISTS Shopee_now(item_name , sales_volume, price, discount, 每小時銷售量, 剩餘量, 總銷售量, 商品評價)')


item_df.to_sql('Shopee_now', conn, if_exists='append', index=False)
#將本次新增的資料表合併至全體資料表中
cursor.execute("INSERT INTO Shopee_ALL SELECT * FROM Shopee_now")


conn.commit()
conn.close()

