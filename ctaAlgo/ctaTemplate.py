# encoding: UTF-8

'''
本文件包含了CTA引擎中的策略开发用模板，开发策略时需要继承CtaTemplate类。
'''

from ctaBase import *
from vtConstant import *
import json

########################################################################
class CtaTemplate(object):
    """CTA策略模板"""
    
    # 策略类的名称和作者
    className = 'CtaTemplate'
    author = EMPTY_UNICODE
    
    # MongoDB数据库的名称，K线数据库默认为1分钟
    tickDbName = TICK_DB_NAME
    barDbName = MINUTE_DB_NAME
    
    # 策略的基本参数
    name = EMPTY_UNICODE           # 策略实例名称
    vtSymbol = EMPTY_STRING        # 交易的合约vt系统代码
    tradeparam={}
    productClass = EMPTY_STRING    # 产品类型（只有IB接口需要）
    currency = EMPTY_STRING        # 货币（只有IB接口需要）    
    # 策略的基本变量，由引擎管理
    inited = False                 # 是否进行了初始化
    trading = False                # 是否启动交易，由引擎管理
    pos = {}                        # 持仓情况
    
    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol']
    
    # 变量列表，保存了变量的名称
    varList = [ 'inited',
                'trading',
		'buyPrice',
		'postoday',
		'dfr',
		'dfr_2']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        self.ctaEngine = ctaEngine
	self.fileName = "parameter_" + setting['name'] + ".json"
        # 设置策略的参数
        if setting:
            d = self.__dict__
            for key in self.paramList:
                if key in setting:
                    d[key] = setting[key]
                if key =='vtSymbol':
                    self.vtSymbol=setting[key].split(',')
                print 'vtSymbol',self.vtSymbol
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        raise NotImplementedError

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        raise NotImplementedError

    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送（必须由用户继承实现）"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        raise NotImplementedError
    
    #----------------------------------------------------------------------
    def buy(self, price, volume,vtsymbol, closeFirst,stop=False,price2=None):
        """买开"""
        return self.sendOrder(CTAORDER_BUY, price, volume,vtsymbol, closeFirst,stop)
    
    #----------------------------------------------------------------------
    def sell(self, price, volume, vtsymbol, closeFirst, stop=False,price2=None):
        """卖平"""
        return self.sendOrder(CTAORDER_SELL, price, volume, vtsymbol, closeFirst, stop,price2=None)

    #----------------------------------------------------------------------
    def short(self, price, volume,vtsymbol, closeFirst, stop=False,price2=None):
        """卖开"""
        return self.sendOrder(CTAORDER_SHORT, price, volume, vtsymbol, closeFirst, stop,price2=None)
 
    #----------------------------------------------------------------------
    def cover(self, price, volume, vtsymbol, closeFirst, stop=False,price2=None):
        """买平"""
        return self.sendOrder(CTAORDER_COVER, price, volume,vtsymbol, closeFirst, stop,price2=None)
        
    #----------------------------------------------------------------------
    def sendOrder(self, orderType, price, volume, vtsymbol, closeFirst, stop=False,price2=None):
        """发送委托"""

        if self.trading:
            self.tradeparam['price']=price
            self.tradeparam['volume']=volume
            self.tradeparam['vtsymbol']=vtsymbol
            self.tradeparam['orderType']=orderType
            # 如果stop为True，则意味着发本地停止单
            if stop:
                vtOrderID = self.ctaEngine.sendStopOrder(vtsymbol, orderType, price, volume, self, closeFirst)
            else:
                vtOrderID = self.ctaEngine.sendOrder(vtsymbol, orderType, price, volume, self, closeFirst)
            return vtOrderID
        else:
            return None        
        
    #----------------------------------------------------------------------
    def cancelOrder(self, vtOrderID):
        """撤单"""
        if STOPORDERPREFIX in vtOrderID:
            self.ctaEngine.cancelStopOrder(vtOrderID)
        else:
            self.ctaEngine.cancelOrder(vtOrderID)
    
    #----------------------------------------------------------------------
    def insertTick(self,vtsymbol, tick):
        """向数据库中插入tick数据"""
        self.ctaEngine.insertData(self.tickDbName, vtsymbol, tick)
    
    #----------------------------------------------------------------------
    def insertBar(self, vtsymbol,bar):
        """向数据库中插入bar数据"""
        self.ctaEngine.insertData(self.barDbName, vtsymbol, bar)
        
    #----------------------------------------------------------------------
    def loadTick(self, days,vtsymbol):
        """读取tick数据"""
        return self.ctaEngine.loadTick(self.tickDbName, vtsymbol, days)
    
    #----------------------------------------------------------------------
    def loadBar(self, days,vtsymbol):
        """读取bar数据"""
        return self.ctaEngine.loadBar(self.barDbName, vtsymbol, days)
    
    #----------------------------------------------------------------------
    def writeCtaLog(self, content):
        """记录CTA日志"""
        content = self.name + ':' + content
        self.ctaEngine.writeCtaLog(content)
        
    #----------------------------------------------------------------------
    def putEvent(self):
        """发出策略状态变化事件"""
        self.ctaEngine.putStrategyEvent(self.name)

    #----------------------------------------------------------------------
    def onTradeTime(self, ticktime):
        #if  ticktime.hour ==10 or ticktime.hour ==13  or ticktime.hour ==21 or ticktime.hour ==22 \
        raise NotImplementedError
#======================================================================================

    def loadPosInfo(self):
	self.ctaEngine.loadPosInfo()
#========================================================================================
########################################################################
class DataRecorder(CtaTemplate):
    """
    纯粹用来记录历史数据的工具（基于CTA策略），
    建议运行在实际交易程序外的一个vn.trader实例中，
    本工具会记录Tick和1分钟K线数据。
    """
    className = 'DataRecorder'
    author = u'用Python的交易员'
    
    # 策略的基本参数
    name = EMPTY_UNICODE            # 策略实例名称
    vtSymbol = EMPTY_STRING         # 交易的合约vt系统代码    
    
    # 策略的变量
    bar = None                      # K线数据对象
    barMinute = EMPTY_STRING        # 当前的分钟，初始化设为-1  
    
    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'barMinute']    

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(DataRecorder, self).__init__(ctaEngine, setting)

    #----------------------------------------------------------------------
    def onInit(self):
        """初始化"""
        self.writeCtaLog(u'数据记录工具初始化')
        
    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'数据记录工具启动')
        self.putEvent()
    
    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'数据记录工具停止')
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送"""
        # 收到Tick后，首先插入到数据库里
        self.insertTick(tick)
        
        # 计算K线
        tickMinute = tick.datetime.minute
        
        if tickMinute != self.barMinute:    # 如果分钟变了，则把旧的K线插入数据库，并生成新的K线
            if self.bar:
                self.onBar(self.bar)
            
            bar = CtaBarData()              # 创建新的K线，目的在于防止之前K线对象在插入Mongo中被再次修改，导致出错
            bar.vtSymbol = tick.vtSymbol
            bar.symbol = tick.symbol
            bar.exchange = tick.exchange
            
            bar.open = tick.lastPrice
            bar.high = tick.lastPrice
            bar.low = tick.lastPrice
            bar.close = tick.lastPrice
            
            bar.date = tick.date
            bar.time = tick.time
            bar.datetime = tick.datetime    # K线的时间设为第一个Tick的时间
            
            bar.volume = tick.volume
            bar.openInterest = tick.openInterest
            
            self.bar = bar                  # 这种写法为了减少一层访问，加快速度
            self.barMinute = tickMinute     # 更新当前的分钟
            
        else:                               # 否则继续累加新的K线
            bar = self.bar                  # 写法同样为了加快速度
            
            bar.high = max(bar.high, tick.lastPrice)
            bar.low = min(bar.low, tick.lastPrice)
            bar.close = tick.lastPrice
            
            bar.volume = bar.volume + tick.volume   # 成交量是累加的
            bar.openInterest = tick.openInterest    # 持仓量直接更新
        
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送"""
        pass
    
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送"""
        pass
    
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送"""
        self.insertBar(bar)   

    
    
    
