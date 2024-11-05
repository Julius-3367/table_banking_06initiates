from datetime import datetime
from database.db import get_db
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

db = get_db()

def calculate_monthly_interest():
    # Loop through active loans and update monthly interest
    active_loans = db.loans.find({"status": "active"})
    for loan in active_loans:
        monthly_interest = loan["principal"] * loan["interest_rate"]
        db.loans.update_one(
            {"_id": loan["_id"]},
            {"$inc": {"total_interest": monthly_interest}}
        )

def get_group_financial_summary():
    total_funds = db.funds.find_one({}, {"total_funds": 1}) or {"total_funds": 0}
    total_loans = sum([loan["principal"] for loan in db.loans.find()])
    total_interest = sum([loan["total_interest"] for loan in db.loans.find()])
    
    return {
        "total_funds": total_funds.get("total_funds", 0),
        "total_loans": total_loans,
        "total_interest": total_interest
    }

def generate_pdf_statement(member_id):
    transactions = db.transactions.find({"member_id": member_id})
    pdf_path = f"static/statements/{member_id}_statement.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    
    c.drawString(100, height - 50, f"Transaction Statement for Member: {member_id}")
    
    y = height - 80
    for txn in transactions:
        c.drawString(100, y, f"{txn['timestamp']} - {txn['type']}: {txn['amount']}")
        y -= 20
    
    c.save()
    return pdf_path

