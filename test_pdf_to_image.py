from pdf2image import convert_from_path

# Replace 'your_file.pdf' with your actual PDF file name
images = convert_from_path("invoice.pdf")

# Save first page as JPEG
images[0].save("page1.jpg", "JPEG")

print("Image saved successfully!")
