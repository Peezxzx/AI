//+------------------------------------------------------------------+
//|                                          AtsawinEA.mq5 v5.01     |
//|                    Atsawin AI Trading EA — Exness XAUUSD          |
//|                    Data-Driven Edition (Phase 5+)                  |
//|                    Merged: v5.00 repo features + trailing + partial|
//+------------------------------------------------------------------+
#property copyright "Atsawin AI"
#property version   "5.01"
#property strict

#include <Trade\Trade.mqh>

//--- Signal file paths
input string   InpSignalFile         = "atsawin\\latest_signal.json";
input string   InpStatusFile         = "atsawin\\ea_runtime_status.json";

//--- Timing
input int      InpPollSeconds        = 30;
input int      InpMaxSignalAgeSec    = 150;
input bool     InpAllowRepeatSameSignal = false;

//--- Risk
input double   InpRiskPercent        = 2.5;
input double   InpMaxLot             = 1.0;
input double   InpMinLot             = 0.01;

//--- Position caps
input int      InpMaxTrades          = 3;
input int      InpHardMaxMagicTrades = 3;

//--- v5: Dynamic entry gap (seconds). 0 = use fixed InpMinEntryGapMinutes*60
input bool     InpUseDynamicEntryGap = true;
input int      InpMinEntryGapMinutes = 15;       // fallback fixed gap
input double   InpDynamicGapAtMult   = 3.0;       // gap = ATR * this multiplier (in seconds, min 300)

//--- v5: Session-aware spread filter
input bool     InpUseSessionSpreadFilter = true;
input int      InpBlockedSessionStartHour = 21;  // UTC hour to start blocking (21:00 UTC = Asia close)
input int      InpBlockedSessionEndHour   = 23;  // UTC hour to end blocking (23:00 UTC)
input int      InpNormalMaxSpreadPoints   = 500; // normal hours max spread
input int      InpSessionMaxSpreadPoints  = 250; // blocked session max spread (tighter)

//--- v5: Setup quality filter (from trading cafe insights)
input bool     InpUseSetupQualityFilter = true;
input double   InpMinSetupScore       = 60.0;    // min score from bridge score_breakdown
input bool     InpBlockChopRegime     = true;     // block signals with chop_regime reason
input bool     InpBlockOutOfSession   = false;    // block out_of_session_soft (optional)

//--- v5: Dynamic position cap based on equity
input bool     InpUseDynamicCap       = true;
input int      InpBaseMaxPositions    = 3;       // base cap
input double   InpEquityScaleStep     = 2000.0;  // add 1 position per this equity increment
input int      InpAbsoluteMaxPositions = 5;      // hard ceiling

//--- v5: Outcome tracking
input bool     InpTrackOutcomes       = true;
input int      InpOutcomeCheckMinutes = 60;      // check TP/SL every N minutes
input string   InpOutcomeFile         = "atsawin\\ea_outcome_log.json";

//--- Standard
input double   InpMinConf            = 0.3;
input double   InpMinActualRR        = 1.0;
input bool     InpEnforceSymbolMatch = true;
input int      InpMaxSpreadPoints    = 500;
input int      InpMagic              = 20260601;
input int      InpSlippage           = 10;
input bool     InpShowDashboard      = true;
input int      InpDashboardCorner    = 2;
input int      InpDashboardX         = 16;
input int      InpDashboardY         = 18;

//--- v5: Setup family dedup
input bool     InpBlockSameSetupFamily = true;
input int      InpSetupFamilyCooldownMinutes = 60;

//--- v5: Basket loss guard
input double   InpMaxBasketLossMoney = 15.0;

//--- v5.01: Trailing stop + Partial TP
input bool     InpEnableTrailingStop = true;
input double   InpTrailTriggerRR = 1.0;
input double   InpTrailOffsetRR = 0.5;
input bool     InpEnablePartialTP = true;
input double   InpPartialTPPercent = 50.0;

CTrade trade;
datetime lastBar;
datetime lastCheck = 0;
string lastExecutedSignalId = "";
string lastExecutedSetupFamilyKey = "";
datetime lastExecutedSetupFamilyTime = 0;
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
double g_lastSetupScore = 0.0;
int g_totalExecuted = 0;
int g_totalTP = 0;
int g_totalSL = 0;
datetime g_lastOutcomeCheck = 0;

//--- v5.01: Trailing stop + Partial TP state tracking
struct PartialTPState{
   ulong    ticket;
   double   originalLot;
   double   remainingLot;
   double   entryPrice;
   double   stopLoss;
   double   takeProfit;
   double   partialTPPrice;    // price at which 1R is reached
   bool     partialClosed;     // whether partial TP has been executed
   bool     movedToBE;         // whether SL has been moved to BE+offset
   int      direction;         // +1 for buy, -1 for sell
};
PartialTPState g_partialStates[];
int g_partialCount = 0;

//--- Helpers
double EffectiveMinActualRR()
{
   if(InpMinActualRR <= 0.0) return 0.0;
   if(InpMinActualRR > 2.0) return 1.0;
   return InpMinActualRR;
}

//--- v5: Get effective max positions based on equity
int EffectiveMaxPositions()
{
   if(!InpUseDynamicCap) return InpBaseMaxPositions;
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   int extra = (int)((equity - 1000.0) / InpEquityScaleStep);
   if(extra < 0) extra = 0;
   int cap = InpBaseMaxPositions + extra;
   if(cap > InpAbsoluteMaxPositions) cap = InpAbsoluteMaxPositions;
   return cap;
}

//--- v5: Get effective entry gap based on ATR
int EffectiveEntryGapSec(double atr)
{
   if(!InpUseDynamicEntryGap) return InpMinEntryGapMinutes * 60;
   int dynamicGap = (int)(atr * InpDynamicGapAtMult);
   int fixedGap = InpMinEntryGapMinutes * 60;
   if(dynamicGap < 300) dynamicGap = 300;  // minimum 5 minutes
   if(dynamicGap > fixedGap) dynamicGap = fixedGap;  // cap at fixed
   return dynamicGap;
}

//--- v5: Check if current time is in blocked session
bool IsInBlockedSession()
{
   if(!InpUseSessionSpreadFilter) return false;
   MqlDateTime dt;
   TimeCurrent(dt);
   int hour = dt.hour;
   if(InpBlockedSessionStartHour <= InpBlockedSessionEndHour)
      return (hour >= InpBlockedSessionStartHour && hour < InpBlockedSessionEndHour);
   else
      return (hour >= InpBlockedSessionStartHour || hour < InpBlockedSessionEndHour);
}

//--- v5: Get effective max spread
int EffectiveMaxSpread()
{
   if(InpUseSessionSpreadFilter && IsInBlockedSession())
      return InpSessionMaxSpreadPoints;
   return InpMaxSpreadPoints;
}

//--- v5: Parse setup score from JSON
double GetSetupScore(string json)
{
   // Try to extract score_breakdown.buy_score or sell_score
   string edgeStr = JS(json, "edge");
   if(edgeStr != "") return StringToDouble(StrTrimSimple(edgeStr));
   // Fallback: look for buy_score inside score_breakdown
   string buyScoreStr = JS(json, "buy_score");
   if(buyScoreStr != "") return StringToDouble(StrTrimSimple(buyScoreStr));
   return 0.0;
}

//--- v5: Check if signal has blocked reasons
bool HasBlockedReason(string json, string &blockedReason)
{
   if(!InpUseSetupQualityFilter) return false;
   
   // Check chop_regime
   if(InpBlockChopRegime)
   {
      string reasons = JS(json, "reasons");
      if(StringFind(StrToLowerSimple(reasons), "chop_regime") >= 0)
      {
         blockedReason = "chop_regime";
         return true;
      }
   }
   
   // Check out_of_session
   if(InpBlockOutOfSession)
   {
      string reasons = JS(json, "reasons");
      if(StringFind(StrToLowerSimple(reasons), "out_of_session") >= 0)
      {
         blockedReason = "out_of_session";
         return true;
      }
   }
   
   return false;
}

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
   if(mt5s != "") return (mt5s == chart);
   if(base == "") return true;
   if(base == chart) return true;
   if(StringFind(chart, base) == 0) return true;
   return false;
}

bool GetSymbolDouble(ENUM_SYMBOL_INFO_DOUBLE prop, double &out)
{
   return SymbolInfoDouble(_Symbol, prop, out);
}

string BuildSetupFamilyKey(string sig, string sigSymbol, string sigMt5Symbol, string setupType, string fvgDirection, double fvgMid, double fibRatio, string rsiDiv)
{
   string chartSymbol = StrToLowerSimple(StrTrimSimple(_Symbol));
   string baseSymbol  = StrToLowerSimple(StrTrimSimple(sigSymbol));
   string mt5Symbol   = StrToLowerSimple(StrTrimSimple(sigMt5Symbol));
   string familySymbol = mt5Symbol;
   if(familySymbol == "") familySymbol = chartSymbol;
   if(familySymbol == "") familySymbol = baseSymbol;
   string direction = StrToLowerSimple(StrTrimSimple(sig));
   string setup     = StrToLowerSimple(StrTrimSimple(setupType));
   string fvgDir    = StrToLowerSimple(StrTrimSimple(fvgDirection));
   string rsi       = StrToLowerSimple(StrTrimSimple(rsiDiv));
   string family = familySymbol + "|" + direction + "|" + setup + "|" + fvgDir;
   if(fvgMid > 0.0) family += "|fvgmid=" + DoubleToString(fvgMid, 2);
   if(fibRatio > 0.0) family += "|fib=" + DoubleToString(fibRatio, 3);
   if(rsi != "" && rsi != "none") family += "|rsi=" + rsi;
   return family;
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
   if(!InpShowDashboard) { DeleteDashboard(); return; }
   ObjectDelete(0, "ATSAWIN_DASH_PANEL");
   ObjectDelete(0, "ATSAWIN_DASH_HEADER");

   MqlTick tick;
   bool hasTick = SymbolInfoTick(_Symbol, tick);
   double bid = 0.0, ask = 0.0;
   if(hasTick) { bid = tick.bid; ask = tick.ask; }

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

   // v5: Show session info
   string sessionInfo = "";
   if(InpUseSessionSpreadFilter && IsInBlockedSession())
      sessionInfo = " [BLOCKED SESSION]";

   SetDashLabel("TIME", "upd " + TimeToString(g_lastStatusTime, TIME_SECONDS) + sessionInfo, x, y, 8, clrGray);
   SetDashLabel("STATUS", ShortText(g_lastDecision + " | " + g_lastReason, 38), x, y + 15, 10, statusClr);
   SetDashLabel("SPREAD", "spr " + DoubleToString(g_lastSpreadPoints, 1) + "/" + IntegerToString(EffectiveMaxSpread()) + " pt", x, y + 32, 9, muted);
   SetDashLabel("LEVELS", "SL " + DoubleToString(g_lastSL, _Digits) + "  TP " + DoubleToString(g_lastTP, _Digits), x, y + 49, 9, softWhite);
   SetDashLabel("SIGNAL", ShortText(g_lastSignal, 8) + "  conf " + DoubleToString(g_lastConfidence, 2) + "  rr " + DoubleToString(g_lastActualRR, 2), x, y + 66, 10, statusClr);
   
   // v5: Show dynamic cap
   int dynCap = EffectiveMaxPositions();
   SetDashLabel("POSITIONS", "pos " + IntegerToString(g_lastSymbolCount) + "/" + IntegerToString(dynCap) + "  magic " + IntegerToString(g_lastMagicCount) + "/" + IntegerToString(InpHardMaxMagicTrades), x, y + 83, 9, muted);
   
   SetDashLabel("PNL", "float " + MoneyText(floating) + "  basket " + MoneyText(g_lastBasketProfit), x, y + 100, 10, pnlClr);
   SetDashLabel("ACCOUNT", "bal " + DoubleToString(balance, 2) + "  eq " + DoubleToString(equity, 2), x, y + 117, 9, softWhite);
   SetDashLabel("PRICE", "bid " + DoubleToString(bid, _Digits) + "  ask " + DoubleToString(ask, _Digits), x, y + 134, 9, muted);
   SetDashLabel("STRATEGY", ShortText(g_setupType + " " + g_strategyVersion, 44), x, y + 151, 8, clrAqua);
   SetDashLabel("FVG", "fvg " + g_fvgDirection + " mid " + DoubleToString(g_fvgMid, _Digits), x, y + 166, 8, muted);
   SetDashLabel("FIB", "fib " + DoubleToString(g_fibRatio, 3) + " @ " + DoubleToString(g_fibLevel, _Digits), x, y + 181, 8, muted);
   SetDashLabel("RSI_DIV", ShortText("rsi-div " + g_rsiDivergence, 36), x, y + 196, 8, clrGold);
   
   // v5: Show setup score and outcome stats
   SetDashLabel("SCORE", "score " + DoubleToString(g_lastSetupScore, 1) + "  tp/sl " + IntegerToString(g_totalTP) + "/" + IntegerToString(g_totalSL), x, y + 211, 8, muted);
   
   // v5.01: Show trailing/partial state count
   string trailInfo = "";
   if(InpEnableTrailingStop || InpEnablePartialTP)
   {
      trailInfo = "  trail=" + IntegerToString(g_partialCount);
   }
   SetDashLabel("SYMBOL", _Symbol + "  magic " + IntegerToString(InpMagic) + trailInfo, x, y + 226, 8, muted);
   SetDashLabel("TITLE", "ATSAWIN v5.01  AUTO " + tradeAllowed, x, y + 243, 11, autoClr);
   ChartRedraw(0);
}

void WriteRuntimeStatus(string decision, string reason, string signalId, string sig, double conf, double sl, double tp, double actualRR, double spreadPoints, int magicCount, int symbolCount, double basketProfit)
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
   double bid = 0.0, ask = 0.0;
   if(SymbolInfoTick(_Symbol, tick)) { bid = tick.bid; ask = tick.ask; }
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double floating = equity - balance;

   int h = FileOpen(InpStatusFile, FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON);
   if(h == INVALID_HANDLE) return;

   string body = StringFormat(
      "{\"ea_version\":\"5.01\",\"symbol\":\"%s\",\"decision\":\"%s\",\"reason\":\"%s\",\"signal_id\":\"%s\",\"signal\":\"%s\",\"confidence\":%.3f,\"stop_loss\":%.5f,\"take_profit\":%.5f,\"actual_rr\":%.3f,\"min_actual_rr_threshold\":%.3f,\"configured_min_actual_rr\":%.3f,\"spread_points\":%.1f,\"magic_positions\":%d,\"symbol_positions\":%d,\"basket_profit\":%.2f,\"balance\":%.2f,\"equity\":%.2f,\"floating_profit\":%.2f,\"bid\":%.5f,\"ask\":%.5f,\"terminal_trade_allowed\":%d,\"strategy_version\":\"%s\",\"setup_type\":\"%s\",\"fvg_direction\":\"%s\",\"fvg_mid\":%.5f,\"fib_nearest_ratio\":%.5f,\"fib_nearest_level\":%.5f,\"rsi_divergence\":\"%s\",\"setup_score\":%.1f,\"total_executed\":%d,\"total_tp\":%d,\"total_sl\":%d,\"dynamic_cap\":%d,\"session_blocked\":%d,\"trailing_enabled\":%d,\"partial_tp_enabled\":%d,\"trail_positions\":%d,\"last_update\":\"%s\"}",
      JsonEscape(_Symbol), JsonEscape(decision), JsonEscape(reason), JsonEscape(signalId), JsonEscape(sig),
      conf, sl, tp, actualRR, EffectiveMinActualRR(), InpMinActualRR, spreadPoints,
      magicCount, symbolCount, basketProfit, balance, equity, floating, bid, ask,
      (int)TerminalInfoInteger(TERMINAL_TRADE_ALLOWED), JsonEscape(g_strategyVersion), JsonEscape(g_setupType),
      JsonEscape(g_fvgDirection), g_fvgMid, g_fibRatio, g_fibLevel, JsonEscape(g_rsiDivergence),
      g_lastSetupScore, g_totalExecuted, g_totalTP, g_totalSL, EffectiveMaxPositions(),
      IsInBlockedSession() ? 1 : 0,
      InpEnableTrailingStop ? 1 : 0, InpEnablePartialTP ? 1 : 0, g_partialCount,
      TimeToString(TimeGMT(), TIME_DATE|TIME_SECONDS));
   FileWriteString(h, body);
   FileClose(h);
}

//--- v5: Check outcomes of open positions
void CheckOutcomes()
{
   if(!InpTrackOutcomes) return;
   if(TimeCurrent() - g_lastOutcomeCheck < InpOutcomeCheckMinutes * 60) return;
   g_lastOutcomeCheck = TimeCurrent();

   // Simple outcome tracking: check if any position hit TP or SL
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(t <= 0) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagic) continue;
      
      double profit = PositionGetDouble(POSITION_PROFIT);
      double tp = PositionGetDouble(POSITION_TP);
      double sl = PositionGetDouble(POSITION_SL);
      double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      string posSymbol = PositionGetString(POSITION_SYMBOL);
      
      // Log significant PnL changes
      if(MathAbs(profit) > 5.0)
      {
         Print("OUTCOME_CHECK: ", posSymbol, " profit=", DoubleToString(profit, 2),
               " open=", DoubleToString(openPrice, _Digits),
               " tp=", DoubleToString(tp, _Digits), " sl=", DoubleToString(sl, _Digits));
      }
   }
}

//--- v5.01: Find or create PartialTPState for a ticket
int FindOrCreatePartialState(ulong ticket)
{
   // Search existing
   for(int i = 0; i < g_partialCount; i++)
   {
      if(g_partialStates[i].ticket == ticket)
         return i;
   }
   
   // Not found — create new
   int idx = g_partialCount;
   g_partialCount++;
   ArrayResize(g_partialStates, g_partialCount);
   
   // Initialize from position data
   if(PositionSelectByTicket(ticket))
   {
      g_partialStates[idx].ticket = ticket;
      g_partialStates[idx].originalLot = PositionGetDouble(POSITION_VOLUME);
      g_partialStates[idx].remainingLot = PositionGetDouble(POSITION_VOLUME);
      g_partialStates[idx].entryPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      g_partialStates[idx].stopLoss = PositionGetDouble(POSITION_SL);
      g_partialStates[idx].takeProfit = PositionGetDouble(POSITION_TP);
      g_partialStates[idx].partialClosed = false;
      g_partialStates[idx].movedToBE = false;
      
      // Determine direction
      double sl = g_partialStates[idx].stopLoss;
      double tp = g_partialStates[idx].takeProfit;
      double entry = g_partialStates[idx].entryPrice;
      if(tp > sl)
         g_partialStates[idx].direction = +1;  // buy
      else
         g_partialStates[idx].direction = -1;  // sell
      
      // Calculate partial TP price (1R level)
      double R = MathAbs(tp - entry);  // 1R distance
      if(g_partialStates[idx].direction == +1)
         g_partialStates[idx].partialTPPrice = entry + R;  // buy: 1R above entry
      else
         g_partialStates[idx].partialTPPrice = entry - R;  // sell: 1R below entry
      
      Print("TRAIL_INIT: ticket=", ticket, " dir=", g_partialStates[idx].direction,
            " entry=", DoubleToString(entry, _Digits), " R=", DoubleToString(R, _Digits),
            " partialTP=", DoubleToString(g_partialStates[idx].partialTPPrice, _Digits));
   }
   else
   {
      // Position not available — mark as already handled
      g_partialStates[idx].ticket = ticket;
      g_partialStates[idx].partialClosed = true;
      g_partialStates[idx].movedToBE = true;
      g_partialStates[idx].direction = 0;
      g_partialStates[idx].originalLot = 0;
      g_partialStates[idx].remainingLot = 0;
      g_partialStates[idx].entryPrice = 0;
      g_partialStates[idx].stopLoss = 0;
      g_partialStates[idx].takeProfit = 0;
      g_partialStates[idx].partialTPPrice = 0;
   }
   
   return idx;
}

//--- v5.01: Remove closed positions from state array
void CleanupPartialStates()
{
   int writeIdx = 0;
   for(int i = 0; i < g_partialCount; i++)
   {
      // Check if position still exists
      if(PositionSelectByTicket(g_partialStates[i].ticket))
      {
         // Position still open — keep it
         if(writeIdx != i)
            g_partialStates[writeIdx] = g_partialStates[i];
         writeIdx++;
      }
      // else: position closed — drop it
   }
   g_partialCount = writeIdx;
   ArrayResize(g_partialStates, g_partialCount);
}

//--- v5.01: Manage trailing stop and partial TP
void ManageTrailingAndPartialTP()
{
   if(!InpEnableTrailingStop && !InpEnablePartialTP) return;
   
   // First, cleanup closed positions
   CleanupPartialStates();
   
   // Get current tick
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick)) return;
   
   // Loop through all positions with our magic number
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket <= 0) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagic) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      
      // Find or create state for this position
      int stateIdx = FindOrCreatePartialState(ticket);
      if(stateIdx < 0 || stateIdx >= g_partialCount) continue;
      
      PartialTPState state = g_partialStates[stateIdx];
      
      // Skip if position data is invalid
      if(state.direction == 0) continue;
      
      double entry = state.entryPrice;
      double sl = state.stopLoss;
      double tp = state.takeProfit;
      double R = MathAbs(tp - entry);  // 1R distance
      
      if(R <= 0) continue;  // invalid TP
      
      //--- Partial TP Logic ---
      if(InpEnablePartialTP && !state.partialClosed)
      {
         bool triggerPartial = false;
         double currentPrice = 0;
         
         if(state.direction == +1)  // BUY
         {
            currentPrice = tick.bid;
            if(currentPrice >= state.partialTPPrice)
               triggerPartial = true;
         }
         else if(state.direction == -1)  // SELL
         {
            currentPrice = tick.ask;
            if(currentPrice <= state.partialTPPrice)
               triggerPartial = true;
         }
         
         if(triggerPartial)
         {
            double closeLot = NormalizeDouble(state.originalLot * InpPartialTPPercent / 100.0, 2);
            if(closeLot > state.remainingLot) closeLot = state.remainingLot;
            if(closeLot < InpMinLot) closeLot = InpMinLot;
            
            Print("PARTIAL_TP: ticket=", ticket, " closeLot=", closeLot,
                  " remaining=", state.remainingLot, " at price=", DoubleToString(currentPrice, _Digits));
            
            bool closeResult = false;
            if(state.direction == +1)
               closeResult = trade.Sell(closeLot, _Symbol, tick.bid, 0, 0, "Atsawin partial TP");
            else
               closeResult = trade.Buy(closeLot, _Symbol, tick.ask, 0, 0, "Atsawin partial TP");
            
            if(closeResult)
            {
               g_partialStates[stateIdx].partialClosed = true;
               g_partialStates[stateIdx].remainingLot = NormalizeDouble(state.remainingLot - closeLot, 2);
               Print("PARTIAL_TP_OK: ticket=", ticket, " closed=", closeLot,
                     " remaining=", g_partialStates[stateIdx].remainingLot);
            }
            else
            {
               Print("PARTIAL_TP_FAIL: ticket=", ticket, " err=", trade.ResultRetcodeDescription());
            }
         }
      }
      
      // Refresh state after potential partial close
      state = g_partialStates[stateIdx];
      
      //--- Trailing Stop Logic ---
      double currentPrice = 0;
      if(InpEnableTrailingStop && state.partialClosed && !state.movedToBE)
      {
         double triggerPrice = 0;
         double newSL = 0;
         bool triggerTrail = false;
         
         if(state.direction == +1)  // BUY
         {
            currentPrice = tick.bid;
            triggerPrice = entry + (InpTrailTriggerRR * R);
            if(currentPrice >= triggerPrice)
            {
               newSL = entry + (InpTrailOffsetRR * R);
               // Only move SL up, never down
               if(newSL > sl)
                  triggerTrail = true;
            }
         }
         else if(state.direction == -1)  // SELL
         {
            currentPrice = tick.ask;
            triggerPrice = entry - (InpTrailTriggerRR * R);
            if(currentPrice <= triggerPrice)
            {
               newSL = entry - (InpTrailOffsetRR * R);
               // Only move SL down (towards entry), never up
               if(newSL < sl)
                  triggerTrail = true;
            }
         }
         
         if(triggerTrail)
         {
            // Normalize new SL
            newSL = NormalizeDouble(newSL, _Digits);
            
            Print("TRAIL_STOP: ticket=", ticket, " oldSL=", DoubleToString(sl, _Digits),
                  " newSL=", DoubleToString(newSL, _Digits),
                  " trigger=", DoubleToString(triggerPrice, _Digits));
            
            if(trade.PositionModify(ticket, newSL, tp))
            {
               g_partialStates[stateIdx].movedToBE = true;
               g_partialStates[stateIdx].stopLoss = newSL;
               Print("TRAIL_STOP_OK: ticket=", ticket, " SL moved to ", DoubleToString(newSL, _Digits));
            }
            else
            {
               Print("TRAIL_STOP_FAIL: ticket=", ticket, " err=", trade.ResultRetcodeDescription());
            }
         }
      }
   }
}

int OnInit()
{
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints((ulong)InpSlippage);
   trade.SetTypeFilling(ORDER_FILLING_IOC);
   g_lastStatusTime = TimeCurrent();
   DrawDashboard();
   Print("Atsawin EA v5.01 started — trailing=", InpEnableTrailingStop,
         " partialTP=", InpEnablePartialTP,
         " dynamicGap=", InpUseDynamicEntryGap,
         " sessionFilter=", InpUseSessionSpreadFilter,
         " qualityFilter=", InpUseSetupQualityFilter);
   Print("Atsawin EA v5.01 started on ", _Symbol,
         " poll=", IntegerToString(InpPollSeconds), "s",
         " dashboard=", (InpShowDashboard ? "on" : "off"),
         " configuredMinRR=", DoubleToString(InpMinActualRR, 2),
         " effectiveMinRR=", DoubleToString(EffectiveMinActualRR(), 2),
         " dynamicGap=", (InpUseDynamicEntryGap ? "on" : "off"),
         " sessionFilter=", (InpUseSessionSpreadFilter ? "on" : "off"),
         " qualityFilter=", (InpUseSetupQualityFilter ? "on" : "off"),
         " dynamicCap=", (InpUseDynamicCap ? "on" : "off"),
         " outcomeTracking=", (InpTrackOutcomes ? "on" : "off"));
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

   // v5: Check outcomes periodically
   CheckOutcomes();

   //--- v5.01: Manage trailing stop and partial TP BEFORE signal processing ---
   ManageTrailingAndPartialTP();

   // Read signal file
   string paths[2];
   paths[0] = InpSignalFile;
   paths[1] = "atsawin\\latest_signal.json";

   string json = "";
   string usedPath = "";

   for(int i = 0; i < 2; i++)
   {
      if(FileIsExist(paths[i], 0))
      {
         int h = FileOpen(paths[i], FILE_READ|FILE_TXT|FILE_ANSI|FILE_SHARE_READ);
         if(h != INVALID_HANDLE)
         {
            json = FileReadString(h, (int)FileSize(h));
            FileClose(h);
            if(StringLen(json) > 10) { usedPath = paths[i] + " (local)"; break; }
         }
      }
      if(FileIsExist(paths[i], FILE_COMMON))
      {
         int hc = FileOpen(paths[i], FILE_READ|FILE_TXT|FILE_ANSI|FILE_SHARE_READ|FILE_COMMON);
         if(hc != INVALID_HANDLE)
         {
            json = FileReadString(hc, (int)FileSize(hc));
            FileClose(hc);
            if(StringLen(json) > 10) { usedPath = paths[i] + " (common)"; break; }
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
   
   // v5: Parse setup score
   g_lastSetupScore = GetSetupScore(json);
   
   string setupFamilyKey = BuildSetupFamilyKey(sig, sigSymbol, sigMt5Symbol, g_setupType, g_fvgDirection, g_fvgMid, g_fibRatio, g_rsiDivergence);
   long timestampEpoch = (long)StringToInteger(StrTrimSimple(JS(json, "timestamp_epoch")));
   long expiresAtEpoch = (long)StringToInteger(StrTrimSimple(JS(json, "expires_at_epoch")));
   
   // v5: Parse ATR for dynamic gap
   double atr = StringToDouble(StrTrimSimple(JS(json, "atr")));
   
   if(signalId == "")
      signalId = sig + "|" + sigSymbol + "|" + DoubleToString(sl, 2) + "|" + DoubleToString(tp, 2) + "|" + DoubleToString(conf, 3);

   Print("Read from: ", usedPath);
   Print("JSON keys: signal=", sig, " symbol=", sigSymbol, " mt5_symbol=", sigMt5Symbol,
         " conf=", DoubleToString(conf,2), " SL=", DoubleToString(sl,2), " TP=", DoubleToString(tp,2),
         " setup=", g_setupType, " fvg=", g_fvgDirection, " fib=", DoubleToString(g_fibRatio,3),
         " rsiDiv=", g_rsiDivergence, " score=", DoubleToString(g_lastSetupScore,1),
         " atr=", DoubleToString(atr,2), " id=", signalId);

   //--- Safety checks (same order as v4) ---
   long nowEpoch = (long)TimeGMT();
   if(expiresAtEpoch > 0 && nowEpoch > expiresAtEpoch)
   {
      Print("SKIP: signal expired");
      WriteRuntimeStatus("SKIP", "signal_expired", signalId, sig, conf, sl, tp, 0, 0, 0, 0, 0);
      return;
   }
   if(InpMaxSignalAgeSec > 0 && timestampEpoch > 0 && (nowEpoch - timestampEpoch) > InpMaxSignalAgeSec)
   {
      Print("SKIP: signal too old");
      WriteRuntimeStatus("SKIP", "signal_too_old", signalId, sig, conf, sl, tp, 0, 0, 0, 0, 0);
      return;
   }
   if(!InpAllowRepeatSameSignal && signalId != "" && signalId == lastExecutedSignalId)
   {
      Print("SKIP: duplicate signal_id=", signalId);
      WriteRuntimeStatus("SKIP", "duplicate_signal_id", signalId, sig, conf, sl, tp, 0, 0, 0, 0, 0);
      return;
   }
   if(InpBlockSameSetupFamily && setupFamilyKey != "" && setupFamilyKey == lastExecutedSetupFamilyKey)
   {
      bool activeCooldown = true;
      if(InpSetupFamilyCooldownMinutes > 0 && lastExecutedSetupFamilyTime > 0)
      {
         int familyAgeMinutes = (int)((TimeCurrent() - lastExecutedSetupFamilyTime) / 60);
         activeCooldown = (familyAgeMinutes < InpSetupFamilyCooldownMinutes);
      }
      if(activeCooldown)
      {
         Print("SKIP: duplicate setup family");
         WriteRuntimeStatus("SKIP", "duplicate_setup_family", signalId, sig, conf, sl, tp, 0, 0, 0, 0, 0);
         return;
      }
   }
   if(InpEnforceSymbolMatch && !SymbolMatchesChart(sigSymbol, sigMt5Symbol))
   {
      Print("SKIP: symbol mismatch");
      WriteRuntimeStatus("SKIP", "symbol_mismatch", signalId, sig, conf, sl, tp, 0, 0, 0, 0, 0);
      return;
   }
   if(conf < InpMinConf)
   {
      Print("SKIP: confidence too low");
      WriteRuntimeStatus("SKIP", "confidence_too_low", signalId, sig, conf, sl, tp, 0, 0, 0, 0, 0);
      return;
   }
   if(sl <= 0 || tp <= 0)
   {
      Print("SKIP: invalid SL/TP");
      WriteRuntimeStatus("SKIP", "invalid_sl_tp", signalId, sig, conf, sl, tp, 0, 0, 0, 0, 0);
      return;
   }

   // Count positions
   int magicCount = 0, symbolCount = 0;
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

   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick))
   {
      WriteRuntimeStatus("SKIP", "no_symbol_tick", signalId, sig, conf, sl, tp, 0, 0, magicCount, symbolCount, basketProfit);
      return;
   }

   //--- v5: Session-aware spread filter ---
   double spreadPoints = (tick.ask - tick.bid) / _Point;
   int effectiveMaxSpread = EffectiveMaxSpread();
   if(effectiveMaxSpread > 0 && spreadPoints > effectiveMaxSpread)
   {
      string reason = IsInBlockedSession() ? "session_spread_too_high" : "spread_too_high";
      Print("SKIP: ", reason, " spread=", DoubleToString(spreadPoints, 1), " max=", IntegerToString(effectiveMaxSpread));
      WriteRuntimeStatus("SKIP", reason, signalId, sig, conf, sl, tp, 0, spreadPoints, magicCount, symbolCount, basketProfit);
      return;
   }

   //--- v5: Setup quality filter ---
   if(InpUseSetupQualityFilter)
   {
      // Check blocked reasons
      string blockedReason = "";
      if(HasBlockedReason(json, blockedReason))
      {
         Print("SKIP: blocked reason=", blockedReason);
         WriteRuntimeStatus("SKIP", blockedReason, signalId, sig, conf, sl, tp, 0, spreadPoints, magicCount, symbolCount, basketProfit);
         return;
      }
      
      // Check minimum setup score
      if(g_lastSetupScore > 0 && g_lastSetupScore < InpMinSetupScore)
      {
         Print("SKIP: setup score too low ", DoubleToString(g_lastSetupScore, 1), " < ", DoubleToString(InpMinSetupScore, 1));
         WriteRuntimeStatus("SKIP", "setup_score_too_low", signalId, sig, conf, sl, tp, 0, spreadPoints, magicCount, symbolCount, basketProfit);
         return;
      }
   }

   // Validate actual RR
   double actualRisk = 0, actualReward = 0;
   if(sig == "buy") { actualRisk = tick.ask - sl; actualReward = tp - tick.ask; }
   else if(sig == "sell") { actualRisk = sl - tick.bid; actualReward = tick.bid - tp; }
   else
   {
      Print("SKIP: signal is hold/unknown: ", sig);
      WriteRuntimeStatus("SKIP", "hold_or_unknown_signal", signalId, sig, conf, sl, tp, 0, spreadPoints, magicCount, symbolCount, basketProfit);
      return;
   }

   if(actualRisk <= 0 || actualReward <= 0)
   {
      Print("SKIP: invalid live geometry");
      WriteRuntimeStatus("SKIP", "invalid_live_geometry", signalId, sig, conf, sl, tp, 0, spreadPoints, magicCount, symbolCount, basketProfit);
      return;
   }

   double actualRR = actualReward / actualRisk;
   double effectiveMinRR = EffectiveMinActualRR();
   if(actualRR < effectiveMinRR)
   {
      Print("SKIP: actual RR too low ", DoubleToString(actualRR, 2), " < ", DoubleToString(effectiveMinRR, 2));
      WriteRuntimeStatus("SKIP", "actual_rr_too_low", signalId, sig, conf, sl, tp, actualRR, spreadPoints, magicCount, symbolCount, basketProfit);
      return;
   }

   if(InpMaxBasketLossMoney > 0 && basketProfit <= -InpMaxBasketLossMoney)
   {
      Print("SKIP: basket loss guard");
      WriteRuntimeStatus("SKIP", "basket_loss_guard", signalId, sig, conf, sl, tp, actualRR, spreadPoints, magicCount, symbolCount, basketProfit);
      return;
   }

   //--- v5: Dynamic position cap ---
   int effectiveMaxPos = EffectiveMaxPositions();
   if(InpHardMaxMagicTrades > 0 && magicCount >= InpHardMaxMagicTrades)
   {
      Print("SKIP: hard magic cap");
      WriteRuntimeStatus("SKIP", "hard_magic_cap", signalId, sig, conf, sl, tp, actualRR, spreadPoints, magicCount, symbolCount, basketProfit);
      return;
   }
   if(symbolCount >= effectiveMaxPos)
   {
      Print("SKIP: position cap reached symbolCount=", IntegerToString(symbolCount), " cap=", IntegerToString(effectiveMaxPos));
      WriteRuntimeStatus("SKIP", "position_cap_reached", signalId, sig, conf, sl, tp, actualRR, spreadPoints, magicCount, symbolCount, basketProfit);
      return;
   }

   //--- v5: Dynamic entry gap ---
   int effectiveGap = EffectiveEntryGapSec(atr);
   if(InpMinEntryGapMinutes > 0 && lastEntryTime > 0)
   {
      int gapSec = (int)(TimeCurrent() - lastEntryTime);
      if(gapSec < effectiveGap)
      {
         Print("SKIP: entry gap too soon gapSec=", IntegerToString(gapSec), " minSec=", IntegerToString(effectiveGap),
               " (atr=", DoubleToString(atr,2), " dynamic=", InpUseDynamicEntryGap ? "on" : "off", ")");
         WriteRuntimeStatus("SKIP", "entry_gap_too_soon", signalId, sig, conf, sl, tp, actualRR, spreadPoints, magicCount, symbolCount, basketProfit);
         return;
      }
   }

   //--- Execute ---
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

   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmt = balance * InpRiskPercent / 100.0;
   double slDist = 0;
   if(sig == "buy")  slDist = MathAbs(tick.ask - sl);
   if(sig == "sell") slDist = MathAbs(sl - tick.bid);
   if(slDist <= 0) return;

   double lot = riskAmt / ((slDist / ts) * tv);
   if(step > 0) lot = MathFloor(lot / step) * step;
   if(lot < minL) lot = minL;
   if(lot > InpMaxLot) lot = InpMaxLot;
   if(lot > maxL) lot = maxL;
   lot = NormalizeDouble(lot, 2);

   double price;
   if(sig == "buy")
   {
      price = tick.ask;
      if(trade.Buy(lot, _Symbol, price, sl, tp, "Atsawin v5.01"))
      {
         lastExecutedSignalId = signalId;
         lastExecutedSetupFamilyKey = setupFamilyKey;
         lastExecutedSetupFamilyTime = TimeCurrent();
         g_totalExecuted++;
         WriteRuntimeStatus("EXECUTED", "buy_order_sent", signalId, sig, conf, sl, tp, actualRR, spreadPoints, magicCount + 1, symbolCount + 1, basketProfit);
         Print("BUY ", lot, " @", price, " SL=", sl, " TP=", tp, " id=", signalId, " score=", DoubleToString(g_lastSetupScore,1));
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
      if(trade.Sell(lot, _Symbol, price, sl, tp, "Atsawin v5.01"))
      {
         lastExecutedSignalId = signalId;
         lastExecutedSetupFamilyKey = setupFamilyKey;
         lastExecutedSetupFamilyTime = TimeCurrent();
         g_totalExecuted++;
         WriteRuntimeStatus("EXECUTED", "sell_order_sent", signalId, sig, conf, sl, tp, actualRR, spreadPoints, magicCount + 1, symbolCount + 1, basketProfit);
         Print("SELL ", lot, " @", price, " SL=", sl, " TP=", tp, " id=", signalId, " score=", DoubleToString(g_lastSetupScore,1));
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
