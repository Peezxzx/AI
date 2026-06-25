//+------------------------------------------------------------------+
//|                                          AtsawinEA.mq5 v4.04     |
//|                    Atsawin AI Trading EA — Exness XAUUSD          |
//+------------------------------------------------------------------+
#property copyright "Atsawin AI"
#property version   "4.04"
#property strict

#include <Trade\Trade.mqh>

input string   InpSignalFile         = "atsawin\\latest_signal.json";
input string   InpStatusFile         = "atsawin\\ea_runtime_status.json";
input int      InpPollSeconds        = 30;     // poll signal by time, not only on a new candle
input int      InpMaxSignalAgeSec    = 150;    // 0 disables; bridge writes timestamp_epoch/expires_at_epoch
input bool     InpAllowRepeatSameSignal = false; // false = one successful order per signal_id/setup_key
input double   InpRiskPercent        = 2.5;
input double   InpMaxLot             = 1.0;
input double   InpMinLot             = 0.01;
input int      InpMaxTrades          = 3;
input int      InpHardMaxMagicTrades = 3;     // absolute safety cap across all charts using this magic
input int      InpMinEntryGapMinutes = 15;    // minimum gap between entries for this magic+symbol
input double   InpMaxBasketLossMoney = 15.0;  // block new entries if this magic basket loses more than this; 0 disables
input double   InpMinConf            = 0.3;
input double   InpMinActualRR        = 1.0;   // block late entries where current price makes RR too small/negative
input bool     InpEnforceSymbolMatch = true;  // prevent XAUUSD signal from trading on USDJPY/etc.
input int      InpMaxSpreadPoints    = 500;   // XAUUSDm spread guard; 0 disables
input int      InpMagic              = 20260601;
input int      InpSlippage           = 10;
input bool     InpShowDashboard      = true;   // show live EA dashboard on chart
input int      InpDashboardCorner    = 2;      // 0=left upper, 1=left lower, 2=right lower, 3=right upper
input int      InpDashboardX         = 16;
input int      InpDashboardY         = 18;

CTrade trade;
datetime lastBar;
datetime lastCheck = 0;
string lastExecutedSignalId = "";
string g_lastDecision = "BOOT";
string g_lastReason = "waiting_for_tick";
string g_lastSignalId = "";
string g_lastSignal = "";
double g_lastConfidence = 0.0;
double g_lastSL = 0.0;
double g_lastTP = 0.0;
double g_lastActualRR = 0.0;
double g_lastSpreadPoints = 0.0;
int g_lastMagicCount = 0;
int g_lastSymbolCount = 0;
double g_lastBasketProfit = 0.0;
datetime g_lastStatusTime = 0;
string g_strategyVersion = "";
string g_setupType = "";
string g_fvgDirection = "";
double g_fvgMid = 0.0;
double g_fibRatio = 0.0;
double g_fibLevel = 0.0;
string g_rsiDivergence = "";

string JS(string json, string key)
{
   string s = "\"" + key + "\":";
   int p = StringFind(json, s);
   if(p < 0) return "";
   p += StringLen(s);
   while(p < StringLen(json))
   {
      int ch = StringGetCharacter(json, p);
      if(ch==' ' || ch=='\t' || ch=='\r' || ch=='\n') p++;
      else break;
   }
   if(p >= StringLen(json)) return "";

   bool q = (StringGetCharacter(json, p) == '"');
   if(q) p++;

   int e = p;
   if(q)
   {
      while(e < StringLen(json) && StringGetCharacter(json, e) != '"') e++;
   }
   else
   {
      while(e < StringLen(json))
      {
         int ch2 = StringGetCharacter(json, e);
         if(ch2 == ',' || ch2 == '}' || ch2 == '\r' || ch2 == '\n') break;
         e++;
      }
   }
   return StringSubstr(json, p, e - p);
}

string StrTrimSimple(string s)
{
   int i = 0;
   int j = StringLen(s) - 1;
   while(i <= j)
   {
      int ch = StringGetCharacter(s, i);
      if(ch==' ' || ch=='\t' || ch=='\r' || ch=='\n') i++;
      else break;
   }
   while(j >= i)
   {
      int ch2 = StringGetCharacter(s, j);
      if(ch2==' ' || ch2=='\t' || ch2=='\r' || ch2=='\n') j--;
      else break;
   }
   if(j < i) return "";
   return StringSubstr(s, i, j - i + 1);
}

string StrToLowerSimple(string s)
{
   string out = "";
   for(int i=0; i<StringLen(s); i++)
   {
      int ch = StringGetCharacter(s, i);
      if(ch >= 'A' && ch <= 'Z') ch += 32;
      out += CharToString((uchar)ch);
   }
   return out;
}

bool SymbolMatchesChart(string sigSymbol, string sigMt5Symbol)
{
   string chart = StrToLowerSimple(StrTrimSimple(_Symbol));
   string mt5s  = StrToLowerSimple(StrTrimSimple(sigMt5Symbol));
   string base  = StrToLowerSimple(StrTrimSimple(sigSymbol));

   if(mt5s != "")
      return (mt5s == chart);

   if(base == "")
      return true; // old minimal signals had no symbol; keep compatibility

   if(base == chart)
      return true;

   // Broker suffix compatibility: XAUUSD signal may run on XAUUSDm chart.
   if(StringFind(chart, base) == 0)
      return true;

   return false;
}

// Get SymbolInfoDouble safely
bool GetSymbolDouble(ENUM_SYMBOL_INFO_DOUBLE prop, double &out)
{
   return SymbolInfoDouble(_Symbol, prop, out);
}

string JsonEscape(string s)
{
   StringReplace(s, "\\", "\\\\");
   StringReplace(s, "\"", "\\\"");
   StringReplace(s, "\r", " ");
   StringReplace(s, "\n", " ");
   return s;
}

string ShortText(string s, int maxLen)
{
   if(StringLen(s) <= maxLen) return s;
   return StringSubstr(s, 0, maxLen - 3) + "...";
}

string MoneyText(double v)
{
   string sign = "";
   if(v > 0) sign = "+";
   return sign + DoubleToString(v, 2);
}

color DecisionColor(string decision, string sig)
{
   string d = StrToLowerSimple(decision);
   string s = StrToLowerSimple(sig);
   if(d == "executed") return clrLime;
   if(d == "failed") return clrTomato;
   if(d == "skip") return clrOrange;
   if(s == "buy") return clrDeepSkyBlue;
   if(s == "sell") return clrHotPink;
   return clrSilver;
}

void SetDashRect(string name, int x, int y, int w, int h, color bg, color border)
{
   if(!InpShowDashboard) return;
   string obj = "ATSAWIN_DASH_" + name;
   if(ObjectFind(0, obj) < 0)
      ObjectCreate(0, obj, OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, obj, OBJPROP_CORNER, InpDashboardCorner);
   ObjectSetInteger(0, obj, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, obj, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, obj, OBJPROP_XSIZE, w);
   ObjectSetInteger(0, obj, OBJPROP_YSIZE, h);
   ObjectSetInteger(0, obj, OBJPROP_BGCOLOR, bg);
   ObjectSetInteger(0, obj, OBJPROP_BORDER_COLOR, border);
   ObjectSetInteger(0, obj, OBJPROP_BACK, false);
   ObjectSetInteger(0, obj, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, obj, OBJPROP_HIDDEN, true);
}

void SetDashLabel(string name, string text, int x, int y, int fontSize, color clr)
{
   if(!InpShowDashboard) return;
   string obj = "ATSAWIN_DASH_" + name;
   if(ObjectFind(0, obj) < 0)
      ObjectCreate(0, obj, OBJ_LABEL, 0, 0, 0);

   ENUM_ANCHOR_POINT anchor = ANCHOR_LEFT_UPPER;
   if(InpDashboardCorner == 1) anchor = ANCHOR_LEFT_LOWER;
   if(InpDashboardCorner == 2) anchor = ANCHOR_RIGHT_LOWER;
   if(InpDashboardCorner == 3) anchor = ANCHOR_RIGHT_UPPER;

   ObjectSetInteger(0, obj, OBJPROP_CORNER, InpDashboardCorner);
   ObjectSetInteger(0, obj, OBJPROP_ANCHOR, anchor);
   ObjectSetInteger(0, obj, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, obj, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, obj, OBJPROP_FONTSIZE, fontSize);
   ObjectSetInteger(0, obj, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, obj, OBJPROP_BACK, false);
   ObjectSetInteger(0, obj, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, obj, OBJPROP_HIDDEN, true);
   ObjectSetString(0, obj, OBJPROP_FONT, "Consolas");
   ObjectSetString(0, obj, OBJPROP_TEXT, text);
}

void DeleteDashboard()
{
   for(int i = ObjectsTotal(0) - 1; i >= 0; i--)
   {
      string obj = ObjectName(0, i);
      if(StringFind(obj, "ATSAWIN_DASH_") == 0)
         ObjectDelete(0, obj);
   }
}

void DrawDashboard()
{
   if(!InpShowDashboard)
   {
      DeleteDashboard();
      return;
   }

   // v4.04: compact text-only dashboard with bridge strategy metadata, default bottom-right.
   ObjectDelete(0, "ATSAWIN_DASH_PANEL");
   ObjectDelete(0, "ATSAWIN_DASH_HEADER");

   MqlTick tick;
   bool hasTick = SymbolInfoTick(_Symbol, tick);
   double bid = 0.0, ask = 0.0;
   if(hasTick)
   {
      bid = tick.bid;
      ask = tick.ask;
   }

   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double floating = equity - balance;
   string tradeAllowed = TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) ? "ON" : "OFF";

   int x = InpDashboardX;
   int y = InpDashboardY;
   color statusClr = DecisionColor(g_lastDecision, g_lastSignal);
   color pnlClr = (floating >= 0 ? clrLime : clrTomato);
   color basketClr = (g_lastBasketProfit >= 0 ? clrLime : clrTomato);
   color autoClr = (tradeAllowed == "ON" ? clrLime : clrTomato);
   color softWhite = clrWhite;
   color muted = clrSilver;

   // With bottom-right corner/anchor, larger Y values are drawn higher on the chart.
   SetDashLabel("TIME", "upd " + TimeToString(g_lastStatusTime, TIME_SECONDS), x, y, 8, clrGray);
   SetDashLabel("STATUS", ShortText(g_lastDecision + " | " + g_lastReason, 38), x, y + 15, 10, statusClr);
   SetDashLabel("SPREAD", "spr " + DoubleToString(g_lastSpreadPoints, 1) + "/" + IntegerToString(InpMaxSpreadPoints) + " pt", x, y + 32, 9, muted);
   SetDashLabel("LEVELS", "SL " + DoubleToString(g_lastSL, _Digits) + "  TP " + DoubleToString(g_lastTP, _Digits), x, y + 49, 9, softWhite);
   SetDashLabel("SIGNAL", ShortText(g_lastSignal, 8) + "  conf " + DoubleToString(g_lastConfidence, 2) + "  rr " + DoubleToString(g_lastActualRR, 2), x, y + 66, 10, statusClr);
   SetDashLabel("POSITIONS", "pos " + IntegerToString(g_lastSymbolCount) + "/" + IntegerToString(InpMaxTrades) + "  magic " + IntegerToString(g_lastMagicCount) + "/" + IntegerToString(InpHardMaxMagicTrades), x, y + 83, 9, muted);
   SetDashLabel("PNL", "float " + MoneyText(floating) + "  basket " + MoneyText(g_lastBasketProfit), x, y + 100, 10, pnlClr);
   SetDashLabel("ACCOUNT", "bal " + DoubleToString(balance, 2) + "  eq " + DoubleToString(equity, 2), x, y + 117, 9, softWhite);
   SetDashLabel("PRICE", "bid " + DoubleToString(bid, _Digits) + "  ask " + DoubleToString(ask, _Digits), x, y + 134, 9, muted);
   SetDashLabel("STRATEGY", ShortText(g_setupType + " " + g_strategyVersion, 44), x, y + 151, 8, clrAqua);
   SetDashLabel("FVG", "fvg " + g_fvgDirection + " mid " + DoubleToString(g_fvgMid, _Digits), x, y + 166, 8, muted);
   SetDashLabel("FIB", "fib " + DoubleToString(g_fibRatio, 3) + " @ " + DoubleToString(g_fibLevel, _Digits), x, y + 181, 8, muted);
   SetDashLabel("RSI_DIV", ShortText("rsi-div " + g_rsiDivergence, 36), x, y + 196, 8, clrGold);
   SetDashLabel("SYMBOL", _Symbol + "  magic " + IntegerToString(InpMagic), x, y + 211, 8, muted);
   SetDashLabel("TITLE", "ATSAWIN v4.04  AUTO " + tradeAllowed, x, y + 228, 11, autoClr);
   ChartRedraw(0);
}

void WriteRuntimeStatus(string decision,
                        string reason,
                        string signalId,
                        string sig,
                        double conf,
                        double sl,
                        double tp,
                        double actualRR,
                        double spreadPoints,
                        int magicCount,
                        int symbolCount,
                        double basketProfit)
{
   g_lastDecision = decision;
   g_lastReason = reason;
   g_lastSignalId = signalId;
   g_lastSignal = sig;
   g_lastConfidence = conf;
   g_lastSL = sl;
   g_lastTP = tp;
   g_lastActualRR = actualRR;
   g_lastSpreadPoints = spreadPoints;
   g_lastMagicCount = magicCount;
   g_lastSymbolCount = symbolCount;
   g_lastBasketProfit = basketProfit;
   g_lastStatusTime = TimeCurrent();
   DrawDashboard();

   MqlTick tick;
   double bid = 0.0;
   double ask = 0.0;
   if(SymbolInfoTick(_Symbol, tick))
   {
      bid = tick.bid;
      ask = tick.ask;
   }
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double floating = equity - balance;

   int h = FileOpen(InpStatusFile, FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON);
   if(h == INVALID_HANDLE) return;

   string body = StringFormat(
      "{\"ea_version\":\"4.04\",\"symbol\":\"%s\",\"decision\":\"%s\",\"reason\":\"%s\",\"signal_id\":\"%s\",\"signal\":\"%s\",\"confidence\":%.3f,\"stop_loss\":%.5f,\"take_profit\":%.5f,\"actual_rr\":%.3f,\"spread_points\":%.1f,\"magic_positions\":%d,\"symbol_positions\":%d,\"basket_profit\":%.2f,\"balance\":%.2f,\"equity\":%.2f,\"floating_profit\":%.2f,\"bid\":%.5f,\"ask\":%.5f,\"terminal_trade_allowed\":%d,\"strategy_version\":\"%s\",\"setup_type\":\"%s\",\"fvg_direction\":\"%s\",\"fvg_mid\":%.5f,\"fib_nearest_ratio\":%.5f,\"fib_nearest_level\":%.5f,\"rsi_divergence\":\"%s\",\"last_update\":\"%s\"}",
      JsonEscape(_Symbol),
      JsonEscape(decision),
      JsonEscape(reason),
      JsonEscape(signalId),
      JsonEscape(sig),
      conf,
      sl,
      tp,
      actualRR,
      spreadPoints,
      magicCount,
      symbolCount,
      basketProfit,
      balance,
      equity,
      floating,
      bid,
      ask,
      (int)TerminalInfoInteger(TERMINAL_TRADE_ALLOWED),
      JsonEscape(g_strategyVersion),
      JsonEscape(g_setupType),
      JsonEscape(g_fvgDirection),
      g_fvgMid,
      g_fibRatio,
      g_fibLevel,
      JsonEscape(g_rsiDivergence),
      TimeToString(TimeGMT(), TIME_DATE|TIME_SECONDS)
   );
   FileWriteString(h, body);
   FileClose(h);
}

int OnInit()
{
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints((ulong)InpSlippage);
   trade.SetTypeFilling(ORDER_FILLING_IOC);
   g_lastStatusTime = TimeCurrent();
   DrawDashboard();
   Print("Atsawin EA v4.04 started on ", _Symbol, " poll=", IntegerToString(InpPollSeconds), "s dashboard=", (InpShowDashboard ? "on" : "off"));
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   DeleteDashboard();
}

void OnTick()
{
   if(InpPollSeconds > 0 && lastCheck > 0 && (TimeCurrent() - lastCheck) < InpPollSeconds) return;
   lastCheck = TimeCurrent();

   // Read signal file (ANSI/UTF-8 safe)
   string paths[2];
   paths[0] = InpSignalFile;                  // terminal data folder MQL5\\Files\\...
   paths[1] = "atsawin\\latest_signal.json"; // fallback

   string json = "";
   string usedPath = "";

   for(int i = 0; i < 2; i++)
   {
      // Try local terminal Files
      if(FileIsExist(paths[i], 0))
      {
         int h = FileOpen(paths[i], FILE_READ|FILE_TXT|FILE_ANSI|FILE_SHARE_READ);
         if(h != INVALID_HANDLE)
         {
            json = FileReadString(h, (int)FileSize(h));
            FileClose(h);
            if(StringLen(json) > 10)
            {
               usedPath = paths[i] + " (local)";
               break;
            }
         }
      }

      // Try common shared Files
      if(FileIsExist(paths[i], FILE_COMMON))
      {
         int hc = FileOpen(paths[i], FILE_READ|FILE_TXT|FILE_ANSI|FILE_SHARE_READ|FILE_COMMON);
         if(hc != INVALID_HANDLE)
         {
            json = FileReadString(hc, (int)FileSize(hc));
            FileClose(hc);
            if(StringLen(json) > 10)
            {
               usedPath = paths[i] + " (common)";
               break;
            }
         }
      }
   }

   if(StringLen(json) < 10)
   {
      Print("No signal file content");
      WriteRuntimeStatus("SKIP", "no_signal_file_content", "", "", 0, 0, 0, 0, 0, 0, 0, 0);
      return;
   }

   json = StrTrimSimple(json);
   string sig = StrToLowerSimple(StrTrimSimple(JS(json, "signal")));
   string signalId = StrTrimSimple(JS(json, "signal_id"));
   string setupKey = StrTrimSimple(JS(json, "setup_key"));
   if(signalId == "") signalId = setupKey;
   string sigSymbol = StrTrimSimple(JS(json, "symbol"));
   string sigMt5Symbol = StrTrimSimple(JS(json, "mt5_symbol"));
   double conf = StringToDouble(StrTrimSimple(JS(json, "confidence")));
   double sl   = StringToDouble(StrTrimSimple(JS(json, "stop_loss")));
   double tp   = StringToDouble(StrTrimSimple(JS(json, "take_profit")));
   g_strategyVersion = StrTrimSimple(JS(json, "strategy_version"));
   g_setupType = StrTrimSimple(JS(json, "setup_type"));
   g_fvgDirection = StrTrimSimple(JS(json, "fvg_direction"));
   g_fvgMid = StringToDouble(StrTrimSimple(JS(json, "fvg_mid")));
   g_fibRatio = StringToDouble(StrTrimSimple(JS(json, "fib_nearest_ratio")));
   g_fibLevel = StringToDouble(StrTrimSimple(JS(json, "fib_nearest_level")));
   g_rsiDivergence = StrTrimSimple(JS(json, "rsi_divergence"));
   long timestampEpoch = (long)StringToInteger(StrTrimSimple(JS(json, "timestamp_epoch")));
   long expiresAtEpoch = (long)StringToInteger(StrTrimSimple(JS(json, "expires_at_epoch")));
   if(signalId == "")
      signalId = sig + "|" + sigSymbol + "|" + DoubleToString(sl, 2) + "|" + DoubleToString(tp, 2) + "|" + DoubleToString(conf, 3);

   Print("Read from: ", usedPath);
   Print("JSON keys: signal=", sig,
         " symbol=", sigSymbol,
         " mt5_symbol=", sigMt5Symbol,
         " conf=", DoubleToString(conf,2),
         " SL=", DoubleToString(sl,2),
         " TP=", DoubleToString(tp,2),
         " setup=", g_setupType,
         " fvg=", g_fvgDirection,
         " fib=", DoubleToString(g_fibRatio,3),
         " rsiDiv=", g_rsiDivergence,
         " id=", signalId);

   long nowEpoch = (long)TimeGMT();
   if(expiresAtEpoch > 0 && nowEpoch > expiresAtEpoch)
   {
      Print("SKIP: signal expired expires_at_epoch=", (string)expiresAtEpoch, " now=", (string)nowEpoch);
      WriteRuntimeStatus("SKIP", "signal_expired", signalId, sig, conf, sl, tp, 0, 0, 0, 0, 0);
      return;
   }
   if(InpMaxSignalAgeSec > 0 && timestampEpoch > 0 && (nowEpoch - timestampEpoch) > InpMaxSignalAgeSec)
   {
      Print("SKIP: signal too old ageSec=", (string)(nowEpoch - timestampEpoch), " max=", IntegerToString(InpMaxSignalAgeSec));
      WriteRuntimeStatus("SKIP", "signal_too_old", signalId, sig, conf, sl, tp, 0, 0, 0, 0, 0);
      return;
   }
   if(!InpAllowRepeatSameSignal && signalId != "" && signalId == lastExecutedSignalId)
   {
      Print("SKIP: duplicate already executed signal_id=", signalId);
      WriteRuntimeStatus("SKIP", "duplicate_signal_id", signalId, sig, conf, sl, tp, 0, 0, 0, 0, 0);
      return;
   }

   if(InpEnforceSymbolMatch && !SymbolMatchesChart(sigSymbol, sigMt5Symbol))
   {
      Print("SKIP: signal symbol mismatch chart=", _Symbol,
            " symbol=", sigSymbol,
            " mt5_symbol=", sigMt5Symbol);
      WriteRuntimeStatus("SKIP", "symbol_mismatch", signalId, sig, conf, sl, tp, 0, 0, 0, 0, 0);
      return;
   }

   if(conf < InpMinConf)
   {
      Print("SKIP: confidence too low (", DoubleToString(conf,2), " < ", DoubleToString(InpMinConf,2), ")");
      WriteRuntimeStatus("SKIP", "confidence_too_low", signalId, sig, conf, sl, tp, 0, 0, 0, 0, 0);
      return;
   }
   if(sl <= 0 || tp <= 0)
   {
      Print("SKIP: invalid SL/TP");
      WriteRuntimeStatus("SKIP", "invalid_sl_tp", signalId, sig, conf, sl, tp, 0, 0, 0, 0, 0);
      return;
   }

   // Count open positions with our magic. Use two limits:
   // 1) InpMaxTrades for this chart symbol
   // 2) InpHardMaxMagicTrades as an absolute safety cap across every chart using this magic
   int magicCount = 0;
   int symbolCount = 0;
   double basketProfit = 0.0;
   datetime lastEntryTime = 0;

   for(int i = PositionsTotal()-1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(t <= 0) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagic) continue;

      magicCount++;
      basketProfit += PositionGetDouble(POSITION_PROFIT);

      string posSymbol = PositionGetString(POSITION_SYMBOL);
      datetime posTime = (datetime)PositionGetInteger(POSITION_TIME);
      if(posSymbol == _Symbol)
      {
         symbolCount++;
         if(posTime > lastEntryTime) lastEntryTime = posTime;
      }
   }

   // Get live tick before any cap/skip decisions so runtime status can show real spread and actual RR.
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick))
   {
      WriteRuntimeStatus("SKIP", "no_symbol_tick", signalId, sig, conf, sl, tp, 0, 0, magicCount, symbolCount, basketProfit);
      return;
   }

   double spreadPoints = (tick.ask - tick.bid) / _Point;
   if(InpMaxSpreadPoints > 0)
   {
      if(spreadPoints > InpMaxSpreadPoints)
      {
         Print("SKIP: spread too high ", DoubleToString(spreadPoints, 1),
               " > ", IntegerToString(InpMaxSpreadPoints));
         WriteRuntimeStatus("SKIP", "spread_too_high", signalId, sig, conf, sl, tp, 0, spreadPoints, magicCount, symbolCount, basketProfit);
         return;
      }
   }

   // Validate actual RR at execution price before cap checks so SKIP statuses are informative.
   // Bridge RR is calculated at signal-generation price; if price moves close to TP before the next entry,
   // later entries can have tiny/negative live RR even though JSON still says rr is acceptable.
   double actualRisk = 0;
   double actualReward = 0;
   if(sig == "buy")
   {
      actualRisk = tick.ask - sl;
      actualReward = tp - tick.ask;
   }
   else if(sig == "sell")
   {
      actualRisk = sl - tick.bid;
      actualReward = tick.bid - tp;
   }
   else
   {
      Print("SKIP: signal is hold/unknown: ", sig);
      WriteRuntimeStatus("SKIP", "hold_or_unknown_signal", signalId, sig, conf, sl, tp, 0, spreadPoints, magicCount, symbolCount, basketProfit);
      return;
   }

   if(actualRisk <= 0 || actualReward <= 0)
   {
      Print("SKIP: invalid live geometry sig=", sig,
            " bid=", DoubleToString(tick.bid, _Digits),
            " ask=", DoubleToString(tick.ask, _Digits),
            " SL=", DoubleToString(sl, _Digits),
            " TP=", DoubleToString(tp, _Digits),
            " risk=", DoubleToString(actualRisk, 2),
            " reward=", DoubleToString(actualReward, 2));
      WriteRuntimeStatus("SKIP", "invalid_live_geometry", signalId, sig, conf, sl, tp, 0, spreadPoints, magicCount, symbolCount, basketProfit);
      return;
   }

   double actualRR = actualReward / actualRisk;
   if(actualRR < InpMinActualRR)
   {
      Print("SKIP: actual RR too low ", DoubleToString(actualRR, 2),
            " < ", DoubleToString(InpMinActualRR, 2),
            " sig=", sig,
            " bid=", DoubleToString(tick.bid, _Digits),
            " ask=", DoubleToString(tick.ask, _Digits),
            " SL=", DoubleToString(sl, _Digits),
            " TP=", DoubleToString(tp, _Digits));
      WriteRuntimeStatus("SKIP", "actual_rr_too_low", signalId, sig, conf, sl, tp, actualRR, spreadPoints, magicCount, symbolCount, basketProfit);
      return;
   }

   if(InpHardMaxMagicTrades > 0 && magicCount >= InpHardMaxMagicTrades)
   {
      Print("SKIP: hard magic position cap reached magicCount=", IntegerToString(magicCount),
            " cap=", IntegerToString(InpHardMaxMagicTrades),
            " basketProfit=", DoubleToString(basketProfit, 2));
      WriteRuntimeStatus("SKIP", "hard_magic_cap", signalId, sig, conf, sl, tp, actualRR, spreadPoints, magicCount, symbolCount, basketProfit);
      return;
   }

   if(symbolCount >= InpMaxTrades)
   {
      Print("SKIP: symbol position cap reached symbolCount=", IntegerToString(symbolCount),
            " cap=", IntegerToString(InpMaxTrades));
      WriteRuntimeStatus("SKIP", "symbol_position_cap", signalId, sig, conf, sl, tp, actualRR, spreadPoints, magicCount, symbolCount, basketProfit);
      return;
   }

   if(InpMaxBasketLossMoney > 0 && basketProfit <= -InpMaxBasketLossMoney)
   {
      Print("SKIP: basket loss guard basketProfit=", DoubleToString(basketProfit, 2),
            " maxLoss=", DoubleToString(InpMaxBasketLossMoney, 2));
      WriteRuntimeStatus("SKIP", "basket_loss_guard", signalId, sig, conf, sl, tp, actualRR, spreadPoints, magicCount, symbolCount, basketProfit);
      return;
   }

   if(InpMinEntryGapMinutes > 0 && lastEntryTime > 0)
   {
      int gapSec = (int)(TimeCurrent() - lastEntryTime);
      int minGapSec = InpMinEntryGapMinutes * 60;
      if(gapSec < minGapSec)
      {
         Print("SKIP: entry gap too soon gapSec=", IntegerToString(gapSec),
               " minSec=", IntegerToString(minGapSec));
         WriteRuntimeStatus("SKIP", "entry_gap_too_soon", signalId, sig, conf, sl, tp, actualRR, spreadPoints, magicCount, symbolCount, basketProfit);
         return;
      }
   }

   // Tick, spread, and actual live RR were validated before cap checks.

   // Get symbol properties
   double tv = 0, ts = 0, minL = 0, maxL = 0, step = 0;
   if(!GetSymbolDouble(SYMBOL_TRADE_TICK_VALUE, tv)) return;
   if(!GetSymbolDouble(SYMBOL_TRADE_TICK_SIZE, ts)) return;
   GetSymbolDouble(SYMBOL_VOLUME_MIN, minL);
   GetSymbolDouble(SYMBOL_VOLUME_MAX, maxL);
   GetSymbolDouble(SYMBOL_VOLUME_STEP, step);
   if(tv <= 0 || ts <= 0) return;
   if(minL <= 0) minL = 0.01;
   if(maxL <= 0) maxL = 1.0;
   if(step <= 0) step = 0.01;

   // Calculate lot from risk %
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmt = balance * InpRiskPercent / 100.0;
   double slDist  = 0;
   if(sig == "buy")  slDist = MathAbs(tick.ask - sl);
   if(sig == "sell") slDist = MathAbs(sl - tick.bid);
   if(slDist <= 0) return;

   double lot = riskAmt / ((slDist / ts) * tv);
   if(step > 0) lot = MathFloor(lot / step) * step;
   if(lot < minL) lot = minL;
   if(lot > InpMaxLot) lot = InpMaxLot;
   if(lot > maxL) lot = maxL;
   lot = NormalizeDouble(lot, 2);

   // Execute
   double price;
   if(sig == "buy")
   {
      price = tick.ask;
      if(trade.Buy(lot, _Symbol, price, sl, tp, "Atsawin v4.04"))
      {
         lastExecutedSignalId = signalId;
         WriteRuntimeStatus("EXECUTED", "buy_order_sent", signalId, sig, conf, sl, tp, actualRR, spreadPoints, magicCount + 1, symbolCount + 1, basketProfit);
         Print("BUY ", lot, " @", price, " SL=", sl, " TP=", tp, " id=", signalId);
      }
      else
      {
         WriteRuntimeStatus("FAILED", trade.ResultRetcodeDescription(), signalId, sig, conf, sl, tp, actualRR, spreadPoints, magicCount, symbolCount, basketProfit);
         Print("BUY failed: ", trade.ResultRetcodeDescription());
      }
   }
   else if(sig == "sell")
   {
      price = tick.bid;
      if(trade.Sell(lot, _Symbol, price, sl, tp, "Atsawin v4.04"))
      {
         lastExecutedSignalId = signalId;
         WriteRuntimeStatus("EXECUTED", "sell_order_sent", signalId, sig, conf, sl, tp, actualRR, spreadPoints, magicCount + 1, symbolCount + 1, basketProfit);
         Print("SELL ", lot, " @", price, " SL=", sl, " TP=", tp, " id=", signalId);
      }
      else
      {
         WriteRuntimeStatus("FAILED", trade.ResultRetcodeDescription(), signalId, sig, conf, sl, tp, actualRR, spreadPoints, magicCount, symbolCount, basketProfit);
         Print("SELL failed: ", trade.ResultRetcodeDescription());
      }
   }
}

void OnBookEvent(const string& symbol)
{
   // Required by some MT5 builds; intentionally unused.
}
