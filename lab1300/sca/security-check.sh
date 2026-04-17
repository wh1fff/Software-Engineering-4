#!/bin/bash

echo "Running npm audit..."
npm audit --audit-level=moderate

if [ $? -ne 0 ]; then
    echo "❌ Vulnerabilities found"
    exit 1
fi

echo "Running OWASP ZAP..."
docker run -v $(pwd):/zap/wrk -t owasp/zap2docker-stable \
    zap-baseline.py -t http://localhost:3000 \
    -r zap_report.html

echo "✅ Security checks passed"