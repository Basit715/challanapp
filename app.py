from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.http import MediaIoBaseDownload
import io
import json


from PIL import Image 
def gdrive_service():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets['gcp'],
        scopes = ["https://www.googleapis.com/auth/drive"]
    )

    return build("drive","v3",credentials=creds)
def read_excel_from_drive(file_id):
    service = gdrive_service()

    # Export Google Sheet to Excel
    data = service.files().export(
        fileId=file_id,
        mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ).execute()

    buffer = io.BytesIO()
    buffer.write(data)
    buffer.seek(0)

    df = pd.read_excel(buffer, engine="openpyxl")
    return df
def write_excel_to_drive(df, file_id):
    service = gdrive_service()

    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, engine="openpyxl")
    excel_buffer.seek(0)

    media = MediaIoBaseUpload(
        excel_buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        resumable=False
    )

    service.files().update(
        fileId=file_id,
        media_body=media
    ).execute()

# challan_app_with_daybook.py
import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
from fpdf import FPDF
from io import BytesIO
from urllib.parse import quote_plus
st.sidebar.header("Tools")
if st.sidebar.button("Clear Cache"):
    st.cache_data.clear()
    st.session_state.clear()
    st.success("cleared cache")

# -------------------- LOGIN SYSTEM --------------------

# Create session state key
# prevent rest of app from loading

# If logged in, continue app normally


# Load image from repo
img = Image.open("Gemini_Generated_Image_j18vq7j18vq7j18v.png")  # just the filename if in same folder
st.image(img,caption = "Basit Pushoo - Developer", width=150)          # adjust size as needed




# ---------------- Config ----------------
DATA_DIR = "."
CHALLAN_FILE = os.path.join(DATA_DIR, "challans.xlsx")
CHALLAN_ID = "1Lw1iy1eCXd82tMUEQB2Z7VcRzR7jgQUwiBrd5o_raVg"
MEDICINES_FILE = os.path.join(DATA_DIR, "medicines.xlsx")
MEDICINE_ID = "1JeFEFSwd8P2Ekwq1xonc9ENLrR4MdmiujSMNhNgd8yc"
DAYBOOK_FILE = os.path.join(DATA_DIR, "daybook.xlsx")
DAYBOOK_ID = "1F4re8JIwfx8B_C9qhAjlhbfUcP6caiDZiM6i-LLc-_8"
LEDGER_FILE = os.path.join(DATA_DIR, "ledger.xlsx")
LEDGER_ID = "1zg8jEUH3wibNvS6BfH6Jh0kcikXbfVsRFWKl9ZDMlSk"
RECURRING_FILE = os.path.join(DATA_DIR,"recurring.xlsx")
RECURRING_ID = "1Gti-tD9DlYpDqZUicvzmTBFKTYU-_NabM8i8etY0b4k"
DAILY_EARNING_FILE = os.path.join(DATA_DIR, "daily_earnings.xlsx")
DAILY_EARNINGS_ID = "1kx3GUOsWtkKiGbH_S6_983gEm8qkOcFtRWxh9teufx8"
BILLS_FILE = os.path.join(DATA_DIR, "bills.xlsx")
BILLS_ID = "1JneZFd8IuQGbUTFznvseUecVUweCKk5XgijTi5gOyOA"
PAYMENTS_FILE = os.path.join(DATA_DIR,"payments.xlsx")
PAYMENTS_ID = "1Ae6Q87LKAeN5_U8jfX8K-NfHX1JagGOtOkQc_R7ejCU"
MAX_ITEMS = 50
DEFAULT_GST = 5.0
APP_TITLE = "💊 NEW PharmaWAYS — WE SELL QUALITY MEDICINES"

# ---------------- Dark theme CSS (modern) ----------------
st.set_page_config(page_title="Pharma Challan Manager", layout="wide", initial_sidebar_state="auto")
st.markdown("""
<style>
/* Button pressed (active) animation */
.stButton>button:active, .stDownloadButton>button:active {
    transform: scale(0.95);
    background: linear-gradient(90deg, #1e90ff, #5ab2ff) !important;
    box-shadow: 0 2px 6px rgba(46,166,255,0.20) inset;
}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
:root{
  --bg: #08090b;
  --panel: #0b1220;
  --muted: #9fb7d8;
  --accent: #2ea6ff;
  --card: #071026;
  --glass: rgba(255,255,255,0.03);
}
body { background: var(--bg); color: #e6eef6; }
.stApp > header, .stApp > footer { display: none; }
section.main { padding-top: 10px; }
.css-1lcbmhc { background-color: var(--panel); } /* page main bg */
[data-testid="stToolbar"] { display: none; }
.stButton>button, .stDownloadButton>button {
  background: linear-gradient(90deg,var(--accent),#6fb8ff) !important;
  color: white !important;
  border: none !important;
  height: 38px;
  box-shadow: 0 4px 10px rgba(46,166,255,0.12);
}
.stTextInput>div>div>input, .stNumberInput>div>div>input, textarea, select {
  background: var(--glass) !important;
  color: #000000 !important;  /* black text inside white-ish boxes */
  border: 1px solid rgba(255,255,255,0.04) !important;
}
.stDataFrame, .element-container { background: transparent !important; }
.css-1d391kg{ background-color: transparent; }
.card {
  background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
  border-radius: 12px;
  padding: 14px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.6);
  border: 1px solid rgba(255,255,255,0.03);
}
.small-muted { color: var(--muted); font-size: 12px; }
.h1 { font-size: 20px; font-weight:700; }
</style>
""", unsafe_allow_html=True)

# ---------------- Helpers: files ----------------
def init_files():
    # challans: each row = single line item (same challan_no repeats)
    if not os.path.exists(CHALLAN_FILE):
        pd.DataFrame(columns=[
            "challan_no", "date", "party", "item", "batch",
            "qty", "rate", "discount", "gst", "amount", "grand_total"
        ]).to_excel(CHALLAN_FILE, index=False, engine="openpyxl")
    # medicines: batch-level inventory
    if not os.path.exists(MEDICINES_FILE):
        # small preloaded sample
        sample = pd.DataFrame([
            {"med_id":"M0001","name":"Paracetamol 500mg","batch":"B1001","expiry":"2026-06-30","qty":100,"rate":12.5,"mrp":15.0,"gst":DEFAULT_GST,"use":"Pain and fever"},
            {"med_id":"M0002","name":"Ciprofloxacin 500mg","batch":"C2001","expiry":"2025-12-31","qty":50,"rate":28.0,"mrp":35.0,"gst":DEFAULT_GST,"use":"Bacterial"},
            {"med_id":"M0003","name":"Vitamin C 500mg","batch":"V3001","expiry":"2027-01-01","qty":200,"rate":8.0,"mrp":10.0,"gst":DEFAULT_GST,"use":"immunity"},
        ])
        sample.to_excel(MEDICINES_FILE, index=False, engine="openpyxl")
    # daybook
    if not os.path.exists(DAYBOOK_FILE):
        pd.DataFrame(columns=[
            "entry_id", "date", "type", "party_or_payee", "category", "amount", "note"
        ]).to_excel(DAYBOOK_FILE, index=False, engine="openpyxl")

def load_challans():
    try:
        df = read_excel_from_drive(st.secrets['files']['CHALLAN_ID'])
        return df.fillna("")
    except Exception as e:
        st.error(f"Error loading challans. {e}")
        return pd.DataFrame(columns=[
            "challan_no", "date", "party", "item", "batch",
            "qty", "rate", "discount", "gst", "amount", "grand_total"
        ])

def save_challans(df):
    try:
        write_excel_to_drive(df,st.secrets['files']['CHALLAN_ID'])
    except Exception as e:
        st.error(f"Error saving medicines {e}")

def load_medicines():
    try:
        df = read_excel_from_drive(st.secrets['files']['MEDICINE_ID'])
        return df.fillna("")
    except Exception as e:
        st.error(f"Error loading medicines {e}")
        return pd.DataFrame(columns=["med_id","name","batch","expiry","qty","rate","mrp","gst"])

def save_medicines(df):
    try:
        write_excel_to_drive(df,st.secrets['files']['MEDICINE_ID'])
    except Exception as e:
        st.error(f"Error saving medicines {e}")

def load_daybook():
    try:
        df = read_excel_from_drive(st.secrets['files']['DAYBOOK_ID'])
        return df.fillna("")
    except Exception as e:
        st.error(f"Error loading daybook {e}")
        return pd.DataFrame(columns=["entry_id","date","type","party_or_payee","category","amount","note"])

def save_daybook(df):
    try:
        write_excel_to_drive(df,st.secrets['files']['DAYBOOK_ID'])
    except Exception as e:
        st.error(f"Error loading daybook {e}")

# ---------------- Ledger Setup ----------------


def load_ledger():
    try:
        df = read_excel_from_drive(LEDGER_ID)
        return df.fillna("")
    except:
        return pd.DataFrame(columns=["entry_id","party","date","type","amount","balance","note"])

def save_ledger(df):
    try:
        write_excel_to_drive(df, LEDGER_ID)
    except Exception as e:
        st.error(f"Error saving ledger: {e}")

ledger_df = load_ledger()
# ---------------- Initialize ledger with starting balances if empty ----------------
if ledger_df.empty:
    # Example: add starting balances for existing parties
    starting_entries = pd.DataFrame([
        {"entry_id":1,"party":"Party A","date":"2025-01-01","type":"Starting Balance","amount":0.0,"balance":1000.0,"note":"Initial balance"},
        {"entry_id":2,"party":"Party B","date":"2025-01-01","type":"Starting Balance","amount":0.0,"balance":500.0,"note":"Initial balance"}
    ])
    ledger_df = pd.concat([ledger_df, starting_entries], ignore_index=True)
    save_ledger(ledger_df)
@st.cache_data
def load_recurring():
    try:
        df = read_excel_from_drive(RECURRING_ID)
        return df.fillna("")
    except:
        # Initialize empty table
        return pd.DataFrame(columns=["party","schedule_type","day_of_week","days_of_month","note"])

def save_recurring(df):
    try:
        write_excel_to_drive(df, RECURRING_ID)
    except Exception as e:
        st.error(f"Error saving recurring: {e}")

recurring_df = load_recurring()

        
if recurring_df.empty:
    starting_entrie = pd.DataFrame([
        {"party":"Party A", "shedule_type":"weekly","day_of_week":0,"days_of_month":[],"note":"Pay every monday 10% of balance"},
        {"party":"Party B", "schedule_type":"monthly","day_of_week":None,"days_of_month":[1,10,20],"note":"Pay on ist,10th,20th 10% of balance"}
    ])
    recurring_df = pd.concat([recurring_df,starting_entrie],ignore_index=True)
    save_recurring(recurring_df)
    
def load_daily_earnings():
    try:
        df = read_excel_from_drive(DAILY_EARNINGS_ID)
        return df.fillna("")
    except:
        return pd.DataFrame(columns = ["DATE","MRP","PTR","PTS","QUANTITY","EARNING"])
def save_daily_earnings(df):
    try:
        write_excel_to_drive(df, DAILY_EARNINGS_ID)
    except Exception as e:
        st.error(f"Error Saving daily_earning {e}")
daily_earnings_df = load_daily_earnings()
if daily_earnings_df.empty:
    starting_entries = pd.DataFrame([
        {"DATE":"2025-11-12","MRP":10,"PTR":6,"PTS":3,"QUANTITY":10,"EARNING":30}
    ])
    daily_earnings_df = pd.concat([daily_earnings_df,starting_entries],ignore_index = True)
    save_daily_earnings(daily_earnings_df)
def load_bills():
    try:
        df = read_excel_from_drive(BILLS_ID)
        return df.fillna("")
    except Exception as e:
        return pd.DataFrame(columns = ["bill_id", "party", "date", "items", "bill_amount"])
def save_bill(df):
    try:
        write_excel_to_drive(df, BILLS_ID)
    except Exception as e:
        st.error(f"Error saving bill {e}")
bill_df = load_bills()
if bill_df.empty:
    starting_entries = pd.DataFrame([
        {"bill_id":1, "party":"basit","date":"01/05/2025","items":json.dumps([{"name":"abc","qty":30,"mrp":10,"rate":21,"total":210}]),"bill_amount":1000}
    ])
    bill_df = pd.concat([bill_df,starting_entries], ignore_index = True)
    save_bill(bill_df)
def load_payments():
    try:
        df = read_excel_from_drive(PAYMENTS_ID)
        return df.fillna("")
    except Exception as e:
        return pd.DataFrame(columns = ["date", "reciepts", "payments", "expenses"])
def save_payments(df):
    try:
        write_excel_to_drive(df, PAYMENTS_ID)
    except Exception as e:
        st.error(f"Error saving payments {e}")
        
        
        
# ---------------- Calculations & PDF ----------------
def compute_row_amount(qty, rate, discount_pct, gst_pct):
    try: q = float(qty)
    except: q = 0.0
    try: r = float(rate)
    except: r = 0.0
    try: disc = float(discount_pct)
    except: disc = 0.0
    try: gst = float(gst_pct)
    except: gst = 0.0
    net = q * r
    discount_amt = net * (disc / 100.0)
    taxable = net - discount_amt
    gst_amt = taxable * (gst / 100.0)
    total = taxable + gst_amt
    return round(total, 2)

class InvoicePDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 8, "New PharmaWays", ln=True, align="C")
        self.set_font("Arial", "", 10)
        self.cell(0, 6, "Challan / Invoice", ln=True, align="C")
        self.ln(4)
    def footer(self):
        self.set_y(-12)
        self.set_font("Arial", "I", 8)
        self.cell(0, 6, f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C")

def challan_to_pdf_page(pdf, ch_df):
    """Append one page for a challan to existing FPDF instance."""
    pdf.add_page()
    first = ch_df.iloc[0]
    pdf.set_font("Arial","",11)
    pdf.cell(0,6, f"Challan No: {first['challan_no']}", ln=True)
    pdf.cell(0,6, f"Date: {first['date']}", ln=True)
    pdf.cell(0,6, f"Party: {first['party']}", ln=True)
    pdf.ln(6)
    pdf.set_font("Arial","B",10)
    pdf.cell(70,8,"Item", border=1)
    pdf.cell(30,8,"Batch", border=1)
    pdf.cell(18,8,"Qty", border=1, align="R")
    pdf.cell(25,8,"Rate", border=1, align="R")
    pdf.cell(25,8,"Amount", border=1, align="R")
    pdf.ln()
    pdf.set_font("Arial","",10)
    for _, r in ch_df.iterrows():
        pdf.cell(70,8, str(r["item"])[:40], border=1)
        pdf.cell(30,8, str(r["batch"])[:15], border=1)
        pdf.cell(18,8, f"{float(r['qty']):.2f}", border=1, align="R")
        pdf.cell(25,8, f"{float(r['rate']):.2f}", border=1, align="R")
        pdf.cell(25,8, f"{float(r['amount']):.2f}", border=1, align="R")
        pdf.ln()
    pdf.ln(6)
    grand = float(first.get("grand_total", ch_df["amount"].sum()))
    pdf.set_font("Arial","B",12)
    pdf.cell(0,8, f"Grand Total: Rs {grand:.2f}", ln=True, align="R")

def challan_to_pdf_bytes(ch_df):
    pdf = InvoicePDF()
    challan_to_pdf_page(pdf, ch_df)
    return pdf.output(dest="S").encode("latin-1")

def all_challans_booklet_bytes(challans_df):
    """Create one PDF with each challan on its own page."""
    pdf = InvoicePDF()
    unique_ch = []
    if not challans_df.empty:
        unique_ch = sorted(challans_df["challan_no"].unique().tolist(), key=lambda x: int(x) if str(x).isdigit() else str(x))
    if not unique_ch:
        # empty PDF
        pdf.add_page()
        pdf.set_font("Arial","",12)
        pdf.cell(0,10,"No challans available.", ln=True)
        return pdf.output(dest="S").encode("latin-1")
    for ch in unique_ch:
        ch_df = challans_df[challans_df["challan_no"]==ch].copy()
        if ch_df.empty:
            continue
        challan_to_pdf_page(pdf, ch_df)
    return pdf.output(dest="S").encode("latin-1")

def daybook_to_pdf_bytes(db_df, title="Day Book"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial","B",14)
    pdf.cell(0,8, title, ln=True, align="C")
    pdf.ln(4)
    pdf.set_font("Arial","B",10)
    pdf.cell(30,8,"Date", border=1)
    pdf.cell(20,8,"Type", border=1)
    pdf.cell(60,8,"Party/Payee", border=1)
    pdf.cell(40,8,"Category", border=1)
    pdf.cell(30,8,"Amount", border=1, align="R")
    pdf.ln()
    pdf.set_font("Arial","",10)
    total = 0.0
    for _, r in db_df.iterrows():
        pdf.cell(30,8, str(r["date"])[:10], border=1)
        pdf.cell(20,8, str(r["type"])[:10], border=1)
        pdf.cell(60,8, str(r["party_or_payee"])[:30], border=1)
        pdf.cell(40,8, str(r["category"])[:20], border=1)
        amount = pd.to_numeric(r.get("amount", 0), errors="coerce")
        if pd.isna(amount):
            amount = 0
            
        pdf.cell(30,8, f"{amount:.2f}", border=1, align="R")
        pdf.ln()
        if pd.notna(r["amount"]):
            try:
                total += float(r["amount"])
            except:
                pass
    pdf.ln(6)
    pdf.set_font("Arial","B",12)
    pdf.cell(0,8, f"Total amount (all entries): Rs {total:.2f}", ln=True, align="R")
    return pdf.output(dest="S").encode("latin-1")

# ---------------- Init ----------------
init_files()
challans_df = load_challans()
med_df = load_medicines()
daybook_df = load_daybook()

# ---------------- UI ----------------
st.title(APP_TITLE)
st.caption("whatsaApp: set default reciepeint phone (country code, no +).Optional")
wa_default_number = st.text_input("Default whatsapp number e.g; +91 9541292214",value="",key="wa_default_number")
# At the top, after loading ledger_df
parties = sorted(ledger_df['party'].dropna().unique().tolist())
if "daily_earnings" not in st.session_state:
    st.session_state.daily_earnings = []  # list to store earnings of each calculation
if 'direct_bill_items' not in st.session_state:
    st.session_state.direct_bill_items = []

tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8,tab9,tab10,tab11,tab12,tab13,tab14,tab15 = st.tabs(["Challans", "Medicines (Inventory)", "Reports / Utilities", "Day Book",
     "Dashboard", "Advertisement", "Ledger", "Recurring Payment", "Billing","Calculator","Daily Earnings","Special Discount","Edit Party / view & Update balance","Sales Book","Daily Payments"])

# Tab order: Challans | Medicines | Reports | Day Book (user chose B)

                                                
# ---------------- TAB: Medicines inventory ----------------
with tab2:
    st.header("📦 Medicines Inventory (batch-level)")
    colA, colB = st.columns([2,1])
    with colA:
        st.subheader("Add new batch")
        med_name = st.text_input("Medicine name", key="med_add_name")
        batch = st.text_input("Batch", key="med_add_batch")
        use = st.text_input("Use / Description",key="med_add_use")
                            
        expiry = ""
        if st.checkbox("Set expiry?", key="chk_med_exp"):
            expiry = st.date_input("Expiry (optional)", value=date.today(), key="med_add_expiry").strftime("%Y-%m-%d")
        qty = st.number_input("Qty", min_value=0.0, value=0.0, step=1.0, key="med_add_qty")
        rate = st.number_input("Rate", min_value=0.0, value=0.0, key="med_add_rate")
        mrp = st.number_input("MRP", min_value=0.0, value=0.0, key="med_add_mrp")
        gst = st.number_input("GST %", min_value=0.0, max_value=28.0, value=DEFAULT_GST, key="med_add_gst")
        if st.button("Add Medicine", key="btn_add_batch"):
            if not med_name or not batch:
                st.error("Provide medicine name and batch.")
            else:
                mid = f"M{len(med_df)+1:04d}"
                new_row = {
                    "med_id": mid,
                    "name": med_name,
                    "batch": batch,
                    "expiry": expiry,
                    "qty": qty,
                    "rate": rate,
                    "mrp": mrp,
                    "gst": gst,
                    "use": use
                }
                med_df = pd.concat([med_df, pd.DataFrame([new_row])], ignore_index=True)
                save_medicines(med_df)
                st.success(f"Added batch {batch} for {med_name}.")
                med_df = load_medicines()
    with colB:
        st.subheader("Search / Edit inventory")
        search_med = st.text_input("Search medicine or batch", key="med_search")
        view_df = med_df.copy()
        if search_med:
            mask = view_df["name"].astype(str).str.contains(search_med, case=False, na=False) | view_df["batch"].astype(str).str.contains(search_med, case=False, na=False)
            view_df = view_df[mask]
        st.dataframe(view_df.reset_index(drop=True))
        # simple edit: choose row by index
        if not view_df.empty:
            idx = st.number_input("Select row index to edit (index from above table)", min_value=0, max_value=max(0, len(view_df)-1), step=1, key="med_edit_idx")
            if st.button("Load row for edit", key="btn_load_med"):
                actual_idx = view_df.index[int(idx)]
                st.session_state["_edit_med_idx"] = int(actual_idx)
                st.rerun()
        if "_edit_med_idx" in st.session_state:
            eidx = st.session_state["_edit_med_idx"]
            if eidx < len(med_df):
                st.markdown("---")
                st.subheader("Edit selected batch")
                er = med_df.loc[eidx]
                ename = st.text_input("Medicine name", value=er["name"], key="edit_med_name")
                ebatch = st.text_input("Batch", value=er["batch"], key="edit_med_batch")
                eexpiry = st.text_input("Expiry (YYYY-MM-DD)", value=str(er.get("expiry","")), key="edit_med_expiry")
                eqty = st.number_input("Qty", min_value=0.0, value=float(er.get("qty",0)), key="edit_med_qty")
                erate = st.number_input("Rate", min_value=0.0, value=float(er.get("rate",0)), key="edit_med_rate")
                emrp = st.number_input("MRP", min_value=0.0, value=float(er.get("mrp",0)), key="edit_med_mrp")
                egst = st.number_input("GST %", min_value=0.0, max_value=28.0, value=float(er.get("gst",DEFAULT_GST)), key="edit_med_gst")
                c1, c2 = st.columns([1,1])
                with c1:
                    if st.button("Save changes to batch", key="btn_save_med"):
                        med_df.at[eidx, "name"] = ename
                        med_df.at[eidx, "batch"] = ebatch
                        med_df.at[eidx, "expiry"] = eexpiry
                        med_df.at[eidx, "qty"] = eqty
                        med_df.at[eidx, "rate"] = erate
                        med_df.at[eidx, "mrp"] = emrp
                        med_df.at[eidx, "gst"] = egst
                        save_medicines(med_df)
                        st.success("Saved changes.")
                        del st.session_state["_edit_med_idx"]
                        st.rerun()
                with c2:
                    if st.button("Delete this batch", key="btn_del_med"):
                        med_df = med_df.drop(index=eidx).reset_index(drop=True)
                        save_medicines(med_df)
                        st.success("Deleted batch.")
                        del st.session_state["_edit_med_idx"]
                        st.rerun()

# ---------------- TAB: Challans ----------------
with tab1:
    st.header("➕ Create / View Challans")
    col1, col2 = st.columns([2,3])
    with col1:
        st.subheader("Create New Challan")
        # next challan number
        existing = challans_df["challan_no"].dropna().unique().tolist() if not challans_df.empty else []
        if existing:
            try:
                next_no = int(max(existing)) + 1
            except:
                next_no = int(datetime.now().strftime("%Y%m%d%H%M%S")[:10])
        else:
            next_no = 1
        challan_no = st.number_input("Challan No", min_value=1, value=int(next_no), step=1, key="new_challan_no")
        party_list = ledger_df["party"].unique().tolist()

        party = st.selectbox(
           "Party Name",
            options=party_list,
            index=None,
           placeholder="Type or choose a party..."
          )
        date_val = st.date_input("Date", value=date.today(), key="new_date")
        num_items = st.number_input("Number of items", min_value=1, max_value=MAX_ITEMS, value=1, key="new_num_items")
        new_items = []
        # prepare medicine names list
        med_names = sorted(med_df["name"].dropna().unique().tolist())
        for i in range(int(num_items)):
            st.markdown(f"---\n**Item #{i+1}**")
            c1,c2,c3 = st.columns([4,2,2])
            with c1:
                selected_med = st.selectbox(f"Medicine {i+1}", options=["-- type or pick --"] + med_names, key=f"sel_med_{challan_no}_{i}")
                batch_opts = []
                if selected_med and selected_med != "-- type or pick --":
                    batch_opts = med_df[med_df["name"]==selected_med]["batch"].astype(str).tolist()
                selected_batch = st.selectbox(f"Batch {i+1}", options=["-- select batch --"] + batch_opts, key=f"sel_batch_{challan_no}_{i}")
                item_name = st.text_input(f"Item name (or override)", value=selected_med if selected_med and selected_med != "-- type or pick --" else "", key=f"item_name_{challan_no}_{i}")
            with c2:
                qty = st.number_input(f"Qty {i+1}", min_value=0.0, value=1.0, step=1.0, key=f"qty_{challan_no}_{i}")
                # show stock for selected batch
                stock_text = ""
                if selected_med and selected_batch and selected_batch != "-- select batch --":
                    batch_row = med_df[(med_df["name"]==selected_med) & (med_df["batch"]==selected_batch)]
                    if not batch_row.empty:
                        stock_text = f"Stock: {batch_row.iloc[0]['qty']}"
                st.markdown(stock_text)
            with c3:


                # autofill rate & gst from selected batch if available
                

                # Create session keys for this row
                mrp_key = f"mrp_{challan_no}_{i}"
                rate_key = f"rate_{challan_no}_{i}"
                gst_key = f"gst_{challan_no}_{i}"

                # Initialize keys if not exist
                if mrp_key not in st.session_state:
                    st.session_state[mrp_key] = 0.0
                if rate_key not in st.session_state:
                    st.session_state[rate_key] = 0.0
                if gst_key not in st.session_state:
                    st.session_state[gst_key] = DEFAULT_GST

                # Find matching batch row
                if selected_med != "-- type or pick --" and selected_batch != "-- select batch --":
                    match = med_df[
                        (med_df["name"].astype(str).str.strip().str.upper() == selected_med.strip().upper()) &
                        (med_df["batch"].astype(str).str.strip().str.upper() == selected_batch.strip().upper())
                    ]
                    if not match.empty:
                        row = match.iloc[0]

                        # UPDATE SESSION VALUES (autofill happens here)
                        st.session_state[mrp_key] = float(row.get("mrp", row.get("MRP", 0)) or 0)
                        st.session_state[rate_key] = float(row.get("rate", row.get("RATE", 0)) or 0)
                        st.session_state[gst_key] = float(row.get("gst", row.get("GST", DEFAULT_GST)) or DEFAULT_GST)

                # Now create widgets USING session_state
                mrp = st.number_input(
                    f"MRP {i+1}",
                    min_value=0.0,
                    key=mrp_key
                )
                rate = st.number_input(
                    f"Rate {i+1}",
                    min_value=0.0,
                    key=rate_key
                )
                gst = st.number_input(
                    f"GST % {i+1}",
                    min_value=0.0,
                    max_value=28.0,
                    key=gst_key
                )
                discount = st.number_input(
                    f"Discount % {i+1}",
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0,
                    key=f"disc_{challan_no}_{i}"
                )

            amt = compute_row_amount(qty, rate, discount, gst)
            st.write(f"Row total (after discount + GST): **₹ {amt:.2f}**")
            new_items.append({
                "challan_no": int(challan_no),
                "date": date_val.strftime("%Y-%m-%d"),
                "party": party,
                "item": selected_med,
                "batch": selected_batch if selected_batch and selected_batch!="-- select batch --" else "",
                "qty": qty,
                "rate": rate,
                "mrp":mrp,
                "discount": discount,
                "gst": gst,
                "amount": amt,
                "grand_total": 0.0
            })
        grand_total = round(sum(x["amount"] for x in new_items), 2)
        st.subheader(f"Grand Total: ₹ {grand_total:.2f}")
        if st.button("Save Challan and reduce stock", key=f"save_ch_{challan_no}"):
            if not party:
                st.error("Enter party name.")
            else:
                # check stock availability for each item (if batch chosen)
                for it in new_items:
                    if it["batch"]:
                        batch_row = med_df[(med_df["name"]==it["item"]) & (med_df["batch"]==it["batch"])]
                        if batch_row.empty:
                            batch_row = med_df[med_df["batch"]==it["batch"]]
                        if not batch_row.empty:
                            available = float(batch_row.iloc[0]["qty"])
                            if available < float(it["qty"]):
                                st.error(f"Not enough stock for {it['item']} batch {it['batch']}. Available {available}, requested {it['qty']}")
                                st.stop()
                # apply changes: reduce stock and append challan rows
                for it in new_items:
                    it["grand_total"] = grand_total
                    if it["batch"]:
                        idxs = med_df[(med_df["batch"]==it["batch"]) & (med_df["name"]==it["item"])].index
                        if len(idxs)==0:
                            idxs = med_df[med_df["batch"]==it["batch"]].index
                        if len(idxs)>0:
                            midx = idxs[0]
                            med_df.at[midx,"qty"] = float(med_df.at[midx,"qty"]) - float(it["qty"])
                # append to challan dataframe
                new_df = pd.DataFrame(new_items)
                challans_df = load_challans()
                challans_df = pd.concat([challans_df, new_df], ignore_index=True)
                save_challans(challans_df)
                save_medicines(med_df)
                st.success(f"Challan {challan_no} saved. Grand total ₹ {grand_total:.2f}")
                # reload data
                challans_df = load_challans()
                med_df = load_medicines()
                try:
                    st.experimental_rerun()
                except:
                    pass

    with col2:
        st.subheader("Saved Challans")
        if challans_df.empty:
            st.info("No challans yet.")
        else:
            # unique challans
            unique_ch = sorted(challans_df["challan_no"].unique().tolist(), reverse=True)
            search = st.text_input("Search party or item (partial)", key="search_ch")
            filtered = []
            for ch in unique_ch:
                chdf = challans_df[challans_df["challan_no"]==ch]
                if search:
                    if chdf["party"].astype(str).str.contains(search, case=False, na=False).any() or chdf["item"].astype(str).str.contains(search, case=False, na=False).any():
                        filtered.append(ch)
                else:
                    filtered.append(ch)
            for ch in filtered:
                chdf = challans_df[challans_df["challan_no"]==ch].copy()
                if chdf.empty:
                    continue
                party = chdf.iloc[0]["party"]
                date_str = chdf.iloc[0]["date"]
                grand = float(chdf.iloc[0].get("grand_total", chdf["amount"].sum()))
                with st.expander(f"Challan {ch} — {party} — {date_str} — Grand ₹{grand:.2f}", expanded=False):
                    st.write(f"Party: **{party}** &nbsp;&nbsp; Date: **{date_str}**")
                    st.dataframe(chdf[["item","batch","qty","rate","discount","gst","amount"]].reset_index(drop=True))
                    # Download PDF
                    pdf_bytes = challan_to_pdf_bytes(chdf)
                    st.download_button("Download Challan (PDF)", data=pdf_bytes, file_name=f"challan_{ch}.pdf", mime="application/pdf", key=f"dlpdf_{ch}")
                    msg_lines = []
                    msg_lines.append(f"challan {ch} | Date: {date_str}")
                    msg_lines.append(f"Party: {party}")
                    msg_lines.append("")
                    for _,row in chdf.iterrows():
                        item = str(row.get("item",""))
                        batch = str(row.get("batch",""))
                        qty = row.get("qty",0)
                        rate = row.get("rate",0)
                        amt = row.get("amount",0)
                        msg_lines.append(f"{item} | Batch:{batch} | Qty: {qty} | Rate:{rate} | Amt: {amt}")
                        msg_lines.append("")
                        msg_lines.append(f"Grand Total: Rs {grand:.2f}")
                        msg_lines.append("")
                        msg_lines.append("Please find challan attached. - New pharmaways")
                        message_text = "\n".join(msg_lines)
                        encoded = quote_plus(message_text)

                        if wa_default_number and wa_default_number.strip():
                            wa_link = f"https://wa.me/{wa_default_number.strip()}?text={encoded}"
                        else:
                            wa_link = f"https://wa.me/?text={encoded}"
                        st.markdown("**WhatsApp message preview**")
                        st.code(message_text)
                        st.markdown(f'<a href="{wa_link}" target="_blank>Send via Whatsapp</a>"')
                    c1,c2,c3 = st.columns([1,1,1])
                    with c1:
                        if st.button("Edit Challan", key=f"edit_ch_{ch}"):
                            st.session_state["_edit_challan"] = ch
                            try:
                                st.experimental_rerun()
                            except:
                                pass
                    with c2:
                        if st.button("Delete Challan", key=f"del_ch_{ch}"):
                            # delete all rows with this challan
                            challans_df = challans_df[challans_df["challan_no"] != ch]
                            save_challans(challans_df)
                            st.success(f"Deleted challan {ch}")
                            try:
                                st.experimental_rerun()
                            except:
                                pass
                    with c3:
                        # export summary CSV as well
                        agg = pd.DataFrame([{
                            "challan_no": ch,
                            "party": party,
                            "date": date_str,
                            "grand_total": grand,
                            "items_count": len(chdf)
                        }])
                        st.download_button("Download summary CSV", data=agg.to_csv(index=False).encode("utf-8"), file_name=f"challan_{ch}_summary.csv", mime="text/csv", key=f"dl_sum_{ch}")

# ---------------- Edit Challan if requested ----------------
if "_edit_challan" in st.session_state:
    edit_no = st.session_state["_edit_challan"]
    st.markdown("---")
    st.header(f"✏️ Edit Challan {edit_no}")
    edit_df = challans_df[challans_df["challan_no"]==edit_no].copy()
    if edit_df.empty:
        st.error("Challan not found (it may have been deleted).")
        del st.session_state["_edit_challan"]
    else:
        edit_party = st.text_input("Party", value=str(edit_df.iloc[0]["party"]), key=f"edit_party_{edit_no}")
        edit_date = st.date_input("Date", value=pd.to_datetime(edit_df.iloc[0]["date"]).date() if pd.notna(edit_df.iloc[0]["date"]) else date.today(), key=f"edit_date_{edit_no}")
        st.markdown("**Edit line items**")
        updated_items = []
        for local_idx, row in edit_df.reset_index(drop=True).iterrows():
            st.markdown(f"---\n**Row {local_idx+1}**")
            c1, c2, c3 = st.columns([4,2,2])
            with c1:
                new_item = st.text_input(f"Item {local_idx}", value=row.get("item",""), key=f"edit_item_{edit_no}_{local_idx}")
                new_batch = st.text_input(f"Batch {local_idx}", value=row.get("batch",""), key=f"edit_batch_{edit_no}_{local_idx}")
            with c2:
                new_qty = st.number_input(f"Qty {local_idx}", min_value=0.0, value=float(row.get("qty",0.0)), key=f"edit_qty_{edit_no}_{local_idx}")
                new_rate = st.number_input(f"Rate {local_idx}", min_value=0.0, value=float(row.get("rate",0.0)), key=f"edit_rate_{edit_no}_{local_idx}")
            with c3:
                new_disc = st.number_input(f"Discount % {local_idx}", min_value=0.0, max_value=100.0, value=float(row.get("discount",0.0)), key=f"edit_disc_{edit_no}_{local_idx}")
                new_gst = st.number_input(f"GST % {local_idx}", min_value=0.0, max_value=28.0, value=float(row.get("gst",DEFAULT_GST)), key=f"edit_gst_{edit_no}_{local_idx}")
            new_amount = compute_row_amount(new_qty, new_rate, new_disc, new_gst)
            st.write(f"Row total: **₹ {new_amount:.2f}**")
            updated_items.append({
                "challan_no": edit_no,
                "date": edit_date.strftime("%Y-%m-%d"),
                "party": edit_party,
                "item": new_item,
                "batch": new_batch,
                "qty": new_qty,
                "rate": new_rate,
                "discount": new_disc,
                "gst": new_gst,
                "amount": new_amount,
                "grand_total": 0.0
            })
        new_grand = round(sum(x["amount"] for x in updated_items), 2)
        st.subheader(f"Updated Grand Total: ₹ {new_grand:.2f}")
        csave, ccancel = st.columns([1,1])
        with csave:
            if st.button("Save Edited Challan", key=f"save_edit_{edit_no}"):
                challans_df = challans_df[challans_df["challan_no"] != edit_no]
                for r in updated_items:
                    r["grand_total"] = new_grand
                challans_df = pd.concat([challans_df, pd.DataFrame(updated_items)], ignore_index=True)
                save_challans(challans_df)
                st.success("Challan updated.")
                del st.session_state["_edit_challan"]
                try:
                    st.experimental_rerun()
                except:
                    pass
        with ccancel:
            if st.button("Cancel Edit", key=f"cancel_edit_{edit_no}"):
                del st.session_state["_edit_challan"]
                try:
                    st.experimental_rerun()
                except:
                    pass

# ---------------- TAB: Reports / Utilities ----------------
with tab3:
    st.header("📊 Reports & Utilities")
    c1,c2 = st.columns(2)
    with c1:
        st.subheader("Export")
        if not challans_df.empty:
            st.download_button("Download All Challans CSV", data=challans_df.to_csv(index=False).encode("utf-8"), file_name="all_challans.csv", mime="text/csv")
            # consolidated PDF booklet of all challans
            pdf_all = all_challans_booklet_bytes(challans_df)
            st.download_button("Download ALL Challans (PDF booklet)", data=pdf_all, file_name="all_challans_booklet.pdf", mime="application/pdf")
        if not med_df.empty:
            st.download_button("Download Medicines CSV", data=med_df.to_csv(index=False).encode("utf-8"), file_name="medicines.csv", mime="text/csv")
    with c2:
        st.subheader("Summary")
        total_ch = len(challans_df["challan_no"].unique()) if not challans_df.empty else 0
        total_items = len(challans_df) if not challans_df.empty else 0
        st.write("Total challans:", total_ch)
        st.write("Total line items:", total_items)
        st.write("Total outstanding stock (sum of all batch qty):", float(med_df["qty"].astype(float).sum()) if not med_df.empty else 0.0)
    st.markdown("---")
    st.subheader("GSTR-1 Simple Report (from challans)")
    if not challans_df.empty:
        b = challans_df.copy()
        b["date"] = pd.to_datetime(b["date"], errors="coerce")
        # gst amount & taxable value approximations
        b["gst_amount"] = ( (b["qty"].astype(float) * b["rate"].astype(float) - (b["qty"].astype(float) * b["rate"].astype(float) * b["discount"].astype(float)/100.0)) * (b["gst"].astype(float)/100.0) ).round(2)
        b["taxable_value"] = (b["qty"].astype(float) * b["rate"].astype(float) - (b["qty"].astype(float) * b["rate"].astype(float) * b["discount"].astype(float)/100.0)).round(2)
        b["month"] = b["date"].dt.to_period("M").astype(str)
        monthly = b.groupby("month").agg(invoices=("challan_no","nunique"), taxable_value=("taxable_value","sum"), gst_amount=("gst_amount","sum"), total_value=("amount","sum")).reset_index()
        st.dataframe(monthly)
        st.download_button("Download GST monthly CSV", data=monthly.to_csv(index=False).encode("utf-8"), file_name="gstr1_monthly.csv", mime="text/csv")
    else:
        st.info("No challans to generate GST report.")

# ---------------- TAB: Day Book ----------------
with tab4:
    st.header("📒 Day Book (Cash / Bank / Party payments)")
    st.markdown("Use Day Book to record party payments (Credit) and expenses (Debit).")
    colA, colB = st.columns([2,1])
    with colA:
        st.subheader("Add Day Book Entry")
        entry_type = st.selectbox("Type", options=["Credit (Party Payment)","Debit (Expense)"], key="db_type")
        entry_date = st.date_input("Date", value=date.today(), key="db_date")
        party_or_payee = st.text_input("Party / Payee (Name)", key="db_party")
        if entry_type.startswith("Credit"):
            category = st.selectbox("Category (credit)", options=["Payment Received", "Adjustment", "Credit Note"], key="db_cat_credit")
        else:
            category = st.selectbox("Category (debit)", options=["JK Bank", "Office Expense", "TA", "Other"], key="db_cat_debit")
        amount = st.number_input("Amount (₹)", min_value=0.0, value=0.0, key="db_amount")
        note = st.text_input("Note / Narration", key="db_note")
        if st.button("Save Day Book Entry", key="db_save"):
            if not party_or_payee:
                st.error("Enter party / payee name.")
            elif amount <= 0:
                st.error("Enter amount greater than zero.")
            else:
                # generate id
                db = load_daybook()
                next_id = len(db) + 1
                eid = f"D{next_id:05d}"
                new_row = {
                    "entry_id": eid,
                    "date": entry_date.strftime("%Y-%m-%d"),
                    "type": "CREDIT" if entry_type.startswith("Credit") else "DEBIT",
                    "party_or_payee": party_or_payee,
                    "category": category,
                    "amount": amount,
                    "note": note
                }
                daybook_df = pd.concat([db, pd.DataFrame([new_row])], ignore_index=True)
                save_daybook(daybook_df)
                st.success(f"Saved daybook entry {eid}")
                # reload
                daybook_df = load_daybook()
    with colB:
        st.subheader("Quick Day Totals")
        db = load_daybook()
        if db.empty:
            st.info("No day book entries yet.")
        else:
            # show totals today
            today_str = date.today().strftime("%Y-%m-%d")
            today_df = db[db["date"]==today_str]
            tot_credit = today_df[today_df["type"]=="CREDIT"]["amount"].astype(float).sum() if not today_df.empty else 0.0
            tot_debit = today_df[today_df["type"]=="DEBIT"]["amount"].astype(float).sum() if not today_df.empty else 0.0
            st.metric("Total Credits (today)", f"₹ {tot_credit:.2f}")
            st.metric("Total Debits (today)", f"₹ {tot_debit:.2f}")

    st.markdown("---")
    st.subheader("View / Filter Day Book")
    db = load_daybook()
    if db.empty:
        st.info("No entries recorded.")
    else:
        # filters
        colf1, colf2, colf3 = st.columns([1,1,1])
        with colf1:
            d_from = st.date_input("From", value=pd.to_datetime(db["date"]).min().date() if not db.empty else date.today(), key="db_from")
        with colf2:
            d_to = st.date_input("To", value=pd.to_datetime(db["date"]).max().date() if not db.empty else date.today(), key="db_to")
        with colf3:
            ftype = st.selectbox("Type (All/Credit/Debit)", options=["All","CREDIT","DEBIT"], key="db_filter_type")
        filtered = db.copy()
        filtered["date"] = pd.to_datetime(filtered["date"], errors="coerce")
        filtered = filtered[(filtered["date"].dt.date >= d_from) & (filtered["date"].dt.date <= d_to)]
        if ftype != "All":
            filtered = filtered[filtered["type"] == ftype]
        st.dataframe(filtered.reset_index(drop=True))
        # totals
        total_credit = filtered[filtered["type"]=="CREDIT"]["amount"].astype(float).sum() if not filtered.empty else 0.0
        total_debit = filtered[filtered["type"]=="DEBIT"]["amount"].astype(float).sum() if not filtered.empty else 0.0
        st.write(f"Total Credit in filtered: ₹ {total_credit:.2f}")
        st.write(f"Total Debit in filtered: ₹ {total_debit:.2f}")
        # downloads
        st.download_button("Download filtered Day Book CSV", data=filtered.to_csv(index=False).encode("utf-8"), file_name="daybook_filtered.csv", mime="text/csv")
        pdf_db = daybook_to_pdf_bytes(filtered, title=f"Day Book {d_from} to {d_to}")
        st.download_button("Download filtered Day Book PDF", data=pdf_db, file_name="daybook_filtered.pdf", mime="application/pdf")
        # ability to delete an entry (careful)
        if st.button("Purge all filtered entries (DELETE)", key="db_purge"):
            confirm = st.text_input("Type YES to confirm purge", key="db_confirm_text")
            if confirm == "YES":
                # remove those rows from master daybook
                master = load_daybook()
                # build mask for removal
                to_remove_ids = filtered["entry_id"].tolist()
                master = master[~master["entry_id"].isin(to_remove_ids)]
                save_daybook(master)
                st.success("Purged filtered entries.")
                st.experimental_rerun()
            else:
                st.warning("Type YES to confirm.")
    # ---------------- TAB: Dashboard ----------------


with tab5:
    st.header("📊 Dynamic Dashboard")
    
    # ---------- Challans Analytics ----------
    st.subheader("Challans Analytics")
    if not challans_df.empty:
        df = challans_df.copy()
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["month"] = df["date"].dt.to_period("M").astype(str)
        
        monthly_sales = df.groupby("month")["grand_total"].sum().reset_index()
        top_meds = df.groupby("item")["qty"].sum().sort_values(ascending=False).head(10).reset_index()
        
        col1, col2 = st.columns(2)
        with col1:
            st.bar_chart(monthly_sales.set_index("month"))
        with col2:
            st.bar_chart(top_meds.set_index("item"))
    else:
        st.info("No challans data for analytics.")


    # ---------- Inventory Analytics ----------
    st.subheader("Inventory Analytics")
    if not med_df.empty:
        low_stock = med_df[med_df["qty"]<10]
        col1, col2 = st.columns([2,1])
        with col1:
            stock_chart = med_df.groupby("name")["qty"].sum().sort_values(ascending=False)
            st.bar_chart(stock_chart)
        with col2:
            st.write("Low Stock (<10 units)")
            st.dataframe(low_stock[["name","batch","qty"]])
    else:
        st.info("No medicines data for inventory analytics.")

    # ---------- Daybook Analytics ----------
    st.subheader("Day Book Analytics")
    if not daybook_df.empty:
        db = daybook_df.copy()
        db["date"] = pd.to_datetime(db["date"], errors="coerce")
        daily_credit = db[db["type"]=="CREDIT"].groupby("date")["amount"].sum().reset_index()
        daily_debit = db[db["type"]=="DEBIT"].groupby("date")["amount"].sum().reset_index()
        col1, col2 = st.columns([1,1])
        with col1:
            st.line_chart(daily_credit.set_index("date"))
        with col2:
            st.line_chart(daily_debit.set_index("date"))
        
        total_credit = daily_credit["amount"].sum()
        total_debit = daily_debit["amount"].sum()
        st.metric("Total Credit", f"₹ {total_credit:.2f}")
        st.metric("Total Debit", f"₹ {total_debit:.2f}")
        st.metric("Net Balance", f"₹ {total_credit-total_debit:.2f}")
    else:
        st.info("No daybook data for analytics.")
with tab6:
    st.header("🌟 Our Medicine Catalog")

    # Copy medicine dataframe
    med_catalog = med_df.copy()

    # Search box
    search_term = st.text_input("Search medicine or use:", key="adv_search")
    if search_term:
        med_catalog = med_catalog[
            med_catalog['name'].str.contains(search_term, case=False, na=False) |
            med_catalog['batch'].str.contains(search_term, case=False, na=False)
        ]

    # Filter by category (if we add categories later)
    st.subheader("Medicine List")
    for idx, row in med_catalog.iterrows():
        st.markdown(f"**{row['name']}**  |  Batch: {row['batch']}  |  Price: ₹{row['rate']:.2f}")
        st.write(f"**Use:**{row.get('use','N/A')}")
        st.write(f"Expiry: {row.get('expiry','N/A')}, Stock: {row.get('qty',0)}")
        st.markdown("---")

    # Download catalog
    st.download_button("📥 Download Catalog as CSV", med_catalog.to_csv(index=False), "medicines_catalog.csv")
with tab7:
    st.header("Party Ledger / Balances")

    # ---------------- Add New Party ----------------
    st.subheader("➕ Add New Party")
    new_party_name = st.text_input("Party Name", key="new_party_name")
    initial_balance = st.number_input("Initial Balance (₹)", min_value=0.0, value=0.0, key="new_party_balance")
    note = st.text_input("Note / Reference", value="Initial balance", key="new_party_note")

    if st.button("Add Party", key="btn_add_party"):
        if not new_party_name:
            st.error("Enter party name")
        else:
            if new_party_name in ledger_df['party'].values:
                st.warning(f"Party '{new_party_name}' already exists.")
            else:
                new_entry = {
                    "entry_id": len(ledger_df)+1,
                    "party": new_party_name,
                    "date": date.today().strftime("%Y-%m-%d"),
                    "type": "initial",
                    "amount": initial_balance,
                    "balance": initial_balance,
                    "note": note
                }
                ledger_df = pd.concat([ledger_df, pd.DataFrame([new_entry])], ignore_index=True)
                save_ledger(ledger_df)
                st.success(f"Party '{new_party_name}' added!")

    # ---------------- Select Party ----------------
    parties = sorted(ledger_df['party'].dropna().unique().tolist())
    selected_party = st.selectbox("Select Party", options=parties)

    # ---------------- Show Party Entries ----------------
    party_entries = ledger_df[ledger_df['party'] == selected_party]
    st.dataframe(party_entries)

    # ---------------- Record Payment ----------------
    st.subheader("💵 Record Payment")
    payment_party = st.selectbox("Select Party", options=parties, key="pay_party")
    payment_amount = st.number_input("Payment Amount", min_value=0.0)
    payment_note = st.text_input("Note / Reference", key="pay_note")

    if st.button("Add Payment", key="btn_add_payment"):
        last_balance = float(ledger_df[ledger_df['party'] == payment_party]['balance'].iloc[-1])
        new_balance = last_balance - payment_amount
        new_entry = {
            "entry_id": len(ledger_df)+1,
            "party": payment_party,
            "date": date.today().strftime("%Y-%m-%d"),
            "type": "payment",
            "amount": payment_amount,
            "balance": new_balance,
            "note": payment_note
        }
        ledger_df = pd.concat([ledger_df, pd.DataFrame([new_entry])], ignore_index=True)
        save_ledger(ledger_df)
        st.success("Payment added!") 
with tab8:
    party_sel = st.selectbox("Select Party", options=parties, key="party_sel_recurring")
    schedule_type = st.radio("Schedule type", options=["weekly","monthly"])
    note_rec = st.text_input("Note (optional)")

    if schedule_type == "weekly":
        day_week = st.selectbox("Day of Week", options=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
    else:
        days_input = st.text_input("Enter days of month (comma-separated, e.g., 1,10,20)")

    if st.button("Add Recurring Payment"):
        new_row = {"party": party_sel, "schedule_type": schedule_type, "day_of_week": None, "days_of_month": [], "note": note_rec}
        if schedule_type == "weekly":
            new_row["day_of_week"] = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"].index(day_week)
        else:
            try:
                new_row["days_of_month"] = [int(d.strip()) for d in days_input.split(",") if 1 <= int(d.strip()) <= 31]
                if not new_row["days_of_month"]:
                    st.error("Enter valid day numbers (1-31).")
                    st.stop()
            except:
                st.error("Invalid day input")
                st.stop()

        recurring_df = pd.concat([recurring_df, pd.DataFrame([new_row])], ignore_index=True)
        save_recurring(recurring_df)
        st.success(f"Recurring payment for {party_sel} added successfully!")

    # ====== Run this every time, not just after adding a payment ======
    today = datetime.today()
    today_day = today.day        # 1-31
    today_weekday = today.weekday()  # 0=Monday

    # Weekly due today
    weekly_due = recurring_df[
        (recurring_df['schedule_type'] == "weekly") & 
        (recurring_df['day_of_week'] == today_weekday)
    ]

    # Monthly due today
    monthly_due = recurring_df[
        (recurring_df['schedule_type'] == "monthly") & 
        (recurring_df['days_of_month'].apply(lambda x: today_day in x if isinstance(x, list) else False))
    ]

    due_today = pd.concat([weekly_due, monthly_due], ignore_index=True)

    if not due_today.empty:
        st.subheader("💰 Payments Due Today (10% of Balance)")
        for _, row in due_today.iterrows():
            party_name = row['party']
            note = row['note']
            # get current balance from ledger
            party_entries = ledger_df[ledger_df['party'] == party_name]
            if not party_entries.empty:
                current_balance = float(party_entries['balance'].iloc[-1])
                due_amount = round(current_balance * 0.10, 2)
                st.write(f"{party_name} → ₹ {due_amount:.2f} ({note})")
            else:
                st.write(f"{party_name} → No balance recorded")
    else:
        st.info("No payments due today")
with tab9:
    st.header("💳 Billing System")

    billing_type = st.radio(
        "Select Billing Type",
        ["Billing from Challans (NO GST)", "Direct Billing (WITH GST)"]
    )

    # ==============================================================
    # 1️⃣ BILLING FROM CHALLANS (NO GST)
    # ==============================================================
    if billing_type == "Billing from Challans (NO GST)":

        st.subheader("📄 Merge Multiple Challans (NO GST)")

        # Step 1: Select Party
        parties = sorted(challans_df["party"].dropna().unique().tolist())
        party_sel = st.selectbox("Select Party", parties)

        # Step 2: Select multiple challans of party
        party_challans = challans_df[challans_df["party"] == party_sel]["challan_no"].unique().tolist()

        challan_selected = st.multiselect("Select Challans to Merge", party_challans)

        if challan_selected:
            # Filter items from selected challans
            merged_items = challans_df[challans_df["challan_no"].isin(challan_selected)]
            items_json = merged_items.to_dict(orient="records")

            st.write("### Merged Items")
            st.dataframe(merged_items, use_container_width=True)

            total_amount = merged_items["amount"].sum()

            st.markdown(f"### **Total (No GST): ₹{total_amount}**")
            bill_df = load_bills()

            if st.button("💾 Save Bill from Challans"):

                selected_party = party_sel.strip()     # FIXED
                bill_total = total_amount      # FIXED

                # --- Save to daybook ---
                new_bill_entry = {
                    "bill_id": len(bill_df)+1,
                    "party": selected_party,
                    "date": str(date.today()),
                    "total_amount": bill_total,
                    "items":json.dumps(items_json),
                    "gst": 0,
                    "discount": 0,
                    "bill_amount": bill_total,
                    "note": f"Billed from {len(challan_selected)} challans"
                }

                bills_df = load_bills()
                bills_df = pd.concat([bills_df, pd.DataFrame([new_bill_entry])], ignore_index=True)
                save_bill(bills_df)

                # --- Update ledger balance only ---
                # --- Update Ledger Cumulative Balance ---
                ledger_df = load_ledger()

                ledger_df['party_clean'] = (
                    ledger_df['party']
                    .astype(str)
                    .str.strip()
                    .str.upper()
                    .replace(r"\s+", " ", regex=True)
                )
                
                current_party_clean = selected_party.strip().upper().replace(" ", " ")
                party_rows = ledger_df[ledger_df['party_clean'] == current_party_clean]
                
                if not party_rows.empty:
                    # ---- UPDATE EXISTING PARTY LAST ROW ----
                    last_idx = party_rows.index[-1]
                
                    try:
                        last_balance = float(ledger_df.at[last_idx, "balance"])
                    except:
                        last_balance = 0.0
                
                    new_balance = last_balance + bill_total
                
                    # update only balance + note + amount
                    ledger_df.at[last_idx, "amount"] = bill_total
                    ledger_df.at[last_idx, "balance"] = new_balance
                    ledger_df.at[last_idx, "note"] = "Bill No GST (Updated from Challan)"
                
                else:
                    # ---- NO PARTY EXISTS → CREATE NEW ENTRY ----
                    new_balance = bill_total
                    new_entry = {
                        "entry_id": len(ledger_df) + 1,
                        "party": selected_party.strip(),
                        "date": str(date.today()),
                        "type": "Credit",
                        "amount": bill_total,
                        "balance": new_balance,
                        "note": "Bill No GST"
                    }
                    ledger_df = pd.concat([ledger_df, pd.DataFrame([new_entry])], ignore_index=True)
                
                save_ledger(ledger_df)
                st.success("Bill created from selected challans successfully")


                                
            

                
                    
                                       
                
                
                
               
    # ==============================================================
    # 2️⃣ DIRECT BILLING (WITH GST)
    # ==============================================================
    else:
        st.subheader("🧾 Direct Billing (GST + Discount)")

        # Select Party
        parties = ledger_df["party"].unique().tolist()
        selected_party = st.selectbox("Select Customer / Party", parties)

        st.write("### Add Items")

        # Initialize blank rows
        if "direct_bill_items" not in st.session_state:
            st.session_state.direct_bill_items = []

        # Add new item row
        if st.button("➕ Add Item Row"):
            st.session_state.direct_bill_items.append({
                "item": "",
                "batch": "",
                "mrp": 0.0,
                "qty": 1,
                "rate": 0.0,
                "discount_percent": 0.0,
                "gst": 0.0
            })

        remove_rows = []

        for i, r in enumerate(st.session_state.direct_bill_items):

            medicines_df = load_medicines()

            item_list = medicines_df["name"].unique().tolist()

            st.markdown(f"#### Item {i+1}")
            c = st.columns([2, 2, 1.5, 1, 1.5, 1, 1])

            # -------------------------
            #   SELECT ITEM (AUTO-FILL)
            # -------------------------
            with c[0]:
                selected_item = st.selectbox(
                    "Item",
                    options=["-- Select --"] + item_list,
                    index=item_list.index(r["item"]) + 1 if r["item"] in item_list else 0,
                    key=f"item_{i}"
                )
                r["item"] = selected_item

                # Load autofill values
                if selected_item != "-- Select --":
                    med = medicines_df[medicines_df["name"] == selected_item].iloc[0]
                    st.session_state[f"mrp_{i}"] = float(med["mrp"])
                    st.session_state[f"rate_{i}"] = float(med["rate"])
                    st.session_state[f"gst_{i}"] = float(med["gst"])
                    st.session_state[f"batch_{i}"] = str(med["batch"])

                    
                    r["mrp"] = float(med["mrp"])
                    r["rate"] = float(med["rate"])
                    r["gst"] = float(med["gst"])
                    r["batch"] = str(med["batch"])

            # -------------------------
            #   BATCH
            # -------------------------
            with c[1]:
                batch_list = medicines_df[medicines_df["name"] == selected_item]["batch"].unique().tolist() \
                            if selected_item != "-- Select --" else []
                r["batch"] = st.selectbox("Batch", ["-- Select --"] + batch_list,
                                        index=batch_list.index(r["batch"]) + 1 if r["batch"] in batch_list else 0,
                                        key=f"batch_{i}")

            # -------------------------
            #   MRP (Auto-filled)
            # -------------------------
            with c[2]:
                r["mrp"] = st.number_input("MRP", min_value=0.0, value=r["mrp"], key=f"mrp_{i}")

            # -------------------------
            #   QTY
            # -------------------------
            with c[3]:
                r["qty"] = st.number_input("Qty", min_value=1, value=r["qty"], key=f"qty_{i}")

            # -------------------------
            #   RATE (Auto-filled)
            # -------------------------
            with c[4]:
                r["rate"] = st.number_input("Rate", min_value=0.0, value=r["rate"], key=f"rate_{i}")

            # -------------------------
            #   DISCOUNT
            # -------------------------
            with c[5]:
                r["discount_percent"] = st.number_input("Discount %", min_value=0.0, value=r["discount_percent"], key=f"disc_{i}")

            # -------------------------
            #   GST (Auto-filled)
            # -------------------------
            with c[6]:
                r["gst"] = st.number_input("GST %", min_value=0.0, value=r["gst"], key=f"gst_{i}")

            # DELETE ROW
            if st.button("🗑", key=f"del_{i}"):
                remove_rows.append(i)


        # Remove rows
        for i in sorted(remove_rows, reverse=True):
            del st.session_state.direct_bill_items[i]

        # Calculate totals
        calculated_rows = []
        total_discount = 0
        total_gst = 0
        grand_total = 0

        for r in st.session_state.direct_bill_items:
            amount = r["qty"] * r["rate"]
            discount_amt = amount * r["discount_percent"] / 100
            amount_after_discount = amount - discount_amt
            gst_amt = amount_after_discount * r["gst"] / 100
            total = amount_after_discount + gst_amt

            calculated_rows.append({
                **r,
                "amount": amount,
                "discount_amt": discount_amt,
                "gst_amt": gst_amt,
                "total": total
            })

            total_discount += discount_amt
            total_gst += gst_amt
            grand_total += total

        # Show table
        st.write("### Bill Preview")
        df = pd.DataFrame(calculated_rows)
        st.dataframe(df, use_container_width=True)

        st.markdown(f"### Total Discount: ₹{total_discount}")
        st.markdown(f"### Total GST: ₹{total_gst}")
        st.markdown(f"### **Grand Total: ₹{grand_total}**")

        # Save Bill
        # Save Bill
    if st.button("💾 Save Bill (GST Added)"):
        selected_party = selected_party.strip()
        #save bill to bill sheet
        bill_df = load_bills()
        new_bill = {
            "bill_id": len(bill_df)+1,
            "party":selected_party,
            "date":str(date.today()),
            "items":json.dumps(st.session_state.direct_bill_items),
            "bill_amount":grand_total
        }
        bill_df = pd.concat([bill_df,pd.DataFrame([new_bill])],ignore_index=True)
        save_bill(bill_df)
        
        


        # --- Update ledger ---
        # --- Update ledger balance only ---
        ledger_df = load_ledger()
        ledger_df['party'] = ledger_df['party'].str.strip()
        selected_party = selected_party.strip()

        if selected_party in ledger_df['party'].values:
            idx = ledger_df[ledger_df['party'] == selected_party].index[0]
            ledger_df.at[idx, 'balance'] += grand_total
            ledger_df.at[idx, 'date'] = str(date.today())
        else:
            ledger_entry = {
                "entry_id": len(ledger_df) + 1,
                "party": selected_party,
                "date": str(date.today()),
                "type": "opening",
                "amount": 0,                     # ❗ NO bill amount here
                "balance": grand_total,
                "note": "Opening balance auto-created"
            }
            ledger_df = pd.concat([ledger_df, pd.DataFrame([ledger_entry])], ignore_index=True)

        save_ledger(ledger_df)


        # --- Update stock for each billed item ---
        med_df = load_medicines()
        med_df['name'] = med_df['name'].astype(str).str.strip().str.upper()
        med_df['qty'] = pd.to_numeric(med_df['qty'], errors='coerce').fillna(0)

        stock_errors = []
        for r in st.session_state.direct_bill_items:
            med_name = str(r.get("name", "")).strip()
            try:
                qty_sold = float(r.get("qty", 0))
            except Exception:
                qty_sold = 0.0

            if med_name == "":
                stock_errors.append(f"Invalid selection for item '{med_name}' / batch '{batch}' — skipping stock update.")
                continue

            # Try exact match on batch + name first (case-insensitive)
            match = med_df[med_df["name"] == med_name]

            # fallback: same batch, partial name contains
            if match.empty:
                stock_errors.append(f"❌ No stock found for: {med_name}")
                continue

            # prefer the first match (you can adjust logic if you want)
            idx = match.index[0]
            old_qty = float(med_df.at[idx, "qty"])
            if qty_sold > old_qty:
                # warn but reduce to zero (or choose to prevent saving)
                stock_errors.append(f"Insufficient stock for {med_name} | batch {batch}. Available {old_qty}, sold {qty_sold}. Setting to 0.")
                new_qty = 0.0
            else:
                med_df.at[idx, "qty"] = old_qty - qty_sold


        save_medicines(med_df)

        # result messages
        if stock_errors:
            for e in stock_errors:
                st.warning(e)
            st.success(f"Bill saved (ID {new_bill['bill_id']}). Ledger updated. Stock updated with warnings.")
        else:
            st.success(f"Bill saved (ID {new_bill['bill_id']}). Ledger and stock updated successfully.")

if "daily_earnings_df" not in st.session_state:
    st.session_state.daily_earnings_df = load_daily_earnings()
with tab10:
    st.title("Retailer Purchase Rate (PTR) Calculator")
    st.caption("Adjust percentages to match your system")

# Input fields
    mrp = st.number_input("Enter MRP (₹):", min_value=0.0, value=0.0, step=0.1)
    retailer_margin = 20
    stokist_margin = 10
    gst = st.radio("Choose G.S.T", [12, 5])
    quantity = st.number_input("Enter quantity", min_value = 1, value = 1, step = 1)
    hPTR = (mrp - (mrp * (retailer_margin /100)))/(1 + (gst/100))
    PTR = round(hPTR * 1.01,2)
    PTS = round(hPTR - ( hPTR * stokist_margin / 100),2)
    earning_per_strip = PTR - PTS 
    total_earning = round(earning_per_strip * quantity, 2)
    st.write(f"Price to retalier: Rs {PTR}")
    st.write(f"Price to Stokist: Rs {PTS}")
    st.write(f"Your earning:{total_earning}")
    if st.button("Add to Daily Earnings"):
    
        new_row = {
        "DATE": date.today().strftime("%Y-%m-%d"),
        "MRP": mrp,
        "PTR": PTR,
        "PTS": PTS,
        "QUANTITY": quantity,
        "EARNING": total_earning
    }
        st.session_state.daily_earnings_df = pd.concat([st.session_state.daily_earnings_df, pd.DataFrame([new_row])], ignore_index=True)
        save_daily_earnings(st.session_state.daily_earnings_df)
        st.success(f"₹ {total_earning} added to daily earnings for {date.today().strftime('%Y-%m-%d')}")
        
with tab11:
    st.title("Daily Earnings Tracker")
    daily_earnings_df = st.session_state.daily_earnings_df



    if not daily_earnings_df.empty:
        # Select which day's earnings to view
        selected_date = st.date_input("Select Date", value=date.today())
        df_day = daily_earnings_df[daily_earnings_df["DATE"] == selected_date.strftime("%Y-%m-%d")]

        if not df_day.empty:
            st.subheader(f"Earnings for {selected_date.strftime('%Y-%m-%d')}")
            st.dataframe(df_day[["MRP", "PTR", "PTS", "QUANTITY", "EARNING"]])
            total_day_earnings = df_day["EARNING"].sum()
            st.subheader(f"Total Earnings: ₹ {round(total_day_earnings,2)}")
        else:
            st.info("No earnings recorded for this day.")
    st.subheader("Weekly Earning Chart")
    df_week = daily_earnings_df.copy()
    df_week['DATE'] = pd.to_datetime(df_week['DATE'])
    df_week['Week'] = df_week['DATE'].dt.isocalendar().week
    df_week['Year'] = df_week['DATE'].dt.year
    weekly_df = df_week.groupby(['Year','Week'],as_index = False)['EARNING'].sum()
    weekly_df['Week_Label'] = ("Week " + weekly_df['Week'].astype(str) + " " + weekly_df['Year'].astype(str))
    st.write('###weekly Trend')
    st.line_chart(weekly_df, x = "Week_Label", y = "EARNING")
    st.write("###Weekly Bar chart")
    st.bar_chart(weekly_df, x = 'Week_Label', y = 'EARNING')
                  
             
        
        # Optional: delete entries for selected date
    if st.button("Delete Earnings for this Date"):
            daily_earnings_df = daily_earnings_df[daily_earnings_df["DATE"] != selected_date.strftime("%Y-%m-%d")]
            save_daily_earnings(daily_earnings_df)
            st.success("Earnings deleted for selected date.")
    else:
        st.info("No earnings recorded yet.")
with tab12:
    st.title("Special Discount")
    amount = st.number_input("Enter Product Amount (₹)", min_value=0.0)
    discount_percent = st.number_input("Discount (%)", min_value=0.0, max_value=100.0)

    if st.button("Calculate"):
        # Step 1: After discount
        after_discount = amount - (amount * discount_percent / 100)

        # Step 2: 4.45% of discounted amount
        extra_445 = after_discount * 4.45 / 100

        st.success(f"Amount After Discount: ₹ {after_discount:.2f}")
        st.success(f"4.45% of Discounted Amount: ₹ {extra_445:.2f}")
with tab13:
    st.title("Edit Party / view & Update balance")
    ledger_df = load_ledger()
    party_names = ledger_df["party"].unique().tolist()
    selected_party = st.selectbox("Select Party to edit",["--select--"] + party_names)
    if selected_party != "--select--":
        party_row = ledger_df[ledger_df["party"] == selected_party].iloc[0]
        if "balance" in ledger_df.columns:
            st.markdown(f"**Current balance:** Rs {party_row['balance']}")
        new_part_name = st.text_input("Party Name", value = party_row['party'])
        if "balance" in ledger_df.columns:
            new_balance = st.number_input("Balance", value = float(party_row['balance']), step = 1.0)
            if st.button("Save Changes"):
                idx = ledger_df[ledger_df['party'] == selected_party].index[0]
                ledger_df.at[idx, 'party'] = new_party_name
                if 'balance' in ledger_df.columns:
                    ledger_df.at[idx, 'balance'] = new_balance
                save_ledger(ledger_df)
                st.success(f"Party '{selected_party}' updated successfully")
bills_df = load_bills()
with tab14:
    st.title("Sales Book")
    
    if bills_df.empty:
          st.info("No bills Found in excel")
    else:
          st.dataframe(bills_df[["bill_id","party","date"]],use_container_width = True)
          bill_id = st.number_input("Enter bill id to view details", min_value = int(bills_df['bill_id'].min()),max_value = int(bills_df['bill_id'].max()), step = 1)
          selected_bill = bills_df[bills_df['bill_id']==bill_id]
          if not selected_bill.empty:
              bill = selected_bill.iloc[0]
              st.write(f"**Bill Id**{bill['bill_id']}")
              st.write(f"**Party**{bill['party']}")
              st.write(f"**Date**{bill['date']}")
              st.write(f"**Bill Amount** ₹{bill['bill_amount']}")
              try:
                  items = json.loads(bill['items'])
                  items_df = pd.DataFrame(items)
                  st.table(items_df)
              except:
                  st.warning("Cannot parse items for this bill")
          else:
              st.warning("Bill not Found")
with tab15:
    st.title("💰 Daily Payment Book")
    df = load_payments()
    prev_balance = df["balance"].iloc[-1] if len(df) > 0 else 0
    st.info(f"**Previous Balance: ₹ {prev_balance}**")
    st.subheader("Enter Today’s Figures")
    today = date.today()
    todays_receipts = st.number_input("Today's Receipts (₹)", min_value=0, value=0, step=100)
    todays_expenses = st.number_input("Today's Expenses (₹)", min_value=0, value=0, step=100)
    if st.button("Save Today’s Entry"):
        new_balance = prev_balance + todays_receipts - todays_expenses
        new_row = {
            "date": str(today),
            "receipts": todays_receipts,
            "expenses": todays_expenses,
            "balance": new_balance
        }
        df = pd.concat([df, pd.DataFrame([new_row])],ignore_index = True)
        save_payments(df)
    st.subheader("📘 Full Payment History")
    st.dataframe(df)
    st.subheader("🗑 Delete Any Entry")
    if len(df) > 0:
        df["label"] = df.apply(
            lambda row: f"{row['date']} | Receipts: ₹{row['receipts']} | Expenses: ₹{row['expenses']} | Balance: ₹{row['balance']}",axis=1)
        selected_label = st.selectbox("Select entry to delete", df["label"].tolist())
        if st.button("Delete Selected Entry"):
            idx = df[df["label"] == selected_label].index[0]
            df = df.drop(idx).reset_index(drop=True)
            if len(df) > 0:
                df["balance"] = df["receipts"].cumsum() - df["expenses"].cumsum()
            else:
                df["balance"] = []
            save_payments(df)
            st.success("Entry deleted successfully!")
    else:
        st.info("No entries available to delete.")


       
                  
            
                       
        
          
          


          
                                                   

    
    


        
    
    


    
    
       
# ---------------- Save final state (ensure persisted) ----------------
save_challans(challans_df)
save_medicines(med_df)
save_daybook(daybook_df) 
