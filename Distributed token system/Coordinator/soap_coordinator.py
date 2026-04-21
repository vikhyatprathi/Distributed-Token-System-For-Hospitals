from http.server import BaseHTTPRequestHandler, HTTPServer
import json, os

FILE = "bookings.json"

if not os.path.exists(FILE):
    with open(FILE, "w") as f:
        json.dump([], f)

class SOAPHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        length = int(self.headers['Content-Length'])
        data = self.rfile.read(length).decode()

        if "<get_bookings" in data:

            with open(FILE) as f:
                bookings = json.load(f)

            response = f"""<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <get_bookingsResponse>
      <data>{bookings}</data>
    </get_bookingsResponse>
  </soap:Body>
</soap:Envelope>"""

            self.send_response(200)
            self.send_header("Content-Type", "text/xml")
            self.end_headers()
            self.wfile.write(response.encode())

        else:
            self.send_response(400)
            self.end_headers()

if __name__ == "__main__":
    print("SOAP Server running at http://localhost:8000")
    HTTPServer(("0.0.0.0", 8000), SOAPHandler).serve_forever()