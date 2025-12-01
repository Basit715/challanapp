import streamlit as st
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


# ------------------ Page Config ------------------
st.set_page_config(
    page_title="Pharma Challan Manager",
    layout="wide",
    initial_sidebar_state="auto"
)

# ------------------ CSS Theme ------------------
st.markdown("""
<style>
:root{
  --bg: #0a0b10;
  --panel: #101522;
  --muted: #9fb7d8;
  --accent: #2ea6ff;
  --accent2: #5ab2ff;
  --card: #0e1628;
  --glass: rgba(255,255,255,0.05);
}
.stApp > header, .stApp > footer { display: none; }
body { background: var(--bg); color: #e6eef6; }
.css-1lcbmhc, .stApp { background: var(--bg); }

.card {
    background: var(--card);
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.60);
    border: 1px solid rgba(255,255,255,0.05);
    text-align: center;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-bottom: 20px;
}
.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 28px rgba(46,166,255,0.4);
}
.card h3 {
    margin: 10px 0 0 0;
    font-size: 18px;
}
.card p {
    margin: 5px 0 0 0;
    font-size: 13px;
    color: var(--muted);
}
</style>
""", unsafe_allow_html=True)

# ------------------ Session State ------------------
if "current_tab" not in st.session_state:
    st.session_state.current_tab = "Dashboard"

# ------------------ Tabs / Quick Actions ------------------
tabs = [
    ("📋 Challans", "View & create challans"),
    ("💊 Medicines", "Inventory management"),
    ("📄 Reports/Utilities", "Reports & tools"),
    ("📔 Day Book", "Daily transaction book"),
    ("📊 Dashboard", "App overview"),
    ("📢 Advertisement", "Promotions & ads"),
    ("🧾 Ledger", "Party ledger"),
    ("💳 Recurring Payment", "Automatic payments"),
    ("🧾 Billing", "Create bills"),
    ("🧮 Calculator", "Quick calculations"),
    ("💰 Daily Earnings", "Track earnings"),
    ("🏷️ Special Discount", "Apply discounts"),
    ("👤 Edit Party / Balance", "Update party info"),
    ("📚 Sales Book", "Sales records"),
    ("💵 Daily Payments", "Payments received"),
    ("📦 Challan Status", "Track challan status")
]

# ------------------ Dashboard Grid ------------------
st.markdown("<h1 style='text-align:center;'>Pharma Challan Manager</h1>", unsafe_allow_html=True)
st.markdown("---")

cols = st.columns(4)
for i, (title, subtitle) in enumerate(tabs):
    with cols[i % 4]:
        # Use clickable card via st.markdown and JS
        if st.markdown(f"""
            <div class="card" onclick="window.location.href='#{title}'">
                <h3>{title}</h3>
                <p>{subtitle}</p>
            </div>
        """, unsafe_allow_html=True):
            st.session_state.current_tab = title

st.markdown("---")

# ------------------ Render Selected Tab ------------------
st.markdown(f"<h2 style='color:#2ea6ff'>{st.session_state.current_tab}</h2>", unsafe_allow_html=True)

# Example: render content per tab
if st.session_state.current_tab == "📋 Challans":
    st.write("Here you can view and create challans...")
elif st.session_state.current_tab == "💊 Medicines":
    st.write("Here is your inventory management page...")
elif st.session_state.current_tab == "📄 Reports/Utilities":
    st.write("Reports and utilities go here...")
elif st.session_state.current_tab == "📔 Day Book":
    st.write("Day book content...")
# ... continue for all 16 tabs
