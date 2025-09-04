import csv

data = [
    {
        "Product Name": "Bananas",
        "Vendor Name": "United States",
        "Product Title": "Bananas",
        "Price": 1.50,
        "Currency": "USD",
        "Vendor Website": "https://www.e-fresco.io/bananas-4dqa.html",
        "Short Product Description": "Bananas for retailers, available through an online platform.",
        "Minimum Order Quantity": "",
        "Shipping Time": "",
        "Bulk Discounts or Deals": "",
        "Vendor Location": "United States"
    },
    {
        "Product Name": "",
        "Vendor Name": "Wali Trading",
        "Product Title": "",
        "Price": "",
        "Currency": "",
        "Vendor Website": "https://wali-trading.com/",
        "Short Product Description": "Offers a wide range of fruits, including bananas, from Morocco.",
        "Minimum Order Quantity": "",
        "Shipping Time": "",
        "Bulk Discounts or Deals": "",
        "Vendor Location": "Morocco"
    },
    {
        "Product Name": "",
        "Vendor Name": "Zenkal Trading SARL",
        "Product Title": "",
        "Price": "",
        "Currency": "",
        "Vendor Website": "https://www.zenkaltrading.com/",
        "Short Product Description": "Global exporter of fresh fruits and vegetables, offering various products from Morocco.",
        "Minimum Order Quantity": "",
        "Shipping Time": "",
        "Bulk Discounts or Deals": "",
        "Vendor Location": "Casablanca, MA"
    },
    {
        "Product Name": "Pomme products",
        "Vendor Name": "Pomme de Pain Maroc",
        "Product Title": "",
        "Price": "",
        "Currency": "",
        "Vendor Website": "https://www.linkedin.com/company/pomme-de-pain-maroc",
        "Short Product Description": "Offers a variety of pomme (apple) products along with other fresh items.",
        "Minimum Order Quantity": "",
        "Shipping Time": "",
        "Bulk Discounts or Deals": "",
        "Vendor Location": "Casablanca, MA"
    }
]

# Create CSV
with open('data.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ["Product Name", "Vendor Name", "Product Title", "Price", "Currency", "Bulk Discounts or Deals", "Vendor Website", "Short Product Description", "Minimum Order Quantity", "Shipping Time", "Vendor Location"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for entry in data:
        writer.writerow(entry)