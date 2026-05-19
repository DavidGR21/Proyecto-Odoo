FROM odoo:18

USER root

# Dependencias para facturación electrónica SRI Ecuador
RUN pip3 install \
    --break-system-packages \
    --ignore-installed \
    --no-cache-dir \
    zeep \
    python-barcode[images] \
    python-stdnum

USER odoo