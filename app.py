import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from fpdf import FPDF
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Define the path to the key
# Render stores secret files at /etc/secrets/
render_secret_path = "/etc/secrets/firebase_key.json"
local_secret_path = "firebase_key.json"

# Check if we are running on Render (file exists there) or locally
if os.path.exists(render_secret_path):
    cred_path = render_secret_path
    print(f"Using Render Secret File: {render_secret_path}")
else:
    cred_path = local_secret_path
    print(f"Using Local File: {local_secret_path}")

# Initialize Firebase with the correct file path
try:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"Failed to initialize Firebase: {e}")
    
# Reconstruct the Firebase credentials dictionary from environment variables
firebase_creds_dict = {
    "type": os.getenv("FIREBASE_TYPE"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    # ... inside your configuration dictionary in app.py ...
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n') if os.getenv("FIREBASE_PRIVATE_KEY") else None,
# ...
    # IMPORTANT: Replace literal \n string with actual newline characters
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n') if os.getenv("FIREBASE_PRIVATE_KEY") else None,
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL"),
    "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN")
}

# --- CONFIGURATION ---
cred = credentials.Certificate(firebase_creds_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()



ADMIN_PASSWORD = os.getenv("admin_PASSWORD")
COMPANY_ID = os.getenv("company_id")
app = Flask(__name__)
CORS(app)

# --- EMAIL CONFIG ---
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SYSTEM_EMAIL = os.getenv("MAIL_USERNAME")
SYSTEM_PASSWORD = os.getenv("MAIL_PASSWORD")
COMPANY_EMAIL = "raimonacargo@gmail.com"

# ==========================================
#  🎨 ADVANCED DARK THEME PDF CLASS
# ==========================================
class PDF(FPDF):
    def header(self):
        # 1. Dark Background for the whole page
        # Note: FPDF adds pages white by default. We draw a big rect.
        # But header() runs at start of page.
        self.set_fill_color(15, 23, 42) # #0f172a (Slate 900)
        self.rect(0, 0, 210, 297, 'F')

        # 2. Header Gradient/Shape Effect (Top Banner)
        self.set_fill_color(30, 41, 59) # #1e293b (Slate 800)
        self.rect(0, 0, 210, 50, 'F')
        
        # 3. Logo / Brand Text
        self.set_font('Arial', 'B', 24)
        self.set_text_color(255, 255, 255) # White
        self.set_xy(10, 15)
        self.cell(0, 10, 'RAIMONA CARGO', 0, 1, 'L')
        
        self.set_font('Arial', '', 10)
        self.set_text_color(148, 163, 184) # Slate 400
        self.set_xy(10, 25)
        self.cell(0, 5, 'Logistics & Transportation Solutions', 0, 1, 'L')

        # 4. "INVOICE" Title (Right Side)
        self.set_font('Arial', 'B', 32)
        self.set_text_color(255, 255, 255)
        self.set_xy(140, 15)
        self.cell(60, 15, 'INVOICE', 0, 1, 'R')

    def footer(self):
        self.set_y(-30)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(148, 163, 184) # Slate 400
        self.cell(0, 10, 'Thank you for your business. For support: raimonacargo@gmail.com', 0, 1, 'C')
        self.cell(0, 5, f'Page {self.page_no()}', 0, 0, 'C')

# ==========================================
#  🖨️ GENERATE PDF FUNCTION
# ==========================================
# ==========================================
#  🖨️ GENERATE PDF FUNCTION (Updated)
# ==========================================
# ==========================================
#  🖨️ GENERATE PDF FUNCTION (Fixed Layout)
# ==========================================
def generate_pdf(data, booking_id):
    pdf = PDF()
    pdf.add_page()
    
    # --- ORDER ID BADGE ---
    pdf.set_xy(140, 32)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(147, 197, 253) # Blue 300
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
    
    # 1. BILL TO SECTION (Left)
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
    
    # Address Handling (Left Side)
    address = data.get('address', '')
    pdf.set_x(20)
    if len(address) > 40:
        pdf.multi_cell(80, 5, address)
    else:
        pdf.cell(80, 6, address, 0, 1)
    
    y_end_left = pdf.get_y()

    # 2. SHIPMENT DETAILS (Right Side - Gray Box)
    pdf.set_xy(110, 90)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(80, 8, "SHIPMENT DETAILS", 0, 1)
    
    # Gray Background Box (Height increased to 60 to fit wrapped text)
    box_top_y = 100
    pdf.set_fill_color(248, 250, 252) 
    pdf.rect(110, box_top_y, 80, 60, 'F') 
    
    # -- Route Section --
    pdf.set_xy(115, box_top_y + 5)
    pdf.set_font('Arial', 'B', 8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(80, 5, "ROUTE", 0, 2)
    
    # Online Label
    route_content_y = pdf.get_y() + 2
    pdf.set_xy(115, route_content_y)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(15, 5, "Online", 0, 0)
    
    # Arrow
    pdf.set_text_color(148, 163, 184)
    pdf.cell(8, 5, ">>", 0, 0, 'C')
    
    # Destination (Wrapped inside box)
    pdf.set_text_color(37, 99, 235) # Blue 600
    dest_x = 138 # 115 + 15 + 8
    pdf.set_xy(dest_x, route_content_y)
    # 47 width ensures it fits within the 80 width box (110+80=190 boundary)
    pdf.multi_cell(47, 5, data.get('address', 'Dest'), 0, 'L')
    
    # -- Item Description (Dynamic Position below Route) --
    new_y = pdf.get_y() + 6 # Add padding below address
    pdf.set_xy(115, new_y)
    pdf.set_font('Arial', 'B', 8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(80, 5, "ITEM DESCRIPTION", 0, 2)
    
    pdf.set_font('Arial', 'I', 9)
    pdf.set_text_color(71, 85, 105)
    # Wrap item description inside box
    pdf.set_x(115)
    pdf.multi_cell(70, 5, data.get('productDescription', '-'))
    
    y_end_right = pdf.get_y()

    # 3. SERVICE TABLE
    # Ensure table starts below the lowest point of either column
    y_table = max(y_end_left, y_end_right, box_top_y + 60) + 15
    pdf.set_xy(20, y_table)
    
    # Table Header
    pdf.set_fill_color(241, 245, 249) 
    pdf.set_text_color(71, 85, 105) 
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(110, 10, "  SERVICE TYPE", 0, 0, 'L', True)
    pdf.cell(60, 10, "QUANTITY / WEIGHT  ", 0, 1, 'R', True)
    
    # Table Row
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(15, 23, 42) 
    
    qty = float(data.get('weight', 0)) if data.get('orderType') == 'weight' else float(data.get('boxCount', 0))
    unit = 'kg' if data.get('orderType') == 'weight' else 'boxes'
    service_name = "Air Freight Service" if data.get('orderType') == 'weight' else "Standard Box Delivery"
    
    pdf.ln(10)
    pdf.set_x(20)
    pdf.cell(110, 12, f"  {service_name}", 0, 0, 'L')
    pdf.cell(60, 12, f"{qty} {unit}  ", 0, 1, 'R')
    
    # Bottom Line
    pdf.set_draw_color(226, 232, 240)
    pdf.line(20, pdf.get_y()+12, 190, pdf.get_y()+12)

    filename = f"booking_{booking_id}.pdf"
    pdf.output(filename)
    return filename

# ==========================================
#  📧 EMAIL FUNCTION (HTML Email Matching Theme)
# ==========================================
def send_email_with_pdf(pdf_filename, data):
    customer_email = data.get('email', '')
    customer_name = data.get('fullName', 'Customer')

    recipients = [COMPANY_EMAIL]
    if customer_email and '@' in customer_email:
        recipients.append(customer_email)

    msg = MIMEMultipart()
    msg['From'] = SYSTEM_EMAIL
    msg['To'] = ", ".join(recipients)
    msg['Reply-To'] = customer_email
    msg['Subject'] = f"Booking Confirmation #{data.get('id')}"

    # --- DARK THEME EMAIL HTML ---
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #0f172a; color: #e2e8f0;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 8px; overflow: hidden; margin-top: 40px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
          
          <div style="background: linear-gradient(to right, #234c6a, #7294ad); padding: 30px; text-align: center;">
            <h1 style="margin: 0; color: white; font-size: 24px; text-transform: uppercase; letter-spacing: 1px;">Raimona Cargo</h1>
            <p style="margin: 5px 0 0; color: #e0f2fe; font-size: 12px; text-transform: uppercase;">Logistics & Transportation</p>
          </div>

          <div style="padding: 40px;">
            <h2 style="color: #ffffff; margin-top: 0;">Booking Confirmed</h2>
            <p style="color: #94a3b8;">Dear {customer_name},</p>
            <p style="color: #cbd5e1; line-height: 1.6;">
              Thank you for choosing Raimona Cargo. Your shipment has been successfully scheduled. 
              Please find your official invoice attached to this email.
            </p>
            
            <div style="background-color: #0f172a; border-radius: 6px; padding: 20px; margin: 20px 0; border: 1px solid #334155;">
              <table style="width: 100%; color: #e2e8f0;">
                <tr>
                  <td style="padding: 8px 0; color: #94a3b8; font-size: 12px; text-transform: uppercase;">Order ID</td>
                  <td style="padding: 8px 0; text-align: right; font-weight: bold;">#{data.get('id')}</td>
                </tr>
                <tr>
                  <td style="padding: 8px 0; color: #94a3b8; font-size: 12px; text-transform: uppercase;">Destination</td>
                  <td style="padding: 8px 0; text-align: right; font-weight: bold;">{data.get('address')}</td>
                </tr>
              </table>
            </div>

            <p style="color: #94a3b8; font-size: 14px; text-align: center;">
              📎 <strong>Your Invoice PDF is attached below.</strong>
            </p>
          </div>

          <div style="background-color: #0f172a; padding: 20px; text-align: center; color: #64748b; font-size: 12px;">
            <p>&copy; 2026 Raimona Cargo. All rights reserved.</p>
          </div>
        </div>
      </body>
    </html>
    """
    msg.attach(MIMEText(html_body, 'html')) 

    with open(pdf_filename, "rb") as f:
        attach = MIMEApplication(f.read(),_subtype="pdf")
        attach.add_header('Content-Disposition','attachment',filename=str(pdf_filename))
        msg.attach(attach)

    try:
        s = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        s.starttls()
        s.login(SYSTEM_EMAIL, SYSTEM_PASSWORD)
        s.send_message(msg)
        s.quit()
        return True
    except Exception as e:
        print(f"Email Error: {e}")
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
        try:
            pdf_file = generate_pdf(data, order_id)
            send_email_with_pdf(pdf_file, data)
            if os.path.exists(pdf_file):
                os.remove(pdf_file)
        except Exception as e:
            print(f"PDF/Email failed but DB saved: {e}")

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