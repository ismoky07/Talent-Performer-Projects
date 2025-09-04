import csv

# Data to be written into the CSV file
rows = [
    ["iPhone", "Jojo Phone", "iPhone 11", 4500, "د.م.", None, "https://jojophone.ma/produit/iphone-11/", "The iPhone 11 includes a dual camera module and an A13 Bionic processor.", None, None, None],
    ["iPhone", "iSTYLE", "iPhone 16", 512, "د.م.", None, "https://istyle.ma/iphone/iphone-16.html", "iPhone 16 with expert support and special education discounts.", None, "24h to Casablanca", None],
    ["iPhone", "Amazon", None, None, None, None, "https://www.amazon.com/iPhone-Straight-Outta-Casablanca-Morocco/dp/B0CNS8KL8S", None, None, None, None]
]

# Define CSV file column headers
headers = ["Product Name", "Vendor Name", "Product Title", "Price", "Currency", "Bulk Discounts or Deals", "Vendor Website", "Short Product Description", "Minimum Order Quantity", "Shipping Time", "Vendor Location"]

# Writing to csv file
with open('data.csv', 'w', newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(headers)  # Write the header
    csvwriter.writerows(rows)  # Write the data rows