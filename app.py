import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify
from flask_cors import CORS
import resend  # <--- CHANGED: Import Resend instead of smtplib
from fpdf import FPDF
import uuid
from datetime import datetime
import threading
import os
from dotenv import load_dotenv

load_dotenv()

# ==========================================
#  🔥 FIREBASE SETUP
# ==========================================
# Define the path to the key
render_secret_path = "/etc/secrets/firebase_key.json"
local_secret_path = "firebase_key.json"

if os.path.exists(render_secret_path):
    cred_path = render_secret_path
else:
    cred_path = local_secret_path

# Initialize Firebase
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized successfully.")
    
    db = firestore.client()
except Exception as e:
    print(f"Failed to initialize Firebase: {e}")

# ==========================================
#  ⚙️ CONFIGURATION
# ==========================================
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

ADMIN_PASSWORD = os.getenv("admin_PASSWORD")
COMPANY_ID = os.getenv("company_id")
COMPANY_EMAIL = "raimonacargo@gmail.com"

# --- EMAIL CONFIG (UPDATED FOR VERCEL) ---
# We retrieve the key safely from environment variables
resend.api_key = os.getenv("RESEND_API_KEY")

# ==========================================
#  🎨 PDF CLASS
# ==========================================
class PDF(FPDF):
    def header(self):
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 297, 'F')
        self.set_fill_color(30, 41, 59)
        self.rect(0, 0, 210, 50, 'F')
        
        self.set_font('Arial', 'B', 24)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 15)
        self.cell(0, 10, 'RAIMONA CARGO', 0, 1, 'L')
        
        self.set_font('Arial', '', 10)
        self.set_text_color(148, 163, 184)
        self.set_xy(10, 25)
        self.cell(0, 5, 'Logistics & Transportation Solutions', 0, 1, 'L')

        self.set_font('Arial', 'B', 32)
        self.set_text_color(255, 255, 255)
        self.set_xy(140, 15)
        self.cell(60, 15, 'INVOICE', 0, 1, 'R')

    def footer(self):
        self.set_y(-30)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, 'Thank you for your business. For support: raimonacargo@gmail.com', 0, 1, 'C')
        self.cell(0, 5, f'Page {self.page_no()}', 0, 0, 'C')

# ==========================================
#  🖨️ GENERATE PDF FUNCTION
# ==========================================
def generate_pdf(data, booking_id):
    pdf = PDF()
    pdf.add_page()
    
    # --- ORDER ID BADGE ---
    pdf.set_xy(140, 32)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(147, 197, 253)
    pdf.cell(60, 8, f"#{booking_id}", 0, 1, 'R')

    # --- STATUS BAR ---
    pdf.set_y(50)
    pdf.set_fill_color(255, 255, 255) 
    pdf.rect(0, 50, 210, 20, 'F')
    
    # Date Label
    pdf.set_xy(10, 53)
    pdf.set_font('Arial', 'B', 8)
    pdf.set_text_color(100, 116, 139) 
    pdf.cell(30, 5, "DATE ISSUED", 0, 2)
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(30, 41, 59) 
    pdf.cell(30, 6, datetime.now().strftime('%b %d, %Y'), 0, 0)

    # Due Date
    pdf.set_xy(60, 53)
    pdf.set_font('Arial', 'B', 8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(30, 5, "DUE DATE", 0, 2)
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(30, 6, "Upon Receipt", 0, 0)

    # Status Badge
    pdf.set_xy(160, 55)
    pdf.set_fill_color(254, 243, 199) 
    pdf.set_text_color(180, 83, 9)   
    pdf.set_font('Arial', 'B', 9)
    pdf.rect(160, 54, 40, 10, 'F') 
    pdf.set_xy(160, 56)
    pdf.cell(40, 6, "PENDING", 0, 0, 'C')

    # --- MAIN CONTENT AREA ---
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(10, 80, 190, 180, 'F')
    
    # 1. BILL TO SECTION
    pdf.set_xy(20, 90)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(148, 163, 184) 
    pdf.cell(80, 8, "BILL TO", 0, 1)
    
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(15, 23, 42) 
    pdf.set_x(20)
    pdf.cell(80, 8, data.get('fullName', 'Guest'), 0, 1)
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(59, 130, 246)
    pdf.set_x(20)
    pdf.cell(80, 6, data.get('email', ''), 0, 1)
    
    pdf.set_text_color(71, 85, 105) 
    pdf.set_x(20)
    pdf.cell(80, 6, data.get('phone', ''), 0, 1)
    
    address = data.get('address', '')
    pdf.set_x(20)
    if len(address) > 40:
        pdf.multi_cell(80, 5, address)
    else:
        pdf.cell(80, 6, address, 0, 1)
    
    # 2. SHIPMENT DETAILS
    box_top_y = 100
    pdf.set_fill_color(248, 250, 252) 
    pdf.rect(110, box_top_y, 80, 60, 'F') 
    
    pdf.set_xy(115, box_top_y + 5)
    pdf.set_font('Arial', 'B', 8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(80, 5, "ROUTE", 0, 2)
    
    route_content_y = pdf.get_y() + 2
    pdf.set_xy(115, route_content_y)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(15, 5, "Online", 0, 0)
    
    pdf.set_text_color(148, 163, 184)
    pdf.cell(8, 5, ">>", 0, 0, 'C')
    
    pdf.set_text_color(37, 99, 235)
    dest_x = 138
    pdf.set_xy(dest_x, route_content_y)
    pdf.multi_cell(47, 5, data.get('address', 'Dest'), 0, 'L')
    
    new_y = pdf.get_y() + 6
    pdf.set_xy(115, new_y)
    pdf.set_font('Arial', 'B', 8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(80, 5, "ITEM DESCRIPTION", 0, 2)
    
    pdf.set_font('Arial', 'I', 9)
    pdf.set_text_color(71, 85, 105)
    pdf.set_x(115)
    pdf.multi_cell(70, 5, data.get('productDescription', '-'))
    
    # 3. SERVICE TABLE
    y_table = 180 # Fixed position for stability
    pdf.set_xy(20, y_table)
    
    pdf.set_fill_color(241, 245, 249) 
    pdf.set_text_color(71, 85, 105) 
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(110, 10, "  SERVICE TYPE", 0, 0, 'L', True)
    pdf.cell(60, 10, "QUANTITY / WEIGHT  ", 0, 1, 'R', True)
    
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(15, 23, 42) 
    
    qty = float(data.get('weight', 0)) if data.get('orderType') == 'weight' else float(data.get('boxCount', 0))
    unit = 'kg' if data.get('orderType') == 'weight' else 'boxes'
    service_name = "Air Freight Service" if data.get('orderType') == 'weight' else "Standard Box Delivery"
    
    pdf.ln(10)
    pdf.set_x(20)
    pdf.cell(110, 12, f"  {service_name}", 0, 0, 'L')
    pdf.cell(60, 12, f"{qty} {unit}  ", 0, 1, 'R')
    
    pdf.set_draw_color(226, 232, 240)
    pdf.line(20, pdf.get_y()+12, 190, pdf.get_y()+12)

    filename = f"/tmp/booking_{booking_id}.pdf" # Use /tmp for serverless (Vercel)
    pdf.output(filename)
    return filename

# ==========================================
#  📧 EMAIL FUNCTION (REPLACED WITH RESEND API)
# ==========================================
def send_email_with_pdf(pdf_filename, data):
    customer_email = data.get('email', '')
    customer_name = data.get('fullName', 'Customer')

    # HTML Content
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #0f172a; color: #e2e8f0;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 8px; overflow: hidden; margin-top: 40px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
          
          <div style="background: linear-gradient(to right, #234c6a, #7294ad); padding: 30px; text-align: center;">
            <h1 style="margin: 0; color: white; font-size: 24px;">Raimona Cargo</h1>
          </div>

          <div style="padding: 40px;">
            <h2 style="color: #ffffff; margin-top: 0;">Booking Confirmed</h2>
            <p style="color: #94a3b8;">Dear {customer_name},</p>
            <p style="color: #cbd5e1;">
              Thank you for choosing Raimona Cargo. Your shipment has been successfully scheduled. 
              Please find your official invoice attached.
            </p>
          </div>
        </div>
      </body>
    </html>
    """

    try:
        # Read the PDF file as a list of bytes
        with open(pdf_filename, "rb") as f:
            pdf_bytes = list(f.read())

        # Send via Resend API
        r = resend.Emails.send({
            "from": "Raimona Cargo <onboarding@resend.dev>", # Change this after verifying your domain in Resend
            "to": [customer_email, COMPANY_EMAIL],
            "subject": f"Booking Confirmation #{data.get('id')}",
            "html": html_body,
            "attachments": [
                {
                    "filename": f"Invoice-{data.get('id')}.pdf",
                    "content": pdf_bytes
                }
            ]
        })
        print(f"✅ Email sent successfully via Resend. ID: {r.get('id')}")
        return True

    except Exception as e:
        print(f"❌ Email Error: {e}")
        return False

# ==========================================
#  🚀 MAIN ROUTES
# ==========================================

@app.route('/api/book', methods=['POST'])
def create_booking():
    try:
        data = request.json
        timestamp_str = datetime.utcnow().strftime('%Y%m%d')
        unique_suffix = str(uuid.uuid4())[:4].upper()
        order_id = f"RMC-{timestamp_str}-{unique_suffix}"
        current_time = datetime.utcnow().isoformat() + "Z"

        new_order = {
            "order_id": order_id,
            "created_at": current_time,
            "status": "Pending",
            "customer": {
                "name": data.get('fullName'),
                "email": data.get('email'),
                "phone": data.get('phone'),
                "address": data.get('address')
            },
            "shipment": {
                "description": data.get('productDescription'),
                "type": data.get('orderType'),
                "details": f"{data.get('weight')} kg" if data.get('orderType') == 'weight' else f"{data.get('boxCount')} Boxes",
                "origin": "Online Booking", 
                "destination": data.get('address')
            },
            "history": [{
                "status": "Pending",
                "timestamp": current_time,
                "note": "Order placed via Website"
            }]
        }
        
        db.collection('orders').document(order_id).set(new_order)

        data['id'] = order_id 
        
        # Run email in background
        def handle_email_background(data, order_id):
            try:
                pdf_file = generate_pdf(data, order_id)
                send_email_with_pdf(pdf_file, data)
                
                # Cleanup: Remove the temporary PDF file
                if os.path.exists(pdf_file):
                    os.remove(pdf_file)
            except Exception as e:
                print(f"⚠️ Background Email Error: {e}")
                
        email_thread = threading.Thread(target=handle_email_background, args=(data, order_id))
        email_thread.start()
        
        return jsonify({"success": True, "bookingId": order_id}), 201

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    try:
        orders_ref = db.collection('orders')
        docs = orders_ref.stream()
        all_orders = [doc.to_dict() for doc in docs]
        return jsonify(all_orders), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/orders/<order_id>/status', methods=['PUT'])
def update_status(order_id):
    try:
        new_status = request.json.get('status')
        current_time = datetime.utcnow().isoformat() + "Z"
        order_ref = db.collection('orders').document(order_id)
        order_ref.update({
            "status": new_status,
            "history": firestore.ArrayUnion([{
                "status": new_status,
                "timestamp": current_time,
                "note": f"Status updated to {new_status}"
            }])
        })
        return jsonify({"message": "Updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/invoice/<order_id>', methods=['GET'])
def get_order_details(order_id):
    try:
        doc_ref = db.collection('orders').document(order_id)
        doc = doc_ref.get()
        if doc.exists:
            return jsonify(doc.to_dict()), 200
        else:
            return jsonify({"error": "Order not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.json
        input_password = data.get('password', '').strip()
        input_company_code = data.get('companyCode', '').strip()
        
        if input_password == ADMIN_PASSWORD and input_company_code == COMPANY_ID:
            return jsonify({"success": True, "message": "Login successful"}), 200
        else:
            return jsonify({"success": False, "message": "Incorrect password or company code"}), 401
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)