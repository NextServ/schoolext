# Copyright (c) 2023, SERVIO Enterprise and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

# SERVICE_PRODUCTION_BASE_URL = "https://gw.dragonpay.ph/api/collect/v1"
SERVICE_PRODUCTION_BASE_URL = "https://test.dragonpay.ph/api/collect/v1"
SERVICE_TEST_BASE_URL = "https://test.dragonpay.ph/api/collect/v1"

STATUS_CODES = {
        "S": "Success",
        "F": "Failure",
        "P": "Pending",
        "U": "Unknown",
        "R": "Refund",
        "K": "Chargeback",
        "V": "Void",
        "A": "Authorized"
    }

class DragonPaySettings(Document):
    pass

