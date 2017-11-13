#!/usr/bin/python3
#
# A proxy for Wikipedia metrics to be exposed in Prometheus
# format.

import http.server
import json
import urllib.request

PORT = 8001
METRICS_URL = "https://en.wikipedia.org/w/api.php?action=query&meta=siteinfo&siprop=statistics&format=json"
BACKLOG_URL = ("https://en.wikipedia.org/w/api.php?action=query&prop=categoryinfo&" +
               "format=json&titles=" + "|".join([
  "Category:All accuracy disputes",
  "Category:Pages missing lead section",
  "Category:Good article nominees"
  "Category:Good article nominees awaiting review"
  ]))

class MetricsHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        metric_json = urllib.request.urlopen(METRICS_URL)
        metric_data = json.loads(metric_json.read().decode())
        self.send_response(200)
        self.end_headers()

        for k in sorted(metric_data["query"]["statistics"]):
            v = metric_data["query"]["statistics"][k]
            k = k.replace("-", "")
            self.wfile.write(bytes("# HELP wikipedia_%s_total Total number of %s\n" % (k, k), "utf8"))
            self.wfile.write(bytes("# TYPE wikipedia_%s_total gauge\n" % k, "utf8"))
            self.wfile.write(bytes("wikipedia_%s_total %s\n\n" % (k, v), "utf8"))

def main():
    server_address = ('', 8001)
    httpd = http.server.HTTPServer(server_address, MetricsHandler)
    httpd.serve_forever()

if __name__ == "__main__":
    main()
