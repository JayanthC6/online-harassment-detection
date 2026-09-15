import requests
from reportlab.pdfgen import canvas
import json

# 1. Create PDF
pdf_path = "suspicious_job_offer.pdf"
c = canvas.Canvas(pdf_path)
c.drawString(100, 750, "Junior Software Developer job offer")
c.drawString(100, 730, "Congratulations! Your salary is ₹50,000/month.")
c.drawString(100, 710, "Your joining date is next week.")
c.drawString(100, 690, "Please pay ₹4,999 refundable processing/registration fee")
c.drawString(100, 670, "Payment required before joining.")
c.drawString(100, 650, "Contact our Telegram recruitment contact immediately.")
c.drawString(100, 630, "For support, reach out on WhatsApp communication.")
c.drawString(100, 610, "There is an urgency to complete onboarding.")
c.save()

# 2. Upload to /predict/file
url = "http://127.0.0.1:5000/predict/file"
files = {'file': open(pdf_path, 'rb')}
r = requests.post(url, files=files)

data = r.json()
print(json.dumps(data, indent=2))

# 3. Create a clean PDF
pdf_path_clean = "clean_job_offer.pdf"
c2 = canvas.Canvas(pdf_path_clean)
c2.drawString(100, 750, "Junior Software Developer job offer")
c2.drawString(100, 730, "Congratulations! Your salary is ₹50,000/month.")
c2.drawString(100, 710, "Your joining date is next week.")
c2.drawString(100, 690, "Our company policy states we NEVER charge a processing fee.")
c2.save()

files_clean = {'file': open(pdf_path_clean, 'rb')}
r2 = requests.post(url, files=files_clean)
print("\n--- CLEAN PDF ---\n")
print(json.dumps(r2.json(), indent=2))
