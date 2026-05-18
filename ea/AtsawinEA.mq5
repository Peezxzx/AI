//+------------------------------------------------------------------+
//|                                          AtsawinEA.mq5           |
//|                    Atsawin AI Trading EA for MetaTrader 5         |
//|                                                                    |
//|  อ่านสัญญาณจาก JSON file (เขียนโดย Python Bridge)                  |
//|  แล้ว execute order บน MT5 พร้อม SL/TP/Position Sizing             |
//|                                                                    |
//|  Flow:  Python Bridge → latest_signal.json → AtsawinEA → Execute  |
//+------------------------------------------------------------------+
#property copyright "Atsawin AI"
#property link      ""
#property version   "1.00"
#property strict

//+------------------------------------------------------------------+
//| CONFIG — แก้ค่าตรงนี้                                              |
//+------------------------------------------------------------------+
input string   InpSignalFile    = "atsawin\\latest_signal.json";  // ไฟล์สัญญาณ
input string   InpStatusFile    = "atsawin\\ea_status.json";      // ไฟล์สถานะ
input long     InpMagicNumber   = 20250518;                       // Magic Number
input double   InpRiskPercent   = 2.0;                            // Risk % ต่อเทรด
input double   InpMaxLot        = 1.0;                             // Lot สูงสุด
input double   InpMinLot        = 0.01;                            // Lot ต่ำสุด
input double   InpMaxSpreadPt   = 30;                              // Spread สูงสุด (points)
input double   InpSlippagePt    = 10;                              // Slippage สูงสุด (points)
input int      InpMaxOpenTrades = 3;                               // จำนวนเทรดสูงสุด
input double   InpMinConfidence = 0.5;                             // ความมั่นใจขั้นต่ำ
input int      InpSignalExpiry  = 60;                              // อายุสัญญาณ (นาที)
input bool     InpEnableLogging = true;                            // เปิด log

//+------------------------------------------------------------------+
//| GLOBAL VARIABLES                                                  |
//+------------------------------------------------------------------+
string   g_signalFile;          // เส้นทางไฟล์สัญญาณเต็ม
string   g_statusFile;          // เส้นทางไฟล์สถานะเต็ม
string   g_logFile;             // เส้นทางไฟล์ log
datetime g_lastSignalTime;      // เวลาอ่านสัญญาณล่าสุด
datetime g_lastBarTime;         // เวลา bar ล่าสุด
int      g_totalTrades;         // จำนวนเทรดทั้งหมด
double   g_totalPnL;            // PnL รวม
bool     g_initialized;         // เริ่มต้นแล้ว?

// โครงสร้างสัญญาณ
struct SignalData
{
   string   version;
   string   signal;             // "buy" / "sell" / "hold"
   string   symbol;             // สัญญา
   string   timeframe;
   double   confidence;         // 0-1
   string   consensus;          // "strong_buy" / "weak_buy" / etc
   double   buy_score;
   double   sell_score;
   double   entry_price;
   double   stop_loss;
   double   take_profit;
   double   position_size;
   double   risk_reward_ratio;
   string   timestamp;          // ISO timestamp
   bool     valid;              // อ่านสำเร็จ?
};

SignalData g_currentSignal;     // สัญญาณปัจจุบัน

//+------------------------------------------------------------------+
//| Symbol Mapping: API name → MT5 name                               |
//+------------------------------------------------------------------+
string SymbolToMT5(string apiSymbol)
{
   if(apiSymbol == "BTCUSDT") return "BTCUSD";
   if(apiSymbol == "ETHUSDT") return "ETHUSD";
   if(apiSymbol == "XRPUSDT") return "XRPUSD";
   if(apiSymbol == "BNBUSDT") return "BNBUSD";
   if(apiSymbol == "SOLUSDT") return "SOLUSD";
   if(apiSymbol == "XAUUSDT") return "XAUUSD";
   if(apiSymbol == "EURUSDT") return "EURUSD";
   if(apiSymbol == "GBPUSDT") return "GBPUSD";
   return apiSymbol;  // ถ้าไม่ตรง ใช้ตัวเดิม
}

//+------------------------------------------------------------------+
//| Logging                                                           |
//+------------------------------------------------------------------+
void LogMessage(string msg)
{
   if(!InpEnableLogging) return;
   string fullMsg = TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + " [AtsawinEA] " + msg;
   Print(fullMsg);

   // เขียนลงไฟล์
   int handle = FileOpen(g_logFile, FILE_WRITE|FILE_TXT|FILE_SHARE_READ|FILE_COMMON);
   if(handle != INVALID_HANDLE)
   {
      FileSeek(handle, 0, SEEK_END);
      FileWriteString(handle, fullMsg + "\r\n");
      FileClose(handle);
   }
}

//+------------------------------------------------------------------+
//| อ่านสัญญาณจาก JSON file                                           |
//+------------------------------------------------------------------+
bool ReadSignal(SignalData &signal)
{
   signal.valid = false;

   // ตรวจว่าไฟล์มีอยู่
   if(!FileIsExist(g_signalFile, FILE_COMMON))
   {
      LogMessage("Signal file not found: " + g_signalFile);
      return false;
   }

   // อ่านไฟล์
   int handle = FileOpen(g_signalFile, FILE_READ|FILE_TXT|FILE_SHARE_READ|FILE_COMMON);
   if(handle == INVALID_HANDLE)
   {
      LogMessage("Cannot open signal file");
      return false;
   }

   string content = "";
   while(!FileIsEnding(handle))
   {
      content += FileReadString(handle) + "\n";
   }
   FileClose(handle);

   // Parse JSON แบบ manual (MQL5 ไม่มี JSON library built-in)
   signal.signal      = JSONString(content, "signal");
   signal.symbol      = JSONString(content, "symbol");
   signal.timeframe   = JSONString(content, "timeframe");
   signal.confidence  = JSONDouble(content, "confidence");
   signal.consensus   = JSONString(content, "consensus");
   signal.buy_score   = JSONDouble(content, "buy_score");
   signal.sell_score  = JSONDouble(content, "sell_score");
   signal.entry_price = JSONDouble(content, "entry_price");
   signal.stop_loss   = JSONDouble(content, "stop_loss");
   signal.take_profit = JSONDouble(content, "take_profit");
   signal.position_size = JSONDouble(content, "position_size");
   signal.risk_reward_ratio = JSONDouble(content, "risk_reward_ratio");
   signal.timestamp   = JSONString(content, "timestamp");
   signal.version     = JSONString(content, "version");

   // Map symbol
   signal.symbol = SymbolToMT5(signal.symbol);

   // ตรวจความถูกต้อง
   if(signal.signal == "" || signal.symbol == "")
   {
      LogMessage("Invalid signal: empty signal or symbol");
      return false;
   }

   // ตรวจอายุสัญญาณ
   if(signal.timestamp != "")
   {
      datetime sigTime = StringToTime(signal.timestamp);
      int ageMinutes = (int)((TimeCurrent() - sigTime) / 60);
      if(ageMinutes > InpSignalExpiry)
      {
         LogMessage("Signal expired (" + IntegerToString(ageMinutes) + " min old)");
         return false;
      }
   }

   signal.valid = true;
   return true;
}

//+------------------------------------------------------------------+
//| JSON Parser helpers (simple, no external lib)                     |
//+------------------------------------------------------------------+
string JSONString(string json, string key)
{
   string searchKey = "\"" + key + "\"";
   int pos = StringFind(json, searchKey);
   if(pos < 0) return "";

   pos = StringFind(json, ":", pos + StringLen(searchKey));
   if(pos < 0) return "";

   // ข้าม whitespace
   pos++;
   while(pos < StringLen(json) && (json[pos] == ' ' || json[pos] == '\t'))
      pos++;

   if(pos >= StringLen(json)) return "";

   // ถ้าเป็น string (มี quote)
   if(json[pos] == '"')
   {
      int end = StringFind(json, "\"", pos + 1);
      if(end < 0) return "";
      return StringSubstr(json, pos + 1, end - pos - 1);
   }

   // ถ้าเป็น number หรือ boolean
   int end = pos;
   while(end < StringLen(json) && json[end] != ',' && json[end] != '}' && json[end] != '\n')
      end++;
   string val = StringSubstr(json, pos, end - pos);
   StringTrimRight(val);
   return val;
}

double JSONDouble(string json, string key)
{
   string val = JSONString(json, key);
   if(val == "") return 0.0;
   return StringToDouble(val);
}

//+------------------------------------------------------------------+
//| ตรวจสอบว่ามี position เปิดอยู่แล้วหรือไม่                            |
//+------------------------------------------------------------------+
bool HasOpenPosition(string symbol)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
      return true;
   }
   return false;
}

//+------------------------------------------------------------------+
//| นับจำนวน position ที่เปิดอยู่                                      |
//+------------------------------------------------------------------+
int CountOpenPositions()
{
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
      count++;
   }
   return count;
}

//+------------------------------------------------------------------+
//| คำนวณ Position Size จาก Risk %                                    |
//+------------------------------------------------------------------+
double CalculateLotSize(string symbol, double stopLossPrice)
{
   double accountBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmount = accountBalance * InpRiskPercent / 100.0;

   double symbolPoint = SymbolInfoDouble(symbol, SYMBOL_POINT);
   int    symbolDigits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);

   if(stopLossPrice <= 0 || ask <= 0) return InpMinLot;

   double slDistance = MathAbs(ask - stopLossPrice);
   double tickValue  = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize   = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);

   if(tickValue <= 0 || tickSize <= 0) return InpMinLot;

   double lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
   double minLot  = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);

   // คำนวณ lot
   double lots = riskAmount / (slDistance / tickSize * tickValue);

   // Round ให้ตรง lot step
   lots = MathFloor(lots / lotStep) * lotStep;

   // Clamp
   lots = MathMax(lots, MathMax(minLot, InpMinLot));
   lots = MathMin(lots, MathMin(maxLot, InpMaxLot));

   // ถ้า signal มี position_size ให้ใช้ถ้าเล็กกว่า
   if(g_currentSignal.position_size > 0)
   {
      lots = MathMin(lots, g_currentSignal.position_size);
   }

   return NormalizeDouble(lots, 2);
}

//+------------------------------------------------------------------+
//| Execute Buy Order                                                 |
//+------------------------------------------------------------------+
bool ExecuteBuy(string symbol, double sl, double tp, double lots)
{
   double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);

   // ถ้า signal มี entry_price ที่ต่างจาก ask มาก → ใช้ ask
   double entry = ask;
   if(g_currentSignal.entry_price > 0)
   {
      double diff = MathAbs(g_currentSignal.entry_price - ask) / SymbolInfoDouble(symbol, SYMBOL_POINT);
      if(diff < 100) entry = g_currentSignal.entry_price;  // ถ้าต่างกันไม่เกิน 100 points
   }

   sl = NormalizeDouble(sl, digits);
   tp = NormalizeDouble(tp, digits);

   MqlTradeRequest request = {};
   MqlTradeResult  result  = {};

   request.action    = TRADE_ACTION_DEAL;
   request.symbol    = symbol;
   request.volume    = lots;
   request.type      = ORDER_TYPE_BUY;
   request.price     = entry;
   request.sl        = sl;
   request.tp        = tp;
   request.deviation = InpSlippagePt;
   request.magic     = InpMagicNumber;
   request.comment   = "AtsawinAI";
   request.type_filling = ORDER_FILLING_IOC;

   if(!OrderSend(request, result))
   {
      LogMessage("BUY OrderSend failed: " + IntegerToString(GetLastError()));
      return false;
   }

   if(result.retcode != TRADE_RETCODE_DONE && result.retcode != TRADE_RETCODE_PLACED)
   {
      LogMessage("BUY failed, retcode: " + IntegerToString(result.retcode));
      return false;
   }

   LogMessage("✅ BUY executed: " + symbol + " " + DoubleToString(lots, 2) + " lots @ " +
              DoubleToString(entry, digits) + " SL=" + DoubleToString(sl, digits) +
              " TP=" + DoubleToString(tp, digits));
   g_totalTrades++;
   return true;
}

//+------------------------------------------------------------------+
//| Execute Sell Order                                                |
//+------------------------------------------------------------------+
bool ExecuteSell(string symbol, double sl, double tp, double lots)
{
   double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);

   double entry = bid;
   if(g_currentSignal.entry_price > 0)
   {
      double diff = MathAbs(g_currentSignal.entry_price - bid) / SymbolInfoDouble(symbol, SYMBOL_POINT);
      if(diff < 100) entry = g_currentSignal.entry_price;
   }

   sl = NormalizeDouble(sl, digits);
   tp = NormalizeDouble(tp, digits);

   MqlTradeRequest request = {};
   MqlTradeResult  result  = {};

   request.action    = TRADE_ACTION_DEAL;
   request.symbol    = symbol;
   request.volume    = lots;
   request.type      = ORDER_TYPE_SELL;
   request.price     = entry;
   request.sl        = sl;
   request.tp        = tp;
   request.deviation = InpSlippagePt;
   request.magic     = InpMagicNumber;
   request.comment   = "AtsawinAI";
   request.type_filling = ORDER_FILLING_IOC;

   if(!OrderSend(request, result))
   {
      LogMessage("SELL OrderSend failed: " + IntegerToString(GetLastError()));
      return false;
   }

   if(result.retcode != TRADE_RETCODE_DONE && result.retcode != TRADE_RETCODE_PLACED)
   {
      LogMessage("SELL failed, retcode: " + IntegerToString(result.retcode));
      return false;
   }

   LogMessage("✅ SELL executed: " + symbol + " " + DoubleToString(lots, 2) + " lots @ " +
              DoubleToString(entry, digits) + " SL=" + DoubleToString(sl, digits) +
              TP=" + DoubleToString(tp, digits));
   g_totalTrades++;
   return true;
}

//+------------------------------------------------------------------+
//| ตรวจ Spread                                                       |
//+------------------------------------------------------------------+
bool IsSpreadOK(string symbol)
{
   double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   if(point <= 0) return true;

   int spreadPoints = (int)((ask - bid) / point);
   if(spreadPoints > InpMaxSpreadPt)
   {
      LogMessage("Spread too high: " + IntegerToString(spreadPoints) + " > " + IntegerToString(InpMaxSpreadPt));
      return false;
   }
   return true;
}

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   // สร้างเส้นทางไฟล์
   string terminalPath = TerminalInfoString(TERMINAL_DATA_PATH);
   g_signalFile = terminalPath + "\\MQL5\\Files\\" + InpSignalFile;
   g_statusFile = terminalPath + "\\MQL5\\Files\\" + InpStatusFile;
   g_logFile    = terminalPath + "\\MQL5\\Files\\atsawin\\ea_log.txt";

   // สร้างโฟลเดอร์
   FolderCreate(terminalPath + "\\MQL5\\Files\\atsawin");

   LogMessage("========================================");
   LogMessage("Atsawin EA v1.0 Initialized");
   LogMessage("Signal file: " + g_signalFile);
   LogMessage("Symbol: " + _Symbol);
   LogMessage("Magic: " + IntegerToString(InpMagicNumber));
   LogMessage("Risk: " + DoubleToString(InpRiskPercent, 1) + "%");
   LogMessage("========================================");

   g_initialized = true;
   g_totalTrades = 0;
   g_totalPnL = 0;
   g_lastBarTime = 0;

   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   LogMessage("Atsawin EA stopped. Total trades: " + IntegerToString(g_totalTrades));
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   if(!g_initialized) return;

   // ตรวจว่าเปิด bar ใหม่หรือยัง (ทำงานครั้งเดียวต่อ bar)
   datetime currentBarTime = iTime(_Symbol, _Period, 0);
   if(currentBarTime == g_lastBarTime) return;  // ยังเป็น bar เดิม
   g_lastBarTime = currentBarTime;

   // อ่านสัญญาณ
   SignalData sig;
   if(!ReadSignal(sig))
   {
      return;  // ไม่มีสัญญาณ
   }

   if(!sig.valid)
   {
      return;
   }

   g_currentSignal = sig;

   LogMessage("Signal: " + sig.signal + " " + sig.symbol +
              " conf=" + DoubleToString(sig.confidence, 2) +
              " consensus=" + sig.consensus);

   // ตรวจ confidence
   if(sig.confidence < InpMinConfidence)
   {
      LogMessage("Confidence too low: " + DoubleToString(sig.confidence, 2));
      return;
   }

   // ตรวจว่าเป็น hold
   if(sig.signal == "hold")
   {
      LogMessage("Signal is HOLD — no action");
      return;
   }

   // ตรวจ symbol ตรงกับ chart หรือไม่
   if(sig.symbol != "" && sig.symbol != _Symbol)
   {
      LogMessage("Signal symbol " + sig.symbol + " != chart " + _Symbol + " — skipping");
      return;
   }

   // ตรวจจำนวน position
   if(CountOpenPositions() >= InpMaxOpenTrades)
   {
      LogMessage("Max open positions reached: " + IntegerToString(InpMaxOpenTrades));
      return;
   }

   // ตรวจว่ามี position เปิดอยู่แล้วหรือไม่
   if(HasOpenPosition(_Symbol))
   {
      LogMessage("Position already open for " + _Symbol);
      return;
   }

   // ตรวจ spread
   if(!IsSpreadOK(_Symbol))
   {
      return;
   }

   // คำนวณ lot size
   double lots = CalculateLotSize(_Symbol, sig.stop_loss);
   if(lots <= 0)
   {
      LogMessage("Invalid lot size: " + DoubleToString(lots, 2));
      return;
   }

   // Execute
   bool success = false;
   if(sig.signal == "buy")
   {
      success = ExecuteBuy(_Symbol, sig.stop_loss, sig.take_profit, lots);
   }
   else if(sig.signal == "sell")
   {
      success = ExecuteSell(_Symbol, sig.stop_loss, sig.take_profit, lots);
   }
   else
   {
      LogMessage("Unknown signal: " + sig.signal);
   }

   // เขียนสถานะ
   if(success)
   {
      string status = "{\"status\":\"executed\",\"signal\":\"" + sig.signal +
                       "\",\"symbol\":\"" + _Symbol +
                       "\",\"lots\":" + DoubleToString(lots, 2) +
                       ",\"time\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\"}";
      int h = FileOpen(g_statusFile, FILE_WRITE|FILE_TXT|FILE_SHARE_READ|FILE_COMMON);
      if(h != INVALID_HANDLE)
      {
         FileWriteString(h, status);
         FileClose(h);
      }
   }
}

//+------------------------------------------------------------------+
//| Trade transaction function — ติดตาม PnL                            |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
{
   if(trans.type == TRADE_TRANSACTION_DEAL_ADD)
   {
      if(trans.deal != 0)
      {
         ulong dealTicket = trans.deal;
         if(HistoryDealSelect(dealTicket))
         {
            ENUM_DEAL_ENTRY entry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(dealTicket, DEAL_ENTRY);
            double profit = HistoryDealGetDouble(dealTicket, DEAL_PROFIT);

            if(entry == DEAL_ENTRY_OUT || entry == DEAL_ENTRY_OUT_BY)
            {
               g_totalPnL += profit;
               string type = (entry == DEAL_ENTRY_OUT) ? "CLOSED" : "CLOSED_BY";
               LogMessage(type + " PnL: " + DoubleToString(profit, 2) +
                          " Total: " + DoubleToString(g_totalPnL, 2));
            }
         }
      }
   }
}
//+------------------------------------------------------------------+
