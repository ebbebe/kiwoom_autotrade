from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config_.errorCode import *
import schedule
import time
import datetime
import math


class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        print("kiwoom 클래스입니다")
        
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
        self.LOSS_BASED_PERCENTAGE = -2 # 손절시 전량 매도 퍼센트 기준
        self.PROFIT_BEGINNING_PERCENTAGE = 3 # 몇퍼센트 올랐을 때 매도 할 것인지 첫번째 기준
        self.PROFIT_MIDDLE_PERCENTAGE = 7 # 두번째 기준
        self.PROFIT_END_PERCENTAGE = 10 # 세번째 기준
        self.SELL_BEGINNING_PERCENTAGE = 20 # 첫번째 매도시 몇퍼센트 매도할 것인지
        self.SELL_MIDDLE_PERCENTAGE = 30 # 두번째 매도시 몇퍼센트 매도할 것인지
        
        
        self.idx = 0
        self.CONDITION_NAME = "1분봉단타"
        
        self.BOUGHT_STOCK_LIST = dict() # 보유 주식 리스트
        self.account_stock_dict = {} # 영상 강의 학습용 딕셔너리
        self.not_account_stock_dict = {} # 영상 강의 학습용 딕셔너리
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
        self.not_concluded_account() # 미체결 요청
        
        self.calculator_fnc() # 종목 분석용, 임시용으로 실행
        
        self.load_condition()
        self.search_condition()
        
        self.check_stock()
        self.regit_realTime_data()
        
        

    
        
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
        print(errors(errCode))
        
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
            if result != "":
                pass
            print("조건검색: %s" % result)
            
        
        self.condition_search_loop.exit()
        
        
    def condition_load_slot(self, iRet, sMsg):
        print(sMsg) # 조건 검색식 불러오기 서버 응답 결과
        ConditionNameList = self.dynamicCall("GetConditionNameList()").split(";")
        print(f"보유 조건식:\n{ConditionNameList}")
        
        self.condition_load_loop.exit()
        
    def stock_slot(self, scrNo, rqName, trCode, msg):
        """ 주문, 잔고처리 관련 서버 통신후 수신한 서버메시지 알림

        Args:
            scrNo (_type_): 화면번호
            rqName (_type_): 사용자 구분명
            trCode (_type_): TR이름
            msg (_type_): 서버에서 전달하는 메시지
        """
        print(f"stock_slot() msg: {msg}" )
        
    def real_data_slot(self, sCode, sRealType):
        
        if sRealType == "종목프로그램매매":
            #현재 보유 하고 있는 주식을 실시간 데이터에 등록해 판매하기 위해 대기중
            
            
            now_price = abs(float(self.dynamicCall("GetCommRealData(String, int)", sCode, 10)))
            self.idx += 1
            # print(f"종목프로그램매매 : 종목명: {self.BOUGHT_STOCK_LIST[sCode]['종목명']}, 종목코드: {sCode} 현재가: {abs(int(now_price))}, {self.idx} 번째 ")
            
            # 수익률 계산
            quantity = self.BOUGHT_STOCK_LIST[sCode]['보유수량']
            bought_price = float(self.BOUGHT_STOCK_LIST[sCode]['매입가'])
            percent = round(((now_price - bought_price) / bought_price) * 100, 2)

            print("@@@@@@@@@@@@@@@@@팔림??@@@@@@@@@@@@@@@@@@@@@@")
            print(self.BOUGHT_STOCK_LIST[sCode])
            
            
            if percent <= self.LOSS_BASED_PERCENTAGE:
                #손실나서 전량 매도
                self.trade_stock(sCode, quantity, self.SELL)
                print("손절(전량매도)")
                
            elif (percent >= self.PROFIT_BEGINNING_PERCENTAGE) and (percent < self.PROFIT_MIDDLE_PERCENTAGE):
                # 첫번째 매도
                sell_quantity = math.floor(quantity * self.SELL_BEGINNING_PERCENTAGE / 100)
                self.trade_stock(sCode, sell_quantity, self.SELL)
                print("첫번째 매도")
                print(f"sell_quantity: {sell_quantity}")
                
            elif (percent >= self.PROFIT_MIDDLE_PERCENTAGE) and (percent < self.PROFIT_END_PERCENTAGE):
                # 두번째 매도
                print("두번째 매도")
                sell_quantity = math.floor(quantity * self.SELL_MIDDLE_PERCENTAGE / 100)
                print(f"sell_quantity: {sell_quantity}")
                self.trade_stock(sCode, sell_quantity, self.SELL)
            
            elif percent >= self.PROFIT_END_PERCENTAGE :
                # 마지막(전량) 매도
                print("마지막(전량) 매도")
                print(f"sell_quantity: {sell_quantity}")
                self.trade_stock(sCode, quantity, self.SELL)
                
            
            
            
        self.regit_realTime_data_loop.exit()
        
    
    def real_condition_slot(self, sCode, sType, sConditionName, sConditionIndex):
        print(f"real_condition(): {sCode}, {sType}, {sConditionName}, {sConditionIndex}" )
        if sType == "I": #종목편입
            self.trade_stock(sCode, 1, self.BUY)
            self.dynamicCall("SetRealReg(String, String, String, String)", "9001", sCode, "10", 1)
            print("조건검색 종목편입: %s " %sCode)
        elif sType == "D": #종목이탈
            # self.dynamicCall("SetRealRemove(String, String)", "ALL", sCode)
            print("조건검색 종목이탈: %s " %sCode)
        
            
            
    def chejan_slot(self, sGubun, nItemCnt, sFidList):
        print(f"체결 데이터:\nsGubun: {sGubun}, nItemCnt: {nItemCnt}, sFidList: {sFidList}")
        # sGubun=1(잔고변경) : 9201;9001;917;916;302;10;930;931;932;933;945;946;950;951;27;28;307;8019;957;958;918;990;991;992;993;959;924;10010;25;11;12;306;305;970;10012;10025;10011
        # sGubun=0(접수및체결) : 9201;9203;9205;9001;912;913;302;900;901;902;903;904;905;906;907;908;909;910;911;10;27;28;914;915;938;939;919;920;921;922;923;949;10010;969;819
        
        if sGubun == "0":
            #접수및체결
            bought_sPrice = self.dynamicCall("GetChejanData(int)", 910).strip()
            bought_sCode = self.dynamicCall("GetChejanData(int)", 9001).strip()[1:]
            bought_sName = self.dynamicCall("GetChejanData(int)", 302).strip()
            bought_sQuantity = self.dynamicCall("GetChejanData(int)", 900).strip()
            print(f"접수및체결:\n매입가: {bought_sPrice}, 종목코드: {bought_sCode}, 종목명: {bought_sName}, 주문수량: {bought_sQuantity}")
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
            
            print(f"잔고변경:\n 종목명: {sName}, 수익률: {profit_percent}, 보유수량: {sQuantity}, 매입가: {bought_sPrice}, 체결구분: {sell_buy}")
            
            # bought_stock_list 업데이트
            if sell_buy == "매도" and sQuantity == "0":
                del self.BOUGHT_STOCK_LIST[sCode]   
                self.dynamicCall("SetRealRemove(String, String)", "ALL", sCode) #전량매도시 실시간등록 해제
                print(f"BOUGHT_STOCK_LIST에서 {sName} 삭제")
                    
            elif sell_buy == "매수":
                self.BOUGHT_STOCK_LIST[sCode].update({"종목명" : sName})
                self.BOUGHT_STOCK_LIST[sCode].update({"수익률" : profit_percent})
                self.BOUGHT_STOCK_LIST[sCode].update({"보유수량" : sQuantity})
                self.BOUGHT_STOCK_LIST[sCode].update({"매입가" : total_bought_sPrice})
            
            
            print("BOUGHT_STOCK_LIST UPDATE:")
            for i in self.BOUGHT_STOCK_LIST:
                print(self.BOUGHT_STOCK_LIST[i])
        
        
        
        # 이곳에서 bought_stock_list 초기화 하기
        self.BOUGHT_STOCK_LIST[bought_sCode].update({"보유수량" : bought_sQuantity})
        self.BOUGHT_STOCK_LIST[bought_sCode].update({""})
        
        
        
        # 월요일 되면 할 것 정리
        # chejan_slot에서 체결과 잔고으로 들어온 데이터 둘 다 종목코드(9001), 종목명(302)
        # 조회시 잔고 내의 전체 데이터 조회가 가능한지, 아니면 하나의 데이터만 조회 가능한지 알아보기
        # 그 후 bought_stock_list 딕셔너리에 값 새로 업데이트 하기
        # real_data_slot() 의 종목프로그램매매 부분 조건별 매도식 quantity 부분 다시 만들어야함


    
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
        print("not_concluded_account()")
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
        print("search_condition()")
        mSearch = self.dynamicCall("SendCondition(String, String, int, int)", "0156", self.CONDITION_NAME, 9, 1) ## 조건식 이름, 인덱스 넣어서 바꿀 수 있게 수정하기
        if mSearch != 1:
            print("조건 검색 실패")
        
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
            print("check_stock() error : %s" % result)
        
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
        print("regit_realReg()")
        self.dynamicCall("SetRealReg(String, String, String, String)", "9998", self.Mcode_list, "10", )
        

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        '''
        모든 tr 요청을 받는 구역, 슬롯
        :param sScrNo: 스크린 번호
        :param sRQName: 사용자 구분명
        :param sTrCode: TR이름(요청 id, tr코드)
        :param sRecordName: 사용 안함
        :param sPrevNext: 연속조회 유무를 판단하는 값 0: 연속(추가조회)데이터 없음, 2:연속(추가조회) 데이터 있음 (다음 페이지가 있는지)
        '''
        
        print("trdata_slot() RqName: %s" % sRQName)
        
        if sRQName == "예수금상세현황요청":
            deposit = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "예수금")
            print("예수금 %s" % int(deposit))
        
            self.use_money = int(deposit) * self.use_money_percent # 잔고 금액 쪼개서 투자
            self.use_money = self.use_money / 4
            
            ok_deposit = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "출금가능금액")
            print("출금가능금액 %s" % int(ok_deposit))
            
            self.detail_account_info_event_loop.exit()
            
        if sRQName == "계좌평가잔고내역요청":
            
            total_buy_money = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "총매입금액")
            total_buy_money_result = int(total_buy_money)
            
            print("총매입금액: %s" % total_buy_money_result)
            
            total_profit_loss_rate = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "총수익률(%)")
            total_profit_loss_rate_result = float(total_profit_loss_rate)
            
            print("총수익률(%%): %s" % total_profit_loss_rate_result)
            
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
                
            print("계좌에 가지고 있는 종목:")
            for i in self.account_stock_dict:
                print(self.account_stock_dict[i])
            
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
   
                print("미체결 종목 : %s " % self.not_account_stock_dict[order_no])
                
            self.detail_account_info_event_loop.exit()
            
        if sRQName == "계좌평가현황요청":
            mystock = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "총매입금액")
            print("계좌평가현황: %s" % mystock)
            self.mystock_value_now_loop.exit()
        
        if sRQName == "구매주식정보조회":
            mystock_count = self.dynamicCall("GetRepeatCnt(String, String)", sTrCode, sRQName)
            # print("구매한 종목 개수 : %s" % mystock_count)
            self.LIST_STOCKS_I_BOUGHT = dict() # 계좌 구매 주식 리스트 초기화
            
            for i in range(mystock_count):
                # print("strCode 확인: ++ %s" % sTrCode)
                mystock_name = str(self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "종목명")).strip()
                mystock_code = str(self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "종목번호")[1:]).strip()
                mystock_percent = float(self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "수익률(%)"))
                mystock_quantity = int(self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "보유수량"))
                mystock_bought_price = int(self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "매입가"))
                
                
                mystock_info = {"종목명" : mystock_name, "수익률" : mystock_percent, "보유수량" : mystock_quantity, "매입가" : mystock_bought_price}
                self.BOUGHT_STOCK_LIST[mystock_code] = mystock_info
                # print(f"{mystock_name} 수익률 : {mystock_percent}, 종목번호 확인 : {mystock_code}, 보유 수량 확인 : {mystock_quantity}")
                
            print("self.BOUGHT_STOCK_LIST 값 확인 :")
            for i in self.BOUGHT_STOCK_LIST:
                print(self.BOUGHT_STOCK_LIST[i])
            self.trade_stock_loop.exit()
            
    
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
        print("코스닥 갯수 %s " % len(code_list))

    def day_kiwoom_db(self, code=None, date=None, sPrevNext="0"):
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        
        if date != None:
            self.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)
            
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", sPrevNext, self.screen_calculation_stock)
            
            
    
    
    
    # 21일 수요일 할 것 정리
    # real_data_slot 의 sell_quantity 값 확인하기 ([RC4099] 모의투자 주문수량(0)을 확인하세요.)
    #  ?? 팔림?? 들어왔는데 왜 안팔리는지, 왜 들어왔는지 확인하기
    # 처음 전체 보유수에서 판매 해야하는데 현재 전체 보유수에서 판매하는것 고치기
    # 매수 금액 일정하게 맞추는 기능 구현
    
