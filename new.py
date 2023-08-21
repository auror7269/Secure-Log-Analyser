import os
import json
from flask import Flask, render_template, request, redirect, url_for
from termcolor import colored
from transformers import pipeline
from docx2txt import process
# from pdfminer.high_level import extract_text

app = Flask(__name__)

model = pipeline(task="text-classification", model="nlptown/bert-base-multilingual-uncased-sentiment")

iso27001_controls = {
    "Access Control": ["access control", "authentication", "authorization", "user access", "access request"],
    "Information Security Policy": ["policy document", "security policy", "information security", "policy compliance"],
    "Asset Management": ["asset management", "asset inventory", "hardware inventory", "software inventory"],
    "Human Resource Security": ["human resource security", "employee training", "background checks", "employee onboarding"],
    "Physical and Environmental Security": ["physical security", "environmental security", "security cameras", "access points"],
    "Communications and Operations Management": ["communications security", "operations management", "incident response", "business continuity"],
    "Information Systems Acquisition, Development, and Maintenance": ["system acquisition", "software development", "system maintenance", "vendor assessment"],
    "Cryptography": ["cryptography", "encryption", "decryption", "key management"],
    "Supplier Relationships": ["supplier relationships", "third-party vendors", "vendor assessment", "supplier contracts"],
    "Security Awareness and Training": ["security awareness", "training program", "employee education", "security culture"],
}

def analyze_log(log_text):
    result = model(log_text)[0]
    sentiment = result["label"]
    return sentiment

def check_compliance(log_text):
    compliance_results = {}
    for control, keywords in iso27001_controls.items():
        if any(keyword in log_text.lower() for keyword in keywords):
            compliance_results[control] = True
        else:
            compliance_results[control] = False
    return compliance_results

# def process_pdf(pdf_path):
#     pdf_text = extract_text(pdf_path)
#     return pdf_text

def process_docx(docx_path):
    return process(docx_path)

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            return redirect(request.url)

        if file.filename.endswith(".log"):
            logs = file.read().decode("utf-8").split('\n')
        elif file.filename.endswith(".pdf"):
            pdf_text = process_pdf(file)
            logs = pdf_text.split('\n')
        else:
            return "Please upload a .log or .pdf file."

        compliance_report = []

        for idx, log in enumerate(logs):
            log = log.strip()
            sentiment = analyze_log(log)
            compliance_results = check_compliance(log)

            if all(compliant for compliant in compliance_results.values()):
                color = "green"
            else:
                color = "red"

            colored_log = colored(log, color)
            log_report = {
                "log_entry": log,
                "sentiment": sentiment,
                "compliance_results": compliance_results
            }
            compliance_report.append(log_report)

        report_filename = os.path.splitext(file.filename)[0] + "_iso27001_compliance_report.json"
        with open(report_filename, "w") as report_file:
            json.dump(compliance_report, report_file, indent=4)

        return render_template("results.html", report_filename=report_filename)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
