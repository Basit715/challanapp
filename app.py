from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.http import MediaIoBaseDownload
import io
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
password = st.text_input("Enter password:", type="password")
if password:
    if password != st.secrets["APP_PASSWORD"]:
        st.warning("❌ Incorrect password. Access denied.")
        st.stop()
else:
    st.info("🔒 Please enter the password to access the app.")
    st.stop()
st.success("Welcome.You have full access to this app now")    

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
MAX_ITEMS = 50
DEFAULT_GST = 5.0
APP_TITLE = "💊 NEW PharmaWAYS — Challan Manager (BY BASIT PUSHOO)"

# ---------------- Dark theme CSS (modern) ----------------
st.set_page_config(page_title="Pharma Challan Manager", layout="wide", initial_sidebar_state="auto")
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
        pdf.cell(30,8, f"{float(r['amount']):.2f}", border=1, align="R")
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
wa_default_number = st.text_input("Default whatsapp number e.g; 919541292214",value="",key="wa_default_number")

# Tab order: Challans | Medicines | Reports | Day Book (user chose B)
tab1, tab2, tab3, tab4, tab5,tab6,tab7,tab8 = st.tabs(["Challans", "Medicines (Inventory)", "Reports / Utilities", "Day Book","📈 Dashboard","💊 Advertisement","LEDGER","Recurring_Payment"]
                                                )
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
        if st.button("Add Batch", key="btn_add_batch"):
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
        party = st.text_input("Party Name", key="new_party")
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
                rate_default = 0.0
                gst_default = DEFAULT_GST
                mrp_default = 0.0
                if selected_med and selected_batch and selected_batch != "-- select batch --":
                    br = med_df[(med_df["name"]==selected_med) & (med_df["batch"]==selected_batch)]
                    if not br.empty:
                        rate_default = float(br.iloc[0]["rate"] or 0.0)
                        gst_default = float(br.iloc[0]["gst"] or DEFAULT_GST)
                        mrp_default = float(br.iloc[0]["mrp"] or 0.0)
                rate = st.number_input(f"Rate {i+1}", min_value=0.0, value=float(rate_default), key=f"rate_{challan_no}_{i}")
                discount = st.number_input(f"Discount % {i+1}", min_value=0.0, max_value=100.0, value=0.0, key=f"disc_{challan_no}_{i}")
                gst = st.number_input(f"GST % {i+1}", min_value=0.0, max_value=28.0, value=float(gst_default), key=f"gst_{challan_no}_{i}")
            amt = compute_row_amount(qty, rate, discount, gst)
            st.write(f"Row total (after discount + GST): **₹ {amt:.2f}**")
            new_items.append({
                "challan_no": int(challan_no),
                "date": date_val.strftime("%Y-%m-%d"),
                "party": party,
                "item": item_name,
                "batch": selected_batch if selected_batch and selected_batch!="-- select batch --" else "",
                "qty": qty,
                "rate": rate,
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
                if party:
                    total_amount = sum(item['amount'] for item in new_items)
                    if not ledger_df[ledger_df['party']==party].empty:
                        last_balance = float(ledger_df[ledger_df['party']==party]['balance'].iloc[-1])
                    else:
                        last_balance = 0.0

                    new_balance = last_balance + total_amount

                    new_entry = {
                        "entry_id": len(ledger_df)+1,
                        "party": party,
                        "date": date_val.strftime("%Y-%m-%d"),
                        "type": "Credit",
                        "amount": total_amount,
                        "balance": new_balance,
                        "note": f"Challan #{challan_no}"
                    }
                    ledger_df = pd.concat([ledger_df, pd.DataFrame([new_entry])], ignore_index=True)
                    save_ledger(ledger_df)
                    st.success(f"Ledger updated for {party}. New balance: ₹ {new_balance:.2f}")
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
            st.bar_chart(monthly_sales.rename(columns={"month":"index"}).set_index("month"))
        with col2:
            st.bar_chart(top_meds.rename(columns={"item":"index"}).set_index("item"))
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
            st.line_chart(daily_credit.rename(columns={"date":"index"}).set_index("date"))
        with col2:
            st.line_chart(daily_debit.rename(columns={"date":"index"}).set_index("date"))
        
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

    # Select party
    parties = sorted(ledger_df['party'].dropna().unique().tolist())
    selected_party = st.selectbox("Select Party", options=parties)

    # Show party entries
    party_entries = ledger_df[ledger_df['party']==selected_party]
    if not party_entries.empty:
        st.dataframe(party_entries[['date','type','amount','balance','note']].sort_values('date'))
        st.write(f"**Current Balance:** ₹ {party_entries['balance'].iloc[-1]:.2f}")
    else:
        st.info("No ledger entries for this party yet.")

    # Record Payment
    st.subheader("Record Payment")
    payment_party = st.selectbox("Select Party for Payment", options=parties, key="pay_party")
    payment_date = st.date_input("Payment Date", value=date.today(), key="pay_date")
    payment_amount = st.number_input("Payment Amount", min_value=0.0, value=0.0, key="pay_amount")
    payment_note = st.text_input("Note / Reference", key="pay_note")

    if st.button("Add Payment", key="btn_add_payment"):
        last_balance = float(ledger_df[ledger_df['party']==payment_party]['balance'].iloc[-1])
        new_balance = last_balance - payment_amount
        new_entry = {
            "entry_id": len(ledger_df)+1,
            "party": payment_party,
            "date": payment_date.strftime("%Y-%m-%d"),
            "type": "Payment",
            "amount": payment_amount,
            "balance": new_balance,
            "note": payment_note
        }
        ledger_df = pd.concat([ledger_df, pd.DataFrame([new_entry])], ignore_index=True)
        save_ledger(ledger_df)
        st.success(f"Payment recorded. New balance for {payment_party}: ₹ {new_balance:.2f}")
        st.rerun()
with tab8:
    party_sel = st.selectbox("Select Party", options=parties,key="party_sel_recurring")
    schedule_type = st.radio("Schedule type", options=["weekly","monthly"])
    note_rec = st.text_input("Note (optional)")
    if schedule_type == "weekly":
       day_week = st.selectbox("Day of Week", options=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
    else:
       days_input = st.text_input("Enter days of month (comma-separated, e.g., 1,10,20)")
    if st.button("Add Recurring Payment"):
       new_row = {"party":party_sel, "schedule_type":schedule_type, "day_of_week":None, "days_of_month":[], "note":note_rec}
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
today = datetime.today()
today_day = today.day        # 1-31
today_weekday = today.weekday()  # 0=Monday

# Weekly due today
weekly_due = recurring_df[(recurring_df['schedule_type']=="weekly") & (recurring_df['day_of_week']==today_weekday)]
# Monthly due today
monthly_due = recurring_df[(recurring_df['schedule_type']=="monthly") & (recurring_df['days_of_month'].apply(lambda x: today_day in x if isinstance(x,list) else False))]

due_today = pd.concat([weekly_due, monthly_due], ignore_index=True)

if not due_today.empty:
    st.subheader("💰 Payments Due Today (10% of Balance)")
    for _, row in due_today.iterrows():
        party_name = row['party']
        note = row['note']
        # get current balance from ledger
        party_entries = ledger_df[ledger_df['party']==party_name]
        if not party_entries.empty:
            current_balance = float(party_entries['balance'].iloc[-1])
            due_amount = round(current_balance * 0.10, 2)
            st.write(f"{party_name} → ₹ {due_amount:.2f} ({note})")
        else:
            st.write(f"{party_name} → No balance recorded")
else:
    st.info("No payments due today")
       
# ---------------- Save final state (ensure persisted) ----------------
save_challans(challans_df)
save_medicines(med_df)
save_daybook(daybook_df) 
