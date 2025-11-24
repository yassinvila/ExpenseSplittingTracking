# Centsible
![logo](https://github.com/Halila2727/ExpenseSplittingTracking/blob/main/images/CentsibleLogoAlternate.png)
## The Idea:
We are aiming to create a web app which allows groups to input their expenses and split them among the group based on various settings they have set.
Users will be able to configure the way expenses are split among the group in order to make cost-sharing simple and transparent.

## Team Members:
	- Ahnaf Ahmed
	- Halil Akca
	- Justin Zeng
	- Tony Lin
	- Zara Amer

## Technologies Used:
	Front End: HTML, CSS, Javascript
	Back End: Python
	Database: PostgreSQL

## Setting Up

<a href = "https://www.python.org/downloads" target="_blank">**Python**  
<a href = "https://nodejs.org/en" target ="_blank">**Node**

Installing python from the website should come with pip3. Next, in  Powershell, type:
```
	pip install flask fastapi uvicorn sqlalchemy python-dotenv requests
```
For node, in WSL or linux equivalent, enter:
```
	sudo apt install nodejs npm -y
```
or install it through instructions on the official website, linked above.

### Receipt OCR & Attachments
- Install system binaries so PDF/image OCR works:
  ```
  sudo apt install tesseract-ocr poppler-utils
  ```
- Install new backend dependencies (pytesseract, pdf2image, Pillow) with `pip install -r backend/requirements.txt`.
- Uploaded files are stored under `backend/uploads/expenses/<expense_id>/`. When you're ready to switch to cloud storage, only the upload helper in `backend/app.py` needs to change.

## Minimum Viable Product Goals:
	- Account Registration
	- Automatic Balance Calculation
	- Categorized Expenses
	- Expense Logging
	- Group Creation
	- Payment Tracking

## Stretch Goals:
	- Receipt Scanning
	- Alerts and Reminders
	- Export Reports
