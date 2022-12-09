from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config_.errorCode import *
import schedule
import time
import datetime


class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        print("kiwoom 클래스입니다")
        
        ####### eventLoop 모음
        self.login_event_loop = None
        self.detail_account_info_event_loop = None
        self.detail_account_info_event_loop_2 = None
        self.condition_load_loop = None
        self.condition_search_loop = None
        self.mystock_value_now_loop = None
        self.sendOrder_loop = None
        self.trade_stock_loop = None
        
        ########################
        
        ####### 변수 모음
        self.account_num = None
        self.password = "1234"
        self.BUY = 1 # 신규매수
        self.SELL = 2 # 신규매도
        self.SELL_STANDARD_PERCENTAGE = -2.5
        
        ########################
        
        
        ####### 계좌 관련 변수
        self.use_money = 0
        self.use_money_percent = 0.5
        ########################

        
        
        
        # 키움API 컨트롤 권한 가져오기
        self.get_ocx_instance()
        
        ## 이벤트
        self.event_slots()
        
        ## 함수
        self.signal_login_commConnect()
        self.get_account_info()
        self.detail_account_info()
        self.detail_account_mystock()
        self.load_condition()
        self.search_condition()
        # for i in range(3):
        #     self.trade_stock() # 장시간 동안 매매 반복
        #self.trade_stock() # 장시간 동안 매매 반복
        while True:
            self.check_stock()
        self.trade_stock("140070", 1, self.SELL)
        
        
        self.mystock_value_now()
        
        
        # while True:
        #     print("#@@@@@")
        #     schedule.run_pending()
        #     time.sleep(1)
    
        
    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
    
    
    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot) # 로그인 요청시 발생하는 이벤트
        self.OnReceiveTrData.connect(self.trdata_slot) # trData 조회시 발생하는 이벤트
        self.OnReceiveConditionVer.connect(self.condition_load_slot) # 조건 검색식 불러오기 요청시 발생하는 이벤트
        self.OnReceiveTrCondition.connect(self.condition_search_slot) # 조건 검색 요청에 대한 서버 응답 수신시 발생하는 이벤트
        self.OnReceiveMsg.connect(self.stock_slot) 
        
    
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


        # 리스트의 공백 문자열 제거
        codeList = codeList.split(";")
        self.codeList = list(filter(None, codeList))
        
        # 조건검색식으로 나온 결과 리스트 개별 결과로 재단
        for i in codeList:
            result = self.get_master_code_name(i)
            print("조회 결과 주식 이름: %s" % result)
            
        
        self.condition_search_loop.exit()
        
        
    def condition_load_slot(self, iRet, sMsg):
        print(sMsg) # 조건 검색식 불러오기 서버 응답 결과
        self.condition_load_loop.exit()
        
    def stock_slot(self, scrNo, rqName, trCode, msg):
        """ 주문, 잔고처리 관련 서버 통신후 수신한 서버메시지 알림

        Args:
            scrNo (_type_): 화면번호
            rqName (_type_): 사용자 구분명
            trCode (_type_): TR이름
            msg (_type_): 서버에서 전달하는 메시지
        """
        print("stock_slot 메시지 확인: %s " % msg)
        print("stock_slot rqName 확인: %s " % rqName)

    
    def get_account_info(self):
        """내 계좌번호 가져오기
        """
        account_list = self.dynamicCall("GetLoginInfo(string)", "ACCNO")
        
        self.account_num = account_list.split(";")[0]
        print("나의 보유 계좌번호 %s" % self.account_num) # 8036830611
    
    
    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(String)", code)
        return code_name
    
    # def buy_stock(self):
    #     self.dynamicCall("SendOrder(String, String, String, Long, String, Long, Long, String, String)", ["주식구매", "2000", self.account_num, 1, i, 1, 0, "03", ""]) #(매수 또는 매도)
    #     return "a"
    
    def trade_stock(self, code, quantity, trade):
        """주식 판매

        Args:
            code (_type_): 종목번호
            quantity (_type_): 수량
            trade (_type_): 구매(1) 판매(2)
        """
        self.dynamicCall("SendOrder(String, String, String, Long, String, Long, Long, String, String)", ["주식거래", "2003", self.account_num, trade, code, quantity, 0, "03", ""]) #(매수 또는 매도)

        
    
    def detail_account_info(self):
        """예수금 가져오기
        """
        print("예수금 요청하는 부분")
        
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", self.password)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, String)", "조회구분", "2")
        self.dynamicCall("CommRqData(String, String, int, String)", "예수금상세현황요청", "opw00001", "0", "2000")
        
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
        self.dynamicCall("CommRqData(String, String, int, String)", "계좌평가잔고내역요청", "opw00018", sPrevNext, "2000")
        
        self.detail_account_info_event_loop_2 = QEventLoop()
        self.detail_account_info_event_loop_2.exec_()
        
    
    def mystock_value_now(self):
        """계좌평가 현황요청
        """
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", self.password)
        self.dynamicCall("SetInputValue(String, int)", "상장폐지조회구분", 0)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("CommRqData(String, String, String, String)", "계좌평가현황요청", "opw00004", "0", "2000")
        self.mystock_value_now_loop = QEventLoop()
        self.mystock_value_now_loop.exec_()
        
    
    def load_condition(self):
        """조건 검색식 가져오기
        """
        self.dynamicCall("GetConditionLoad()")
        
        self.condition_load_loop = QEventLoop()
        self.condition_load_loop.exec_()
        
    def search_condition(self):
        """가져온 조건 검색식으로 검색 수행
        """
        mSearch = self.dynamicCall("SendCondition(String, String, int, int)", "0156", "eb", 0, 0)
        print("검색된 조건식 여부: %s" % mSearch)
        
        self.condition_search_loop = QEventLoop()
        self.condition_search_loop.exec_()
    
    
    def check_stock(self):
        print("조건식에 검색된 종목 : %s" % self.codeList)
        
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", self.password)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(String, int)", "조회구분", 2)
        result = self.dynamicCall("CommRqData(String, String, int, String)", "수익률조회", "opw00018", 0, "2001")
        if result != 0:
            print("trade_stock() error : %s" % result)
        
        self.trade_stock_loop = QEventLoop()
        self.trade_stock_loop.exec_()
        
        
    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        '''
        모든 tr 요청을 받는 구역, 슬롯
        :param sScrNo: 스크린 번호
        :param sRQName: 사용자 구분명
        :param sTrCode: TR이름(요청 id, tr코드)
        :param sRecordName: 사용 안함
        :param sPrevNext: 연속조회 유무를 판단하는 값 0: 연속(추가조회)데이터 없음, 2:연속(추가조회) 데이터 있음 (다음 페이지가 있는지)
        '''
        print("수신된 trdata_slot RqName값 확인: %s" % sRQName)
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
            
            print("총매입금액 %s" % total_buy_money_result)
            
            total_profit_loss_rate = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "총수익률(%)")
            total_profit_loss_rate_result = float(total_profit_loss_rate)
            
            print("총수익률(%%) : %s" % total_profit_loss_rate_result)
            
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            cnt = 0
            for i in range(rows):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString", sTrCode, sRQName, cnt, "종목번호")
            
            self.detail_account_info_event_loop_2.exit()
            
        if sRQName == "계좌평가현황요청":
            print("들어옴?")
            mystock = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "잔고")
            print("계좌평가현황: %s" % mystock)
            self.mystock_value_now_loop.exit()
            
        if sRQName == "수익률조회":
            mystock_count = self.dynamicCall("GetRepeatCnt(String, String)", sTrCode, sRQName)
            print("구매한 종목 개수 : %s" % mystock_count)
            for i in range(mystock_count):
                mystock_name = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "종목명")
                mystock_code = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "종목번호")[1:]
                mystock_percent = float(self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "수익률(%)"))
                mystock_quantity = int(self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, i, "보유수량"))
                print(f"{mystock_name.strip()}의 수익률 : {float(mystock_percent)} \n종목번호 확인 : {mystock_code} \n보유 수량 확인 : {mystock_quantity}")
                if mystock_percent <= self.SELL_STANDARD_PERCENTAGE:
                    print("판매 %s" % mystock_code)
                    IS_IT_SUCCESSFUL = self.dynamicCall("SendOrder(sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, Price, HogaGb, OrgOrderNo)", ["주식구매", "2002", self.account_num, self.SELL, mystock_code, mystock_quantity, 0, "03", ""])#(매수 또는 매도)
                    print("IS_IT_SUCCESSFUL : %s " % IS_IT_SUCCESSFUL)
                    if IS_IT_SUCCESSFUL != 0:
                        print("tradata_slot _ SendOrder() error : %s" % IS_IT_SUCCESSFUL)
                    
                    
                    

            self.trade_stock_loop.exit()
    
    

