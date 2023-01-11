from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5.QtTest import *
from config_.errorCode import *
import schedule
import time
from datetime import datetime
import math
import pandas as pd
import csv
import logging
import logging
import logging.handlers


class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        
        ####### 로그 초기화 
        # 로거 인스턴스를 만든다
        self.logger = logging.getLogger('mylogger')

        # 포매터를 만든다
        fomatter = logging.Formatter('[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s > %(message)s')

        # 스트림과 파일로 로그를 출력하는 핸들러를 각각 만든다.
        fileHandler = logging.FileHandler('./myLog.log')
        streamHandler = logging.StreamHandler()

        # 파일 용량이 100MB를 넘어가면 10개까지 로그를 남기고 싶을때 fileHandler를 이렇게 셋팅해주면 된다
        '''
        fileMaxByte = 1024 * 1024 * 100 #100MB
        fileHandler = logging.handlers.RotatingFileHandler('./myLog.log', maxBytes=fileMaxByte, backupCount=10)
        '''

        # 각 핸들러에 포매터를 지정한다.
        fileHandler.setFormatter(fomatter)
        streamHandler.setFormatter(fomatter)

        # 로거 인스턴스에 스트림 핸들러와 파일핸들러를 붙인다.
        # 이 예제는 여러가지의 파일핸들을 logger에 붙여서 로그를 여러군데에 남기는 예제이다.
        self.logger.addHandler(fileHandler)
        self.logger.addHandler(streamHandler)
        self.logger.setLevel(logging.DEBUG)
        ########################
        
        
        
        
        
        
        
        
        self.logger.info("kiwoom 클래스입니다")
        
        ####### 이벤트 루프 모음
        self.login_event_loop = None
        self.detail_account_info_event_loop = QEventLoop()
        self.condition_load_loop = None
        self.condition_search_loop = None
        self.mystock_value_now_loop = None
        self.sendOrder_loop = None
        self.trade_stock_loop = None
        self.regit_realTime_data_loop = None
        self.get_purchase_price_loop = None
        self.get_stocks_track_loop = None
        self.calculator_event_loop = QEventLoop()
        self.tick_data_loop = QEventLoop()
        
        ##########################
        
        ####### 스크린번호 모음
        self.screen_my_info = "2000"
        self.screen_calculation_stock = "4000"
        ##########################
        
        ####### 변수 모음
        self.account_num = None # 계좌번호
        self.password = "1234" # 비밀번호
        self.BUY = 1 # 신규매수
        self.SELL = 2 # 신규매도
        
        self.BUY_STANDARD_AMOUNT = 500000 # 매수 비중
        self.LOSS_BASED_PERCENTAGE = -3 # 손절시 전량 매도 퍼센트 기준
        self.PROFIT_BEGINNING_PERCENTAGE = 1.5 # 몇퍼센트 올랐을 때 매도 할 것인지 첫번째 기준
        self.PROFIT_MIDDLE_PERCENTAGE = 7 # 두번째 기준
        self.PROFIT_END_PERCENTAGE = 10 # 세번째 기준
        self.SELL_BEGINNING_PERCENTAGE = 20 # 첫번째 매도시 몇퍼센트 매도할 것인지
        self.SELL_MIDDLE_PERCENTAGE = 30 # 두번째 매도시 몇퍼센트 매도할 것인지
        self.IS_CONDITION_SEARCH = False # 조건검색에서 온 실시간데이터인지
        
        self.CONDITION_NAME = "eb"
        self.CONDITION_INDEX = 12
        self.TRADE_COUNT = 0
        self.TRADE_LIST = []
        
        
        self.BOUGHT_STOCK_LIST = dict() # 보유 주식 딕셔너리
        self.account_stock_dict = {} # 영상 강의 학습용 딕셔너리
        self.not_account_stock_dict = {} # 영상 강의 학습용 딕셔너리
        self.row_dict = [] # 거래기록 csv저장 리스트
        
        
        ########################
        
        
        
        
        ####### 계좌 관련 변수
        self.use_money = 0
        self.use_money_percent = 0.5
        ########################

        
        
        
        
        
        # 키움API 컨트롤 권한 가져오기
        self.get_ocx_instance()
        
        ## 이벤트
        self.event_slots()
        
        ## 메인 함수
        self.signal_login_commConnect()
        self.get_account_info()
        # self.mystock_value_now()
        # self.detail_account_info() # 예수금 가져오기
        self.detail_account_mystock() # 계좌평가 잔고 내역 요청
        # self.not_concluded_account() # 미체결 요청
        # self.get_tick_data() # 현재 안됨
        # self.calculator_fnc() # 종목 분석용, 임시용으로 실행
        self.load_condition()
        self.search_condition()
        
        self.check_stock()
        # self.regit_realTime_data()
        self.regit_realReg()
        

    
        
    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
    
    
    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot) # 로그인 요청시 발생하는 이벤트
        self.OnReceiveTrData.connect(self.trdata_slot) # trData 조회시 발생하는 이벤트
        self.OnReceiveConditionVer.connect(self.condition_load_slot) # 조건 검색식 불러오기 요청시 발생하는 이벤트
        self.OnReceiveTrCondition.connect(self.condition_search_slot) # 조건 검색 요청에 대한 서버 응답 수신시 발생하는 이벤트
        self.OnReceiveMsg.connect(self.stock_slot) 
        self.OnReceiveRealData.connect(self.real_data_slot)
        self.OnReceiveRealCondition.connect(self.real_condition_slot) #실시간 조건검색
        self.OnReceiveChejanData.connect(self.chejan_slot)


    def signal_login_commConnect(self): 
        """로그인 시도
        """
        self.dynamicCall("CommConnect()")
        
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()
        
        
    def login_slot(self, errCode):
        self.logger.warning(errors(errCode))
        self.login_event_loop.exit()
        
    

    def condition_search_slot(self, scrNo, codeList, conditionName, nIndex, nNext):
        """조건검색식

        Args:
            scrNo (_type_): 화면번호
            codeList (_type_): 종목코드 리스트
            conditionName (_type_): 조건식 이름
            nIndex (_type_): 조건 고유번호
            nNext (_type_): 연속조회 여부
        """

        print("condition_search_slot()")
        # 리스트의 공백 문자열 제거
        codeList = codeList.split(";")
        self.codeList = list(filter(None, codeList))
        
        # 조건검색식으로 나온 주식명 출력
        for i in codeList:
            result = self.get_master_code_name(i)
            if result:
                print("조건검색: %s" % result)
            
        
        self.condition_search_loop.exit()
        
        
    def condition_load_slot(self, iRet, sMsg):
        self.logger.info(sMsg) # 조건 검색식 불러오기 서버 응답 결과
        ConditionNameList = self.dynamicCall("GetConditionNameList()").split(";")
        self.logger.info(f"보유 조건식:\n{ConditionNameList}")
        
        self.condition_load_loop.exit()
        
    def stock_slot(self, scrNo, rqName, trCode, msg):
        """ 주문, 잔고처리 관련 서버 통신후 수신한 서버메시지 알림

        Args:
            scrNo (_type_): 화면번호
            rqName (_type_): 사용자 구분명
            trCode (_type_): TR이름
            msg (_type_): 서버에서 전달하는 메시지
        """
        self.logger.info(f"stock_slot() msg: {msg}")
        
    def real_data_slot(self, sCode, sRealType): 
        # 실시간 데이터
        
        self.logger.info(f"sCode: {sCode}, sRealType = {sRealType}")
        if sRealType == "주식체결":
            # 추적중인 주식 체결 됐을 때 실행
            
            
            
            
            
            if self.IS_CONDITION_SEARCH: # 처음 조건검색 종목편입시 매수
                now_price = abs(float(self.dynamicCall("GetCommRealData(String, int)", sCode, 10)))
                
                
                purchase_quantity = int(self.BUY_STANDARD_AMOUNT / now_price) # 지정금액 근사치 해당하는 주식 매수수량 계산
                self.logger.info(f"purchase_quantity 확인: {purchase_quantity}")
                
                    
                if sCode in self.BOUGHT_STOCK_LIST:
                    self.logger.info("이미 구매리스트에 종목 존재하여 매수 X")
                else:
                    self.trade_stock(sCode, purchase_quantity, self.BUY) # 매수 주문
                    # mystock_info = {"종목명" : mystock_name, "수익률" : mystock_percent, "보유수량" : mystock_quantity, "매입가" : mystock_bought_price, "전고점" : 0, "분할매도수익률" : 0}
                    mystock_info = {"종목명" : "sName", "수익률" : 0, "보유수량" : purchase_quantity, "매입가" : now_price, "전고점" : now_price, "분할매도수익률" : 0}
                    self.BOUGHT_STOCK_LIST[sCode] = mystock_info
                    self.TRADE_LIST.append([self.BOUGHT_STOCK_LIST[sCode]['종목명'], sCode, now_price, now_price, purchase_quantity, 0, "매수", datetime.now()])
                    self.TRADE_COUNT += 1
                
                
                
                self.IS_CONDITION_SEARCH = False
                
            else: # 구매한 종목 판매할 것인지 검사
                try: # 너무 빠르게 많이 들어와 전량매도 후 BOUGHT_STOCK_LIST 에서 요소 삭제한 후에도 들어와서 에러나는 것 무시하기 위함
                    self.logger.info(f"BOUGHT_STOCK_LIST: {self.BOUGHT_STOCK_LIST}")
                    # mystock_info = {"종목명" : mystock_name, "수익률" : mystock_percent, "보유수량" : mystock_quantity, "매입가" : mystock_bought_price, "전고점" : 0, "분할매도수익률" : 0}
                    
                    now_price = abs(float(self.dynamicCall("GetCommRealData(String, int)", sCode, 10)))
                    quantity = float(self.BOUGHT_STOCK_LIST[sCode]['보유수량'])
                    bought_price = float(self.BOUGHT_STOCK_LIST[sCode]['매입가'])
                    percent = round(((now_price - bought_price) / bought_price) * 100, 2)
                    split_sell_percent = self.BOUGHT_STOCK_LIST[sCode]["분할매도수익률"]
                    self.BOUGHT_STOCK_LIST[sCode].update({"수익률" : percent})
                    
                    # 전고점 갱신
                    if now_price > float(self.BOUGHT_STOCK_LIST[sCode]["전고점"]):
                        self.BOUGHT_STOCK_LIST[sCode].update({"전고점" : now_price})
                    
                    
                    
                    self.logger.info(f"{self.BOUGHT_STOCK_LIST[sCode]['종목명']}: {percent}% / 현재가: {now_price} / 수량: {quantity} / 구매가: {bought_price}")
                    #                                                                       /       15150        /        13        /         196950
                    
                    if percent <= self.LOSS_BASED_PERCENTAGE:
                        #손실나서 전량 매도
                        self.trade_stock(sCode, quantity, self.SELL)
                        
                        # 엑셀파일 작성위한 리스트
                        self.TRADE_LIST.append([self.BOUGHT_STOCK_LIST[sCode]['종목명'], sCode, now_price, bought_price, quantity, percent, "손절(전량매도)", datetime.now()])
                        self.TRADE_COUNT += 1
                        
                        self.logger.info(f"{self.BOUGHT_STOCK_LIST[sCode]['종목명']} 손절(전량매도)")
                    elif (percent >= self.PROFIT_BEGINNING_PERCENTAGE):
                        self.trade_stock(sCode, quantity, self.SELL)
                        self.logger.info(f"수익률 {percent}%에 전량매도")
                        self.logger.info(f"판매 개수: {quantity}")
                        
                        
                    # elif (percent >= self.PROFIT_BEGINNING_PERCENTAGE) and (percent < self.PROFIT_MIDDLE_PERCENTAGE):
                    #     # 첫번째 매도
                    #     sell_quantity = math.floor(quantity * float(self.SELL_BEGINNING_PERCENTAGE) / 100)
                        
                    #     if sell_quantity == 0:
                    #         sell_quantity = 1
                    #         self.logger.info("수익률 계산시 판매개수 1 이하로 나와 1개로 조정됨")
                        
                    #     self.trade_stock(sCode, sell_quantity, self.SELL)
                        
                        
                    #     # 엑셀파일 작성위한 리스트
                    #     self.TRADE_LIST.append([self.BOUGHT_STOCK_LIST[sCode]['종목명'], sCode, now_price, bought_price, sell_quantity, percent, "첫번째 매도", datetime.now()])
                    #     self.TRADE_COUNT += 1
                        
                    #     self.logger.info("첫번째 매도")
                    #     self.logger.info(f"sell_quantity: {sell_quantity}")
                        
                    # elif (percent >= self.PROFIT_MIDDLE_PERCENTAGE) and (percent < self.PROFIT_END_PERCENTAGE):
                    #     # 두번째 매도
                    #     sell_quantity = math.floor(quantity * float(self.SELL_MIDDLE_PERCENTAGE) / 100)
                    #     if sell_quantity == 0:
                    #         sell_quantity = 1
                    #     self.trade_stock(sCode, sell_quantity, self.SELL)
                        
                    #     # 엑셀파일 작성위한 리스트
                    #     self.TRADE_LIST.append([self.BOUGHT_STOCK_LIST[sCode]['종목명'], sCode, now_price, bought_price, sell_quantity, percent, "두번째 매도", datetime.now()])
                    #     self.TRADE_COUNT += 1
                        
                    #     self.logger.info("두번째 매도")
                    #     self.logger.info(f"sell_quantity: {sell_quantity}")
                    
                    # elif percent >= self.PROFIT_END_PERCENTAGE :
                    #     # 마지막(전량) 매도
                    #     self.trade_stock(sCode, quantity, self.SELL)
                        
                    #     # 엑셀파일 작성위한 리스트
                    #     self.TRADE_LIST.append([self.BOUGHT_STOCK_LIST[sCode]['종목명'], sCode, now_price, bought_price, sell_quantity, percent, "세번째 매도", datetime.now()])
                    #     self.TRADE_COUNT += 1
                        
                    #     self.logger.info("마지막(전량) 매도")
                    #     self.logger.info(f"sell_quantity: {quantity}")
                    
                    
                        
                except Exception as e:
                    self.logger.warning(f"real_data_slot() try문 오류 {e}")
                    self.dynamicCall("SetRealRemove(String, String)", "ALL", sCode) #바로 실시간등록 해제되지 않아 에러 발생시 다시한번 실행
                    self.logger.warning(f"real_data_slot() 실시간등록해제 {sCode}")
                    
                    
                    
            
        
        if sRealType == "종목프로그램매매":
            
            pass
                

            
            
            
            
        # self.regit_realTime_data_loop.exit()
        
    
    def real_condition_slot(self, sCode, sType, sConditionName, sConditionIndex):
        #실시간 조건검색
        
        self.logger.info(f"real_condition(): {sCode}, {sType}, {sConditionName}, {sConditionIndex}")
        if sType == "I": #종목편입
            self.dynamicCall("SetRealReg(String, String, String, String)", "9001", sCode, "10", 1)
            self.logger.info("조건검색 종목편입: %s " %sCode)
            
            self.IS_CONDITION_SEARCH = True
            
            
            
            
        elif sType == "D": #종목이탈
            self.logger.info("조건검색 종목이탈: %s " %sCode)
        
            
            
    def chejan_slot(self, sGubun, nItemCnt, sFidList):
        # self.logger.info(f"체결 데이터:\nsGubun: {sGubun}, nItemCnt: {nItemCnt}, sFidList: {sFidList}")
        # sGubun=1(잔고변경) : 9201;9001;917;916;302;10;930;931;932;933;945;946;950;951;27;28;307;8019;957;958;918;990;991;992;993;959;924;10010;25;11;12;306;305;970;10012;10025;10011
        # sGubun=0(접수및체결) : 9201;9203;9205;9001;912;913;302;900;901;902;903;904;905;906;907;908;909;910;911;10;27;28;914;915;938;939;919;920;921;922;923;949;10010;969;819
        
        if sGubun == "0":
            #접수및체결
            bought_sPrice = self.dynamicCall("GetChejanData(int)", 910).strip()
            bought_sCode = self.dynamicCall("GetChejanData(int)", 9001).strip()[1:]
            bought_sName = self.dynamicCall("GetChejanData(int)", 302).strip()
            bought_sQuantity = self.dynamicCall("GetChejanData(int)", 900).strip()
            # print(f"접수및체결:\n매입가: {bought_sPrice}, 종목코드: {bought_sCode}, 종목명: {bought_sName}, 주문수량: {bought_sQuantity}")
        elif sGubun == "1":
            # 잔고변경 
            sQuantity = self.dynamicCall("GetChejanData(int)", 930).strip()
            sCode = self.dynamicCall("GetChejanData(int)", 9001).strip()[1:]
            profit_percent = self.dynamicCall("GetChejanData(int)", 8019).strip()
            sName = self.dynamicCall("GetChejanData(int)", 302).strip()
            bought_sPrice = self.dynamicCall("GetChejanData(int)", 931).strip()
            total_bought_sPrice = self.dynamicCall("GetChejanData(int)", 932).strip() # 총매입가
            sell_buy = self.dynamicCall("GetChejanData(int)", 946).strip()
            
            if sell_buy == "1":
                sell_buy = "매도"
            elif sell_buy == "2":
                sell_buy = "매수"
            else:
                sell_buy += "_오류"
                
                
            self.logger.info(f"잔고변경:\n 종목명: {sName}, 수익률: {profit_percent}, 보유수량: {sQuantity}, 매입가: {bought_sPrice}, 체결구분: {sell_buy}")
            
            # bought_stock_list 업데이트
            if sCode in self.BOUGHT_STOCK_LIST:
                self.logger.info("요소 있음")
                self.BOUGHT_STOCK_LIST[sCode].update({"종목명" : sName})
                self.BOUGHT_STOCK_LIST[sCode].update({"수익률" : profit_percent})
                self.BOUGHT_STOCK_LIST[sCode].update({"보유수량" : sQuantity})
                self.BOUGHT_STOCK_LIST[sCode].update({"매입가" : bought_sPrice})
            else:
                self.logger.info("요소 없음")
                mystock_info = {"종목명" : sName, "수익률" : profit_percent, "보유수량" : sQuantity, "매입가" : bought_sPrice, "전고점" : bought_sPrice, "분할매도수익률" : 0}
                self.BOUGHT_STOCK_LIST[sCode] = mystock_info
                
            if sell_buy == "매도" and sQuantity == "0":
                del self.BOUGHT_STOCK_LIST[sCode]
                self.dynamicCall("SetRealRemove(String, String)", "ALL", sCode) #전량매도시 실시간등록 해제
                self.logger.info(f"BOUGHT_STOCK_LIST에서 {sName} 삭제")


                
            
            self.logger.info("BOUGHT_STOCK_LIST UPDATE:")
            for i in self.BOUGHT_STOCK_LIST:
                self.logger.info(self.BOUGHT_STOCK_LIST[i])

                
                
        
        
        



    
    def get_account_info(self):
        """내 계좌번호 가져오기
        """
        account_list = self.dynamicCall("GetLoginInfo(string)", "ACCNO")
        
        self.account_num = account_list.split(";")[0]
        # print("나의 보유 계좌번호 %s" % self.account_num) # 8036830611
    
    
    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(String)", code)
        return code_name
    
    
    def trade_stock(self, code, quantity, trade):
        """주식 구매 및 판매

        Args:
            code (_type_): 종목번호
            quantity (_type_): 수량
            trade (_type_): 구매(1) 판매(2)
        """
        self.dynamicCall("SendOrder(String, String, String, Long, String, Long, Long, String, String)", ["주식거래", "2003", self.account_num, trade, code, quantity, 0, "03", ""]) #(매수 또는 매도)
        self.TRADE_COUNT += 1
        if self.TRADE_COUNT >= 3:
            self.logger.info(f"{self.TRADE_COUNT}회 이상 매매하여 csv파일에 기록")
            with open('매매기록.csv','a',newline='') as f:
                writer = csv.writer(f)
                for i in self.TRADE_LIST:
                    writer.writerow(i)
                
                
                self.logger.info(f"TRADE_LIST 값 확인: {self.TRADE_LIST}")
                self.TRADE_LIST.clear()
                self.logger.info(f"TRADE_LIST 초기화 확인: {self.TRADE_LIST}")
                self.TRADE_COUNT = 0

        
        
    
    def detail_account_info(self):
        """예수금 가져오기
        """
        # print("예수금 요청하는 부분")
        
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", self.password)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, String)", "조회구분", "2")
        self.dynamicCall("CommRqData(String, String, int, String)", "예수금상세현황요청", "opw00001", "0", self.screen_my_info)
        
        self.detail_account_info_event_loop = QEventLoop()
        self.detail_account_info_event_loop.exec_()
        
        
    def detail_account_mystock(self, sPrevNext = "0"):
        """계좌평가 잔고 내역 요청

        Args:
            sPrevNext (str, optional): _description_. Defaults to "0".
        """
        
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", self.password) 
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, String)", "조회구분", "2")
        self.dynamicCall("CommRqData(String, String, int, String)", "계좌평가잔고내역요청", "opw00018", sPrevNext, self.screen_my_info)
        
        self.detail_account_info_event_loop.exec_()
        
    
    def not_concluded_account(self, sPrevNext = "0"):
        self.logger.info("not_concluded_account()")
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "체결번호", "1") 
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "실시간미체결요청", "opt10075", sPrevNext, self.screen_my_info)
        
        self.detail_account_info_event_loop.exec()
    
    def mystock_value_now(self):
        """계좌평가 현황요청
        """
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", self.password)
        self.dynamicCall("SetInputValue(String, int)", "상장폐지조회구분", 0)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("CommRqData(String, String, String, String)", "계좌평가현황요청", "opw00004", "0", "2010")
        
        self.mystock_value_now_loop = QEventLoop()
        self.mystock_value_now_loop.exec_()
        
        
        
        
    
    def load_condition(self):
        """조건 검색식 가져오기
        """
        self.dynamicCall("GetConditionLoad()")
        
        self.condition_load_loop = QEventLoop()
        self.condition_load_loop.exec_()
        
    def search_condition(self) :
        """가져온 조건 검색식으로 검색 수행
        """
        self.logger.info("search_condition()")
        mSearch = self.dynamicCall("SendCondition(String, String, int, int)", "0156", self.CONDITION_NAME, self.CONDITION_INDEX, 1) ## 조건식 이름, 인덱스 넣어서 바꿀 수 있게 수정하기
        if mSearch != 1:
            self.logger.warning("조건 검색 실패")
        
        self.condition_search_loop = QEventLoop()
        self.condition_search_loop.exec_()
    
    
    def check_stock(self):
        # print("조건식에 검색된 종목 : %s" % self.codeList)
        
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", self.password)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, int)", "조회구분", 2)
        result = self.dynamicCall("CommRqData(String, String, int, String)", "구매주식정보조회", "opw00018", 0, "2001")
        if result != 0:
            self.logger.warning("check_stock() error : %s" % result)
            
            
        
        self.trade_stock_loop = QEventLoop()
        self.trade_stock_loop.exec_()
        
    def regit_realTime_data(self):
        self.Mcode_list = ""
        for i in self.BOUGHT_STOCK_LIST.keys():
            code = i + ';'
            self.Mcode_list += code
        
        self.dynamicCall("CommKwRqData(String, String, int, String, String, String)", [str(self.Mcode_list), "0", len(self.BOUGHT_STOCK_LIST.keys()), "0", "RQNAME", "9999"])
        
        self.regit_realTime_data_loop = QEventLoop()
        self.regit_realTime_data_loop.exec_()
        

         
    def regit_realReg(self):
        self.logger.info("regit_realReg()")

        for i in self.BOUGHT_STOCK_LIST:
            self.logger.info(f"{i} 종목 실시간 등록")

            self.dynamicCall("SetRealReg(String, String, String, String)", "9001", i, "10", "1")
        

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        '''
        모든 tr 요청을 받는 구역, 슬롯
        :param sScrNo: 스크린 번호
        :param sRQName: 사용자 구분명
        :param sTrCode: TR이름(요청 id, tr코드)
        :param sRecordName: 사용 안함
        :param sPrevNext: 연속조회 유무를 판단하는 값 0: 연속(추가조회)데이터 없음, 2:연속(추가조회) 데이터 있음 (다음 페이지가 있는지)
        '''
        
        self.logger.info("trdata_slot() RqName: %s" % sRQName)
        
        if sRQName == "예수금상세현황요청":
            deposit = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "예수금")
            self.logger.info("예수금 %s" % int(deposit))
            self.use_money = int(deposit) * self.use_money_percent # 잔고 금액 쪼개서 투자
            self.use_money = self.use_money / 4
            
            ok_deposit = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "출금가능금액")
            self.logger.info("출금가능금액 %s" % int(ok_deposit))
            
            self.detail_account_info_event_loop.exit()
            
        if sRQName == "계좌평가잔고내역요청":
            
            total_buy_money = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "총매입금액")
            total_buy_money_result = int(total_buy_money)
            
            self.logger.info("총매입금액: %s" % total_buy_money_result)
            
            total_profit_loss_rate = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "총수익률(%)")
            total_profit_loss_rate_result = float(total_profit_loss_rate)
            
            self.logger.info("총수익률(%%): %s" % total_profit_loss_rate_result)
            
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            cnt = 0
            for i in range(rows):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString", sTrCode, sRQName, i, "종목번호").strip()[1:]
                code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명")
                stock_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", sTrCode, sRQName, i, "보유수량")
                buy_price = self.dynamicCall("GetCommData(QString, QString, int, QString", sTrCode, sRQName, i, "매입가")
                learn_rate = self.dynamicCall("GetCommData(QString, QString, int, QString", sTrCode, sRQName, i, "수익률(%)")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString", sTrCode, sRQName, i, "현재가")
                total_chegual_price = self.dynamicCall("GetCommData(QString, QString, int, QString", sTrCode, sRQName, i, "매입금액")
                possible_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", sTrCode, sRQName, i, "매매가능수량")
                
                if code in self.account_stock_dict:
                    pass
                else:
                    self.account_stock_dict[code] = {}
                
                code_nm = code_nm.strip()
                stock_quantity = int(stock_quantity.strip())
                buy_price = int(buy_price.strip())
                learn_rate = float(learn_rate.strip())
                current_price = int(current_price.strip())
                total_chegual_price = int(total_chegual_price.strip())
                possible_quantity = int(possible_quantity.strip())
                
                
                self.account_stock_dict[code].update({"종목명": code_nm})
                self.account_stock_dict[code].update({"보유수량": stock_quantity})
                self.account_stock_dict[code].update({"매입가": buy_price})
                self.account_stock_dict[code].update({"수익률(%)": learn_rate})
                self.account_stock_dict[code].update({"현재가": current_price})
                self.account_stock_dict[code].update({"매입금액": total_chegual_price})
                self.account_stock_dict[code].update({"매매가능수량": possible_quantity})

                cnt += 1
                
            self.logger.info("계좌에 가지고 있는 종목:")
            for i in self.account_stock_dict:
                self.logger.info(self.account_stock_dict[i])
            
            # 다음페이지 존재할 시 다음페이지까지 조회
            if sPrevNext == "2":
                self.detail_account_mystock(sPrevNext="2")
            else:
                self.detail_account_info_event_loop.exit()
                
        if sRQName == "실시간미체결요청":
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            
            for i in range(rows):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString", sTrCode, sRQName, i, "종목번호")
                code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명")
                order_no = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문번호")
                order_status = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문상태")
                order_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문수량")
                order_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문가격")
                order_gubun = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문구분")
                not_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "미체결수량")
                ok_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "체결량")
                
                code = code.strip()
                code_nm = code_nm.strip()
                order_no = int(order_no.strip())
                order_status = order_status.strip()
                order_quantity = int(order_quantity.strip())
                order_price = int(order_price.strip())
                order_gubun = order_gubun.strip().lstrip('+').lstrip('-')
                not_quantity = int(not_quantity.strip())
                ok_quantity = int(ok_quantity.strip())
                
                if order_no in self.not_account_stock_dict: 
                    pass
                else:
                    self.not_account_stock_dict[order_no] = {}
                
                nasd = self.not_account_stock_dict[order_no]
                
                nasd.update({"종목코드" : code})
                nasd.update({"종목명" : code_nm})
                nasd.update({"주문번호" : order_no})
                nasd.update({"주문상태" : order_status})
                nasd.update({"주문수량" : order_quantity})
                nasd.update({"주문가격" : order_price})
                nasd.update({"주문구분" : order_gubun})
                nasd.update({"미체결수량" : not_quantity})
                nasd.update({"체결량" : ok_quantity})
   
                self.logger.info("미체결 종목 : %s " % self.not_account_stock_dict[order_no])
                
            self.detail_account_info_event_loop.exit()
        
        if sRQName == "주식일봉차트조회":
            code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "종목코드")
            code = code.strip()
            self.logger.info(f"{code} 일봉데이터 요청")
            
            
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            self.logger.info(rows)
            
            if sPrevNext == "2":
                self.day_kiwoom_db(code=code, sPrevNext=sPrevNext)
            else:
                self.calculator_event_loop.exit()
            
            
        if sRQName == "계좌평가현황요청":
            mystock = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "총매입금액")
            self.logger.info("계좌평가현황: %s" % mystock)
            self.mystock_value_now_loop.exit()
        
        if sRQName == "구매주식정보조회":
            mystock_count = self.dynamicCall("GetRepeatCnt(String, String)", sTrCode, sRQName)
            # print("구매한 종목 개수 : %s" % mystock_count)
            
            for i in range(mystock_count):
                # print("strCode 확인: ++ %s" % sTrCode)
                mystock_name = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "종목명").strip()
                mystock_code = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "종목번호")[1:].strip()
                mystock_percent = float(self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "수익률(%)"))
                mystock_quantity = int(self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "보유수량"))
                mystock_bought_price = int(self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "매입가"))
                
                
                mystock_info = {"종목명" : mystock_name, "수익률" : mystock_percent, "보유수량" : mystock_quantity, "매입가" : mystock_bought_price, "전고점" : 0, "분할매도수익률" : 0}
                self.BOUGHT_STOCK_LIST[mystock_code] = mystock_info
                # print(f"{mystock_name} 수익률 : {mystock_percent}, 종목번호 확인 : {mystock_code}, 보유 수량 확인 : {mystock_quantity}")
                
            self.logger.info("self.BOUGHT_STOCK_LIST 값 확인 :")
            for i in self.BOUGHT_STOCK_LIST:
                self.logger.info(self.BOUGHT_STOCK_LIST[i])
                
                
            
            self.trade_stock_loop.exit()
            
        if sRQName == "주식틱차트조회요청":
            

            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            # print(rows)
            
            # print(f"체결시간: {result}, 현재가: {price}, 거래량: {trade_qunatity}, 시가: {now_price}, 고가: {high_price}, 저가: {low_price}")
            # print(f"sPrevNext: {sPrevNext}")

            sample_dict = []
            
            for i in range(rows): # rows
                result = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "체결시간").strip()
                price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가").strip()
                trade_qunatity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "거래량").strip()
                now_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "시가").strip()
                high_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "고가").strip()
                low_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "저가").strip()
                
                str = {"체결시간" : result, "현재가" : price, "거래량" : trade_qunatity, "시가" : now_price, "고가" : high_price, "저가" : low_price}
                sample_dict.append(str)
                

            

            
            col_name=["체결시간","현재가","거래량","시가","고가","저가"]
            with open("trades.csv", 'w', newline="") as csvFile:
                wr = csv.DictWriter(csvFile, fieldnames=col_name)
                wr.writeheader()
                for ele in sample_dict:
                    wr.writerow(ele)
                    
                    
                    


            
            
            self.logger.info(f"{rows}")
            
            self.tick_data_loop.exit()
            # if sPrevNext == "2":
            #     self.get_tick_data()
            # else:
            #     self.tick_data_loop.exit()
            
            



    
    def get_code_list_by_market(self, market_code):
        """
        종목 코드들 반환

        Args:
            market_code (_type_): _description_

        Returns:
            _type_: _description_
        """
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market_code)
        code_list = code_list.split(";")[:-1]
        return code_list
            
    
    def calculator_fnc(self):
        """
        종목 분석 실행용 함수
        """
        code_list = self.get_code_list_by_market("10")
        self.logger.info("코스닥 갯수 %s " % len(code_list))
        
        for idx, code in enumerate(code_list):
            
            self.dynamicCall("DisconnectRealData(QString)", self.screen_calculation_stock)
            
            self.logger.info(f"{idx+1} / {len(code_list)} / KOSDAQ Stock Code : {code} is updating.. ")
            
            self.day_kiwoom_db(code=code)

    def day_kiwoom_db(self, code=None, date=None, sPrevNext="0"):
        
        QTest.qWait(3600)
        
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        
        if date != None:
            self.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)
            
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", sPrevNext, self.screen_calculation_stock)
        
        self.calculator_event_loop.exec_()
            
            
    
    def get_tick_data(self):
        
        QTest.qWait(3600)
        
        
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", "039490")
        self.dynamicCall("SetInputValue(QString, QString)", "틱범위", "1")
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        
        
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "주식틱차트조회요청", "opt10079", 0, "7777")
        
        self.tick_data_loop.exec_()
        
        

        
    # 22일(금요일) 할 것 정리
    
    # A. 백테스팅 기능 만들기:
        # 1.조건 검색식에 들어온 종목 opt10079(틱차트조회) 로 조건 검색식에 조회 되기 전, 후 데이터 가져와 엑셀로 저장하기
        # 2.backTest.py 클래스로 만들고 테스트 가능하게 만들기
    # D. 분할 매도 빠르게 팔아버리는 문제 
    # E. 시장 시작전 실행시켜놓으면 장이 시작할 때 에러 나는 문제
    
    
    # 우선도 낮은 것
    
    # 처음 전체 보유수에서 판매 해야하는데 현재 전체 보유수에서 판매하는것 고치기
    # 시간마다 slack 통해 알람
    # 매일 5시마다 점검이기 때문에 버전처리 및 끊긴 로그인 다시 시도 기능
    # 과거 장 데이터와 조건검색 판매 조건까지 설정해서 비교 가능한지 알아보기
    # 서버에 올려서 24시간 돌아가게 만들기
    
    
    # 알아두어야 할 것
    
    # mystock_info = {"종목명" : mystock_name, "수익률" : mystock_percent, "보유수량" : mystock_quantity, "매입가" : mystock_bought_price, "전고점" : 0, "분할매도수익률" : 0}

    
